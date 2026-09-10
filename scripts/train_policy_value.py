#!/usr/bin/env python3
"""Train the small policy/value model on generated JSONL.GZ decisions."""

from __future__ import annotations

import argparse
import gzip
import json
import random
import sys
import time
from collections import defaultdict
from functools import partial
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import torch
import torch.nn.functional as F
from torch.utils.data import DataLoader, Dataset, Subset

from hsa.torch_model import (
    BilinearPolicyValueNet,
    InteractionPolicyValueNet,
    PolicyValueNet,
    ResidualPolicyValueNet,
    StructuredResidualPolicyValueNet,
)
from hsa.training import (
    temperature_scale_probabilities,
    value_weighted_policy_target,
)


class DecisionDataset(Dataset):
    def __init__(self, paths: list[Path], max_records: int | None = None):
        self.records = []
        self.headers = []
        for path in paths:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                header = json.loads(next(handle))
                self.headers.append(header)
                if len(self.headers) > 1 and (
                    header["feature_schema"] != self.headers[0]["feature_schema"]
                ):
                    raise ValueError("all datasets must use the same feature schema")
                if len(self.headers) > 1 and (
                    header.get("ruleset") != self.headers[0].get("ruleset")
                ):
                    raise ValueError("all datasets must use the same ruleset")
                for line in handle:
                    if max_records is not None and len(self.records) >= max_records:
                        break
                    record = json.loads(line)
                    if record.get("record_type") == "decision":
                        self.records.append(record)
            if max_records is not None and len(self.records) >= max_records:
                break
        self.header = self.headers[0]
        if not self.records:
            raise ValueError("dataset contains no decision records")

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int):
        return self.records[index]


def collate_decisions(
    records: list[dict], *, hard_policy_targets: bool = False,
    policy_target_temperature: float = 1.0,
    value_weighted_targets: bool = False,
    policy_value_temperature: float = 0.5,
):
    if policy_target_temperature <= 0:
        raise ValueError("policy target temperature must be positive")
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
    for row, record in enumerate(records):
        count = len(record["actions"])
        states[row] = torch.tensor(record["state"], dtype=torch.float32)
        actions[row, :count] = torch.tensor(record["actions"], dtype=torch.float32)
        mask[row, :count] = True
        chosen[row] = int(record["chosen_action"])
        values[row] = float(record["value_target"])
        target = None if hard_policy_targets else record.get("policy_target")
        if target is None:
            policy_targets[row, chosen[row]] = 1.0
        else:
            if value_weighted_targets:
                action_values = record.get("teacher_action_values")
                if action_values is None:
                    raise ValueError(
                        "value-weighted targets require teacher_action_values"
                    )
                target = value_weighted_policy_target(
                    target, action_values, policy_value_temperature
                )
            probabilities = torch.tensor(
                temperature_scale_probabilities(
                    target, policy_target_temperature
                ),
                dtype=torch.float32,
            )
            policy_targets[row, :count] = probabilities
    return states, actions, mask, chosen, values, policy_targets


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
    model.eval()
    correct = count = policy_count = 0
    absolute_error = 0.0
    squared_error = 0.0
    policy_cross_entropy = 0.0
    policy_target_entropy = 0.0
    with torch.no_grad():
        for states, actions, mask, chosen, targets, policy_targets in loader:
            states, actions, mask = states.to(device), actions.to(device), mask.to(device)
            chosen, targets = chosen.to(device), targets.to(device)
            policy_targets = policy_targets.to(device)
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
    return {
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
    }


