#!/usr/bin/env python3
"""Export causally ordered real-log observations for audit, never training.

The output deliberately carries no policy/value labels or inferred opponent
hands. A candidate only means its own action and preceding public snapshot
were observable; legality and state-transition validation remain separate.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.real_log_decisions import (extract_causal_decision_records,
                                    infer_observer_controller)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="sanitized causal Power.log JSON")
    parser.add_argument("--local-controller", type=int, choices=(1, 2), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output exists; choose a new audit file")
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    game = payload["games"][-1] if payload.get("games") else payload
    observer = infer_observer_controller(game)
    if (observer["controller"] is not None
            and observer["controller"] != args.local_controller):
        parser.error("--local-controller contradicts opening-hand visibility")
    records = extract_causal_decision_records(
        game, local_controller=args.local_controller)
    local_records = [row for row in records
                     if row.get("actor_controller") == args.local_controller]
    report = {
        "schema": "real-log-causal-decisions-v1",
        "source_sha256": payload.get("source_sha256"),
        "input_identity_timing": game.get("identity_timing"),
        "local_controller": args.local_controller,
        "observer_inference": observer,
        "decision_blocks": len(records),
        "causal_observation_candidates": sum(
            row["causal_observation_candidate"] for row in records),
        "client_option_confirmed_candidates": sum(
            row["causal_observation_candidate"] and row["client_option_confirmed"]
            for row in records),
        "trade_candidates": sum(
            row["causal_observation_candidate"] and row["action"]["kind"] == "TRADE"
            for row in records),
        "candidate_action_counts": dict(Counter(
            row["action"]["kind"] for row in records
            if row["causal_observation_candidate"])),
        "candidates_with_consistent_public_transition": sum(
            row["causal_observation_candidate"]
            and row["public_transition_audit"]["status"] == "public_transition_consistent"
            for row in records),
        "blockers": dict(Counter(
            reason for row in records for reason in row["blockers"])),
        "local_action_counts": dict(Counter(
            row["action"]["kind"] for row in local_records)),
        "local_blockers": dict(Counter(
            reason for row in local_records for reason in row["blockers"])),
        "local_blocked_actions": sum(bool(row["blockers"])
                                     for row in local_records),
        "public_transition_review_reasons": dict(Counter(
            reason for row in records if row["causal_observation_candidate"]
            for reason in row["public_transition_audit"]["blockers"])),
        "mana_cost_checks": dict(Counter(
            row["public_transition_audit"]["mana_cost_check"]
            for row in records if row["causal_observation_candidate"])),
        "training_authorized": False,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "decision_blocks", "causal_observation_candidates",
        "client_option_confirmed_candidates", "trade_candidates",
        "candidate_action_counts",
        "candidates_with_consistent_public_transition", "blockers",
        "local_action_counts", "local_blockers", "local_blocked_actions",
        "public_transition_review_reasons",
        "mana_cost_checks",
        "training_authorized")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
