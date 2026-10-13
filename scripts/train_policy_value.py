#!/usr/bin/env python3
"""Train the small policy/value model on generated JSONL.GZ decisions."""

from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import re
import sys
import time
from collections import OrderedDict, defaultdict
from functools import partial
from pathlib import Path

try:
    import orjson as _fast_json
except ImportError:
    _fast_json = None

def _loads(line):
    return _fast_json.loads(line) if _fast_json is not None else json.loads(line)


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch
import torch.nn.functional as F
from torch.nn.utils.rnn import pad_sequence
from torch.utils.data import DataLoader, Dataset, Sampler, Subset

from hsa.encoding import compatible_feature_schema
from hsa.torch_model import (
    BilinearPolicyValueNet,
    InteractionPolicyValueNet,
    JointEntityPolicyValueNet,
    PolicyValueNet,
    ResidualPolicyValueNet,
    StructuredResidualPolicyValueNet,
)
from hsa.training import (
    temperature_scale_probabilities,
    value_weighted_policy_target,
)


class _LazyRecordView:
    def __init__(self, dataset: "DecisionDataset"):
        self.dataset = dataset

    def __len__(self):
        return len(self.dataset._index)

    def __getitem__(self, index):
        return self.dataset[index]

    def __iter__(self):
        for index in range(len(self)):
            yield self[index]


class DecisionDataset(Dataset):
    def __init__(self, paths: list[Path], max_records: int | None = None,
                 allow_mixed_rulesets: bool = False,
                 index_cache: Path | None = None):
        # Keep only lightweight locations/labels in memory.  The old loader
        # retained every decoded JSON dict, which expanded a 70 MB dataset to
        # well over 100 GB.  Records are decoded a file at a time on demand.
        self._index = []
        self._actors = []
        self._winner_by_seed = {}
        self._file_cache = OrderedDict()
        # A single matchup file can contain many thousands of decisions and
        # decoding several files at once defeats the purpose of the lazy
        # loader.  Keep one decoded file resident; the training iterator still
        # makes progress while peak RSS stays bounded by the largest shard.
        self._max_cached_files = 1
        self.headers = []
        source_signature = [
            (str(path), path.stat().st_size, path.stat().st_mtime_ns)
            for path in paths
        ]
        if index_cache is not None and index_cache.exists():
            cached = torch.load(index_cache, map_location="cpu", weights_only=False)
            if (
                cached.get("source_signature") == source_signature
                and cached.get("max_records") == max_records
                and cached.get("allow_mixed_rulesets") == allow_mixed_rulesets
            ):
                self._index = [
                    (Path(path), int(row), int(seed))
                    for path, row, seed in cached["index"]
                ]
                self._actors = [int(value) for value in cached["actors"]]
                self._winner_by_seed = {
                    int(seed): winner
                    for seed, winner in cached["winner_by_seed"].items()
                }
                self.headers = cached["headers"]
                self.header = self.headers[0]
                self.records = _LazyRecordView(self)
                print(
                    f"loaded decision index cache: {len(self._index)} records, "
                    f"{len(self._winner_by_seed)} games",
                    flush=True,
                )
                return
        for path_number, path in enumerate(paths, start=1):
            if path.suffix == ".pt":
                metadata_path = path.with_suffix(".meta.json")
                shared_header_path = path.parent / "_header.json"
                if metadata_path.exists() and shared_header_path.exists():
                    if not self.headers:
                        self.headers.append(_loads(shared_header_path.read_bytes()))
                    metadata = _loads(metadata_path.read_bytes())
                    for row, (seed, actor, raw_winner) in enumerate(zip(
                        metadata["game_seed"], metadata["actor"],
                        metadata["winner"], strict=True,
                    )):
                        if max_records is not None and len(self._index) >= max_records:
                            break
                        winner = None if int(raw_winner) < 0 else int(raw_winner)
                        self._index.append((path, row, int(seed)))
                        self._actors.append(int(actor))
                        self._winner_by_seed.setdefault(int(seed), winner)
                    if max_records is not None and len(self._index) >= max_records:
                        break
                    if path_number % 64 == 0 or path_number == len(paths):
                        print(
                            f"indexed {path_number}/{len(paths)} tensor shards: "
                            f"{len(self._index)} decision records",
                            flush=True,
                        )
                    continue
                payload = torch.load(path, map_location="cpu", weights_only=False)
                header = payload.get("header", self.headers[0] if self.headers else {})
                if not self.headers:
                    self.headers.append(header)
                if "records" in payload:
                    records = payload["records"]
                else:
                    n = int(payload["count"])
                    records = [None] * n
                for row, record in enumerate(records):
                    if max_records is not None and len(self._index) >= max_records:
                        break
                    if record is not None:
                        seed = int(record.get("game_seed", 0))
                        actor = int(record.get("actor", 0))
                        winner = record.get("winner")
                    else:
                        seed_values = payload.get("game_seed")
                        actor_values = payload.get("actor")
                        winner_values = payload.get("winner")
                        seed = int(seed_values[row]) if seed_values is not None else 0
                        actor = int(actor_values[row]) if actor_values is not None else 0
                        raw_winner = (
                            int(winner_values[row]) if winner_values is not None else -1
                        )
                        winner = None if raw_winner < 0 else raw_winner
                    self._index.append((path, row, seed))
                    self._actors.append(actor)
                    self._winner_by_seed.setdefault(seed, winner)
                del payload
                if max_records is not None and len(self._index) >= max_records:
                    break
                continue
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                header = _loads(next(handle))
                if self.headers and not compatible_feature_schema(
                    header["feature_schema"], self.headers[0]["feature_schema"]
                ):
                    raise ValueError("all datasets must use the same feature schema")
                if self.headers and (
                    header.get("ruleset") != self.headers[0].get("ruleset")
                ):
                    raise ValueError("all datasets must use the same ruleset")
                if (not allow_mixed_rulesets) and self.headers and (
                    header.get("ruleset_fingerprint")
                    != self.headers[0].get("ruleset_fingerprint")
                ):
                    raise ValueError("all datasets must use the same ruleset fingerprint")
                if not self.headers:
                    self.headers.append(header)
                for line_no, line in enumerate(handle, start=2):
                    if max_records is not None and len(self._index) >= max_records:
                        break
                    # Avoid decoding the very large state/action arrays while
                    # building the index.  Full JSON decoding is deferred to
                    # _load_file/__getitem__.
                    if '"record_type":"decision"' not in line and '"record_type": "decision"' not in line:
                        continue
                    match = re.search(r'"game_seed"\s*:\s*(-?\d+)', line)
                    if match is not None:
                        game_seed = int(match.group(1))
                        actor_match = re.search(r'"actor"\s*:\s*(-?\d+)', line)
                        winner_match = re.search(
                            r'"winner"\s*:\s*(null|-?\d+)', line
                        )
                        actor = int(actor_match.group(1)) if actor_match else 0
                        winner = None
                        if winner_match and winner_match.group(1) != "null":
                            winner = int(winner_match.group(1))
                        self._index.append((path, line_no, game_seed))
                        self._actors.append(actor)
                        self._winner_by_seed.setdefault(game_seed, winner)
            if max_records is not None and len(self._index) >= max_records:
                break
            if path_number % 16 == 0 or path_number == len(paths):
                print(
                    f"indexed {path_number}/{len(paths)} shards: "
                    f"{len(self._index)} decision records",
                    flush=True,
                )
        self.header = self.headers[0]
        self.records = _LazyRecordView(self)
        if not self._index:
            raise ValueError("dataset contains no decision records")
        if index_cache is not None:
            index_cache.parent.mkdir(parents=True, exist_ok=True)
            temporary = index_cache.with_suffix(index_cache.suffix + ".tmp")
            torch.save(
                {
                    "source_signature": source_signature,
                    "max_records": max_records,
                    "allow_mixed_rulesets": allow_mixed_rulesets,
                    "index": [
                        (str(path), row, seed) for path, row, seed in self._index
                    ],
                    "actors": self._actors,
                    "winner_by_seed": self._winner_by_seed,
                    "headers": self.headers,
                },
                temporary,
            )
            temporary.replace(index_cache)
            print(f"saved decision index cache: {index_cache}", flush=True)

    def game_seeds(self) -> list[int]:
        return sorted({entry[2] for entry in self._index})

    def winner_by_seed(self) -> dict[int, int | None]:
        return dict(self._winner_by_seed)

    def __len__(self) -> int:
        return len(self._index)

    def __getitem__(self, index: int):
        path, line_no, _seed = self._index[index]
        records = self._load_file(path)
        return records[line_no]

    def _load_file(self, path: Path):
        cached = self._file_cache.get(path)
        if cached is not None:
            self._file_cache.move_to_end(path)
            return cached
        if path.suffix == ".pt":
            payload = torch.load(path, map_location="cpu", weights_only=False)
            if "records" in payload:
                records = payload["records"]
            else:
                records = []
                for i in range(int(payload["count"])):
                    count = int(payload["mask"][i].sum().item())
                    records.append({
                        "_columnar_payload": payload,
                        "_columnar_row": i,
                        "state": payload["states"][i],
                        "actions": payload["actions"][i, :count],
                        "chosen_action": int(payload["chosen"][i]),
                        "value_target": float(payload["values"][i]),
                        "policy_target": payload["policy_targets"][i, :count],
                        "teacher_action_values": (
                            payload["teacher_action_values"][i, :count]
                            if "teacher_action_values" in payload else None
                        ),
                        "teacher_action_value_mask": (
                            payload["teacher_action_value_mask"][i, :count]
                            if "teacher_action_value_mask" in payload else None
                        ),
                        "game_seed": int(payload.get("game_seed", torch.zeros(1, dtype=torch.int64))[i]),
                        "winner": (None if int(payload.get("winner", torch.full((1,), -1, dtype=torch.int8))[i]) < 0 else int(payload["winner"][i])),
                        "actor": int(payload.get("actor", torch.zeros(1, dtype=torch.int8))[i]),
                    })
            self._file_cache[path] = records
            self._file_cache.move_to_end(path)
            while len(self._file_cache) > self._max_cached_files:
                self._file_cache.popitem(last=False)
            return records
        records = {}
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            next(handle, None)
            for line_no, line in enumerate(handle, start=2):
                record = _loads(line)
                if record.get("record_type") == "decision":
                    records[line_no] = record
        self._file_cache[path] = records
        self._file_cache.move_to_end(path)
        while len(self._file_cache) > self._max_cached_files:
            self._file_cache.popitem(last=False)
        return records


