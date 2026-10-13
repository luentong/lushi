#!/usr/bin/env python3
"""Bounded eight-deck screen: same model with root search versus greedy play."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import statistics
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from benchmark_mcts import _decoded_decks
from evaluate_entity_policy import play_job, select_policy, summary
from train_entity_selfplay import select_device


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--deck-config", type=Path, default=ROOT / "config/decks_20260925_smoke8.json")
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--device", default="cpu")
    p.add_argument("--budget", type=int, default=32)
    p.add_argument("--rollout-depth", type=int, default=8)
    p.add_argument("--leaf-mode", choices=("heuristic", "entity_value"),
                   default="heuristic")
    p.add_argument("--seed", type=int, default=203901010000)
    p.add_argument("--offsets", type=int, nargs="+", default=[1],
                   help="Opponent deck offsets; each creates a seat-swapped pair per deck")
    p.add_argument("--max-actions", type=int, default=400)
    p.add_argument("--max-game-seconds", type=float, default=600)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.budget < 4 or args.rollout_depth < 0 or args.output.exists() or not args.offsets:
        p.error("budget must be at least four, offsets nonempty, and output directory new")
    import torch
    torch.set_num_threads(2)
    args.save_traces = False
    args.output.mkdir(parents=True)
    decks = _decoded_decks(args.deck_config)
    names = sorted(decks)
    if any(offset % len(names) == 0 for offset in args.offsets):
        p.error("opponent offset must not produce a mirror matchup")
    device = select_device(args.device)
    candidate = select_policy("entity", args.checkpoint, device,
                              search_budget=args.budget, search_rollout_depth=args.rollout_depth,
                              search_leaf_mode=args.leaf_mode)
    opponent = select_policy("entity", args.checkpoint, device)
    report = {"status": "running", "checkpoint": str(args.checkpoint),
        "budget": args.budget, "rollout_depth": args.rollout_depth,
        "leaf_mode": args.leaf_mode,
        "policy_mode": "root_search_vs_same_model_greedy",
        "planned_games": len(names) * len(args.offsets) * 2, "games": []}
    for offset_index, offset in enumerate(args.offsets):
        for i, name in enumerate(names):
            pair_id = offset_index * len(names) + i
            for seat in (0, 1):
                job = {"pair_id": pair_id, "seed": args.seed + pair_id,
                    "candidate_deck": name, "opponent_deck": names[(i + offset) % len(names)],
                    "candidate_seat": seat}
                result = play_job(job, candidate, opponent, decks, args)
                report["games"].append(result)
                report["summary"] = summary(report["games"])
                args.output.joinpath("screen.json").write_text(
                    json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({"game": len(report["games"]), "status": result["status"],
                    "candidate_won": result["winner"] == seat if result["status"] == "complete" else None,
                    "mean_decision_seconds": statistics.mean(result["decision_seconds"])
                        if result["decision_seconds"] else None}, ensure_ascii=False), flush=True)
    report["status"] = "complete"
    args.output.joinpath("screen.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
