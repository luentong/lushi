"""Read-only comparison between a replayed engine state and Power.log state."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Any


_IMPLICIT_HERO_POWER_ID = re.compile(r"^HERO_\d+[a-z]*bp\d*$", re.IGNORECASE)
_NON_BOARD_ENTITY_TYPES = {
    "HERO", "PLAYER", "GAME", "WEAPON", "LOCATION", "HERO_POWER",
    "ENCHANTMENT", "COUNTER",
}


@dataclass
class StateComparison:
    matches: bool
    mismatches: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {"matches": self.matches, "mismatches": self.mismatches[:100]}


def compare_public_state(
    engine: Any,
    visible: dict[str, Any],
    *,
    player_offset: int = 1,
    ignored_entity_ids: set[str] | None = None,
) -> StateComparison:
    """Compare stable public fields; hidden deck order is intentionally ignored."""
    mismatches: list[dict[str, Any]] = []
    ignored_entity_ids = ignored_entity_ids or set()
    if visible.get("turn") is not None and getattr(engine, "turn", None) != visible["turn"]:
        mismatches.append({"field": "turn", "log": visible["turn"],
                           "engine": getattr(engine, "turn", None)})
    if visible.get("active_player") is not None:
        expected = int(visible["active_player"]) - player_offset
        if getattr(engine, "current", None) != expected:
            mismatches.append({"field": "active_player", "log": visible["active_player"],
                               "engine": getattr(engine, "current", None)})
    players = visible.get("players", {})
    for index, player in enumerate(getattr(engine, "players", ())):
        log_player = players.get(str(index + player_offset), {})
        meta = visible.get("player_meta", {}).get(str(index + player_offset), {})
        for field, attr in (("health", "health"), ("armor", "armor"),
                            ("mana", "mana"), ("max_mana", "max_mana")):
            if meta.get(field) is not None and hasattr(player, attr):
                value = getattr(player, attr)
                if value != meta[field]:
                    mismatches.append({"player": index, "field": field,
                                       "log": meta[field], "engine": value})
        # Power.log represents heroes (and sometimes the PLAYER/GAME entity)
        # in PLAY as well.  The simulator keeps them on Player, not board.
        expected_board = [card for card in log_player.get("PLAY", [])
                          if str(card.get("entity", card.get("entity_id"))) not in ignored_entity_ids
                          if card.get("card_type") not in _NON_BOARD_ENTITY_TYPES
                          and not _IMPLICIT_HERO_POWER_ID.fullmatch(str(card.get("card_id") or ""))]
        engine_board = getattr(player, "board", [])
        if len(expected_board) != len(engine_board):
            mismatches.append({"player": index, "field": "board_count",
                               "log": len(expected_board), "engine": len(engine_board)})
        for pos, (logged, actual) in enumerate(zip(expected_board, engine_board)):
            card_id = getattr(actual, "card_id", None)
            if logged.get("card_id") and logged["card_id"] != card_id:
                mismatches.append({"player": index, "field": "board_card",
                                   "position": pos, "log": logged.get("card_id"),
                                   "engine": card_id})
            for field in ("attack", "health", "damage"):
                value = getattr(actual, field, None)
                if logged.get(field) is not None and value != logged[field]:
                    mismatches.append({"player": index, "field": f"board_{field}",
                                       "position": pos, "log": logged[field],
                                       "engine": value})
        expected_hand = log_player.get("HAND", [])
        engine_hand = getattr(player, "hand", [])
        if len(expected_hand) != len(engine_hand):
            mismatches.append({"player": index, "field": "hand_count",
                               "log": len(expected_hand), "engine": len(engine_hand)})
    return StateComparison(not mismatches, mismatches)