class ShardBatchSampler(Sampler[list[int]]):
    """Yield batches grouped by source shard.

    DecisionDataset lazily decodes one gzip shard at a time.  A normal
    ``shuffle=True`` DataLoader defeats that cache by interleaving indices
    from every shard, repeatedly decompressing the same files.  Grouping
    batches by shard preserves stochasticity within each shard while making
    each compressed file be decoded once per epoch.
    """

    def __init__(
        self, dataset: DecisionDataset, batch_size: int, seed: int,
        indices: list[int] | None = None,
    ):
        self.batch_size = int(batch_size)
        self.seed = int(seed)
        groups: dict[Path, list[int]] = defaultdict(list)
        source_indices = (
            range(len(dataset._index)) if indices is None else indices
        )
        for index in source_indices:
            path, _line_no, _game_seed = dataset._index[index]
            groups[path].append(index)
        self.groups = [
            (path.suffix == ".pt", indices) for path, indices in groups.items()
        ]

    def __iter__(self):
        rng = random.Random(self.seed)
        groups = list(self.groups)
        rng.shuffle(groups)
        for is_tensor, indices in groups:
            indices = list(indices)
            # Tensor shards are already randomized during game generation and
            # are sized to one training batch.  Keep their row order so the
            # collator can return zero-copy contiguous tensor views.
            if not is_tensor:
                rng.shuffle(indices)
            for start in range(0, len(indices), self.batch_size):
                yield indices[start : start + self.batch_size]
        self.seed += 1

    def __len__(self):
        return sum(
            (len(indices) + self.batch_size - 1) // self.batch_size
            for _is_tensor, indices in self.groups
        )


