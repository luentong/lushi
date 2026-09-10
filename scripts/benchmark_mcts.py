#!/usr/bin/env python3
"""Seat-swapped engineering benchmark for MCTS v0 versus heuristic v1."""

from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import (
    DeterminizedMCTSPolicy,
    DragonMirrorGame,
    HeuristicPolicy,
    InformationSetMCTSPolicy,
    MCTSPolicy,
)
from hsa.evaluation import wilson_interval


_MODEL_CACHE = {}


def load_model(checkpoint: Path, device: str):
    key = (str(checkpoint.resolve()), device)
    if key not in _MODEL_CACHE:
        from hsa.torch_model import TorchPolicyValueModel
        _MODEL_CACHE[key] = TorchPolicyValueModel.from_checkpoint(
            str(checkpoint), device
        )
    return _MODEL_CACHE[key]


def play(cards: Path, seed: int, mcts_seat: int, args: argparse.Namespace) -> dict:
    game = DragonMirrorGame(cards, seed)
    policies = [HeuristicPolicy(), HeuristicPolicy()]
    if args.baseline == "ismcts":
        baseline_seat = 1 - mcts_seat
        policies[baseline_seat] = InformationSetMCTSPolicy(
            samples=args.samples,
            iterations_per_sample=args.iterations,
            tree_depth=args.tree_depth,
            rollout_depth=args.rollout_depth,
            seed=args.search_seed + seed * 2 + baseline_seat,
        )
    if args.mode == "puct":
        if args.checkpoint is None:
            raise ValueError("--checkpoint is required for puct mode")
        model = load_model(args.checkpoint, args.device)
        if not args.policy_only and not model.value_trained:
            raise ValueError(
                "checkpoint value head was not trained; pass --policy-only"
            )
        search = InformationSetMCTSPolicy(
            samples=args.samples,
            iterations_per_sample=args.iterations,
            tree_depth=args.tree_depth,
            rollout_depth=args.rollout_depth if args.policy_only else 0,
            seed=args.search_seed + seed * 2 + mcts_seat,
            policy_value_model=model,
            use_model_value=not args.policy_only,
        )
    else:
        search = (
            InformationSetMCTSPolicy(
                samples=args.samples,
                iterations_per_sample=args.iterations,
                tree_depth=args.tree_depth,
                rollout_depth=args.rollout_depth,
                seed=args.search_seed + seed * 2 + mcts_seat,
            )
            if args.mode == "ismcts"
            else DeterminizedMCTSPolicy(
                samples=args.samples,
                iterations_per_sample=args.iterations,
                rollout_depth=args.rollout_depth,
                seed=args.search_seed + seed * 2 + mcts_seat,
            )
            if args.mode == "determinized"
            else MCTSPolicy(args.iterations, args.rollout_depth)
        )
    policies[mcts_seat] = search
    actions = searches = nodes = 0
    started = time.perf_counter()
    while not game.finished and actions < args.max_actions:
        actor = game.current
        game.step(policies[actor].choose(game))
        if actor == mcts_seat:
            searches += 1
            nodes += int(search.last_search.get("nodes", 0))
        actions += 1
    return {
        "seed": seed,
        "mcts_seat": mcts_seat,
        "winner": game.winner,
        "mcts_win": game.winner == mcts_seat,
        "finished": game.finished,
        "invalid_actions": game.invalid_actions,
        "turns": game.turn,
        "actions": actions,
        "searches": searches,
        "nodes": nodes,
        "elapsed_seconds": time.perf_counter() - started,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=202609090501)
    parser.add_argument("--iterations", type=int, default=12)
    parser.add_argument("--rollout-depth", type=int, default=8)
    parser.add_argument(
        "--mode", choices=("full", "determinized", "ismcts", "puct"), default="full"
    )
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--tree-depth", type=int, default=8)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument(
        "--policy-only", action="store_true",
        help="use checkpoint priors but retain heuristic rollout leaf values",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--search-seed", type=int, default=20260909)
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--baseline", choices=("heuristic", "ismcts"), default="heuristic"
    )
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "mcts-smoke.json")
    args = parser.parse_args()
    jobs = [
        (args.cards, args.seed + offset, seat, args)
        for offset in range(args.pairs) for seat in (0, 1)
    ]
    benchmark_started = time.perf_counter()
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            games = list(executor.map(
                play,
                (job[0] for job in jobs),
                (job[1] for job in jobs),
                (job[2] for job in jobs),
                (job[3] for job in jobs),
            ))
    else:
        games = [play(*job) for job in jobs]
    wins = sum(row["mcts_win"] for row in games)
    summary = {
        "schema_version": 1,
        "ruleset": "dragon-warrior-closed-v2",
        "candidate": (
            "policy-prior-puct-v1" if args.mode == "puct" and args.policy_only
            else "policy-value-puct-v1" if args.mode == "puct"
            else "shared-tree-ismcts-v1" if args.mode == "ismcts"
            else "root-determinized-mcts-v3" if args.mode == "determinized"
            else "mcts-full-state-v0"
        ),
        "information_mode": (
            "public_dragon_mirror_v3"
            if args.mode in {"determinized", "ismcts", "puct"} else "debug_full_state"
        ),
        "baseline": (
            "shared-tree-ismcts-v1"
            if args.baseline == "ismcts" else "heuristic-tempo-v1"
        ),
        "iterations": args.iterations,
        "tree_depth": args.tree_depth if args.mode in {"ismcts", "puct"} else None,
        "rollout_depth": (
            args.rollout_depth
            if args.mode != "puct" or args.policy_only else 0
        ),
        "leaf_value_source": (
            "heuristic_rollout" if args.mode == "puct" and args.policy_only
            else "model" if args.mode == "puct" else "heuristic_rollout"
        ),
        "samples": args.samples if args.mode in {"determinized", "ismcts", "puct"} else 1,
        "checkpoint": str(args.checkpoint) if args.mode == "puct" else None,
        "device": args.device if args.mode == "puct" else None,
        "workers": args.workers,
        "pairs": args.pairs,
        "games": len(games),
        "finished": sum(row["finished"] for row in games),
        "invalid_actions": sum(row["invalid_actions"] for row in games),
        "mcts_wins": wins,
        "mcts_win_rate": wins / len(games),
        "mcts_win_rate_wilson95": wilson_interval(wins, len(games)),
        "elapsed_seconds": sum(row["elapsed_seconds"] for row in games),
        "wall_clock_seconds": time.perf_counter() - benchmark_started,
        "searches": sum(row["searches"] for row in games),
        "nodes": sum(row["nodes"] for row in games),
    }
    document = {"summary": summary, "games": games}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(document, indent=2) + "\n").encode())
    print(json.dumps(summary, indent=2))
    return 0 if summary["finished"] == summary["games"] and not summary["invalid_actions"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
