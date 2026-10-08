"""Batch-scan search traces for policy/value hard-negative candidates.

The scanner is deliberately model-agnostic: it consumes saved traces that
contain ``steps``/``trace``/``actions`` and ranked root alternatives.  It does
not infer quality from card names; it records measurable search disagreement
for later high-budget relabeling.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def _rows(doc: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ("steps", "trace", "actions", "rows"):
        value = doc.get(key)
        if isinstance(value, list):
            return [row for row in value if isinstance(row, dict)]
    return []


def _state_mana(row: dict[str, Any]) -> int | None:
    state = row.get("state_before")
    if not isinstance(state, dict):
        return None
    players = state.get("players")
    actor = row.get("actor")
    if not isinstance(players, list) or not isinstance(actor, int):
        return None
    # Traces use zero-based actors; tolerate one-based actor values as well.
    index = actor if 0 <= actor < len(players) else actor - 1
    if not 0 <= index < len(players):
        return None
    mana = players[index].get("mana") if isinstance(players[index], dict) else None
    if isinstance(mana, list) and mana:
        return int(mana[0])
    if isinstance(mana, (int, float)):
        return int(mana)
    return None


def scan_file(path: Path, *, regret_gap: float, low_visit: float,
              close_value: float, min_mana: int) -> list[dict[str, Any]]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(doc, dict):
        return []
    findings: list[dict[str, Any]] = []
    for row in _rows(doc):
        alternatives = row.get("ranked_alternatives")
        if not isinstance(alternatives, list):
            continue
        selected = next((item for item in alternatives
                         if isinstance(item, dict) and item.get("selected")), None)
        if not selected or selected.get("mean_value") is None:
            continue
        valued = [item for item in alternatives
                  if isinstance(item, dict) and item.get("mean_value") is not None]
        if not valued:
            continue
        best = max(valued, key=lambda item: float(item["mean_value"]))
        selected_value = float(selected["mean_value"])
        best_value = float(best["mean_value"])
        gap = best_value - selected_value
        share = float(selected.get("visit_share", 1.0))
        description = str(row.get("description", ""))
        legal_count = int(row.get("legal_action_count", len(alternatives)))
        mana = _state_mana(row)
        reasons: list[str] = []
        if gap >= regret_gap and best.get("action") != selected.get("action"):
            reasons.append("value_regret")
        if share <= low_visit and legal_count > 1:
            reasons.append("low_visit_share")
        if len(valued) >= 2:
            ranked = sorted((float(item["mean_value"]) for item in valued), reverse=True)
            if ranked[0] - ranked[1] <= close_value:
                reasons.append("close_candidates")
        if "END_TURN" in description and (mana or 0) >= min_mana and legal_count > 1:
            reasons.append("end_turn_with_mana")
        if not reasons:
            continue
        findings.append({
            "source": str(path),
            "deck_a": doc.get("deck_a"),
            "deck_b": doc.get("deck_b"),
            "seed": doc.get("seed"),
            "step": row.get("step"),
            "turn": row.get("turn_before", row.get("turn")),
            "actor": row.get("actor"),
            "description": description,
            "reasons": reasons,
            "legal_action_count": legal_count,
            "mana_before": mana,
            "selected": selected.get("action"),
            "selected_mean_value": selected_value,
            "selected_visit_share": share,
            "best_alternative": best.get("action"),
            "best_mean_value": best_value,
            "regret_gap": gap,
            "alternatives": alternatives,
            "state_before": row.get("state_before"),
        })
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--regret-gap", type=float, default=0.20)
    parser.add_argument("--low-visit", type=float, default=0.50)
    parser.add_argument("--close-value", type=float, default=0.15)
    parser.add_argument("--min-mana", type=int, default=1)
    args = parser.parse_args()
    files = sorted(args.root.rglob("*.json"))
    findings: list[dict[str, Any]] = []
    scanned = 0
    trace_files = 0
    for path in files:
        if path.resolve() == args.output.resolve():
            continue
        scanned += 1
        rows = scan_file(path, regret_gap=args.regret_gap,
                         low_visit=args.low_visit,
                         close_value=args.close_value,
                         min_mana=args.min_mana)
        if rows:
            trace_files += 1
            findings.extend(rows)
    findings.sort(key=lambda item: (float(item["regret_gap"]),
                                    float(item["selected_visit_share"])), reverse=True)
    result = {
        "schema_version": 1,
        "scanned_json_files": scanned,
        "trace_files_with_findings": trace_files,
        "candidate_count": len(findings),
        "thresholds": {
            "regret_gap": args.regret_gap,
            "low_visit": args.low_visit,
            "close_value": args.close_value,
            "min_mana": args.min_mana,
        },
        "candidates": findings,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in
                      ("scanned_json_files", "trace_files_with_findings", "candidate_count")},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
