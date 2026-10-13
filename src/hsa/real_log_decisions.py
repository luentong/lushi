"""Causal, privacy-safe decision records from a normalized Power.log.

These are observation/action audit records, not expert labels. No hidden hand
identity, inferred deck order, legal-action claim, or simulator outcome is
fabricated. Only a separate rule/deck/legality check may promote a record for
training.
"""

from __future__ import annotations

from typing import Any

from .live_state import LiveGameState, _ordered_game_events


_DECISION_BLOCKS = frozenset({"PLAY", "ATTACK", "TRADE", "LOCATION", "TURN_END"})


def audit_client_selected_options(game: dict[str, Any]) -> list[dict[str, Any]]:
    """Match SendOption to the preceding client option and resulting block.

    A selected option is direct evidence of client legality only when the
    option has no error and its source and target match the next player-action
    block. ``DECK_ACTION`` is a Tradeable decision only under this evidence.
    """
    rows = list(game.get("preamble", ()))
    for block in game.get("blocks", ()):
        rows.extend(block.get("effects", ()))
    offers = sorted((row for row in rows if row.get("kind") == "Options"
                     and row.get("ts")), key=lambda row: row["ts"])
    sends = sorted((row for row in rows if row.get("kind") == "SendOption"
                    and row.get("packet_id") is not None),
                   key=lambda row: int(row["packet_id"]))
    blocks = sorted((block for block in game.get("blocks", ())
                     if block.get("block_type") in {"PLAY", "ATTACK", "DECK_ACTION"}
                     and block.get("packet_id") is not None),
                    key=lambda block: int(block["packet_id"]))
    result: list[dict[str, Any]] = []
    for index, send in enumerate(sends):
        previous = [offer for offer in offers if offer["ts"] <= send.get("ts", "")]
        offer = previous[-1] if previous else None
        options = [item for item in (offer or {}).get("options", ())
                   if item.get("id") == send.get("option")]
        choice = options[0] if len(options) == 1 else None
        next_send = (int(sends[index + 1]["packet_id"])
                     if index + 1 < len(sends) else float("inf"))
        matching_blocks = [block for block in blocks
                           if int(send["packet_id"]) < int(block["packet_id"]) < next_send]
        block = matching_blocks[0] if matching_blocks else None
        end_turn = send.get("option") == 0
        source_match = (choice is not None and block is not None
                        and choice.get("entity") == block.get("source_entity"))
        target_match = (block is not None and str(send.get("target") or 0)
                        == str(block.get("target_entity") or 0))
        no_error = choice is not None and choice.get("error") in (None, "NONE")
        # A matching block alone does not prove that the selected target was
        # offered by the client. Targeted Options carry their own legal-target
        # entries; fail closed if the selected entity is absent or in error.
        target_options = choice.get("options") if choice is not None else None
        if send.get("target") not in (None, 0, "0") and isinstance(target_options, list):
            offered_targets = [option for option in target_options
                               if str(option.get("entity")) == str(send["target"])]
            target_option_legal = (len(offered_targets) == 1 and
                                   offered_targets[0].get("error") in (None, "NONE"))
        else:
            target_option_legal = send.get("target") in (None, 0, "0")
        result.append({
            "send_packet_id": send["packet_id"],
            "offer_id": (offer or {}).get("id"),
            "option_id": send.get("option"),
            "block_packet_id": block.get("packet_id") if block else None,
            "block_type": block.get("block_type") if block else None,
            "source_entity": choice.get("entity") if choice else None,
            "target_entity": send.get("target"),
            "target_option_legal": target_option_legal,
            "client_option_legal": bool(
                not end_turn and no_error and source_match and target_match
                and target_option_legal),
            "reason": ("end_turn" if end_turn else
                       "client_option_and_block_match" if no_error and source_match
                       and target_match and target_option_legal else
                       "target_not_confirmed_in_client_options" if not target_option_legal
                       else "option_or_block_not_resolved"),
        })
    return result


