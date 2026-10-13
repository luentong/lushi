#!/usr/bin/env python3
"""Estimate card-level opening effects from single-card randomized deviations."""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import random
import statistics

from audit_mulligan_actions import opening
from compare_entity_evaluations import JOB_FIELDS, paired_deltas, pair_delta_interval


def bootstrap_interval(values, *, seed=0, samples=2000):
    if not values:
        return None
    rng = random.Random(seed)
    means = sorted(statistics.mean(rng.choices(values, k=len(values))) for _ in range(samples))
    return [means[int(samples * .025)], means[int(samples * .975) - 1]]


def analyze(flip_report, baseline_report):
    for field in ("checkpoint_sha256", "source_sha256", "deck_config_sha256"):
        if flip_report.get(field) != baseline_report.get(field):
            raise ValueError(f"paired evaluations differ: {field}")
    for field in ("seed", "pairs_per_matchup", "deck_config", "cards", "max_actions",
                  "max_game_seconds", "manual_mulligan", "opponent_mulligan_policy"):
        if flip_report["parameters"].get(field) != baseline_report["parameters"].get(field):
            raise ValueError(f"paired evaluations differ: {field}")
    if (flip_report["parameters"]["candidate_mulligan_policy"] != "single_flip"
            or baseline_report["parameters"]["candidate_mulligan_policy"] != "baseline"
            or flip_report["parameters"]["opponent_mulligan_policy"] != "baseline"):
        raise ValueError("expected single-card flip against fixed baseline opening")
    games_a = {tuple(g[field] for field in JOB_FIELDS): g for g in flip_report["games"]}
    games_b = {tuple(g[field] for field in JOB_FIELDS): g for g in baseline_report["games"]}
    deltas = paired_deltas(flip_report, baseline_report)
    rows = []
    for outcome in deltas:
        key = tuple(outcome[field] for field in JOB_FIELDS)
        offered_a, flip, costs_a = opening(
            json.loads(Path(games_a[key]["trace"]).read_text(encoding="utf-8")), key[-1])
        offered_b, baseline, costs_b = opening(
            json.loads(Path(games_b[key]["trace"]).read_text(encoding="utf-8")), key[-1])
        if offered_a != offered_b or costs_a != costs_b:
            raise ValueError("paired opening hands differ")
        difference = flip - baseline, baseline - flip
        if sum(difference[0].values()) + sum(difference[1].values()) != 1:
            raise ValueError("treatment did not flip exactly one card")
        card_id = next(iter(difference[0] or difference[1]))
        treatment = "replace" if difference[0] else "keep"
        rows.append({"deck": outcome["candidate_deck"], "card_id": card_id,
                     "cost": costs_a[card_id], "treatment": treatment,
                     "seed": outcome["seed"], "seat": outcome["candidate_seat"],
                     "treatment_score_delta": outcome["delta"],
                     "replace_minus_keep": (outcome["delta"] if treatment == "replace"
                                            else -outcome["delta"])})
    groups = defaultdict(list)
    for row in rows:
        groups[(row["deck"], row["card_id"])].append(row)
    effects = []
    for (deck, card_id), items in sorted(groups.items()):
        values = [row["replace_minus_keep"] for row in items]
        ci = bootstrap_interval(values, seed=sum(ord(c) for c in deck + card_id))
        effects.append({"deck": deck, "card_id": card_id, "cost": items[0]["cost"],
                        "n": len(items), "replace_treatments": sum(
                            row["treatment"] == "replace" for row in items),
                        "replace_minus_keep_mean": statistics.mean(values),
                        "bootstrap_95_interval": ci,
                        "eligible_for_teacher": len(items) >= 30 and (ci[0] > 0 or ci[1] < 0)})
    by_cost = {}
    for cost in sorted({row["cost"] for row in rows}):
        values = [row["replace_minus_keep"] for row in rows if row["cost"] == cost]
        interval = bootstrap_interval(values, seed=cost + 410)
        by_cost[str(cost)] = {"n": len(values), "replace_minus_keep_mean": statistics.mean(values),
                              "bootstrap_95_interval": interval,
                              "eligible_for_teacher": len(values) >= 30 and
                              (interval[0] > 0 or interval[1] < 0)}
    return {"games": len(rows), "seat_paired_score_delta": pair_delta_interval(deltas),
            "treatment_favored": sum(r["treatment_score_delta"] > 0 for r in rows),
            "control_favored": sum(r["treatment_score_delta"] < 0 for r in rows),
            "unchanged": sum(r["treatment_score_delta"] == 0 for r in rows),
            "teacher_eligible_cards": sum(e["eligible_for_teacher"] for e in effects),
            "by_cost": by_cost, "effects": effects, "rows": rows}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--single-flip", type=Path, required=True)
    p.add_argument("--baseline", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = analyze(json.loads(args.single_flip.read_text(encoding="utf-8")),
                     json.loads(args.baseline.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("games", "treatment_favored", "control_favored",
                                            "unchanged", "teacher_eligible_cards")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