def winner_counts(dataset, indices: list[int]) -> dict[str, int]:
    """Count complete games by winner without weighting long games more."""
    winners = {}
    for index in indices:
        record = dataset.records[index]
        winners.setdefault(record["game_seed"], record.get("winner"))
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
            if int(dataset.records[index]["actor"]) == actor
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data", type=Path, nargs="+",
        default=[ROOT / "reports" / "policy-value-smoke.jsonl.gz"],
    )
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "policy-value-smoke.pt",
    )
    parser.add_argument("--device", choices=("auto", "cpu", "npu"), default="auto")
    parser.add_argument("--epochs", type=int, default=20)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--weight-decay", type=float, default=1e-2)
    parser.add_argument("--gradient-clip", type=float, default=1.0)
    parser.add_argument("--value-weight", type=float, default=0.5)
    parser.add_argument("--policy-weight", type=float, default=1.0)
    parser.add_argument("--validation-ratio", type=float, default=0.2)
    parser.add_argument("--hidden-size", type=int, default=256)
    parser.add_argument("--action-hidden-size", type=int, default=128)
    parser.add_argument(
        "--architecture",
        choices=(
            "additive-v1", "interaction-v2", "bilinear-v3", "residual-v4",
            "structured-v5",
        ),
        default="additive-v1",
        help="Policy head architecture; interaction-v2 models state-action fit.",
    )
    parser.add_argument("--max-records", type=int)
    parser.add_argument(
        "--init-checkpoint", type=Path,
        help="Warm-start from a checkpoint with the same architecture and feature schema.",
    )
    parser.add_argument("--residual-blocks", type=int, default=4)
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
    if args.policy_weight < 0 or args.value_weight < 0:
        parser.error("policy and value weights must be non-negative")
    if args.policy_weight == 0 and args.value_weight == 0:
        parser.error("at least one loss weight must be positive")
    random.seed(args.seed)
    torch.manual_seed(args.seed)
    device = choose_device(args.device)
    dataset = DecisionDataset(args.data, args.max_records)
    schema = dataset.header["feature_schema"]
    model_class = {
        "additive-v1": PolicyValueNet,
        "interaction-v2": InteractionPolicyValueNet,
        "bilinear-v3": BilinearPolicyValueNet,
        "residual-v4": ResidualPolicyValueNet,
        "structured-v5": StructuredResidualPolicyValueNet,
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
    model = model_class(*model_args).to(device)
    if args.init_checkpoint is not None:
        initial = torch.load(
            args.init_checkpoint, map_location="cpu", weights_only=False
        )
        initial_model = initial["report"]["model"]
        if initial_model != model.metadata():
            raise ValueError("initial checkpoint model architecture does not match")
        initial_schema = initial["report"].get("feature_schema")
        if initial_schema != schema:
            raise ValueError("initial checkpoint feature schema does not match")
        model.load_state_dict(initial["model_state_dict"])
    seeds = sorted({record["game_seed"] for record in dataset.records})
    validation_seeds = stratified_validation_seeds(
        dataset.records, args.validation_ratio, args.seed
    )
    validation_games = len(validation_seeds)
    train_indices = [
        index for index, record in enumerate(dataset.records)
        if record["game_seed"] not in validation_seeds
    ]
    validation_indices = [
        index for index, record in enumerate(dataset.records)
        if record["game_seed"] in validation_seeds
    ]
    generator = torch.Generator().manual_seed(args.seed)
    collate = partial(
        collate_decisions,
        hard_policy_targets=args.policy_target == "chosen",
        policy_target_temperature=args.policy_target_temperature,
        value_weighted_targets=args.policy_target == "value-weighted-visits",
        policy_value_temperature=args.policy_value_temperature,
    )
    loader = DataLoader(
        Subset(dataset, train_indices), batch_size=args.batch_size, shuffle=True,
        collate_fn=collate, generator=generator, num_workers=0,
    )
    train_eval_loader = DataLoader(
        Subset(dataset, train_indices), batch_size=args.batch_size, shuffle=False,
        collate_fn=collate, num_workers=0,
    )
    validation_loader = (
        DataLoader(
            Subset(dataset, validation_indices), batch_size=args.batch_size,
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
        for states, actions, mask, chosen, targets, policy_targets in loader:
            states, actions, mask = states.to(device), actions.to(device), mask.to(device)
            chosen, targets = chosen.to(device), targets.to(device)
            policy_targets = policy_targets.to(device)
            optimizer.zero_grad(set_to_none=True)
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
                stale_epochs = 0
            else:
                stale_epochs += 1
            model.train()
            if stale_epochs >= args.early_stopping_patience:
                break
    if best_state is not None:
        model.load_state_dict(best_state)
    if device.type == "npu":
        torch.npu.synchronize()
    train_metrics = evaluate(model, train_eval_loader, device)
    if validation_loader is not None:
        validation_metrics = evaluate(
            model, validation_loader, device
        )
    else:
        validation_metrics = None
    train_actor_metrics = actor_metrics(
        model, dataset, train_indices, collate, args.batch_size, device
    )
    validation_actor_metrics = actor_metrics(
        model, dataset, validation_indices, collate, args.batch_size, device
    )
    report = {
        "schema_version": 1,
        "ruleset": dataset.header.get("ruleset"),
        "data_sources": [path.as_posix() for path in args.data],
        "device": str(device),
        "records": len(dataset),
        "train_records": len(train_indices),
        "validation_records": len(validation_indices),
        "train_games": len(seeds) - validation_games,
        "validation_games": validation_games,
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
        "policy_weight": args.policy_weight,
        "init_checkpoint": (
            str(args.init_checkpoint) if args.init_checkpoint else None
        ),
        "weight_decay": args.weight_decay,
        "gradient_clip": args.gradient_clip,
        "policy_target": args.policy_target,
        "policy_target_temperature": args.policy_target_temperature,
        "policy_value_temperature": (
            args.policy_value_temperature
            if args.policy_target == "value-weighted-visits" else None
        ),
        "value_trained": args.value_weight > 0,
        "initial_loss": losses[0],
        "final_loss": losses[-1],
        "selected_loss": (
            losses[best_epoch - 1] if best_epoch is not None else losses[-1]
        ),
        "train_winners": winner_counts(dataset, train_indices),
        "validation_winners": winner_counts(dataset, validation_indices),
        "train_metrics": train_metrics,
        "validation_metrics": validation_metrics,
        "train_actor_metrics": train_actor_metrics,
        "validation_actor_metrics": validation_actor_metrics,
        # Retain the first report's flat fields for downstream compatibility.
        "train_policy_accuracy": train_metrics["policy_accuracy"],
        "train_value_mae": train_metrics["value_mae"],
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
