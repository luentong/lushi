"""Unified fail-closed gate for live model recommendations."""

from __future__ import annotations

from typing import Any


def evaluate_gate(*, event_stream_closed: bool, session_ready: bool,
                  beliefs: dict[str, Any] | None = None,
                  state_matches: bool = False,
                  mode: str = "closed",
                  belief_action_consensus: bool = False) -> dict[str, Any]:
    reasons: list[str] = []
    if not event_stream_closed:
        reasons.append("event_stream_not_closed")
    if not session_ready:
        reasons.append("initial_state_incomplete")
    if beliefs:
        for controller, belief in beliefs.items():
            compatible = belief.compatible() if hasattr(belief, "compatible") else bool(belief.get("compatible", False))
            if hasattr(belief, "candidate_decks"):
                candidate_count = len(belief.candidate_decks)
            elif isinstance(belief, dict):
                candidate_count = len(belief.get("candidate_decks", []))
            else:
                candidate_count = 0
            if not compatible:
                reasons.append(f"belief_conflict:{controller}")
            if candidate_count == 0 and controller == "2":
                reasons.append(f"opponent_candidates_empty:{controller}")
    if not state_matches and mode != "belief":
        reasons.append("simulator_state_not_verified")
    if mode == "belief" and not belief_action_consensus:
        reasons.append("belief_action_consensus_not_verified")
    belief_ready = mode == "belief" and session_ready and event_stream_closed and not any(
        reason.startswith(("belief_conflict", "opponent_candidates_empty")) for reason in reasons
    )
    return {"available": not reasons, "belief_mode_ready": belief_ready,
            "mode": mode, "reasons": reasons}
