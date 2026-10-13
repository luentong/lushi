#!/usr/bin/env python3
"""Measure the Python rules-engine hot path used by MCTS.

This deliberately excludes neural inference.  It reports the three operations
that dominate tree search: legal-action generation, event-free cloning, and
clone-plus-apply.  Keeping this as a small standalone benchmark makes CPU/NPU
regressions visible without running a full tournament.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import DragonMirrorGame
from hsa.policy import HeuristicPolicy


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=1000)
    parser.add_argument("--warmup", type=int, default=100)
    parser.add_argument("--seed", type=int, default=2026100801)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.iterations < 1 or args.warmup < 0:
        raise ValueError("iterations must be positive and warmup non-negative")

    game = DragonMirrorGame(args.cards, args.seed)
    policy = HeuristicPolicy()
    for _ in range(args.warmup):
        legal = game.legal_actions()
        if not legal:
            game = DragonMirrorGame(args.cards, args.seed)
            continue
        game.step(policy.choose(game))

    def timed(fn):
        samples = []
        start = time.perf_counter()
        for _ in range(args.iterations):
            t0 = time.perf_counter()
            fn()
            samples.append(time.perf_counter() - t0)
        elapsed = time.perf_counter() - start
        return {
            "iterations": args.iterations,
            "elapsed_seconds": elapsed,
            "ops_per_second": args.iterations / elapsed,
            "mean_ms": statistics.mean(samples) * 1000.0,
            "p95_ms": sorted(samples)[max(0, int(len(samples) * 0.95) - 1)] * 1000.0,
        }

    fixed_action = policy.choose(game)
    search_state = game.clone(record_events=False)
    result = {
        "schema_version": 1,
        "seed": args.seed,
        "warmup": args.warmup,
        "state": {"turn": game.turn, "current": game.current},
        "legal_actions": timed(game.legal_actions),
        "cached_search_legal_actions": timed(search_state.legal_actions),
        "clone_event_free": timed(lambda: game.clone(record_events=False)),
        "clone_plus_apply": timed(lambda: game.branch(fixed_action)),
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