def audit_client_end_turn_options(game: dict[str, Any]) -> dict[int, dict[str, Any]]:
    """Accept option 0 only when the next packet enters MAIN_END.

    Client Options can label end turn INVALID while the actual SendOption(0)
    is accepted. The explicit engine step change, rather than that label, is
    the causal evidence that the player ended their turn.
    """
    timeline = [(kind, item) for _, kind, item, _ in _ordered_game_events(game)]
    result: dict[int, dict[str, Any]] = {}
    for index, (kind, item) in enumerate(timeline[:-1]):
        if (kind != "row" or item.get("kind") != "SendOption"
                or item.get("option") != 0 or item.get("packet_id") is None):
            continue
        following = timeline[index + 1:index + 3]
        accepted = False
        for offset, (next_kind, next_item) in enumerate(following, start=1):
            if (next_kind not in {"row", "effect"}
                    or next_item.get("kind") != "TagChange"
                    or next_item.get("packet_id") != int(item["packet_id"]) + offset):
                break
            if next_item.get("tag") == "STEP" and next_item.get("value") == "MAIN_END":
                accepted = True
                break
        if accepted:
            result[int(item["packet_id"])] = {
                "send_packet_id": item["packet_id"], "option_id": 0,
                "client_option_legal": True,
                "reason": "send_option_followed_by_main_end",
            }
    return result


def infer_observer_controller(game: dict[str, Any]) -> dict[str, Any]:
    """Infer the local side only from card identities in the opening hand.

    This is evidence, not a guarantee: returns ``None`` if both sides expose
    identities or too few opening cards are visible. Later plays/reveals are
    excluded so they cannot retroactively identify the observer.
    """
    first_play = min(
        (int(block["packet_id"]) for block in game.get("blocks", ())
         if str(block.get("block_type") or "").upper() == "PLAY"
         and block.get("packet_id") is not None),
        default=None,
    )
    if first_play is None:
        return {"controller": None, "known_opening_hand": {"1": 0, "2": 0},
                "reason": "no_play_boundary"}
    known: dict[str, set[str]] = {"1": set(), "2": set()}
    rows = list(game.get("preamble", ()))
    for block in game.get("blocks", ()):
        rows.extend(block.get("effects", ()))
    for row in rows:
        if (row.get("kind") not in {"FullEntity", "ShowEntity"}
                or not row.get("card_id")
                or row.get("packet_id") is None
                or int(row["packet_id"]) >= first_play):
            continue
        tags = {str(tag.get("tag")): tag.get("value")
                for tag in row.get("tags", ())}
        side = str(tags.get("CONTROLLER"))
        if tags.get("ZONE") == "HAND" and side in known:
            known[side].add(str(row.get("entity")))
    counts = {side: len(entities) for side, entities in known.items()}
    inferred = (1 if counts["1"] >= 3 and counts["2"] == 0 else
                2 if counts["2"] >= 3 and counts["1"] == 0 else None)
    return {"controller": inferred, "known_opening_hand": counts,
            "reason": "opening_hand_identity_asymmetry" if inferred
                      else "insufficient_or_ambiguous_opening_evidence"}


def _public_snapshot(state: LiveGameState) -> dict[str, Any]:
    visible = state.visible()
    return {key: visible[key] for key in (
        "turn", "active_player", "game_phase", "players", "player_meta",
        "consistency_errors", "reset_count",
    )}


def _find_public_entity(snapshot: dict[str, Any], entity_id: Any) -> dict[str, Any] | None:
    if entity_id in (None, 0, "0"):
        return None
    matches = [
        {"controller": int(controller), "zone": zone, **entity}
        for controller, zones in snapshot["players"].items()
        for zone, entities in zones.items()
        for entity in entities
        if str(entity.get("entity")) == str(entity_id)
    ]
    return matches[0] if len(matches) == 1 else None


