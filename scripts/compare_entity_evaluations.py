#!/usr/bin/env python3
"""Compare a candidate with an initialization selfplay baseline on matched jobs.

Raw own-deck win rates confound policy quality with intrinsic deck strength.
Both evaluations must use the same seeds, ordered decks, seats and opponent.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics

from evaluate_entity_policy import outcome_score

JOB_FIELDS = ("pair_id", "seed", "candidate_deck", "opponent_deck", "candidate_seat")


def paired_deltas(candidate, baseline):
    candidate_jobs = {tuple(game[field] for field in JOB_FIELDS): game
                      for game in candidate["games"]}
    baseline_jobs = {tuple(game[field] for field in JOB_FIELDS): game
                     for game in baseline["games"]}
    if candidate_jobs.keys() != baseline_jobs.keys() or len(candidate_jobs) != len(candidate["games"]):
        raise ValueError("candidate and baseline jobs do not match uniquely")
    rows = []
    for key in sorted(candidate_jobs):
        candidate_game, baseline_game = candidate_jobs[key], baseline_jobs[key]
        if candidate_game["status"] != "complete" or baseline_game["status"] != "complete":
            raise ValueError("incomplete game cannot be a strength comparison")
        rows.append({**dict(zip(JOB_FIELDS, key)),
                     "candidate_score": outcome_score(candidate_game),
                     "baseline_score": outcome_score(baseline_game),
                     "delta": outcome_score(candidate_game) - outcome_score(baseline_game)})
    return rows


def pair_delta_interval(rows, *, resamples=5000, seed=0):
    """Exploratory percentile CI, resampling seat-swapped seed pairs."""
    groups = defaultdict(list)
    for row in rows:
        groups[row["pair_id"]].append(row)
    if any(len(group) != 2 or {row["candidate_seat"] for row in group} != {0, 1}
           for group in groups.values()):
        raise ValueError("comparison requires complete seat-swapped pairs")
    deltas = [statistics.mean(row["delta"] for row in group) for group in groups.values()]
    rng = random.Random(seed)
    means = sorted(statistics.mean(rng.choices(deltas, k=len(deltas)))
                   for _ in range(resamples))
    return {"pairs": len(deltas), "mean": statistics.mean(deltas),
            "bootstrap_95_interval": [means[int(.025 * resamples)],
                                      means[int(.975 * resamples) - 1]]}


def compare(candidate, baseline):
    candidate_params = candidate["parameters"]
    baseline_params = baseline["parameters"]
    for field in ("seed", "pairs_per_matchup", "deck_config", "cards", "max_actions",
                  "max_game_seconds", "policy_mode"):
        if candidate_params.get(field) != baseline_params.get(field):
            raise ValueError(f"evaluation settings differ: {field}")
    if candidate["checkpoint_sha256"]["opponent"] != baseline["checkpoint_sha256"]["opponent"]:
        raise ValueError("evaluations used different frozen opponents")
    if baseline["checkpoint_sha256"]["candidate"] != baseline["checkpoint_sha256"]["opponent"]:
        raise ValueError("baseline candidate and opponent must be the same checkpoint")
    if candidate.get("deck_config_sha256") != baseline.get("deck_config_sha256"):
        raise ValueError("deck configuration changed between evaluations")
    if candidate.get("source_sha256") != baseline.get("source_sha256"):
        raise ValueError("game rules changed between evaluations")
    rows = paired_deltas(candidate, baseline)
    if not rows:
        raise ValueError("no paired games")
    groups = defaultdict(list)
    for row in rows:
        groups[row["candidate_deck"]].append(row)
    return {"candidate": candidate_params["candidate"],
            "baseline": baseline_params["candidate"],
            "games": len(rows),
            "candidate_score": statistics.mean(row["candidate_score"] for row in rows),
            "baseline_score": statistics.mean(row["baseline_score"] for row in rows),
            "mean_score_delta": statistics.mean(row["delta"] for row in rows),
            "paired_delta": pair_delta_interval(rows),
            "by_candidate_deck": {
                deck: {"games": len(items),
                       "candidate_score": statistics.mean(item["candidate_score"] for item in items),
                       "baseline_score": statistics.mean(item["baseline_score"] for item in items),
                       "mean_score_delta": statistics.mean(item["delta"] for item in items),
                       "paired_delta": pair_delta_interval(items)}
                for deck, items in sorted(groups.items())},
            "paired_games": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.candidate.read_text(encoding="utf-8")),
                     json.loads(args.baseline.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "paired_games"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
