"""Public entity/state reconstruction from normalized Power.log packets.

This reconstructs the observable client state (zones, controllers, card IDs,
stats and tags). It intentionally does not infer hidden cards or fabricate a
simulator state; callers must still apply the confidence gate before actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EntityView:
    entity_id: str
    card_id: str | None = None
    controller: int | None = None
    zone: str = ""
    card_type: str | None = None
    attack: int | None = None
    health: int | None = None
    damage: int = 0
    cost: int | None = None
    tags: dict[str, Any] = field(default_factory=dict)

    def apply(self, row: dict[str, Any]) -> None:
        if row.get("card_id"):
            self.card_id = row["card_id"]
        for tag_row in row.get("tags", ()):  # FullEntity/ShowEntity tags
            self._tag(tag_row.get("tag"), tag_row.get("value"))
        self._tag(row.get("tag"), row.get("value"))

    def _tag(self, tag: Any, value: Any) -> None:
        if tag is None:
            return
        key = str(tag)
        self.tags[key] = value
        if key == "CONTROLLER":
            self.controller = int(value)
        elif key == "ZONE":
            self.zone = str(value)
        elif key == "CARDTYPE":
            self.card_type = str(value)
        elif key == "ATK":
            self.attack = int(value)
        elif key in {"HEALTH", "MAX_HEALTH"}:
            self.health = int(value)
        elif key == "DAMAGE":
            self.damage = int(value)
        elif key in {"COST", "TAG_LAST_KNOWN_COST_IN_HAND"}:
            self.cost = int(value)


@dataclass
class LiveGameState:
    entities: dict[str, EntityView] = field(default_factory=dict)
    blocks_seen: int = 0
    turn: int | None = None
    active_player: int | None = None
    game_phase: str | None = None
    fatigue: dict[str, int] = field(default_factory=dict)
    action_history: list[dict[str, Any]] = field(default_factory=list)
    consistency_errors: list[str] = field(default_factory=list)

    def apply_row(self, row: dict[str, Any]) -> None:
        entity = row.get("entity")
        if entity is None:
            return
        key = str(entity)
        view = self.entities.setdefault(key, EntityView(key))
        view.apply(row)

    def apply_game(self, game: dict[str, Any]) -> "LiveGameState":
        for row in game.get("preamble", ()):
            self.apply_row(row)
        for block in game.get("blocks", ()):
            self.blocks_seen += 1
            self._apply_block_metadata(block)
            self.apply_row({"entity": block.get("source_entity"), "card_id": block.get("source_card")})
            self.apply_row({"entity": block.get("target_entity"), "card_id": block.get("target_card")})
            for effect in block.get("effects", ()):
                self.apply_row(effect)
        game_entities = [e for e in self.entities.values() if e.card_type == "GAME"]
        if game_entities:
            game_entity = game_entities[-1]
            if game_entity.tags.get("TURN") is not None:
                self.turn = int(game_entity.tags["TURN"])
            if game_entity.tags.get("CURRENT_PLAYER") is not None:
                self.active_player = int(game_entity.tags["CURRENT_PLAYER"])
        return self

    def _apply_block_metadata(self, block: dict[str, Any]) -> None:
        """Keep a lossless-enough public action timeline for the watcher.

        hslog uses several block names across client versions.  We deliberately
        avoid treating an unrecognised block as a legal simulator transition;
        it is retained in the timeline and the consistency gate is lowered.
        """
        kind = str(block.get("block_type") or block.get("type") or "")
        source = block.get("source_entity")
        target = block.get("target_entity")
        if kind in {"TURN_START", "TURN_END", "START_TURN", "END_TURN"}:
            value = block.get("turn") or block.get("turn_number")
            if value is not None:
                try:
                    self.turn = int(value)
                except (TypeError, ValueError):
                    self.consistency_errors.append(f"invalid turn: {value!r}")
            actor = block.get("player") or block.get("controller") or block.get("actor")
            if actor is not None:
                try:
                    self.active_player = int(actor)
                except (TypeError, ValueError):
                    self.consistency_errors.append(f"invalid actor: {actor!r}")
        if kind in {"PLAY", "ATTACK", "POWER", "TRADE", "LOCATION", "CHOOSE_ONE", "DISCOVER"}:
            self.action_history.append({
                "kind": kind, "source_entity": source,
                "source_card": block.get("source_card"),
                "target_entity": target,
                "target_card": block.get("target_card"),
                "controller": block.get("controller"),
                # The running turn value lets the live bridge recover
                # one-turn-only legality (attacks, Hero Power, Combo) without
                # pretending that earlier-turn actions are still active.
                "turn": self.turn,
            })
        # Some hslog versions expose fatigue as a tag change effect.
        for effect in block.get("effects", ()):
            tag = str(effect.get("tag") or "")
            if tag in {"FATIGUE", "FATIGUE_DAMAGE"}:
                controller = effect.get("controller") or block.get("controller")
                if controller is not None:
                    self.fatigue[str(controller)] = int(effect.get("value", 0))

    def visible(self) -> dict[str, Any]:
        by_player: dict[str, dict[str, list[dict[str, Any]]]] = {}
        player_meta: dict[str, dict[str, Any]] = {}
        for entity in self.entities.values():
            if entity.controller is None:
                continue
            player = by_player.setdefault(str(entity.controller), {})
            meta = player_meta.setdefault(str(entity.controller), {})
            if entity.card_type == "PLAYER":
                meta.update({"mana": entity.tags.get("RESOURCES"),
                             "max_mana": entity.tags.get("MAXRESOURCES"),
                             "fatigue": entity.tags.get("FATIGUE")})
            if entity.card_type == "HERO":
                meta.update({"max_health": entity.health,
                             "health": (entity.health - entity.damage) if entity.health is not None else None,
                             "damage": entity.damage,
                             "armor": entity.tags.get("ARMOR", 0)})
            player.setdefault(entity.zone or "UNKNOWN", []).append({
                "entity": entity.entity_id, "card_id": entity.card_id,
                "card_type": entity.card_type, "attack": entity.attack,
                "health": entity.health, "damage": entity.damage,
                "cost": entity.cost,
            })
        return {
            "blocks_seen": self.blocks_seen,
            "turn": self.turn,
            "active_player": self.active_player,
            "game_phase": self.game_phase,
            "fatigue": dict(self.fatigue),
            "players": by_player,
            "player_meta": player_meta,
            "action_history": list(self.action_history),
            "entity_count": len(self.entities),
            "consistency_errors": list(dict.fromkeys(self.consistency_errors)),
        }


def reconstruct_game(game: dict[str, Any]) -> LiveGameState:
    return LiveGameState().apply_game(game)


def timeline_snapshots(game: dict[str, Any]) -> list[dict[str, Any]]:
    """Return compact public-state snapshots after each normalized block."""
    state = LiveGameState()
    snapshots: list[dict[str, Any]] = []
    for row in game.get("preamble", ()):
        state.apply_row(row)
    for block in game.get("blocks", ()):
        state.blocks_seen += 1
        state._apply_block_metadata(block)
        state.apply_row({"entity": block.get("source_entity"), "card_id": block.get("source_card")})
        state.apply_row({"entity": block.get("target_entity"), "card_id": block.get("target_card")})
        for effect in block.get("effects", ()):
            state.apply_row(effect)
        visible = state.visible()
        snapshots.append({"packet_id": block.get("packet_id"),
                          "block_type": block.get("block_type"),
                          "blocks_seen": state.blocks_seen,
                          "entity_count": visible["entity_count"],
                          "players": visible["players"],
                          "player_meta": visible["player_meta"]})
    return snapshots
