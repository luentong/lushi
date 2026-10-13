#!/usr/bin/env python3
"""Paired comparison of opening policies with both in-game models frozen."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics

from compare_entity_evaluations import paired_deltas, pair_delta_interval


def compare(model_opening, baseline_opening):
    a, b = model_opening, baseline_opening
    for field in ("checkpoint_sha256", "source_sha256", "deck_config_sha256"):
        if a.get(field) != b.get(field):
            raise ValueError(f"evaluation mismatch: {field}")
    for field in ("seed", "pairs_per_matchup", "deck_config", "cards", "max_actions",
                  "max_game_seconds", "candidate_search_budget", "manual_mulligan",
                  "opponent_mulligan_policy"):
        if a["parameters"].get(field) != b["parameters"].get(field):
            raise ValueError(f"evaluation mismatch: {field}")
    if (a["parameters"]["candidate_mulligan_policy"] != "model"
            or b["parameters"]["candidate_mulligan_policy"] != "baseline"
            or a["parameters"]["opponent_mulligan_policy"] != "baseline"
            or not a["parameters"]["manual_mulligan"]):
        raise ValueError("expected model versus baseline opening and fixed baseline opponent")
    rows = paired_deltas(a, b)
    groups = defaultdict(list)
    for row in rows:
        groups[row["candidate_deck"]].append(row)
    return {
        "games": len(rows),
        "model_opening_score": statistics.mean(row["candidate_score"] for row in rows),
        "baseline_opening_score": statistics.mean(row["baseline_score"] for row in rows),
        "paired_delta": pair_delta_interval(rows),
        "by_candidate_deck": {
            deck: {"games": len(items),
                   "model_opening_score": statistics.mean(x["candidate_score"] for x in items),
                   "baseline_opening_score": statistics.mean(x["baseline_score"] for x in items),
                   "paired_delta": pair_delta_interval(items)}
            for deck, items in sorted(groups.items())
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-opening", type=Path, required=True)
    parser.add_argument("--baseline-opening", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.model_opening.read_text(encoding="utf-8")),
                     json.loads(args.baseline_opening.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