def collate_decisions(
    records: list[dict], *, hard_policy_targets: bool = False,
    policy_target_temperature: float = 1.0,
    value_weighted_targets: bool = False,
    policy_value_temperature: float = 0.5,
    include_action_values: bool = False,
):
    if policy_target_temperature <= 0:
        raise ValueError("policy target temperature must be positive")
    payload = records[0].get("_columnar_payload")
    if payload is not None and all(
        record.get("_columnar_payload") is payload for record in records
    ) and not value_weighted_targets:
        row_numbers = [record["_columnar_row"] for record in records]
        contiguous = row_numbers == list(range(
            row_numbers[0], row_numbers[0] + len(row_numbers)
        ))
        if contiguous:
            selection = slice(row_numbers[0], row_numbers[0] + len(row_numbers))
            select = lambda tensor: tensor[selection]
        else:
            rows = torch.tensor(row_numbers, dtype=torch.long)
            select = lambda tensor: tensor.index_select(0, rows)
        full_mask = select(payload["mask"])
        max_actions = int(full_mask.sum(dim=1).max().item())
        mask = full_mask[:, :max_actions]
        states = select(payload["states"]).float()
        actions = select(payload["actions"])[:, :max_actions].float()
        chosen = select(payload["chosen"]).long()
        values = select(payload["values"]).float()
        if hard_policy_targets:
            policy_targets = torch.zeros(mask.shape, dtype=torch.float32)
            policy_targets.scatter_(1, chosen.unsqueeze(1), 1.0)
        else:
            policy_targets = select(
                payload["policy_targets"]
            )[:, :max_actions].float().clamp_min(0.0)
            if policy_target_temperature != 1.0:
                policy_targets.pow_(1.0 / policy_target_temperature)
            policy_targets.masked_fill_(~mask, 0.0)
            totals = policy_targets.sum(dim=1, keepdim=True)
            if bool((totals <= 0).any().item()):
                raise ValueError(
                    "policy target must contain positive probability mass"
                )
            policy_targets.div_(totals)
        result = (states, actions, mask, chosen, values, policy_targets)
        if not include_action_values:
            return result
        action_values = select(
            payload["teacher_action_values"]
        )[:, :max_actions].float()
        action_value_mask = select(
            payload["teacher_action_value_mask"]
        )[:, :max_actions]
        return result + (action_values, action_value_mask)
    if torch.is_tensor(records[0]["state"]) and not value_weighted_targets:
        states = torch.stack([record["state"] for record in records]).float()
        action_rows = [record["actions"].float() for record in records]
        actions = pad_sequence(action_rows, batch_first=True)
        lengths = torch.tensor([len(row) for row in action_rows], dtype=torch.long)
        mask = torch.arange(actions.shape[1]).unsqueeze(0) < lengths.unsqueeze(1)
        chosen = torch.tensor(
            [int(record["chosen_action"]) for record in records], dtype=torch.long
        )
        values = torch.tensor(
            [float(record["value_target"]) for record in records],
            dtype=torch.float32,
        )
        policy_targets = torch.zeros(mask.shape, dtype=torch.float32)
        if hard_policy_targets:
            policy_targets.scatter_(1, chosen.unsqueeze(1), 1.0)
        else:
            raw_policy = pad_sequence([
                record["policy_target"].float() for record in records
            ], batch_first=True).clamp_min_(0.0)
            if policy_target_temperature != 1.0:
                raw_policy.pow_(1.0 / policy_target_temperature)
            raw_policy.masked_fill_(~mask, 0.0)
            totals = raw_policy.sum(dim=1, keepdim=True)
            if bool((totals <= 0).any().item()):
                raise ValueError(
                    "policy target must contain positive probability mass"
                )
            policy_targets = raw_policy / totals
        result = (states, actions, mask, chosen, values, policy_targets)
        if not include_action_values:
            return result
        q_rows = []
        q_mask_rows = []
        for record in records:
            q_values = record.get("teacher_action_values")
            if q_values is None:
                q_values = torch.zeros(len(record["actions"]), dtype=torch.float32)
                q_mask = torch.zeros(len(record["actions"]), dtype=torch.bool)
            else:
                q_values = q_values.float()
                q_mask = record.get("teacher_action_value_mask")
                if q_mask is None:
                    visits = record.get("teacher_action_visits")
                    q_mask = (
                        torch.ones(len(q_values), dtype=torch.bool)
                        if visits is None else torch.as_tensor(visits, dtype=torch.long) > 0
                    )
                else:
                    q_mask = q_mask.bool()
            q_rows.append(q_values)
            q_mask_rows.append(q_mask)
        action_values = pad_sequence(q_rows, batch_first=True)
        action_value_mask = pad_sequence(q_mask_rows, batch_first=True)
        return result + (action_values, action_value_mask)
    state_size = len(records[0]["state"])
    action_size = len(records[0]["actions"][0])
    max_actions = max(len(record["actions"]) for record in records)
    states = torch.zeros((len(records), state_size), dtype=torch.float32)
    actions = torch.zeros(
        (len(records), max_actions, action_size), dtype=torch.float32
    )
    mask = torch.zeros((len(records), max_actions), dtype=torch.bool)
    chosen = torch.empty(len(records), dtype=torch.long)
    values = torch.empty(len(records), dtype=torch.float32)
    policy_targets = torch.zeros((len(records), max_actions), dtype=torch.float32)
    action_values = torch.zeros((len(records), max_actions), dtype=torch.float32)
    action_value_mask = torch.zeros((len(records), max_actions), dtype=torch.bool)
    for row, record in enumerate(records):
        count = len(record["actions"])
        states[row] = torch.as_tensor(record["state"], dtype=torch.float32)
        actions[row, :count] = torch.as_tensor(
            record["actions"], dtype=torch.float32
        )
        mask[row, :count] = True
        teacher_values = record.get("teacher_action_values")
        if teacher_values is not None:
            limit_q = min(count, len(teacher_values))
            if limit_q:
                action_values[row, :limit_q] = torch.as_tensor(
                    teacher_values[:limit_q], dtype=torch.float32
                )
                teacher_mask = record.get("teacher_action_value_mask")
                if teacher_mask is None:
                    visits = record.get("teacher_action_visits")
                    if visits is None:
                        action_value_mask[row, :limit_q] = True
                    else:
                        if len(visits) < limit_q:
                            raise ValueError("action-Q visits shorter than action-Q values")
                        action_value_mask[row, :limit_q] = torch.as_tensor(
                            [count > 0 for count in visits[:limit_q]],
                            dtype=torch.bool,
                        )
                else:
                    action_value_mask[row, :limit_q] = torch.as_tensor(
                        teacher_mask[:limit_q], dtype=torch.bool
                    )
        chosen[row] = int(record["chosen_action"])
        values[row] = float(record["value_target"])
        target = None if hard_policy_targets else record.get("policy_target")
        if target is None:
            policy_targets[row, chosen[row]] = 1.0
        else:
            if value_weighted_targets:
                teacher_action_values = record.get("teacher_action_values")
                if teacher_action_values is None:
                    raise ValueError(
                        "value-weighted targets require teacher_action_values"
                    )
                target = value_weighted_policy_target(
                    target, teacher_action_values, policy_value_temperature
                )
            if torch.is_tensor(target):
                probabilities = target.to(dtype=torch.float32).clamp_min(0.0)
                if policy_target_temperature != 1.0:
                    probabilities = probabilities.pow(
                        1.0 / policy_target_temperature
                    )
                probability_sum = probabilities.sum()
                if float(probability_sum) <= 0:
                    raise ValueError(
                        "policy target must contain positive probability mass"
                    )
                probabilities = probabilities / probability_sum
            else:
                probabilities = torch.as_tensor(
                    temperature_scale_probabilities(
                        target, policy_target_temperature
                    ),
                    dtype=torch.float32,
                )
            # Older/shortened records can contain a policy target whose
            # length does not match the current action list (for example
            # after legal-action canonicalisation).  Keep the aligned
            # prefix and renormalise it instead of failing the whole batch.
            aligned = torch.zeros(count, dtype=torch.float32)
            limit = min(count, int(probabilities.numel()))
            if limit:
                aligned[:limit] = probabilities[:limit]
                total = float(aligned.sum())
                if total > 0:
                    aligned /= total
            policy_targets[row, :count] = aligned
    result = (states, actions, mask, chosen, values, policy_targets)
    return result + (action_values, action_value_mask) if include_action_values else result


