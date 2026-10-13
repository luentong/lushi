#!/usr/bin/env python3
"""Audit action-credit signs and critic drift in saved on-policy trajectories.

This is a diagnostic, not an estimator of which action was actually optimal.
It reads only metadata/value columns; serialized observer views are discarded.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
import math
from pathlib import Path

from train_entity_selfplay import assign_ppo_advantages


def compact_games(paths):
    games = {}
    for path in paths:
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                source = json.loads(line)
                key = (str(path), source["game_seed"])
                if key not in games:
                    games[key] = {"rows": [], "deck_a": source["deck_a"],
                                  "deck_b": source["deck_b"],
                                  "seat": source["actor"],
                                  "opponent": source["opponent_version"]}
                game = games[key]
                if (source["deck_a"], source["deck_b"], source["actor"],
                        source["opponent_version"]) != (game["deck_a"], game["deck_b"],
                                                         game["seat"], game["opponent"]):
                    raise ValueError(f"inconsistent episode metadata: {key}")
                game["rows"].append({"actor": source["actor"],
                                     "old_value": source["old_value"],
                                     "return": source["return"],
                                     "saved_advantage": source["advantage"]})
    return games


def summarize(games, gae_lambda):
    by_deck = defaultdict(lambda: {"games": 0, "wins": 0, "draws": 0, "decisions": 0,
                                   "gae_positive_loss": 0, "gae_negative_win": 0,
                                   "first_value_brier_sum": 0.0,
                                   "game_value_brier_sum": 0.0})
    totals = {"games": 0, "decisions": 0, "wins": 0, "draws": 0,
              "gae_credit_sign_changes": 0, "positive_credit_in_lost_games": 0,
              "negative_credit_in_won_games": 0}
    for game in games.values():
        rows = game["rows"]
        if not rows or any(row["return"] != rows[0]["return"] for row in rows):
            raise ValueError("mixed or empty episode")
        outcome = rows[0]["return"]
        replay = [{"actor": row["actor"], "old_value": row["old_value"]} for row in rows]
        assign_ppo_advantages(replay, outcome, mode="gae", gae_lambda=gae_lambda)
        for old, new in zip(rows, replay):
            expected = outcome - old["old_value"]
            if not math.isclose(old["saved_advantage"], expected, abs_tol=1e-5):
                raise ValueError("saved trajectory is not terminal-credit PPO")
            if expected * new["advantage"] < 0:
                totals["gae_credit_sign_changes"] += 1
        deck = game["deck_a"] if game["seat"] == 0 else game["deck_b"]
        summary = by_deck[deck]
        summary["games"] += 1
        summary["wins"] += outcome == 1
        summary["draws"] += outcome == 0
        summary["decisions"] += len(rows)
        summary["first_value_brier_sum"] += ((rows[0]["old_value"] - outcome) / 2) ** 2
        summary["game_value_brier_sum"] += sum(
            ((row["old_value"] - outcome) / 2) ** 2 for row in rows) / len(rows)
        for row in replay:
            if outcome < 0 and row["advantage"] > 0:
                summary["gae_positive_loss"] += 1
                totals["positive_credit_in_lost_games"] += 1
            if outcome > 0 and row["advantage"] < 0:
                summary["gae_negative_win"] += 1
                totals["negative_credit_in_won_games"] += 1
        totals["games"] += 1
        totals["decisions"] += len(rows)
        totals["wins"] += outcome == 1
        totals["draws"] += outcome == 0
    for summary in by_deck.values():
        summary["win_rate"] = summary["wins"] / summary["games"]
        summary["first_value_brier"] = summary.pop("first_value_brier_sum") / summary["games"]
        summary["game_value_brier"] = summary.pop("game_value_brier_sum") / summary["games"]
    return {"gae_lambda": gae_lambda, "totals": totals,
            "by_learner_deck": dict(sorted(by_deck.items()))}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("inputs", nargs="+", type=Path)
    parser.add_argument("--gae-lambda", type=float, default=0.95)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = summarize(compact_games(args.inputs), args.gae_lambda)
    result["inputs"] = [str(path) for path in args.inputs]
    output = json.dumps(result, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
