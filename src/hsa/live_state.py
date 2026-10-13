"""Public entity/state reconstruction from normalized Power.log packets.

This reconstructs the observable client state (zones, controllers, card IDs,
stats and tags). It intentionally does not infer hidden cards or fabricate a
simulator state; callers must still apply the confidence gate before actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


_ENTITY_LINK_TAGS = {
    "ATTACHED", "LINKED_ENTITY", "CARD_TARGET", "TAG_SCRIPT_DATA_NUM_1",
    "TAG_SCRIPT_DATA_NUM_2", "CREATOR", "DISPLAYED_CREATOR",
    "COPIED_FROM_ENTITY_ID",
}
_DECISION_ZONES = {"HAND", "PLAY", "SECRET"}
_ACTIVE_SETASIDE_TYPES = {"SECRET", "WEAPON", "LOCATION", "HERO", "HERO_POWER", "PLAYER", "GAME"}


def _available_mana(tags: dict[str, Any]) -> int | None:
    """Power.log RESOURCES is total crystals; subtract spent crystals."""
    value = tags.get("RESOURCES")
    if value is None:
        return None
    try:
        resources = int(value)
        used = int(tags.get("RESOURCES_USED", 0) or 0)
    except (TypeError, ValueError):
        return None
    return max(0, resources - used)


def _total_mana(tags: dict[str, Any]) -> int | None:
    """Total current crystals in Power.log, even if MAXRESOURCES is omitted."""
    value = tags.get("MAXRESOURCES")
    if value is None:
        value = tags.get("RESOURCES")
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


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
    first_seen_packet: int | None = None
    last_seen_packet: int | None = None
    zone_history: list[tuple[int | None, str]] = field(default_factory=list)
    references: set[int] = field(default_factory=set)
    initial_controller: int | None = None
    identity_history: list[tuple[int | None, str]] = field(default_factory=list)
    creation_context: dict[str, Any] = field(default_factory=dict)

    def apply(self, row: dict[str, Any]) -> None:
        packet_id = row.get("packet_id")
        try:
            packet_id = int(packet_id) if packet_id is not None else None
        except (TypeError, ValueError):
            packet_id = None
        if self.first_seen_packet is None:
            self.first_seen_packet = packet_id
        if row.get("kind") == "FullEntity" and row.get("_creation_context") and not self.creation_context:
            self.creation_context = dict(row["_creation_context"])
        self.last_seen_packet = packet_id
        if row.get("card_id"):
            self.card_id = row["card_id"]
            if not self.identity_history or self.identity_history[-1][1] != self.card_id:
                self.identity_history.append((packet_id, self.card_id))
        for tag_row in row.get("tags", ()):  # FullEntity/ShowEntity tags
            self._tag(tag_row.get("tag"), tag_row.get("value"), packet_id)
        self._tag(row.get("tag"), row.get("value"), packet_id)

    def _tag(self, tag: Any, value: Any, packet_id: int | None) -> None:
        if tag is None:
            return
        key = str(tag)
        self.tags[key] = value
        if key == "CONTROLLER":
            self.controller = int(value)
            if self.initial_controller is None:
                self.initial_controller = self.controller
        elif key == "ZONE":
            self.zone = str(value)
            if not self.zone_history or self.zone_history[-1][1] != self.zone:
                self.zone_history.append((packet_id, self.zone))
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
        if key in _ENTITY_LINK_TAGS and str(value).lstrip("-").isdigit():
            self.references.add(int(value))


@dataclass
class LiveGameState:
    entities: dict[str, EntityView] = field(default_factory=dict)
    entity_registry: dict[str, EntityView] = field(default_factory=dict)
    blocks_seen: int = 0
    turn: int | None = None
    active_player: int | None = None
    game_phase: str | None = None
    fatigue: dict[str, int] = field(default_factory=dict)
    action_history: list[dict[str, Any]] = field(default_factory=list)
    damage_history: list[dict[str, Any]] = field(default_factory=list)
    consistency_errors: list[str] = field(default_factory=list)
    reset_count: int = 0
    open_choice_candidates: dict[int, tuple[str, ...]] = field(default_factory=dict)
    resolved_choice_rejected_ids: set[str] = field(default_factory=set)

    def apply_row(self, row: dict[str, Any], *, replace_active: bool = False) -> None:
        kind = str(row.get("kind") or "")
        if kind in {"Choices", "ChosenEntities"}:
            try:
                choice_id = int(row["id"])
                options = tuple(str(int(value)) for value in row.get("choices", ()))
            except (KeyError, TypeError, ValueError):
                choice_id, options = None, ()
            if choice_id is not None:
                if kind == "Choices":
                    self.open_choice_candidates[choice_id] = options
                else:
                    candidates = self.open_choice_candidates.pop(choice_id, ())
                    if candidates and options:
                        self.resolved_choice_rejected_ids.update(
                            set(candidates) - set(options))
        entity = row.get("entity")
        if entity is None:
            return
        key = str(entity)
        record = self.entity_registry.setdefault(key, EntityView(key))
        record.apply(row)
        if replace_active:
            view = EntityView(key)
            self.entities[key] = view
        else:
            view = self.entities.setdefault(key, EntityView(key))
        view.apply(row)

    def apply_game(self, game: dict[str, Any]) -> "LiveGameState":
        for _, kind, item, parent in _ordered_game_events(game):
            self._apply_ordered_event(kind, item, parent)
        self._resolve_action_controllers()
        self._refresh_public_game_metadata()
        return self

    def _apply_ordered_event(
        self, kind: str, item: dict[str, Any],
        parent: dict[str, Any] | None,
    ) -> None:
        if kind == "row":
            self.apply_row(item)
            self._refresh_public_game_metadata()
        elif kind == "block":
            # An open block's effects are interleaved with top-level packets
            # and nested blocks. Do not apply its full future effect list yet.
            self.apply_block_delta({**item, "effects": []}, first_observation=True)
        elif parent is not None:
            self.apply_block_delta({**parent, "effects": [item]})

    def apply_block_delta(
        self, block: dict[str, Any], *, effect_start: int = 0,
        first_observation: bool = False,
    ) -> None:
        """Apply a new block, or only newly appended effects of an open block.

        hslog exposes a BLOCK_START before every nested effect is known. A
        live cursor must therefore avoid replaying block metadata/action
        history when a later polling pass merely sees more effects attached to
        that same packet.
        """
        if _is_game_reset(block):
            if first_observation:
                self._reset_from_snapshot(block)
                return
            for effect in block.get("effects", ())[effect_start:]:
                self.apply_row(
                    effect,
                    replace_active=str(effect.get("kind") or "")
                    in {"FullEntity", "ShowEntity"},
                )
            self._refresh_public_game_metadata()
            return
        if first_observation:
            self.blocks_seen += 1
            self._apply_block_metadata(block)
            self.apply_row({"entity": block.get("source_entity"),
                            "card_id": block.get("source_card")})
            self.apply_row({"entity": block.get("target_entity"),
                            "card_id": block.get("target_card")})
        for effect in block.get("effects", ())[effect_start:]:
            self._record_damage_change(effect, block.get("packet_id"))
            if effect.get("kind") == "FullEntity":
                source = self.entities.get(str(block.get("source_entity")))
                tags = {t.get("tag"): t.get("value") for t in effect.get("tags", ())}
                controller = tags.get("CONTROLLER")
                opening_hand_count = sum(
                    e.controller == controller and e.zone == "HAND" and bool(e.zone_history)
                    and e.zone_history[0][1] == "DECK" for e in self.entities.values())
                effect = {**effect, "_creation_context": {
                    "source_card": source.card_id if source else block.get("source_card"),
                    "source_type": source.card_type if source else None,
                    "block_type": block.get("block_type"), "turn": self.turn,
                    "phase": self.game_phase, "opening_hand_count": opening_hand_count,
                }}
            self.apply_row(effect)
            tag = str(effect.get("tag") or "")
            if tag in {"FATIGUE", "FATIGUE_DAMAGE"}:
                controller = effect.get("controller") or block.get("controller")
                if controller is not None:
                    self.fatigue[str(controller)] = int(effect.get("value", 0))
        self._resolve_action_controllers()
        self._refresh_public_game_metadata()

    def _refresh_public_game_metadata(self) -> None:
        game_entities = [e for e in self.entities.values() if e.card_type == "GAME"]
        has_game_current_player = False
        if game_entities:
            game_entity = game_entities[-1]
            step = game_entity.tags.get("STEP") or game_entity.tags.get("NEXT_STEP")
            if step is not None:
                self.game_phase = str(step)
            if game_entity.tags.get("TURN") is not None:
                self.turn = int(game_entity.tags["TURN"])
            if game_entity.tags.get("CURRENT_PLAYER") is not None:
                self.active_player = int(game_entity.tags["CURRENT_PLAYER"])
                has_game_current_player = True
        if not has_game_current_player:
            # Current clients commonly encode CURRENT_PLAYER as a boolean on
            # the two PLAYER entities.  This is authoritative *per turn*:
            # retaining the value inferred at match start makes every later
            # opponent turn look like the local player's turn.
            player_entities = [
                entity for entity in self.entities.values()
                if entity.card_type == "PLAYER"
                or "MULLIGAN_STATE" in entity.tags
                or "PLAYSTATE" in entity.tags
            ]
            player_entities.sort(
                key=lambda entity: int(entity.entity_id)
                if entity.entity_id.lstrip("-").isdigit() else 10**9
            )
            current = []
            for index, entity in enumerate(player_entities[:2], start=1):
                value = entity.tags.get("CURRENT_PLAYER")
                try:
                    is_current = bool(int(value))
                except (TypeError, ValueError):
                    is_current = str(value).upper() in {"TRUE", "YES"}
                if is_current:
                    current.append(index)
            if len(player_entities) == 2 and len(current) == 1:
                self.active_player = current[0]
            elif len(player_entities) == 1 and current == [1]:
                # GAME_RESET test/snapshot fragments can contain only the
                # current PLAYER entity. Its explicit controller is still
                # stronger evidence than leaving an otherwise complete public
                # snapshot without an active player.
                controller = player_entities[0].controller
                if controller in (1, 2):
                    self.active_player = controller

    def _resolve_action_controllers(self) -> None:
        """Backfill ownership once later effects have created a source entity.

        A token may be summoned and attack inside the same parent block. The
        action metadata precedes its FullEntity packet, but the entity registry
        retains that packet even after the token dies.
        """
        for action in self.action_history:
            if action.get("controller") in (1, 2):
                continue
            source = action.get("source_entity")
            entity = (self.entities.get(str(source))
                      or self.entity_registry.get(str(source)))
            if entity is not None and entity.controller in (1, 2):
                action["controller"] = entity.controller

    def _reset_from_snapshot(self, block: dict[str, Any]) -> None:
        """Replace the public state with a Power.log GAME_RESET snapshot.

        A reset is not an ordinary delta: the following FullEntity rows are
        the client-authoritative state. Retaining old entities or current-turn
        action flags would make a later simulator hydration unsafe.
        """
        self.entities.clear()
        self.blocks_seen = 1
        self.turn = None
        self.active_player = None
        self.game_phase = None
        self.fatigue.clear()
        self.action_history.clear()
        self.damage_history.clear()
        self.consistency_errors.clear()
        self.open_choice_candidates.clear()
        self.resolved_choice_rejected_ids.clear()
        self.reset_count += 1
        for effect in block.get("effects", ()):
            self.apply_row(effect, replace_active=str(effect.get("kind") or "") in {"FullEntity", "ShowEntity"})
        self._refresh_public_game_metadata()

    def public_decision_projection(self, open_choice_entities: tuple[int, ...] = ()) -> dict[str, Any]:
        """Project the registry-backed public state onto the decision surface.

        SETASIDE remains in the entity registry, but is not a legal-action
        zone. It becomes relevant only through a live choice or an explicit
        public reference from the current state.
        """
        open_choices = set(open_choice_entities)
        reference_sources: dict[int, list[tuple[EntityView, str]]] = {}
        for entity in self.entities.values():
            for tag in _ENTITY_LINK_TAGS:
                value = entity.tags.get(tag)
                if str(value).lstrip("-").isdigit():
                    reference_sources.setdefault(int(value), []).append((entity, tag))
        decision_entities = [entity.entity_id for entity in self.entities.values()
                             if entity.zone in _DECISION_ZONES]
        inert_setaside: list[str] = []
        active_setaside: list[str] = []
        for entity in self.entities.values():
            if entity.zone != "SETASIDE":
                continue
            entity_id = int(entity.entity_id) if entity.entity_id.lstrip("-").isdigit() else None
            inbound = reference_sources.get(entity_id, []) if entity_id is not None else []
            # A known Secret is hydrated directly.  Its CREATOR object may
            # remain in SETASIDE forever, but cannot itself be played or
            # alter the current legal action set.  Keep every other relation
            # active, especially choices, targets, attachments and unknown
            # secret identities.
            # COPIED_FROM_ENTITY_ID records provenance, not a pending choice
            # or attachment. Script-data pointers from a card already in the
            # graveyard are likewise historical. A live source using either
            # script-data pointer remains active and fail-closed.
            def decision_reference(source: EntityView, tag: str) -> bool:
                if tag == "COPIED_FROM_ENTITY_ID":
                    return False
                if source.zone == "GRAVEYARD" and tag in {
                    "TAG_SCRIPT_DATA_NUM_1", "TAG_SCRIPT_DATA_NUM_2"
                }:
                    return False
                if (tag in {"CREATOR", "DISPLAYED_CREATOR"}
                        and source.zone == "SECRET" and bool(source.card_id)):
                    return False
                return True

            has_live_reference = any(decision_reference(source, tag)
                                     for source, tag in inbound)
            rejected_choice_option = (entity.entity_id in self.resolved_choice_rejected_ids
                                      and not has_live_reference)
            active = (entity_id in open_choices or has_live_reference
                      or (entity.card_type in _ACTIVE_SETASIDE_TYPES
                          and not rejected_choice_option))
            (active_setaside if active else inert_setaside).append(entity.entity_id)
        return {
            "decision_entities": decision_entities,
            "active_setaside": active_setaside,
            "inert_setaside": inert_setaside,
            "registry_entity_count": len(self.entity_registry),
            "reset_count": self.reset_count,
        }

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
            # Current client Block packets commonly omit ``controller``. The
            # source entity already belongs to a public player, so retain that
            # attribution once in the canonical action history. Downstream
            # belief updates and temporary-action legality must not each make
            # their own, potentially different, inference.
            controller = block.get("controller")
            source_entity = self.entities.get(str(source))
            if controller not in (1, 2):
                controller = source_entity.controller if source_entity else controller
            # Current clients encode a Location activation as a PLAY block
            # even though the source was already on the board. Distinguish it
            # from the earlier card play so cooldown and per-turn history can
            # be reconstructed without replaying hidden effects.
            action_kind = ("LOCATION" if kind == "PLAY" and source_entity is not None
                           and source_entity.zone == "PLAY"
                           and source_entity.card_type == "LOCATION" else kind)
            self.action_history.append({
                "kind": action_kind, "source_entity": source,
                "source_card": block.get("source_card"),
                "target_entity": target,
                "target_card": block.get("target_card"),
                "controller": controller,
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

    def _record_damage_change(
        self, effect: dict[str, Any], packet_id: Any = None,
    ) -> None:
        """Retain public, within-turn damage events for condition features.

        A current DAMAGE tag alone cannot reveal whether damage happened this
        turn. Record only an explicit increasing TagChange, and resolve its
        owner from the entity registry after hydration. FullEntity snapshots
        establish a baseline; they are deliberately not treated as new damage.
        """
        if (str(effect.get("kind") or "").upper() != "TAGCHANGE"
                or str(effect.get("tag") or "").upper() != "DAMAGE"):
            return
        raw_entity = effect.get("entity")
        if raw_entity is None:
            return
        key = str(raw_entity)
        entity = self.entities.get(key) or self.entity_registry.get(key)
        if entity is None:
            return
        try:
            new_damage = int(effect.get("value"))
        except (TypeError, ValueError):
            return
        if new_damage <= entity.damage:
            return
        owner = entity.controller
        if owner not in (1, 2):
            try:
                owner = int(effect.get("controller"))
            except (TypeError, ValueError):
                owner = None
        self.damage_history.append({
            "entity": key,
            "controller": owner,
            "turn": self.turn,
            "active_player": self.active_player,
            "packet_id": effect.get("packet_id", packet_id),
        })

    def visible(self) -> dict[str, Any]:
        by_player: dict[str, dict[str, list[dict[str, Any]]]] = {}
        player_meta: dict[str, dict[str, Any]] = {}
        for entity in self.entities.values():
            if entity.controller is None:
                continue
            player = by_player.setdefault(str(entity.controller), {})
            meta = player_meta.setdefault(str(entity.controller), {})
            if entity.card_type == "PLAYER":
                meta.update({"mana": _available_mana(entity.tags),
                             "max_mana": _total_mana(entity.tags),
                             "fatigue": entity.tags.get("FATIGUE"),
                             "corpses": entity.tags.get("CORPSES")})
            # Hero replacement archives the previous hero in SETASIDE. Its
            # stale health/armor must never overwrite the active hero's
            # public stats, regardless of entity insertion order.
            if entity.card_type == "HERO" and entity.zone == "PLAY":
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
        # Current Power.log builds may omit CARDTYPE=PLAYER and CONTROLLER on
        # the two player entities (normally ids 2 and 3), while retaining
        # RESOURCES/MAXRESOURCES.  They are still ordered by controller, as
        # in _refresh_public_game_metadata; hydrate their mana so a live
        # recommendation cannot offer a card after its mana was spent.
        implicit_players = [
            entity for entity in self.entities.values()
            if entity.card_type == "PLAYER"
            or "MULLIGAN_STATE" in entity.tags
            or "PLAYSTATE" in entity.tags
        ]
        implicit_players.sort(
            key=lambda entity: int(entity.entity_id)
            if entity.entity_id.lstrip("-").isdigit() else 10**9
        )
        if len(implicit_players) == 2:
            for controller, entity in enumerate(implicit_players, start=1):
                if (entity.tags.get("RESOURCES") is not None
                        or entity.tags.get("MAXRESOURCES") is not None):
                    player_meta.setdefault(str(controller), {}).update({
                        "mana": _available_mana(entity.tags),
                        "max_mana": _total_mana(entity.tags),
                        "fatigue": entity.tags.get("FATIGUE"),
                        "corpses": entity.tags.get("CORPSES"),
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
            "damage_history": list(self.damage_history),
            "entity_count": len(self.entities),
            "registry_entity_count": len(self.entity_registry),
            "reset_count": self.reset_count,
            "consistency_errors": list(dict.fromkeys(self.consistency_errors)),
        }


def reconstruct_game(game: dict[str, Any]) -> LiveGameState:
    return LiveGameState().apply_game(game)


def _ordered_game_events(game: dict[str, Any]):
    """Merge top-level packets, blocks and effects by original packet id.

    The normalized `preamble` array contains *all* top-level packets, not
    just the opening snapshot. Legacy synthetic fixtures without packet ids
    retain their original preamble-then-block order.
    """
    timeline: list[tuple[int, int, tuple[Any, ...], str,
                         dict[str, Any], dict[str, Any] | None]] = []
    serial = 0

    def packet_number(value: Any, fallback: int) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback

    for index, row in enumerate(game.get("preamble", ())):
        number = packet_number(row.get("packet_id"), -1)
        timeline.append((number, serial, ("row", number if number >= 0 else index),
                         "row", row, None))
        serial += 1
    for index, block in enumerate(game.get("blocks", ())):
        block_number = packet_number(block.get("packet_id"), index)
        block_key = ("block", block_number if block.get("packet_id") is not None
                     else f"index:{index}")
        timeline.append((block_number, serial, block_key, "block", block, None))
        serial += 1
        for effect_index, effect in enumerate(block.get("effects", ())):
            effect_number = packet_number(effect.get("packet_id"), block_number)
            effect_key = ("effect", effect_number if effect.get("packet_id") is not None
                          else (block_key, effect_index))
            timeline.append((effect_number, serial, effect_key,
                             "effect", effect, block))
            serial += 1
    timeline.sort(key=lambda entry: (entry[0], entry[1]))
    for _, _, key, kind, item, parent in timeline:
        yield key, kind, item, parent


@dataclass
class LiveStateCursor:
    """Incrementally project one append-only normalized Power.log game."""

    state: LiveGameState = field(default_factory=LiveGameState)
    preamble_rows_seen: int = 0
    block_effects_seen: dict[str, int] = field(default_factory=dict)
    seen_event_keys: set[tuple[Any, ...]] = field(default_factory=set)

    def apply_game(self, game: dict[str, Any]) -> LiveGameState:
        for key, kind, item, parent in _ordered_game_events(game):
            if key in self.seen_event_keys:
                continue
            self.state._apply_ordered_event(kind, item, parent)
            self.seen_event_keys.add(key)
        self.preamble_rows_seen = len(game.get("preamble", ()))
        self.block_effects_seen = {
            str(block.get("packet_id") if block.get("packet_id") is not None
                else f"index:{index}"): len(block.get("effects", ()))
            for index, block in enumerate(game.get("blocks", ()))
        }
        self.state._refresh_public_game_metadata()
        return self.state


def timeline_snapshots(game: dict[str, Any]) -> list[dict[str, Any]]:
    """Return compact public-state snapshots after each normalized block."""
    state = LiveGameState()
    events = list(_ordered_game_events(game))
    last_effect_key: dict[int, tuple[Any, ...]] = {}
    for key, kind, _, parent in events:
        if kind == "effect" and parent is not None:
            last_effect_key[id(parent)] = key
    snapshots_by_block: dict[int, dict[str, Any]] = {}
    for key, kind, item, parent in events:
        state._apply_ordered_event(kind, item, parent)
        completed = (item if kind == "block" and id(item) not in last_effect_key
                     else parent if kind == "effect" and parent is not None
                     and last_effect_key.get(id(parent)) == key else None)
        if completed is not None:
            visible = state.visible()
            snapshots_by_block[id(completed)] = {
                "packet_id": completed.get("packet_id"),
                "block_type": completed.get("block_type"),
                "blocks_seen": state.blocks_seen,
                "entity_count": visible["entity_count"],
                "players": visible["players"],
                "player_meta": visible["player_meta"],
            }
    return [snapshots_by_block[id(block)] for block in game.get("blocks", ())]


def _is_game_reset(block: dict[str, Any]) -> bool:
    """Identify both normalized reset spellings emitted by hslog clients."""
    if str(block.get("block_type") or block.get("type") or "").upper() == "GAME_RESET":
        return True
    return any(str(effect.get("kind") or "").upper() == "RESETGAME"
               for effect in block.get("effects", ()))