def choose_device(requested: str) -> torch.device:
    if requested == "cpu":
        return torch.device("cpu")
    try:
        import torch_npu  # noqa: F401
        available = torch.npu.is_available()
    except (ImportError, AttributeError):
        available = False
    if requested == "npu" and not available:
        raise RuntimeError("NPU requested but torch-npu is unavailable")
    return torch.device("npu:0" if available else "cpu")


def evaluate(model, loader, device):
    was_training = model.training
    model.eval()
    correct = count = policy_count = 0
    absolute_error = 0.0
    squared_error = 0.0
    policy_cross_entropy = 0.0
    policy_target_entropy = 0.0
    action_q_count = 0
    action_q_absolute_error = 0.0
    action_q_squared_error = 0.0
    with torch.no_grad():
        for batch in loader:
            states, actions, mask, chosen, targets, policy_targets = batch[:6]
            states, actions, mask = states.to(device), actions.to(device), mask.to(device)
            chosen, targets = chosen.to(device), targets.to(device)
            policy_targets = policy_targets.to(device)
            if len(batch) >= 8:
                logits, values, action_q = model.forward_with_action_values(
                    states, actions, mask
                )
                q_targets, q_mask = batch[6].to(device), batch[7].to(device)
                q_valid = q_mask & mask
                if bool(q_valid.any().item()):
                    q_error = action_q[q_valid] - q_targets[q_valid]
                    action_q_count += int(q_valid.sum().item())
                    action_q_absolute_error += float(q_error.abs().sum().item())
                    action_q_squared_error += float(q_error.square().sum().item())
            else:
                logits, values = model(states, actions, mask)
            log_probabilities = F.log_softmax(logits, dim=1)
            nontrivial = mask.sum(dim=1) > 1
            correct += int(
                ((logits.argmax(dim=1) == chosen) & nontrivial).sum().item()
            )
            policy_count += int(nontrivial.sum().item())
            count += len(chosen)
            absolute_error += float((values - targets).abs().sum().item())
            squared_error += float(((values - targets) ** 2).sum().item())
            row_cross_entropy = -(policy_targets * log_probabilities).sum(dim=1)
            policy_cross_entropy += float(row_cross_entropy[nontrivial].sum().item())
            target_logs = torch.where(
                policy_targets > 0,
                torch.log(policy_targets.clamp_min(1e-12)),
                torch.zeros_like(policy_targets),
            )
            row_target_entropy = -(policy_targets * target_logs).sum(dim=1)
            policy_target_entropy += float(
                row_target_entropy[nontrivial].sum().item()
            )
    cross_entropy = policy_cross_entropy / max(1, policy_count)
    target_entropy = policy_target_entropy / max(1, policy_count)
    value_mse = squared_error / count
    metrics = {
        "policy_decisions": policy_count,
        "forced_decisions": count - policy_count,
        "policy_accuracy": correct / max(1, policy_count),
        "policy_cross_entropy": cross_entropy,
        "policy_target_entropy": target_entropy,
        "policy_kl": max(0.0, cross_entropy - target_entropy),
        "value_mae": absolute_error / count,
        "value_mse": value_mse,
        # Targets and predictions are mapped from [-1, 1] to win probability.
        "value_brier": value_mse / 4.0,
        "action_q_count": action_q_count,
        "action_q_mae": (
            action_q_absolute_error / action_q_count
            if action_q_count else None
        ),
        "action_q_mse": (
            action_q_squared_error / action_q_count
            if action_q_count else None
        ),
    }
    model.train(was_training)
    return metrics


def winner_counts(dataset, indices: list[int]) -> dict[str, int]:
    """Count complete games by winner without weighting long games more."""
    selected_seeds = {dataset._index[index][2] for index in indices}
    winners = {
        game_seed: dataset._winner_by_seed.get(game_seed)
        for game_seed in selected_seeds
    }
    counts = {"player_0": 0, "player_1": 0, "draw": 0}
    for winner in winners.values():
        key = "draw" if winner is None else f"player_{int(winner)}"
        counts[key] += 1
    return counts


