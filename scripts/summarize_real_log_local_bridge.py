#!/usr/bin/env python3
"""Summarize local-player bridge readiness across causal decision reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def summarize(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {
        "report": str(path),
        "decision_blocks": payload.get("decision_blocks", 0),
        "causal_observation_candidates": payload.get(
            "causal_observation_candidates", 0),
        "local_action_counts": payload.get("local_action_counts", {}),
        "local_blockers": payload.get("local_blockers", {}),
        "local_blocked_actions": payload.get("local_blocked_actions", 0),
        "public_transition_review_reasons": payload.get(
            "public_transition_review_reasons", {}),
        "training_authorized": payload.get("training_authorized", False),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reports", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = {"schema": "real-log-local-bridge-summary-v1",
              "reports": [summarize(path) for path in args.reports]}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
