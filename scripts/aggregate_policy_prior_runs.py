#!/usr/bin/env python3
"""Aggregate compatible seat-swapped search-agent replications."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.evaluation import paired_seed_summary, wilson_interval


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "policy-prior-replications.json",
    )
    args = parser.parse_args()
    runs = []
    all_games = []
    expected_signature = None
    for path in args.reports:
        document = json.loads(path.read_text(encoding="utf-8"))
        summary = document["summary"]
        signature_fields = (
            "candidate", "baseline", "checkpoint", "baseline_checkpoint",
            "samples", "iterations", "tree_depth", "rollout_depth",
            "baseline_samples", "baseline_iterations", "baseline_tree_depth",
            "baseline_rollout_depth", "leaf_value_source",
            "candidate_expansion_mode", "baseline_expansion_mode",
            "min_simulations_per_root_action", "max_total_iterations",
            "baseline_min_simulations_per_root_action",
            "baseline_max_total_iterations",
        )
        signature = {
            field: summary.get(field) for field in signature_fields
        }
        if expected_signature is None:
            expected_signature = signature
        elif signature != expected_signature:
            raise ValueError(
                f"{path} has an incompatible candidate/baseline configuration"
            )
        games = document["games"]
        wins = sum(bool(game["mcts_win"]) for game in games)
        runs.append({
            "report": path.as_posix(),
            "checkpoint": summary["checkpoint"],
            "games": len(games),
            "wins": wins,
            "win_rate": wins / len(games),
            "wilson95": wilson_interval(wins, len(games)),
            **paired_seed_summary(games),
        })
        all_games.extend(games)
    pooled_wins = sum(bool(game["mcts_win"]) for game in all_games)
    pooled_pairs = paired_seed_summary(all_games)
    result = {
        "schema_version": 1,
        "comparison": expected_signature,
        "runs": runs,
        "pooled": {
            "independent_runs": len(runs),
            "games": len(all_games),
            "wins": pooled_wins,
            "win_rate": pooled_wins / len(all_games),
            "wilson95": wilson_interval(pooled_wins, len(all_games)),
            **pooled_pairs,
        },
        "interpretation": (
            "Pooled statistics are descriptive; checkpoint-level replication "
            "remains the unit of generalization."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