def audit_public_transition(record: dict[str, Any]) -> dict[str, Any]:
    """Check only visible zone/target consequences, not card-rule legality."""
    before = record["pre_action_public_state"]
    after = record["observed_until_next_decision"]
    action = record["action"]
    actor = record["actor_controller"]
    source = _find_public_entity(before, action["source_entity"])
    target = _find_public_entity(before, action["target_entity"])
    source_after = (_find_public_entity(after, action["source_entity"])
                    if after is not None else None)
    blockers: list[str] = []
    kind = action["kind"]
    mana_cost_check = "not_applicable"
    if kind == "PLAY" and source is not None:
        actor_meta = before["player_meta"].get(str(actor), {})
        available = actor_meta.get("mana")
        observed_cost = source.get("cost")
        try:
            available = int(available)
            observed_cost = int(observed_cost)
        except (TypeError, ValueError):
            mana_cost_check = "cost_or_mana_not_observed"
        else:
            mana_cost_check = ("observed_cost_affordable" if observed_cost <= available
                               else "observed_cost_exceeds_mana")
            if observed_cost > available:
                blockers.append("observed_cost_exceeds_available_mana")
    if kind == "TRADE" and source is not None and source["zone"] != "HAND":
        blockers.append("trade_source_not_in_hand")
    if kind == "TURN_END":
        pass
    elif source is None:
        blockers.append("source_missing_before_action")
    elif source["controller"] != actor:
        blockers.append("source_controller_mismatch")
    elif kind == "PLAY" and not (
        source["zone"] == "HAND"
        or source["zone"] == "PLAY"
        and source["card_type"] in {"HERO_POWER", "LOCATION"}
    ):
        blockers.append("play_source_not_in_hand_or_active_power_location")
    elif kind == "ATTACK" and not (
        source["zone"] == "PLAY"
        and source["card_type"] in {"HERO", "MINION"}
    ):
        blockers.append("attack_source_not_active_hero_or_minion")
    if kind == "ATTACK" and source is not None:
        try:
            attack = int(source.get("attack"))
        except (TypeError, ValueError):
            attack = None
        if attack is not None and attack <= 0:
            blockers.append("attacker_has_nonpositive_observed_attack")
    if (source is not None and action["source_card_before_action"]
            and source["card_id"] != action["source_card_before_action"]):
        blockers.append("source_identity_mismatch")
    if action["target_entity"] not in (None, 0, "0"):
        if target is None:
            blockers.append("target_missing_before_action")
        elif kind == "ATTACK" and not (
            target["zone"] == "PLAY"
            and target["card_type"] in {"HERO", "MINION"}
        ):
            blockers.append("attack_target_not_active_hero_or_minion")
        if (target is not None and action["target_card_before_action"]
                and target["card_id"] != action["target_card_before_action"]):
            blockers.append("target_identity_mismatch")
    if (kind == "PLAY" and source is not None and source["zone"] == "HAND"
            and after is not None and source_after is not None
            and source_after["zone"] == "HAND"):
        blockers.append("played_entity_still_in_hand_at_next_decision")
    if (kind == "TRADE" and source is not None and after is not None
            and (source_after is None or source_after["zone"] != "DECK")):
        blockers.append("traded_entity_not_in_deck_at_next_decision")
    return {
        "status": "public_transition_consistent" if not blockers
                  else "public_transition_requires_review",
        "source_before": (source["zone"] if source else None),
        "source_type": (source["card_type"] if source else None),
        "source_at_next_decision": (source_after["zone"] if source_after else None),
        "target_before": (target["zone"] if target else None),
        "mana_cost_check": mana_cost_check,
        "blockers": blockers,
        "rule_legality_verified": False,
    }


