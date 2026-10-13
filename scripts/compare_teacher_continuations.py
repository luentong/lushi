#!/usr/bin/env python3
"""Cross-check root-action outcome evidence under two frozen continuations.

This is diagnostic only. A positive result does not certify optimal play or
authorize distilling the search action into the policy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def compare_reports(left: dict, right: dict) -> dict:
    if left.get("status") != "complete" or right.get("status") != "complete":
        raise ValueError("both continuation reports must be complete")
    for key in ("source_audit", "replicates", "max_actions"):
        if left.get(key) != right.get(key):
            raise ValueError(f"continuation reports disagree on {key}")
    left_rows = {(r["game_seed"], r["step"]): r for r in left["rows"]}
    right_rows = {(r["game_seed"], r["step"]): r for r in right["rows"]}
    if len(left_rows) != len(left["rows"]) or len(right_rows) != len(right["rows"]):
        raise ValueError("duplicate root in continuation report")
    if left_rows.keys() != right_rows.keys():
        raise ValueError("continuations did not audit identical roots")
    rows = []
    for key in sorted(left_rows):
        a, b = left_rows[key], right_rows[key]
        for field in ("deck", "teacher_action", "model_action"):
            if a[field] != b[field]:
                raise ValueError(f"root {key} disagrees on {field}")
        ac, bc = a["comparison"], b["comparison"]
        def direction(item):
            delta = item["score_delta"]
            return "undecided" if delta is None else (
                "teacher" if delta > 0 else "model" if delta < 0 else "tie")
        rows.append({"game_seed": key[0], "step": key[1], "deck": a["deck"],
                     "teacher_action": a["teacher_action"],
                     "model_action": a["model_action"],
                     "left": {**ac, "direction": direction(ac)},
                     "right": {**bc, "direction": direction(bc)}})
    return {
        "schema": "teacher-continuation-comparison-v1",
        "training_authorized": False,
        "left_continuation": left["continuation"],
        "right_continuation": right["continuation"],
        "left_seed": left.get("seed"),
        "right_seed": right.get("seed"),
        "roots": len(rows),
        "both_favor_teacher": sum(r["left"]["direction"] == "teacher"
                                  and r["right"]["direction"] == "teacher"
                                  for r in rows),
        "both_favor_model": sum(r["left"]["direction"] == "model"
                                and r["right"]["direction"] == "model"
                                for r in rows),
        "opposite_directions": sum({r["left"]["direction"],
                                     r["right"]["direction"]} == {"teacher", "model"}
                                   for r in rows),
        "rows": rows,
        "limitation": "Frozen continuations are not optimal opponents; roots were selected for search/model disagreement. Directions are compared by root, not paired across continuation policies.",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--left", type=Path, required=True)
    parser.add_argument("--right", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; use a new experiment name")
    result = compare_reports(json.loads(args.left.read_text(encoding="utf-8")),
                             json.loads(args.right.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({key: result[key] for key in (
        "roots", "both_favor_teacher", "both_favor_model", "opposite_directions")}))


if __name__ == "__main__":
    main()
