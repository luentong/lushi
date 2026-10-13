#!/usr/bin/env python3
"""Audit historical observer PPO rollouts without using training-set metrics as strength.

Game-macro metrics prevent long games from dominating a deck's calibration
summary.  These labels are outcomes under the sampled rollout policy, not
counterfactual action values or independent validation data.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import statistics


def load_games(paths):
    games = defaultdict(list)
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                key = (str(path), row["game_seed"])
                games[key].append(row)
    return games


def game_metrics(rows):
    first = rows[0]
    learner_deck = first["deck_a"] if first["actor"] == 0 else first["deck_b"]
    opponent_deck = first["deck_b"] if first["actor"] == 0 else first["deck_a"]
    targets = {(row["return"] + 1) / 2 for row in rows}
    if len(targets) != 1 or any(row["actor"] != first["actor"] for row in rows):
        raise ValueError("inconsistent terminal label or actor within a game")
    target = targets.pop()
    predictions = [(row["old_value"] + 1) / 2 for row in rows]
    if any(not 0 <= prediction <= 1 for prediction in predictions):
        raise ValueError("critic prediction outside probability range")
    return {"learner_deck": learner_deck, "opponent_deck": opponent_deck,
            "opponent_version": first["opponent_version"], "decisions": len(rows),
            "outcome": target, "predicted": statistics.mean(predictions),
            "brier": statistics.mean((p - target) ** 2 for p in predictions),
            "first_brier": (predictions[0] - target) ** 2}


def summarize(rows):
    if not rows:
        return None
    return {"games": len(rows), "decisions": sum(row["decisions"] for row in rows),
            "decisions_per_game": statistics.mean(row["decisions"] for row in rows),
            "win_rate": statistics.mean(row["outcome"] for row in rows),
            "predicted_win_rate": statistics.mean(row["predicted"] for row in rows),
            "game_macro_brier": statistics.mean(row["brier"] for row in rows),
            "first_decision_brier": statistics.mean(row["first_brier"] for row in rows),
            "constant_0_5_brier": statistics.mean((0.5 - row["outcome"]) ** 2 for row in rows)}


def audit(paths):
    games = [game_metrics(rows) for rows in load_games(paths).values()]
    by_deck = defaultdict(list)
    by_opponent = defaultdict(list)
    by_deck_and_opponent = defaultdict(list)
    for game in games:
        by_deck[game["learner_deck"]].append(game)
        by_opponent[game["opponent_version"]].append(game)
        by_deck_and_opponent[(game["learner_deck"], game["opponent_version"])].append(game)
    return {"files": [str(path) for path in paths], "overall": summarize(games),
            "by_deck": {key: summarize(rows) for key, rows in sorted(by_deck.items())},
            "by_opponent_version": {key: summarize(rows) for key, rows in sorted(by_opponent.items())},
            "by_deck_and_opponent": {deck + " | " + version: summarize(rows)
                                     for (deck, version), rows in sorted(by_deck_and_opponent.items())}}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rollouts", type=Path, nargs="+")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = audit(args.rollouts)
    payload = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.write_text(payload, encoding="utf-8")
    print(payload)


if __name__ == "__main__":
    main()
