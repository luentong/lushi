#!/usr/bin/env python3
"""Equal-simulation comparison of root voting and shared-tree ISMCTS."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import (
    DeterminizedMCTSPolicy,
    DragonMirrorGame,
    HeuristicPolicy,
    InformationSetMCTSPolicy,
)


def run_game(cards: Path, seed: int, seat: int, policy, max_actions: int) -> dict:
    game = DragonMirrorGame(cards, seed)
    policies = [HeuristicPolicy(), HeuristicPolicy()]
    policies[seat] = policy
    actions = nodes = searches = 0
    started = time.perf_counter()
    while not game.finished and actions < max_actions:
        actor = game.current
        game.step(policies[actor].choose(game))
        if actor == seat:
            searches += 1
            nodes += int(policy.last_search.get("nodes", 0))
        actions += 1
    return {
        "seed": seed, "seat": seat, "winner": game.winner,
        "candidate_win": game.winner == seat, "finished": game.finished,
        "invalid_actions": game.invalid_actions, "turns": game.turn,
        "actions": actions, "searches": searches, "nodes": nodes,
        "elapsed_seconds": time.perf_counter() - started,
    }


def summarize(name: str, rows: list[dict]) -> dict:
    elapsed = [row["elapsed_seconds"] for row in rows]
    return {
        "candidate": name,
        "games": len(rows),
        "finished": sum(row["finished"] for row in rows),
        "wins": sum(row["candidate_win"] for row in rows),
        "win_rate": sum(row["candidate_win"] for row in rows) / len(rows),
        "invalid_actions": sum(row["invalid_actions"] for row in rows),
        "elapsed_seconds": sum(elapsed),
        "median_game_seconds": statistics.median(elapsed),
        "searches": sum(row["searches"] for row in rows),
        "nodes": sum(row["nodes"] for row in rows),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=int, default=10)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--rollout-depth", type=int, default=4)
    parser.add_argument("--seed", type=int, default=202609091000)
    parser.add_argument("--search-seed", type=int, default=20260909)
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "search-ab.json",
    )
    args = parser.parse_args()
    constructors = {
        "root-determinized-mcts-v3": lambda: DeterminizedMCTSPolicy(
            samples=args.samples, iterations_per_sample=args.iterations,
            rollout_depth=args.rollout_depth, seed=args.search_seed,
        ),
        "shared-tree-ismcts-v1": lambda: InformationSetMCTSPolicy(
            samples=args.samples, iterations_per_sample=args.iterations,
            rollout_depth=args.rollout_depth, seed=args.search_seed,
        ),
    }
    all_rows = {}
    for name, constructor in constructors.items():
        all_rows[name] = [
            run_game(
                args.cards, args.seed + offset, seat, constructor(), args.max_actions
            )
            for offset in range(args.pairs) for seat in (0, 1)
        ]
    report = {
        "schema_version": 1,
        "budget": {
            "samples": args.samples,
            "iterations_per_sample": args.iterations,
            "simulations_per_decision": args.samples * args.iterations,
            "rollout_depth": args.rollout_depth,
        },
        "baseline": "heuristic-tempo-v1",
        "summaries": [summarize(name, rows) for name, rows in all_rows.items()],
        "runs": all_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"budget": report["budget"], "summaries": report["summaries"]}, indent=2))
    return 0 if all(
        row["finished"] and not row["invalid_actions"]
        for rows in all_rows.values() for row in rows
    ) else 1


if __name__ == "__main__":
    raise SystemExit(main())
