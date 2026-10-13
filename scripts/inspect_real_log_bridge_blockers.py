#!/usr/bin/env python3
"""Inspect only public entities blocking a pre-action Power.log bridge."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from audit_real_log_action_bridge import ordered_packets
from hsa.live_state import LiveGameState


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", type=Path, required=True)
    parser.add_argument("--packets", type=int, nargs="+", required=True)
    parser.add_argument("--entities", type=str, nargs="*", default=[])
    args = parser.parse_args()
    payload = json.loads(args.log.read_text(encoding="utf-8"))
    game = payload["games"][-1] if payload.get("games") else payload
    targets = set(args.packets)
    state = LiveGameState()
    for packet_id, _, kind, item, parent in ordered_packets(game):
        if kind == "row":
            state.apply_row(item)
            state._refresh_public_game_metadata()
        elif kind == "effect":
            state._record_damage_change(item, parent.get("packet_id"))
            state.apply_row(item)
            state._resolve_action_controllers()
            state._refresh_public_game_metadata()
        else:
            if packet_id in targets:
                projection = state.public_decision_projection()
                ids = set(projection["active_setaside"])
                inbound = {entity_id: [
                    {"source_id": source.entity_id, "source_card": source.card_id,
                     "source_zone": source.zone, "tag": tag}
                    for source in state.entities.values()
                    for tag, value in source.tags.items()
                    if str(value) == entity_id
                    and tag in {"ATTACHED", "LINKED_ENTITY", "CARD_TARGET",
                                "TAG_SCRIPT_DATA_NUM_1", "TAG_SCRIPT_DATA_NUM_2",
                                "CREATOR", "DISPLAYED_CREATOR", "COPIED_FROM_ENTITY_ID"}
                ] for entity_id in ids}
                entities = [entity for entity in state.entities.values()
                            if entity.entity_id in ids or
                            entity.entity_id in args.entities or
                            (entity.zone == "PLAY" and
                             (entity.card_type in {"WEAPON", "LOCATION", "HERO_POWER"}
                              or str(entity.card_id or "").endswith("e"))) ]
                print(json.dumps({
                    "packet_id": packet_id,
                    "block_type": item.get("block_type"),
                    "source_card": item.get("source_card"),
                    "turn": state.turn,
                    "active_setaside": projection["active_setaside"],
                    "inbound": inbound,
                    "entities": [{
                        "id": e.entity_id, "card_id": e.card_id,
                        "controller": e.controller, "zone": e.zone,
                        "card_type": e.card_type, "tags": e.tags,
                        "zone_history": e.zone_history,
                    } for e in entities],
                }, ensure_ascii=False, indent=2))
            state.apply_block_delta({**item, "effects": []}, first_observation=True)


if __name__ == "__main__":
    main()
