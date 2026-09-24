#!/usr/bin/env python3
"""Convert packed record dictionaries into padded tensor batches."""
from __future__ import annotations
import argparse
from multiprocessing import Pool
from pathlib import Path
import torch

def columnize(src: Path, dst: Path) -> int:
    payload = torch.load(src, map_location="cpu", weights_only=False)
    records = payload["records"]
    if not records:
        return 0
    state_size = len(records[0]["state"])
    action_size = len(records[0]["actions"][0])
    max_actions = max(len(r["actions"]) for r in records)
    n = len(records)
    states = torch.tensor([r["state"] for r in records], dtype=torch.float32)
    actions = torch.zeros((n, max_actions, action_size), dtype=torch.float32)
    mask = torch.zeros((n, max_actions), dtype=torch.bool)
    chosen = torch.zeros(n, dtype=torch.long)
    values = torch.zeros(n, dtype=torch.float32)
    targets = torch.zeros((n, max_actions), dtype=torch.float32)
    actors = torch.zeros(n, dtype=torch.int8)
    game_seeds = torch.zeros(n, dtype=torch.int64)
    winners = torch.full((n,), -1, dtype=torch.int8)
    for i, r in enumerate(records):
        count = len(r["actions"])
        actions[i, :count] = torch.tensor(r["actions"], dtype=torch.float32)
        mask[i, :count] = True
        chosen[i] = int(r["chosen_action"])
        values[i] = float(r["value_target"])
        actors[i] = int(r.get("actor", 0))
        game_seeds[i] = int(r.get("game_seed", 0))
        if r.get("winner") is not None:
            winners[i] = int(r["winner"])
        target = r.get("policy_target")
        if target is None:
            targets[i, chosen[i]] = 1.0
        else:
            limit = min(count, len(target))
            targets[i, :limit] = torch.tensor(target[:limit], dtype=torch.float32)
    dst.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"header": payload.get("header", {}), "states": states, "actions": actions, "mask": mask,
                "chosen": chosen, "values": values, "actor": actors,
                "game_seed": game_seeds, "winner": winners,
                "policy_targets": targets, "count": n}, dst)
    return n


def _columnize_one(args: tuple[Path, Path]) -> tuple[str, int]:
    src, output = args
    return src.name, columnize(src, output / src.name)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("source", type=Path); p.add_argument("output", type=Path)
    p.add_argument("--workers", type=int, default=1,
                   help="Independent packed shards to convert concurrently.")
    args = p.parse_args(); total = 0
    jobs = [(src, args.output) for src in sorted(args.source.glob("*.pt"))]
    if args.workers > 1:
        with Pool(processes=args.workers) as pool:
            for name, count in pool.imap_unordered(_columnize_one, jobs):
                total += count
                print(name, flush=True)
    else:
        for job in jobs:
            name, count = _columnize_one(job)
            total += count
            print(name, flush=True)
    print("total", total)

if __name__ == "__main__": main()
