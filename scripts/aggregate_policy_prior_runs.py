#!/usr/bin/env python3
"""Aggregate independent policy-prior versus plain-ISMCTS replications."""

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
    for path in args.reports:
        document = json.loads(path.read_text(encoding="utf-8"))
        summary = document["summary"]
        if summary["candidate"] != "policy-prior-puct-v1":
            raise ValueError(f"{path} is not a policy-prior PUCT report")
        if summary["baseline"] != "shared-tree-ismcts-v1":
            raise ValueError(f"{path} is not a direct ISMCTS comparison")
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