def actor_metrics(model, dataset, indices, collate, batch_size, device):
    """Report policy/value generalization separately for each acting seat."""
    result = {}
    for actor in (0, 1):
        actor_indices = [
            index for index in indices
            if dataset._actors[index] == actor
        ]
        if not actor_indices:
            result[f"player_{actor}"] = None
            continue
        loader = DataLoader(
            Subset(dataset, actor_indices), batch_size=batch_size,
            shuffle=False, collate_fn=collate, num_workers=0,
        )
        result[f"player_{actor}"] = evaluate(model, loader, device)
    return result


def stratified_validation_seeds(
    records: list[dict], validation_ratio: float, seed: int
) -> set[int]:
    """Split complete games while approximately preserving winner balance."""
    winner_by_seed = {}
    for record in records:
        winner_by_seed.setdefault(record["game_seed"], record.get("winner"))
    if len(winner_by_seed) <= 1 or validation_ratio <= 0:
        return set()
    buckets: dict[object, list[int]] = defaultdict(list)
    for game_seed, winner in winner_by_seed.items():
        buckets[winner].append(game_seed)
    rng = random.Random(seed)
    selected: set[int] = set()
    for winner in sorted(buckets, key=lambda value: str(value)):
        game_seeds = sorted(buckets[winner])
        rng.shuffle(game_seeds)
        count = round(len(game_seeds) * validation_ratio)
        if len(game_seeds) > 1:
            count = min(len(game_seeds) - 1, max(1, count))
        else:
            count = 0
        selected.update(game_seeds[:count])
    if not selected:
        selected.add(sorted(winner_by_seed)[0])
    return selected


