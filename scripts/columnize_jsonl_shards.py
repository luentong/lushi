#!/usr/bin/env python3
"""Convert compressed decision JSONL into compact tensor-native shards."""

from __future__ import annotations

import argparse
import gzip
import json
from multiprocessing import Pool
from pathlib import Path

import torch

try:
    import orjson
except ImportError:  # pragma: no cover - optional accelerator
    orjson = None


def loads(value):
    return orjson.loads(value) if orjson is not None else json.loads(value)


def _flush(records: list[dict], destination: Path) -> int:
    count = len(records)
    state_size = len(records[0]["state"])
    action_size = len(records[0]["actions"][0])
    max_actions = max(len(record["actions"]) for record in records)
    states = torch.empty((count, state_size), dtype=torch.float32)
    actions = torch.zeros(
        (count, max_actions, action_size), dtype=torch.float32
    )
    mask = torch.zeros((count, max_actions), dtype=torch.bool)
    chosen = torch.empty(count, dtype=torch.int16)
    values = torch.empty(count, dtype=torch.float32)
    policy_targets = torch.zeros((count, max_actions), dtype=torch.float32)
    teacher_values = torch.zeros((count, max_actions), dtype=torch.float32)
    teacher_mask = torch.zeros((count, max_actions), dtype=torch.bool)
    game_seed = torch.empty(count, dtype=torch.int64)
    actor = torch.empty(count, dtype=torch.int8)
    winner = torch.full((count,), -1, dtype=torch.int8)
    for row, record in enumerate(records):
        legal = len(record["actions"])
        states[row] = torch.as_tensor(record["state"], dtype=torch.float32)
        actions[row, :legal] = torch.as_tensor(
            record["actions"], dtype=torch.float32
        )
        mask[row, :legal] = True
        chosen[row] = int(record["chosen_action"])
        values[row] = float(record["value_target"])
        game_seed[row] = int(record.get("game_seed", 0))
        actor[row] = int(record.get("actor", 0))
        if record.get("winner") is not None:
            winner[row] = int(record["winner"])
        policy = record.get("policy_target")
        if policy is None:
            policy_targets[row, chosen[row]] = 1.0
        else:
            limit = min(legal, len(policy))
            policy_targets[row, :limit] = torch.as_tensor(
                policy[:limit], dtype=torch.float32
            )
        action_q = record.get("teacher_action_values")
        if action_q is not None:
            limit = min(legal, len(action_q))
            teacher_values[row, :limit] = torch.as_tensor(
                action_q[:limit], dtype=torch.float32
            )
            value_mask = record.get("teacher_action_value_mask")
            if value_mask is None:
                visits = record.get("teacher_action_visits")
                if visits is not None:
                    value_mask = [count > 0 for count in visits]
            if value_mask is None:
                teacher_mask[row, :limit] = True
            else:
                if len(value_mask) < limit:
                    raise ValueError("action-Q mask shorter than action-Q values")
                teacher_mask[row, :limit] = torch.as_tensor(
                    value_mask[:limit], dtype=torch.bool
                )
    destination.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "states": states,
        "actions": actions,
        "mask": mask,
        "chosen": chosen,
        "values": values,
        "policy_targets": policy_targets,
        "teacher_action_values": teacher_values,
        "teacher_action_value_mask": teacher_mask,
        "game_seed": game_seed,
        "actor": actor,
        "winner": winner,
        "count": count,
    }, destination)
    destination.with_suffix(".meta.json").write_text(json.dumps({
        "count": count,
        "game_seed": game_seed.tolist(),
        "actor": actor.tolist(),
        "winner": winner.tolist(),
    }, separators=(",", ":")), encoding="utf-8")
    return count


def convert_one(job: tuple[str, str, int]) -> tuple[str, int, int]:
    source_text, output_text, chunk_size = job
    source, output = Path(source_text), Path(output_text)
    stem = source.name.removesuffix(".jsonl.gz")
    records: list[dict] = []
    total = chunks = 0
    with gzip.open(source, "rb") as handle:
        next(handle)
        for line in handle:
            record = loads(line)
            if record.get("record_type") != "decision":
                continue
            records.append(record)
            if len(records) >= chunk_size:
                total += _flush(records, output / f"{stem}.{chunks:04d}.pt")
                chunks += 1
                records = []
    if records:
        total += _flush(records, output / f"{stem}.{chunks:04d}.pt")
        chunks += 1
    return source.name, total, chunks


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--chunk-size", type=int, default=256)
    args = parser.parse_args()
    sources = sorted(args.source.glob("*.jsonl.gz"))
    if not sources:
        raise SystemExit("no JSONL.GZ shards found")
    args.output.mkdir(parents=True, exist_ok=True)
    with gzip.open(sources[0], "rb") as handle:
        header = loads(next(handle))
    (args.output / "_header.json").write_text(
        json.dumps(header, separators=(",", ":")), encoding="utf-8"
    )
    jobs = [(str(path), str(args.output), args.chunk_size) for path in sources]
    total = chunks = 0
    with Pool(processes=args.workers) as pool:
        for name, records, produced in pool.imap_unordered(convert_one, jobs):
            total += records
            chunks += produced
            print(
                f"converted {name}: {records} records, {produced} chunks; "
                f"total={total}", flush=True,
            )
    print(f"complete: {total} records in {chunks} tensor shards", flush=True)


if __name__ == "__main__":
    main()
