"""Rank audited teacher-root disagreements with paired, multiplicity-aware tests.

This produces review candidates, never replacement teacher labels. The
continuation policy is not an optimal-play oracle.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from math import comb
from pathlib import Path


def sign_p(better: int, worse: int) -> float | None:
    n = better + worse
    if n == 0:
        return None
    return min(1.0, 2 * sum(comb(n, i) for i in range(min(better, worse) + 1))
               / (2 ** n))


def summarize(report: dict) -> dict:
    if report.get("schema") != "teacher-shard-paired-root-audit-v1":
        raise ValueError("not a teacher-shard root audit")
    accepted = [row for row in report["replay_status"] if row["status"] == "verified"]
    rejected = [row for row in report["replay_status"] if row["status"] == "rejected"]
    invalid_outcomes = sum(result.get("invalid", 0)
                           for audit in report["audits"]
                           for result in audit.get("results", ()))
    truncated_outcomes = sum(result.get("truncated", 0)
                             for audit in report["audits"]
                             for result in audit.get("results", ()))
    root_value_diagnostics = []
    for audit in report["audits"]:
        values = audit.get("teacher_action_values")
        visits = audit.get("teacher_action_visits")
        results = audit.get("results", ())
        if not values or len(values) != len(results):
            continue
        selected_index = next((i for i, row in enumerate(results)
                               if row["action_key"] == audit["teacher_selected_key"]), None)
        if selected_index is None:
            raise ValueError("selected teacher action missing from root results")
        root_value_diagnostics.append({
            "game_index": audit["game_index"], "ply": audit["ply"],
            "selected_q": values[selected_index], "best_sampled_q": max(values),
            "q_gap": max(values) - values[selected_index],
            "selected_visits": (visits[selected_index]
                                if visits and len(visits) == len(values) else None),
        })
    candidates = []
    for audit in report["audits"]:
        for comparison in audit["paired_comparisons"]:
            better = comparison["alternative_better"]
            worse = comparison["selected_better"]
            paired = comparison["paired_decided"]
            if better + worse + comparison["tied"] != paired:
                raise ValueError("paired outcome counts do not add up")
            candidates.append({
                "game_index": audit["game_index"], "game_seed": audit["game_seed"],
                "deck_a": audit["deck_a"], "deck_b": audit["deck_b"],
                "ply": audit["ply"], "teacher_selected": audit["teacher_selected"],
                "alternative": comparison["alternative"],
                "paired_decided": paired, "better": better, "worse": worse,
                "tied": comparison["tied"],
                "mean_score_difference": comparison["mean_score_difference"],
                "paired_sign_p_raw": sign_p(better, worse),
            })
    # Holm controls the family-wise false-positive rate over *all* inspected
    # alternatives, rather than highlighting the best-looking branch alone.
    testable = sorted((row for row in candidates if row["paired_sign_p_raw"] is not None),
                      key=lambda row: row["paired_sign_p_raw"])
    adjusted = 0.0
    for rank, row in enumerate(testable):
        adjusted = max(adjusted, min(1.0, row["paired_sign_p_raw"] *
                                     (len(testable) - rank)))
        row["paired_sign_p_holm"] = adjusted
    candidates.sort(key=lambda row: (-(row["better"] - row["worse"]),
                                     -row["paired_decided"], row["game_index"]))
    return {
        "schema": "teacher-shard-root-review-v1",
        "source_manifest": report["manifest"],
        "continuation_policy": report["continuation_policy"],
        "verified_games": len(accepted), "rejected_games": len(rejected),
        "fingerprint_drifted_verified_games": sum(
            bool(row.get("fingerprint_drift")) for row in accepted),
        "audited_roots": len(report["audits"]),
        "ordered_matchups": {f"{a} vs {b}": count for (a, b), count in sorted(
            Counter((row["deck_a"], row["deck_b"])
                    for row in report["audits"]).items())},
        "inspected_alternatives": len(candidates),
        "tested_alternatives": len(testable),
        "invalid_outcomes": invalid_outcomes,
        "truncated_outcomes": truncated_outcomes,
        "teacher_selected_not_max_sampled_q": sum(
            row["q_gap"] > 1e-12 for row in root_value_diagnostics),
        "teacher_q_diagnostics": root_value_diagnostics,
        "holm_positive_alternatives": sum(
            row.get("paired_sign_p_holm", 1.0) < 0.05 and
            row["better"] > row["worse"] for row in candidates),
        "candidates": candidates,
        "limitation": "Exploratory sampled roots; sign tests are continuation-dependent and not optimal-action proofs. Do not relabel automatically.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audit", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = summarize(json.loads(args.audit.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "verified_games", "rejected_games", "audited_roots",
        "inspected_alternatives", "invalid_outcomes", "truncated_outcomes",
        "holm_positive_alternatives")},
        ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