def stratified_validation_seed_map(
    winner_by_seed: dict[int, int | None], validation_ratio: float, seed: int
) -> set[int]:
    """Split complete games using metadata captured by the lazy index."""
    if len(winner_by_seed) <= 1 or validation_ratio <= 0:
        return set()
    buckets: dict[object, list[int]] = defaultdict(list)
    for game_seed, winner in winner_by_seed.items():
        buckets[winner].append(game_seed)
    rng = random.Random(seed)
    selected: set[int] = set()
    for winner in sorted(buckets, key=lambda value: str(value)):
        game_seeds = sorted(buckets[winner])
        rng.shuffle(game_seeds)
        count = round(len(game_seeds) * validation_ratio)
        if len(game_seeds) > 1:
            count = min(len(game_seeds) - 1, max(1, count))
        else:
            count = 0
        selected.update(game_seeds[:count])
    if not selected:
        selected.add(sorted(winner_by_seed)[0])
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, nargs="+",
        default=[ROOT / "reports" / "policy-value-smoke.jsonl.gz"],
    )
    parser.add_argument(
        "--validation-data", type=Path, nargs="+",
        help=(
            "Independent held-out data. When supplied it replaces the internal "
            "random game split for checkpoint selection and reported validation."
        ),
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "policy-value-smoke.pt",
    )
    parser.add_argument("--device", choices=("auto", "cpu", "npu"), default="auto")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument(
        "--checkpoint-every", type=int, default=0,
        help="Save a resumable epoch checkpoint every N epochs; 0 disables.",
    )
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-2)
    parser.add_argument("--gradient-clip", type=float, default=1.0)
    parser.add_argument("--value-weight", type=float, default=0.5)
    parser.add_argument("--action-q-weight", type=float, default=0.25)
    parser.add_argument("--policy-weight", type=float, default=1.0)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--hidden-size", type=int, default=256)
    parser.add_argument("--action-hidden-size", type=int, default=128)
    parser.add_argument(
        "--architecture",
        choices=(
            "additive-v1", "interaction-v2", "bilinear-v3", "residual-v4",
            "structured-v5", "structured-v5-action-q", "jev-v6-action-q",
            "jev-v7-action-q",
        ),
        default="additive-v1",
        help="Policy head architecture; interaction-v2 models state-action fit.",
    )
    parser.add_argument("--max-records", type=int)
    parser.add_argument(
        "--index-cache", type=Path,
        help="Reusable lightweight seed/actor/winner index for compressed shards.",
    )
    parser.add_argument(
        "--allow-mixed-rulesets", action="store_true",
        help="Allow compatible shards produced by successive ruleset revisions.",
    )
    parser.add_argument(
        "--init-checkpoint", type=Path,
        help="Warm-start from a checkpoint with the same architecture and feature schema.",
    )
    parser.add_argument(
        "--anchor-checkpoint", type=Path,
        help=(
            "Frozen compatible champion used for policy/value distillation while "
            "training on new teacher data."
        ),
    )
    parser.add_argument(
        "--anchor-policy-kl-weight", type=float, default=0.0,
        help="Weight for KL(anchor policy || student policy).",
    )
    parser.add_argument(
        "--anchor-value-weight", type=float, default=0.0,
        help="Weight for MSE between student and frozen anchor values.",
    )
    parser.add_argument("--residual-blocks", type=int, default=4)
    parser.add_argument("--entity-layers", type=int, default=2)
    parser.add_argument("--entity-heads", type=int, default=8)
    parser.add_argument("--card-embedding-size", type=int, default=128)
    parser.add_argument("--seed", type=int, default=20260909)
    parser.add_argument(
        "--early-stopping-patience", type=int, default=0,
        help="Stop on the selected validation objective after this many non-improving epochs; 0 disables.",
    )
    parser.add_argument(
        "--early-stopping-metric",
        choices=("joint", "policy-kl", "value-mse"), default="joint",
        help="Checkpoint selection metric; joint trains a genuine policy/value model.",
    )
    parser.add_argument(
        "--skip-post-training-metrics", action="store_true",
        help=("Save the selected checkpoint immediately after training. Use the "
              "already-computed validation history; omit costly full-dataset "
              "and by-seat inference metrics."),
    )
    parser.add_argument(
        "--policy-target",
        choices=("visits", "chosen", "value-weighted-visits"),
        default="visits",
        help="Distil root visit shares or the teacher's final selected action.",
    )
    parser.add_argument(
        "--policy-target-temperature", type=float, default=1.0,
        help="Sharpen (<1) or flatten (>1) soft root-visit targets.",
    )
    parser.add_argument(
        "--policy-value-temperature", type=float, default=0.5,
        help="Q-value temperature for value-weighted visit targets.",
    )
    args = parser.parse_args()
    if args.policy_target_temperature <= 0:
        parser.error("--policy-target-temperature must be positive")
    if args.policy_value_temperature <= 0:
        parser.error("--policy-value-temperature must be positive")
    if any(weight < 0 for weight in (
        args.policy_weight, args.value_weight, args.action_q_weight,
        args.anchor_policy_kl_weight, args.anchor_value_weight,
    )):
        parser.error("all loss weights must be non-negative")
    if args.policy_weight == 0 and args.value_weight == 0:
        parser.error("at least one loss weight must be positive")
    if (
        args.anchor_policy_kl_weight > 0 or args.anchor_value_weight > 0
    ) and args.anchor_checkpoint is None:
        parser.error("positive anchor loss weights require --anchor-checkpoint")
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = choose_device(args.device)
    dataset = DecisionDataset(
        args.data, args.max_records, args.allow_mixed_rulesets, args.index_cache
    )
    schema = dataset.header["feature_schema"]
    external_validation_dataset = (
        DecisionDataset(
            args.validation_data, args.max_records, args.allow_mixed_rulesets
        )
        if args.validation_data else None
    )
    if external_validation_dataset is not None:
        external_header = external_validation_dataset.header
        if not compatible_feature_schema(external_header["feature_schema"], schema):
            raise ValueError("external validation data feature schema does not match training data")
        if external_header.get("ruleset") != dataset.header.get("ruleset"):
            raise ValueError("external validation data ruleset does not match training data")
        if external_header.get("ruleset_fingerprint") != dataset.header.get("ruleset_fingerprint"):
            raise ValueError("external validation data ruleset fingerprint does not match training data")
    model_class = {
        "additive-v1": PolicyValueNet,
        "interaction-v2": InteractionPolicyValueNet,
        "bilinear-v3": BilinearPolicyValueNet,
        "residual-v4": ResidualPolicyValueNet,
        "structured-v5": StructuredResidualPolicyValueNet,
        "structured-v5-action-q": StructuredResidualPolicyValueNet,
        "jev-v6-action-q": JointEntityPolicyValueNet,
        "jev-v7-action-q": JointEntityPolicyValueNet,
    }[args.architecture]
    model_args = [
        int(schema["state_size"]), int(schema["action_size"]),
        args.hidden_size, args.action_hidden_size,
    ]
    if model_class is ResidualPolicyValueNet:
        model_args.append(args.residual_blocks)
    elif model_class is StructuredResidualPolicyValueNet:
        model_args.extend((
            args.residual_blocks, int(schema["card_vocab_size"]),
            args.card_embedding_size,
        ))
    elif model_class is JointEntityPolicyValueNet:
        model_args.extend((
            args.entity_layers, args.entity_heads,
            int(schema["card_vocab_size"]), args.card_embedding_size,
            int(schema.get("entity_card_slot_count", 0)),
            schema.get("entity_card_semantic_lookup"),
        ))
    model = model_class(*model_args).to(device)

    def load_compatible_checkpoint(
        target: torch.nn.Module, checkpoint_path: Path, label: str,
    ) -> dict:
        checkpoint = torch.load(
            checkpoint_path, map_location="cpu", weights_only=False
        )
        checkpoint_model = checkpoint["report"]["model"]
        current_model = target.metadata()
        # v6 checkpoints added an auxiliary action-Q head without changing
        # the policy/value trunk.  It is safe to warm-start that trunk in the
        # current trainer while leaving the auxiliary head out of this run;
        # reject every other architectural mismatch instead of silently
        # loading incompatible tensors.
        compatible_action_q_suffix = (
            isinstance(checkpoint_model, dict)
            and (
                (checkpoint_model.get("architecture") == "policy-value-structured-residual-v5-action-q-v1"
                 and current_model.get("architecture") == "policy-value-structured-residual-v5")
                or
                (checkpoint_model.get("architecture") == "policy-value-structured-residual-v5"
                 and current_model.get("architecture") == "policy-value-structured-residual-v5-action-q-v1")
            )
            and all(checkpoint_model.get(key) == current_model.get(key)
                    for key in current_model if key != "architecture")
        )
        if checkpoint_model != current_model and not compatible_action_q_suffix:
            raise ValueError(f"{label} checkpoint model architecture does not match")
        checkpoint_schema = checkpoint["report"].get("feature_schema")
        if checkpoint_schema is not None and not compatible_feature_schema(
            checkpoint_schema, schema
        ):
            raise ValueError(f"{label} checkpoint feature schema does not match")
        if compatible_action_q_suffix:
            missing, unexpected = target.load_state_dict(
                checkpoint["model_state_dict"], strict=False
            )
            allowed_missing = (
                set(missing) if current_model.get("architecture") ==
                "policy-value-structured-residual-v5-action-q-v1"
                else set()
            )
            if set(missing) != allowed_missing or any(
                not key.startswith("action_value_head.") for key in unexpected
            ):
                raise ValueError(
                    f"incompatible warm-start tensors: missing={missing}, "
                    f"unexpected={unexpected}"
                )
        else:
            target.load_state_dict(checkpoint["model_state_dict"])
        return checkpoint

    if args.init_checkpoint is not None:
        load_compatible_checkpoint(model, args.init_checkpoint, "initial")
    anchor_model = None
    if args.anchor_checkpoint is not None:
        anchor_model = model_class(*model_args).to(device)
        load_compatible_checkpoint(anchor_model, args.anchor_checkpoint, "anchor")
        anchor_model.eval()
        anchor_model.requires_grad_(False)
    seeds = dataset.game_seeds()
    validation_seeds = (
        set() if external_validation_dataset is not None
        else stratified_validation_seed_map(
            dataset.winner_by_seed(), args.validation_ratio, args.seed
        )
    )
    validation_games = len(validation_seeds)
    train_indices = [
        index for index, (_path, _row, game_seed) in enumerate(dataset._index)
        if game_seed not in validation_seeds
    ]
    validation_dataset = external_validation_dataset or dataset
    validation_indices = (
        list(range(len(validation_dataset)))
        if external_validation_dataset is not None else [
            index for index, (_path, _row, game_seed) in enumerate(dataset._index)
            if game_seed in validation_seeds
        ]
    )
    generator = torch.Generator().manual_seed(args.seed)
    collate = partial(
        collate_decisions,
        hard_policy_targets=args.policy_target == "chosen",
        policy_target_temperature=args.policy_target_temperature,
        value_weighted_targets=args.policy_target == "value-weighted-visits",
        policy_value_temperature=args.policy_value_temperature,
        include_action_values=args.architecture in {
            "structured-v5-action-q", "jev-v6-action-q", "jev-v7-action-q",
        },
    )
    loader = DataLoader(
        dataset, batch_sampler=ShardBatchSampler(
            dataset, args.batch_size, args.seed, train_indices
        ), collate_fn=collate, num_workers=0,
    )
    train_eval_loader = DataLoader(
        Subset(dataset, train_indices), batch_size=args.batch_size, shuffle=False,
        collate_fn=collate, num_workers=0,
    )
    validation_loader = (
        DataLoader(
            Subset(validation_dataset, validation_indices), batch_size=args.batch_size,
            shuffle=False, collate_fn=collate, num_workers=0,
        )
        if validation_indices else None
    )
    optimizer = torch.optim.AdamW(
        model.parameters(), lr=args.learning_rate,
        weight_decay=args.weight_decay,
    )
    losses = []
    validation_history = []
    best_epoch = None
    best_validation_kl = float("inf")
    best_state = None
    stale_epochs = 0
    started = time.perf_counter()
    model.train()
    for epoch in range(1, args.epochs + 1):
        epoch_loss = 0.0
        batches = 0
        for batch in loader:
            states, actions, mask, chosen, targets, policy_targets = batch[:6]
            q_targets = q_mask = None
            if args.architecture in {"structured-v5-action-q", "jev-v6-action-q", "jev-v7-action-q"}:
                q_targets, q_mask = batch[6], batch[7]
            states, actions, mask = states.to(device), actions.to(device), mask.to(device)
            chosen, targets = chosen.to(device), targets.to(device)
            policy_targets = policy_targets.to(device)
            optimizer.zero_grad(set_to_none=True)
            if args.architecture in {"structured-v5-action-q", "jev-v6-action-q", "jev-v7-action-q"}:
                logits, values, action_q = model.forward_with_action_values(
                    states, actions, mask
                )
            else:
                logits, values = model(states, actions, mask)
            policy_loss_rows = -(
                policy_targets * F.log_softmax(logits, dim=1)
            ).sum(dim=1)
            nontrivial = mask.sum(dim=1) > 1
            policy_loss = (
                policy_loss_rows[nontrivial].mean()
                if bool(nontrivial.any().item())
                else policy_loss_rows.sum() * 0.0
            )
            value_loss = F.mse_loss(values, targets)
            loss = args.policy_weight * policy_loss + args.value_weight * value_loss
            if anchor_model is not None:
                with torch.no_grad():
                    anchor_logits, anchor_values = anchor_model(
                        states, actions, mask
                    )
                if args.anchor_policy_kl_weight > 0:
                    anchor_policy = F.softmax(anchor_logits, dim=1)
                    anchor_policy_kl_rows = F.kl_div(
                        F.log_softmax(logits, dim=1), anchor_policy,
                        reduction="none",
                    ).sum(dim=1)
                    anchor_policy_kl = (
                        anchor_policy_kl_rows[nontrivial].mean()
                        if bool(nontrivial.any().item())
                        else anchor_policy_kl_rows.sum() * 0.0
                    )
                    loss = loss + (
                        args.anchor_policy_kl_weight * anchor_policy_kl
                    )
                if args.anchor_value_weight > 0:
                    loss = loss + args.anchor_value_weight * F.mse_loss(
                        values, anchor_values
                    )
            if q_targets is not None:
                q_targets, q_mask = q_targets.to(device), q_mask.to(device)
                q_valid = q_mask & mask
                if bool(q_valid.any().item()):
                    loss = loss + args.action_q_weight * F.mse_loss(
                        action_q[q_valid], q_targets[q_valid]
                    )
            loss.backward()
            if args.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(
                    model.parameters(), args.gradient_clip
                )
            optimizer.step()
            epoch_loss += float(loss.detach().item())
            batches += 1
        losses.append(epoch_loss / batches)
        if args.early_stopping_patience > 0 and validation_loader is not None:
            metrics = evaluate(model, validation_loader, device)
            validation_history.append({"epoch": epoch, **metrics})
            selection_metric = {
                "joint": (
                    metrics["policy_kl"]
                    + args.value_weight * metrics["value_mse"]
                    + args.action_q_weight * (metrics["action_q_mse"] or 0.0)
                ),
                "policy-kl": metrics["policy_kl"],
                "value-mse": metrics["value_mse"],
            }[args.early_stopping_metric]
            validation_history[-1]["selection_metric"] = selection_metric
            if selection_metric < best_validation_kl - 1e-8:
                best_validation_kl = selection_metric
                best_epoch = epoch
                best_state = {
                    key: value.detach().cpu().clone()
                    for key, value in model.state_dict().items()
                }
                # Make the selected weights available before the potentially
                # long full-train and per-seat post-training metric passes.
                # Atomic replacement keeps concurrent evaluators from
                # observing a partially written checkpoint.
                interim_path = args.output.with_name(
                    f"{args.output.stem}.best-interim{args.output.suffix}"
                )
                interim_path.parent.mkdir(parents=True, exist_ok=True)
                temporary_path = interim_path.with_name(interim_path.name + ".tmp")
                torch.save({
                    "model_state_dict": best_state,
                    "report": {
                        "model": model.metadata(),
                        "feature_schema": schema,
                        "epoch": epoch,
                        "best_epoch": epoch,
                        "validation": validation_history[-1],
                        "value_trained": args.value_weight > 0,
                        "action_value_trained": (
                            args.action_q_weight > 0 and args.architecture in {
                                "structured-v5-action-q", "jev-v6-action-q",
                                "jev-v7-action-q",
                            }
                        ),
                        "data_sources": [path.as_posix() for path in args.data],
                    },
                }, temporary_path)
                os.replace(temporary_path, interim_path)
                print(f"saved best interim checkpoint: {interim_path}", flush=True)
                stale_epochs = 0
            else:
                stale_epochs += 1
            model.train()
        progress = {
            "epoch": epoch,
            "train_loss": losses[-1],
            "validation": validation_history[-1] if validation_history else None,
            "best_epoch": best_epoch,
            "stale_epochs": stale_epochs,
        }
        print(json.dumps(progress, sort_keys=True), flush=True)
        if args.checkpoint_every > 0 and epoch % args.checkpoint_every == 0:
            checkpoint_path = args.output.with_name(
                f"{args.output.stem}.epoch{epoch}{args.output.suffix}"
            )
            checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(
                {
                    "model_state_dict": {
                        key: value.detach().cpu()
                        for key, value in model.state_dict().items()
                    },
                    "report": {
                        "model": model.metadata(),
                        "feature_schema": schema,
                        "epoch": epoch,
                        "train_loss": losses[-1],
                        "data_sources": [path.as_posix() for path in args.data],
                        "init_checkpoint": (
                            str(args.init_checkpoint) if args.init_checkpoint else None
                        ),
                        "anchor_checkpoint": (
                            str(args.anchor_checkpoint) if args.anchor_checkpoint else None
                        ),
                        "anchor_policy_kl_weight": args.anchor_policy_kl_weight,
                        "anchor_value_weight": args.anchor_value_weight,
                        "value_trained": args.value_weight > 0,
                        "action_value_trained": (
                            args.action_q_weight > 0 and args.architecture in {
                                "structured-v5-action-q", "jev-v6-action-q",
                                "jev-v7-action-q",
                            }
                        ),
                        "validation": (
                            validation_history[-1] if validation_history else None
                        ),
                    },
                },
                checkpoint_path,
            )
            print(f"saved epoch checkpoint: {checkpoint_path}", flush=True)
        if (
            args.early_stopping_patience > 0
            and validation_loader is not None
            and stale_epochs >= args.early_stopping_patience
        ):
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    if device.type == "npu":
        torch.npu.synchronize()
    if args.skip_post_training_metrics:
        train_metrics = None
        validation_metrics = (
            validation_history[best_epoch - 1]
            if best_epoch is not None else None
        )
        train_actor_metrics = None
        validation_actor_metrics = None
    else:
        train_metrics = evaluate(model, train_eval_loader, device)
        validation_metrics = (
            evaluate(model, validation_loader, device)
            if validation_loader is not None else None
        )
        train_actor_metrics = actor_metrics(
            model, dataset, train_indices, collate, args.batch_size, device
        )
        validation_actor_metrics = actor_metrics(
            model, validation_dataset, validation_indices, collate, args.batch_size, device
        )
    report = {
        "schema_version": 1,
        "ruleset": dataset.header.get("ruleset"),
        "ruleset_fingerprint": dataset.header.get("ruleset_fingerprint"),
        "data_sources": [path.as_posix() for path in args.data],
        "external_validation_sources": (
            [path.as_posix() for path in args.validation_data]
            if args.validation_data else None
        ),
        "validation_mode": (
            "external_held_out" if external_validation_dataset is not None
            else "internal_stratified"
        ),
        "device": str(device),
        "records": len(dataset),
        "train_records": len(train_indices),
        "validation_records": len(validation_indices),
        "train_games": len(seeds) - validation_games,
        "validation_games": (
            len(validation_dataset.game_seeds())
            if external_validation_dataset is not None else validation_games
        ),
        "split_seed": args.seed,
        "validation_game_seeds": sorted(validation_seeds),
        "epochs": len(losses),
        "epochs_requested": args.epochs,
        "early_stopping_patience": args.early_stopping_patience,
        "early_stopping_metric": args.early_stopping_metric,
        "best_validation_objective": (
            best_validation_kl if best_epoch is not None else None
        ),
        "best_epoch": best_epoch,
        "validation_history": validation_history,
        "value_weight": args.value_weight,
        "action_q_weight": args.action_q_weight,
        "policy_weight": args.policy_weight,
        "init_checkpoint": (
            str(args.init_checkpoint) if args.init_checkpoint else None
        ),
        "anchor_checkpoint": (
            str(args.anchor_checkpoint) if args.anchor_checkpoint else None
        ),
        "anchor_policy_kl_weight": args.anchor_policy_kl_weight,
        "anchor_value_weight": args.anchor_value_weight,
        "weight_decay": args.weight_decay,
        "gradient_clip": args.gradient_clip,
        "policy_target": args.policy_target,
        "policy_target_temperature": args.policy_target_temperature,
        "policy_value_temperature": (
            args.policy_value_temperature
            if args.policy_target == "value-weighted-visits" else None
        ),
        "value_trained": args.value_weight > 0,
        "action_value_trained": (
            args.action_q_weight > 0 and args.architecture in {
                "structured-v5-action-q", "jev-v6-action-q", "jev-v7-action-q",
            }
        ),
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "selected_loss": (
            losses[best_epoch - 1] if best_epoch is not None else losses[-1]
        ),
        "train_winners": winner_counts(dataset, train_indices),
        "validation_winners": winner_counts(validation_dataset, validation_indices),
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "train_actor_metrics": train_actor_metrics,
        "validation_actor_metrics": validation_actor_metrics,
        "post_training_metrics_skipped": args.skip_post_training_metrics,
        # Retain the first report's flat fields for downstream compatibility.
        "train_policy_accuracy": (
            train_metrics["policy_accuracy"] if train_metrics else None
        ),
        "train_value_mae": (
            train_metrics["value_mae"] if train_metrics else None
        ),
        "validation_policy_accuracy": (
            validation_metrics["policy_accuracy"] if validation_metrics else None
        ),
        "validation_value_mae": (
            validation_metrics["value_mae"] if validation_metrics else None
        ),
        "elapsed_seconds": time.perf_counter() - started,
        "model": model.metadata(),
        "feature_schema": schema,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model_state_dict": model.state_dict(), "report": report}, args.output
    )
    report_path = args.output.with_suffix(".json")
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
