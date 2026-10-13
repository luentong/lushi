"""Partial deck evidence from identities revealed on opening deck entities.

Only reveals already observed at a requested packet boundary are eligible.
This identifies constraints on a deck hypothesis, never its hidden order or
the complete submitted decklist. New entities are not opening-deck evidence.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from .live_state import _is_game_reset, _ordered_game_events


def collect_deck_evidence(
    game: dict[str, Any], eligible_card_ids: set[str], *,
    before_packet: int | None = None,
) -> dict[str, Any]:
    """Track first visible identities of opening slots, without future reveals.

    ``before_packet`` is exclusive, suitable for a decision's pre-action state.
    ChangeEntity or creator/copy tags before a first reveal invalidate that
    slot as evidence of the submitted list. Later transformation cannot erase
    an identity that was already publicly revealed. Reset snapshots are not
    trusted to preserve entity provenance, so stop collecting at GAME_RESET.
    Eligible identities include collectible cards and known legal companion
    cards encoded in deckstrings, even when the latter are not collectible.
    """
    if game.get("identity_timing") != "causal_reveal_only":
        raise ValueError("deck evidence requires a causal import")
    first_block = min((int(block["packet_id"]) for block in game.get("blocks", ())
                       if block.get("packet_id") is not None), default=None)
    if first_block is None:
        return {"status": "opening_boundary_missing", "observations": [],
                "controllers": {}, "before_packet": before_packet}
    slots: dict[str, dict[str, Any]] = {}
    # Preamble also contains later top-level packets. Bound by packet order.
    for row in game.get("preamble", ()):
        packet = row.get("packet_id")
        if (row.get("kind") != "FullEntity" or packet is None
                or int(packet) >= first_block
                or before_packet is not None and int(packet) >= before_packet):
            continue
        tags = {str(tag["tag"]): tag.get("value") for tag in row.get("tags", ())}
        owner = str(tags.get("CONTROLLER"))
        if tags.get("ZONE") == "DECK" and owner in {"1", "2"}:
            slots[str(row["entity"])] = {
                "controller": owner, "opening_packet_id": int(packet),
                "excluded_reason": None, "revealed": False,
            }
    observations = []
    reset_packet = None
    for _key, kind, row, _parent in _ordered_game_events(game):
        if row.get("packet_id") is None:
            continue
        packet = int(row["packet_id"])
        if before_packet is not None and packet >= before_packet:
            break
        if kind == "block":
            if _is_game_reset(row):
                reset_packet = packet
                break
            continue
        slot = slots.get(str(row.get("entity")))
        if slot is None or slot["revealed"] or slot["excluded_reason"]:
            continue
        tags = {str(tag["tag"]): tag.get("value") for tag in row.get("tags", ())}
        if row.get("kind") == "TagChange":
            tags[str(row.get("tag"))] = row.get("value")
        if row.get("kind") == "ChangeEntity":
            slot["excluded_reason"] = "transformed_before_identity_reveal"
        elif any(tags.get(tag) not in (None, 0, "0", "") for tag in
                 ("CREATOR", "COPIED_FROM_ENTITY_ID")):
            slot["excluded_reason"] = "created_or_copied_before_identity_reveal"
        elif row.get("card_id"):
            card_id = str(row["card_id"])
            if card_id not in eligible_card_ids:
                slot["excluded_reason"] = "first_identity_is_not_eligible_deck_card"
            else:
                slot["revealed"] = True
                observations.append({
                    "entity": str(row["entity"]),
                    "controller": slot["controller"], "card_id": card_id,
                    "opening_packet_id": slot["opening_packet_id"],
                    "revealed_packet_id": packet,
                })
    controllers = {}
    for owner in ("1", "2"):
        own_slots = [slot for slot in slots.values() if slot["controller"] == owner]
        controllers[owner] = {
            "opening_entities": len(own_slots),
            "observed_counts": dict(Counter(row["card_id"] for row in observations
                                            if row["controller"] == owner)),
            "unrevealed_entities": sum(not slot["revealed"] and not slot["excluded_reason"]
                                       for slot in own_slots),
            "all_opening_slots_identified": bool(own_slots) and all(
                slot["revealed"] for slot in own_slots),
            "excluded_reasons": dict(Counter(slot["excluded_reason"] for slot in own_slots
                                             if slot["excluded_reason"])),
        }
    return {"status": "partial_opening_entity_evidence",
            "before_packet": before_packet, "reset_boundary": reset_packet,
            "observations": observations, "controllers": controllers,
            "complete_deck_identified": False}
