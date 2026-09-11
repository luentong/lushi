#!/usr/bin/env python3
"""Run a seat-swapped paired benchmark between heuristic and random policies."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import DragonMirrorGame, RULESET
from hsa.policy import HeuristicPolicy, RandomPolicy


def wilson(successes: int, trials: int, z: float = 1.959963984540054) -> tuple[float, float]:
    if trials == 0:
        return 0.0, 0.0
    p = successes / trials
    denominator = 1 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    radius = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return max(0.0, centre - radius), min(1.0, centre + radius)


def play(cards: Path, seed: int, heuristic_seat: int, max_actions: int) -> dict:
    game = DragonMirrorGame(cards, seed)
    policies = [RandomPolicy(), RandomPolicy()]
    policies[heuristic_seat] = HeuristicPolicy()
    actions = 0
    while not game.finished and actions < max_actions:
        game.step(policies[game.current].choose(game))
        actions += 1
    return {
        "seed": seed,
        "heuristic_seat": heuristic_seat,
        "winner": game.winner,
        "heuristic_win": game.winner == heuristic_seat,
        "finished": game.finished,
        "actions": actions,
        "turns": game.turn,
        "invalid_actions": game.invalid_actions,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=int, default=100)
    parser.add_argument("--seed", type=int, default=202609090001)
    parser.add_argument("--max-actions", type=int, default=5000)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "policy-benchmark.json")
    args = parser.parse_args()

    games = []
    for offset in range(args.pairs):
        seed = args.seed + offset
        games.append(play(args.cards, seed, 0, args.max_actions))
        games.append(play(args.cards, seed, 1, args.max_actions))
    wins = sum(row["heuristic_win"] for row in games)
    low, high = wilson(wins, len(games))
    summary = {
        "schema_version": 1,
        "ruleset": RULESET,
        "generation_profile": "closed_generation_pools",
        "candidate": "heuristic-tempo-v1",
        "baseline": "random-v1",
        "pairs": args.pairs,
        "games": len(games),
        "finished": sum(row["finished"] for row in games),
        "invalid_actions": sum(row["invalid_actions"] for row in games),
        "heuristic_wins": wins,
        "heuristic_win_rate": wins / len(games),
        "wilson_95": [low, high],
        "wins_as_first": sum(row["heuristic_win"] and row["heuristic_seat"] == 0 for row in games),
        "games_as_first": args.pairs,
        "wins_as_second": sum(row["heuristic_win"] and row["heuristic_seat"] == 1 for row in games),
        "games_as_second": args.pairs,
        "mean_turns": statistics.mean(row["turns"] for row in games),
        "mean_actions": statistics.mean(row["actions"] for row in games),
    }
    document = {"summary": summary, "games": games}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Pin UTF-8/LF bytes so Windows and Linux generate the same artifact hash.
    args.output.write_bytes((json.dumps(document, indent=2) + "\n").encode("utf-8"))
    print(json.dumps(summary, indent=2))
    return 0 if summary["finished"] == summary["games"] and not summary["invalid_actions"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
