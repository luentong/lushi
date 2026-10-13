#!/usr/bin/env python3
"""Audit actor-credit and low-information action mass in entity PPO rollouts.

Streams saved training trajectories. This describes labels, not move quality:
a win does not imply every move was good, and GAE sign changes are not proof
that its local credit is correct.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
import math
from pathlib import Path


def audit(paths):
    report = {"schema": "entity-training-signal-audit-v1", "files": [str(p) for p in paths],
              "by_file": []}
    for path in paths:
        counts = Counter()
        by_deck = defaultdict(Counter)
        seeds = set()
        chosen_probability = 0.0
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                view = row["view"]
                action_count = len(view["actions"])
                if action_count < 1 or not 0 <= row["chosen"] < action_count:
                    raise ValueError("invalid recorded action count/index")
                outcome = row["return"]
                advantage = row["advantage"]
                if outcome not in (-1.0, 0.0, 1.0):
                    raise ValueError("rollout lacks valid terminal outcome")
                if not row.get("terminated") or row.get("truncated"):
                    raise ValueError("truncated trajectory cannot be audited as terminal")
                deck = row["deck_a"] if row["actor"] == 0 else row["deck_b"]
                seeds.add(row["game_seed"])
                counts["decisions"] += 1
                by_deck[deck]["decisions"] += 1
                if action_count == 1:
                    counts["single_legal_action"] += 1
                    by_deck[deck]["single_legal_action"] += 1
                kind = row["action_key"][0]
                if kind == "END_TURN":
                    counts["end_turn"] += 1
                if kind.startswith("MULLIGAN"):
                    counts["mulligan"] += 1
                if outcome > 0:
                    counts["won_game_decisions"] += 1
                    counts["positive_advantage_in_won_game"] += advantage > 0
                elif outcome < 0:
                    counts["lost_game_decisions"] += 1
                    counts["negative_advantage_in_lost_game"] += advantage < 0
                chosen_probability += math.exp(row["logp"])
        if not counts["decisions"]:
            raise ValueError(f"empty rollout: {path}")
        report["by_file"].append({"path": str(path), "games": len(seeds),
            "counts": dict(counts),
            "single_legal_share": counts["single_legal_action"] / counts["decisions"],
            "end_turn_share": counts["end_turn"] / counts["decisions"],
            "mean_chosen_probability": chosen_probability / counts["decisions"],
            "by_deck": {deck: dict(values) for deck, values in sorted(by_deck.items())}})
    report["interpretation"] = [
        "A terminal-credit advantage may reward bad moves in wins and penalize good moves in losses.",
        "A single legal action has zero policy-choice information but can still train the value head.",
        "This audit does not establish that GAE or any alternative credit method improves playing strength.",
    ]
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rollouts", nargs="+", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.rollouts)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