def extract_causal_decision_records(
    game: dict[str, Any], *, local_controller: int,
) -> list[dict[str, Any]]:
    """Pair each decision's *pre-action* public state with the next one.

    Effects between two player decisions belong to the previous transition.
    The final record uses the end-of-log state if there is no next decision.
    A completed legacy import may have backfilled future card IDs, so it is
    never eligible even as a causal observation candidate.
    """
    if local_controller not in (1, 2):
        raise ValueError("local_controller must be 1 or 2")
    causal = game.get("identity_timing") == "causal_reveal_only"
    selected = {row["block_packet_id"]: row
                for row in audit_client_selected_options(game)
                if row["block_packet_id"] is not None}
    confirmed_ends = audit_client_end_turn_options(game)
    state = LiveGameState()
    records: list[dict[str, Any]] = []
    for _, event_kind, item, parent in _ordered_game_events(game):
        if (event_kind == "row" and item.get("kind") == "SendOption"
                and item.get("packet_id") in confirmed_ends):
            before = _public_snapshot(state)
            if records:
                records[-1]["observed_until_next_decision"] = before
            actor = before["active_player"]
            reasons = []
            if not causal:
                reasons.append("legacy_import_may_backfill_identity")
            if actor != local_controller:
                reasons.append("opponent_or_unresolved_turn")
            if before["turn"] is None or before["consistency_errors"]:
                reasons.append("turn_or_public_state_unresolved")
            records.append({
                "packet_id": item["packet_id"],
                "action": {"kind": "TURN_END", "source_entity": None,
                           "source_card_before_action": None,
                           "target_entity": None, "target_card_before_action": None},
                "actor_controller": actor,
                "client_selected_option": confirmed_ends[item["packet_id"]],
                "client_option_confirmed": True,
                "pre_action_public_state": before,
                "observed_until_next_decision": None,
                "causal_observation_candidate": not reasons,
                "blockers": reasons,
                "training_authorized": False,
            })
        if event_kind == "block":
            kind = str(item.get("block_type") or "").upper()
            selected_option = selected.get(item.get("packet_id"))
            if kind in _DECISION_BLOCKS or (kind == "DECK_ACTION" and selected_option
                                            and selected_option["client_option_legal"]):
                if kind == "DECK_ACTION":
                    kind = "TRADE"
                before = _public_snapshot(state)
                if records:
                    records[-1]["observed_until_next_decision"] = before
                source_id = item.get("source_entity")
                source = (state.entities.get(str(source_id))
                          or state.entity_registry.get(str(source_id))) if source_id is not None else None
                actor = source.controller if source is not None else None
                source_card = item.get("source_card") or (
                    source.card_id if source is not None else None)
                reasons: list[str] = []
                if not causal:
                    reasons.append("legacy_import_may_backfill_identity")
                if actor not in (1, 2):
                    reasons.append("actor_not_causally_identified")
                elif actor != local_controller:
                    reasons.append("opponent_hidden_information")
                if kind != "TURN_END" and not source_card:
                    reasons.append("source_card_not_known_before_action")
                if before["turn"] is None or before["active_player"] != actor:
                    reasons.append("turn_or_active_player_unresolved")
                if actor in (1, 2):
                    actor_meta = before["player_meta"].get(str(actor), {})
                    if (actor_meta.get("mana") is None
                            or actor_meta.get("health") is None):
                        reasons.append("actor_mana_or_health_unresolved")
                if before["consistency_errors"]:
                    reasons.append("public_state_inconsistent")
                records.append({
                    "packet_id": item.get("packet_id"),
                    "action": {
                        "kind": kind,
                        "source_entity": source_id,
                        "source_card_before_action": source_card,
                        "target_entity": item.get("target_entity"),
                        "target_card_before_action": item.get("target_card"),
                    },
                    "actor_controller": actor,
                    "client_selected_option": selected_option,
                    "client_option_confirmed": bool(
                        selected_option and selected_option["client_option_legal"]),
                    "pre_action_public_state": before,
                    "observed_until_next_decision": None,
                    "causal_observation_candidate": not reasons,
                    "blockers": reasons,
                    "training_authorized": False,
                })
        state._apply_ordered_event(event_kind, item, parent)
    if records:
        records[-1]["observed_until_next_decision"] = _public_snapshot(state)
    for record in records:
        record["public_transition_audit"] = audit_public_transition(record)
    return records
