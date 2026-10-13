#!/usr/bin/env python3
"""Build an auditable replay/bridge report from sanitized Power.log JSON."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.belief_state import build_beliefs
from hsa.live_replay import (audit_post_action_source_reveals,
                             build_simulator_action_plan, make_replay_cursor)
from hsa.live_state import reconstruct_game
from hsa.recommendation_gate import evaluate_gate


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--candidate-decks", type=Path, default=None)
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    game = payload["games"][-1] if payload.get("games") else payload
    state = reconstruct_game(game)
    diagnostics, cursor = make_replay_cursor(game)
    plans = build_simulator_action_plan(diagnostics)
    post_action_reveals = audit_post_action_source_reveals(game, diagnostics)
    candidates = json.loads(args.candidate_decks.read_text(encoding="utf-8")) if args.candidate_decks else {}
    beliefs = build_beliefs(diagnostics.deck_counts, diagnostics.unknown_deck_slots,
                            candidate_decks=candidates)
    report = {
        "state": state.visible(),
        "replay": diagnostics.as_dict(),
        "cursor": {"event_count": len(diagnostics.events), "index": cursor.index,
                    "done": cursor.done},
        "action_plan": {"total": len(plans), "mappable": sum(p.mappable for p in plans),
                        "definition": "structurally mappable player-decision descriptors; not verified training labels",
                        "by_kind": dict(Counter(p.kind for p in plans)),
                        "blocked_reasons": dict(Counter(p.reason for p in plans if not p.mappable)),
                        "post_action_revealed_hidden_plays": len(post_action_reveals),
                        "training_authorized": False,
                        "blocked": next(({"index": p.index, "reason": p.reason}
                                         for p in plans if not p.mappable), None)},
        "beliefs": {key: value.summary() for key, value in beliefs.items()},
        "recommendation_gate": evaluate_gate(
            event_stream_closed=diagnostics.event_stream_closed,
            session_ready=False, beliefs=beliefs, state_matches=False,
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "events": len(diagnostics.events),
                      "structurally_mappable_decisions": sum(p.mappable for p in plans),
                      "training_authorized": False}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
