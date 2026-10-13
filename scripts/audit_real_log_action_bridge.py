#!/usr/bin/env python3
"""Audit whether real PLAY/ATTACK blocks are legal in pre-action belief snapshots.

This never exports training rows. Decks are explicitly marked as hypotheses;
an observed action is not a trustworthy imitation label merely because one
candidate deck makes the simulator accept it.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.live_bridge import build_snapshot_hypothesis
from hsa.live_state import LiveGameState


def target_publicly_resolved(target):
    """A purported target needs a side, zone and type before legality is testable."""
    return (target is not None and target.controller in (1, 2)
            and bool(target.zone) and bool(target.card_type))


def target_resolved_for_action(kind, source, target):
    """A combat/Location target must be visibly in play before judging legality.

    Some sanitized logs retain the card identity but omit the DECK -> PLAY
    transition. Treat that as an observation gap, not an engine rule failure.
    Ordinary PLAY effects may target a card in hand, so they are not subject
    to this extra zone test.
    """
    if not target_publicly_resolved(target):
        return False
    if kind == "ATTACK" or (kind == "PLAY" and source is not None
                            and source.card_type == "LOCATION"
                            and source.zone == "PLAY"):
        return target.zone == "PLAY"
    return True


def action_matches(block, game, state):
    block_kind = str(block.get("block_type") or "").upper()
    # TURN_END has no source entity or target. The simulator exposes exactly
    # one END_TURN action when the active player's turn can be closed.
    if block_kind in {"TURN_END", "MAIN_END", "END_TURN"}:
        return any(action.kind == "END_TURN" for action in game.legal_actions())
    source_id = block.get("source_entity")
    target_id = block.get("target_entity")
    try:
        source_id = int(source_id)
        target_id = int(target_id) if target_id not in (None, 0, "0") else None
    except (TypeError, ValueError):
        return False
    if target_id is not None:
        target = (state.entities.get(str(target_id))
                  or state.entity_registry.get(str(target_id)))
        if target is None or target.controller not in (1, 2):
            return False
        target_player = target.controller - 1
        target_is_hero = target.card_type == "HERO" or str(target.card_id or "").startswith("HERO_")
    else:
        target_player, target_is_hero = None, False
    source = (state.entities.get(str(source_id))
              or state.entity_registry.get(str(source_id)))
    source_type = source.card_type if source is not None else None
    for action in game.legal_actions():
        if block_kind in {"DECK_ACTION", "TRADE"}:
            expected_kind = "TRADE"
        elif block_kind == "PLAY":
            expected_kind = ("HERO_POWER" if source_type == "HERO_POWER"
                             else "LOCATION" if source_type == "LOCATION" and source.zone == "PLAY"
                             else "PLAY")
            if action.kind != expected_kind:
                continue
        elif block_kind == "ATTACK":
            expected_kind = "HERO_ATTACK" if source_type == "HERO" else "ATTACK"
            if action.kind != expected_kind:
                continue
        else:
            continue
        if action.kind != expected_kind:
            continue
        expected_source = None if expected_kind in {"HERO_POWER", "HERO_ATTACK"} else source_id
        if action.source != expected_source:
            continue
        if target_id is None:
            if action.target_entity is None and action.target_player is None:
                return True
        elif (action.target_player == target_player
              and action.target_entity == (None if target_is_hero else target_id)):
            return True
    return False


def ordered_packets(game):
    # A completed normalized file stores *all* top-level TagChanges in
    # ``preamble``; applying that array before block 1 leaks the final state
    # into every opening decision. Merge by original packet id instead.
    timeline = []
    for row in game.get("preamble", ()):
        if row.get("packet_id") is not None:
            timeline.append((int(row["packet_id"]), 0, "row", row, None))
    for block in game.get("blocks", ()):
        packet_id = block.get("packet_id")
        if packet_id is None:
            raise ValueError("cannot audit a block without packet_id")
        timeline.append((int(packet_id), 1, "block", block, None))
        for effect in block.get("effects", ()):
            if effect.get("packet_id") is None:
                raise ValueError("cannot audit a block effect without packet_id")
            timeline.append((int(effect["packet_id"]), 2, "effect", effect, block))
    timeline.sort(key=lambda item: (item[0], item[1]))
    return timeline


def initial_public_classes(game):
    """Read class only from opening heroes, before any transformation.

    Deck/class hypotheses with a different class can make an unrelated
    simulator action appear to match. Never report that as replay evidence.
    """
    result = {}
    for row in sorted(game.get("preamble", ()),
                      key=lambda item: int(item.get("packet_id") or 0)):
        if row.get("kind") != "FullEntity":
            continue
        tags = {str(tag.get("tag")): tag.get("value")
                for tag in row.get("tags", ())}
        if tags.get("CARDTYPE") != "HERO" or tags.get("ZONE") != "PLAY":
            continue
        try:
            controller = int(tags.get("CONTROLLER"))
        except (TypeError, ValueError):
            continue
        if controller in (1, 2) and controller not in result and tags.get("CLASS"):
            result[controller] = str(tags["CLASS"]).upper()
    return result


def audit_game(game, cards, counts, classes, max_actions, local_controller=None):
    timeline = ordered_packets(game)
    state = LiveGameState()
    rows = []
    for _packet_id, _order, event_kind, item, parent in timeline:
        if event_kind == "row":
            state.apply_row(item)
            state._refresh_public_game_metadata()
            continue
        if event_kind == "effect":
            state._record_damage_change(item, parent.get("packet_id"))
            state.apply_row(item)
            state._resolve_action_controllers()
            state._refresh_public_game_metadata()
            continue
        block = item
        kind = str(block.get("block_type") or "").upper()
        if kind in {"PLAY", "ATTACK"} and len(rows) < max_actions:
            source = (state.entities.get(str(block.get("source_entity")))
                      or state.entity_registry.get(str(block.get("source_entity"))))
            controller = source.controller if source else block.get("controller")
            if local_controller is not None and controller != local_controller:
                state.apply_block_delta({**block, "effects": []}, first_observation=True)
                continue
            row = {"packet_id": block.get("packet_id"), "kind": kind,
                   "source_card": block.get("source_card"),
                   "controller": controller, "status": None}
            if controller not in (1, 2):
                row["status"] = "unknown_actor"
            else:
                bridge = build_snapshot_hypothesis(
                    cards_path=cards, state=state,
                    own_deck=counts[controller], opponent_deck=counts[3 - controller],
                    player_classes=classes, self_controller=controller,
                    seed=1000 + len(rows), setaside_policy="advisory")
                if not bridge.available:
                    row["status"] = "bridge_rejected"
                    row["reason"] = bridge.reason
                    if bridge.public_match is not None:
                        row["public_mismatch"] = bridge.public_match
                else:
                    row["status"] = ("legal_action_matched" if action_matches(
                        block, bridge.game, state) else "observed_action_not_legal")
                    if row["status"] == "observed_action_not_legal":
                        row["source_entity"] = block.get("source_entity")
                        row["target_entity"] = block.get("target_entity")
                        if kind == "ATTACK" and source is not None and source.zone != "PLAY":
                            row["status"] = "unresolved_observed_source_zone"
                        target = state.entities.get(str(block.get("target_entity")))
                        if (row["status"] == "observed_action_not_legal"
                                and block.get("target_entity") not in (None, 0, "0")
                                and not target_resolved_for_action(kind, source, target)):
                            row["status"] = "unresolved_observed_target"
                        row["observed_target"] = ({
                            "card_id": target.card_id, "zone": target.zone,
                            "controller": target.controller, "card_type": target.card_type,
                        } if target is not None else None)
                        row["legal_actions"] = [
                            {"kind": action.kind, "source": action.source,
                             "target_player": action.target_player,
                             "target_entity": action.target_entity}
                            for action in bridge.game.legal_actions()[:40]
                        ]
            rows.append(row)
        state.apply_block_delta({**block, "effects": []}, first_observation=True)
    return {"actions_examined": len(rows),
            "status_counts": dict(Counter(row["status"] for row in rows)),
            "bridge_reasons": dict(Counter(row.get("reason") for row in rows
                                           if row["status"] == "bridge_rejected")),
            "rows": rows}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--log", type=Path, required=True)
    p.add_argument("--known-1", type=Path, required=True,
                   help="Exported card-ID/count file for controller 1 hypothesis")
    p.add_argument("--known-2", type=Path, required=True,
                   help="Exported card-ID/count file for controller 2 hypothesis")
    p.add_argument("--class-1", required=True)
    p.add_argument("--class-2", required=True)
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--max-actions", type=int, default=100)
    p.add_argument("--local-controller", type=int, choices=(1, 2),
                   help="Audit only the hand-visible player's actions")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error("output exists; choose a new audit file")
    if args.max_actions < 1:
        p.error("--max-actions must be positive")
    def load_counts(path):
        content = json.loads(path.read_text(encoding="utf-8"))
        if len(content) != 1:
            raise ValueError(f"{path} must contain exactly one controller deck")
        counts = next(iter(content.values()))
        if sum(map(int, counts.values())) < 30:
            raise ValueError(f"{path} contains fewer than 30 cards")
        return counts
    counts = {1: load_counts(args.known_1), 2: load_counts(args.known_2)}
    classes = (args.class_1.upper(), args.class_2.upper())
    payload = json.loads(args.log.read_text(encoding="utf-8"))
    game = payload["games"][-1] if payload.get("games") else payload
    opening_classes = initial_public_classes(game)
    for controller, claimed in enumerate(classes, start=1):
        if controller in opening_classes and opening_classes[controller] != claimed:
            p.error(f"controller {controller} opening hero class is "
                    f"{opening_classes[controller]}, not {claimed}; "
                    "deck/class hypothesis cannot be audited")
    result = audit_game(game, args.cards, counts, classes, args.max_actions,
                        args.local_controller)
    result.update({"schema": "real-log-action-bridge-audit-v1",
                   "source_sha256": payload.get("source_sha256"),
                   "input_identity_timing": (game.get("identity_timing")
                                             or payload.get("identity_timing")
                                             or "unknown_legacy"),
                   "local_controller": args.local_controller,
                   "deck_hypotheses": {"1": str(args.known_1), "2": str(args.known_2)},
                   "training_authorized": False,
                   "warning": "A matched legal action under one guessed deck pair is not a verified expert label; legacy normalized logs may backfill identities from later reveals."})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"actions_examined": result["actions_examined"],
                      "status_counts": result["status_counts"],
                      "bridge_reasons": result["bridge_reasons"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
