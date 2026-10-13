#!/usr/bin/env python3
"""Audit the actual opening decisions in two matched evaluation runs."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

from compare_entity_evaluations import JOB_FIELDS, paired_deltas


def opening(trace, seat):
    hand = trace["initial_state"]["players"][seat]["hand"]
    offered = Counter(card["id"] for card in hand)
    costs = {card["id"]: card["cost"] for card in hand}
    replaced = Counter()
    for step in trace["steps"]:
        if step["turn_before"] != 0 or not step["candidate_acted"]:
            continue
        if step["action_key"][0] == "MULLIGAN_TOGGLE":
            card_id = step["description"].rsplit("[", 1)[1].split("]", 1)[0]
            replaced[card_id] += 1
    if replaced - offered:
        raise ValueError("replacement did not come from offered hand")
    return offered, replaced, costs


def audit(model_report, baseline_report):
    games_a = {tuple(g[field] for field in JOB_FIELDS): g for g in model_report["games"]}
    games_b = {tuple(g[field] for field in JOB_FIELDS): g for g in baseline_report["games"]}
    deltas = paired_deltas(model_report, baseline_report)
    by_deck = defaultdict(list)
    for row in deltas:
        key = tuple(row[field] for field in JOB_FIELDS)
        a, b = games_a[key], games_b[key]
        offer_a, selected_a, costs_a = opening(json.loads(Path(a["trace"]).read_text()), key[-1])
        offer_b, selected_b, costs_b = opening(json.loads(Path(b["trace"]).read_text()), key[-1])
        if offer_a != offer_b or costs_a != costs_b:
            raise ValueError("paired games did not share the same opening hand")
        by_deck[row["candidate_deck"]].append({
            "pair_id": row["pair_id"], "seed": row["seed"], "seat": row["candidate_seat"],
            "offered": dict(offer_a), "model_replaced": dict(selected_a),
            "baseline_replaced": dict(selected_b), "costs": costs_a,
            "decision_changed": selected_a != selected_b, "score_delta": row["delta"],
        })
    result = {}
    for deck, rows in sorted(by_deck.items()):
        changed = [r for r in rows if r["decision_changed"]]
        result[deck] = {
            "games": len(rows), "changed_opening_games": len(changed),
            "changed_opening_score_delta": sum(r["score_delta"] for r in changed),
            "model_low_cost_replacements": sum(n for r in rows for card, n in
                                               r["model_replaced"].items() if r["costs"][card] <= 2),
            "model_high_cost_keeps": sum(n - r["model_replaced"].get(card, 0)
                                         for r in rows for card, n in r["offered"].items()
                                         if r["costs"][card] >= 4),
            "changed_examples": changed[:8],
        }
    return {"by_candidate_deck": result,
            "total_changed_opening_games": sum(v["changed_opening_games"] for v in result.values()),
            "total_games": len(deltas)}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--model-evaluation", type=Path, required=True)
    p.add_argument("--baseline-evaluation", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    result = audit(json.loads(args.model_evaluation.read_text(encoding="utf-8")),
                   json.loads(args.baseline_evaluation.read_text(encoding="utf-8")))
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"total_changed_opening_games": result["total_changed_opening_games"],
                      "total_games": result["total_games"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
