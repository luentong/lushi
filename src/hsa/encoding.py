"""Versioned, framework-neutral state/action encoding for policy/value models."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from .dragon_mirror import Action, DragonMirrorGame, SUPPORTED_IDS


STATE_SCHEMA_VERSION = 2
LEGACY_STATE_SCHEMA_VERSION = 1
ACTION_KINDS = (
    "END_TURN", "MULLIGAN_TOGGLE", "MULLIGAN_CONFIRM", "TRADE", "PLAY",
    "PREPARE", "ATTACK", "HERO_ATTACK", "LOCATION", "HERO_POWER",
    "DISCOVER_PICK", "REWIND_KEEP", "REWIND_RETRY", "AMMUNITION_PICK",
    "CORPSE_SPEND",
)
CARD_VOCAB = tuple(sorted(set(SUPPORTED_IDS) | {"GAME_005", "JAIL_732"}))
CARD_INDEX = {card_id: index for index, card_id in enumerate(CARD_VOCAB)}
ZONE_NAMES = ("none", "hand", "board", "location", "choice", "literal")
TARGET_KINDS = ("none", "hero", "card", "literal")
MAX_HAND_SLOTS = 10
MAX_BOARD_SLOTS = 7


def _one_hot(index: int | None, size: int) -> list[float]:
    result = [0.0] * size
    if index is not None and 0 <= index < size:
        result[index] = 1.0
    return result


def _card_histogram(cards) -> list[float]:
    result = [0.0] * len(CARD_VOCAB)
    for card in cards:
        index = CARD_INDEX.get(card.card_id)
        if index is not None:
            result[index] += 1.0
    return result


def encode_state(
    game: DragonMirrorGame,
    observer: int | None = None,
    *,
    schema_version: int = STATE_SCHEMA_VERSION,
) -> tuple[float, ...]:
    """Encode only information visible to ``observer`` into a fixed vector."""
    if schema_version not in {LEGACY_STATE_SCHEMA_VERSION, STATE_SCHEMA_VERSION}:
        raise ValueError(f"unsupported state schema version: {schema_version}")
    observer = game.current if observer is None else observer
    if observer not in (0, 1):
        raise ValueError("observer must be player 0 or 1")
    own = game.players[observer]
    enemy = game.players[1 - observer]
    values = [
        min(game.turn, 100) / 100.0,
        float(game.current == observer),
        own.health / 30.0, own.armor / 30.0,
        own.mana / 10.0, own.max_mana / 10.0, own.fatigue / 10.0,
        len(own.hand) / 10.0, len(own.deck) / 32.0, len(own.board) / 7.0,
        enemy.health / 30.0, enemy.armor / 30.0,
        enemy.mana / 10.0, enemy.max_mana / 10.0, enemy.fatigue / 10.0,
        len(enemy.hand) / 10.0, len(enemy.deck) / 32.0, len(enemy.board) / 7.0,
        (own.weapon.attack / 10.0 if own.weapon else 0.0),
        (own.weapon.durability / 10.0 if own.weapon else 0.0),
        (enemy.weapon.attack / 10.0 if enemy.weapon else 0.0),
        (enemy.weapon.durability / 10.0 if enemy.weapon else 0.0),
        float(own.hero_power_used), float(enemy.hero_power_used),
    ]
    values.extend(_card_histogram(own.hand))
    values.extend(_card_histogram(own.board))
    values.extend(_card_histogram(enemy.board))
    if schema_version == LEGACY_STATE_SCHEMA_VERSION:
        return tuple(values)

    # Schema v2 adds public dynamic state that cannot be reconstructed from a
    # card-id histogram. In particular, temporary hero Attack from spells is
    # distinct from weapon Attack and is required to compare HERO_ATTACK with
    # END_TURN correctly.
    for player in (own, enemy):
        values.extend((
            player.attack / 30.0,
            player.hero_attacks_this_turn / 2.0,
            float(player.frozen_turn >= 0),
            float(player.hero_divine_shield),
            player.corpses / 30.0,
            player.locked_mana / 10.0,
            player.overload_next_turn / 10.0,
            game._spell_damage(player) / 10.0,
        ))

    # Own hand identities remain in the histogram above; these aligned slots
    # expose enchantment-dependent cost and stats to source-position actions.
    for position in range(MAX_HAND_SLOTS):
        card = own.hand[position] if position < len(own.hand) else None
        values.extend((
            card.cost / 10.0 if card else 0.0,
            card.attack / 20.0 if card else 0.0,
            card.health / 20.0 if card else 0.0,
            float(card is not None and not card.started_in_deck),
        ))

    # Board slots are public. Preserve ordering so the action source/target
    # position features can be joined with current combat stats and keywords.
    for player in (own, enemy):
        for position in range(MAX_BOARD_SLOTS):
            card = player.board[position] if position < len(player.board) else None
            if card is None:
                values.extend((0.0,) * 19)
                continue
            values.extend((
                card.attack / 20.0,
                card.health / 20.0,
                card.max_health / 20.0,
                card.damage / 20.0,
                card.attacks_this_turn / 2.0,
                card.dormant_turns / 3.0,
                float(card.summoned_turn == game.turn),
                float(card.frozen_turn >= 0),
                float(card.cant_attack),
                float(game._has_taunt(player.index, card)),
                float(card.rush),
                float(card.charge),
                float(card.lifesteal),
                float(card.elusive),
                float(card.stealth),
                float(card.divine_shield),
                float(card.windfury),
                float(card.reborn),
                float(card.poisonous or card.aura_poisonous),
            ))

    for player in (own, enemy):
        for position in range(MAX_BOARD_SLOTS):
            location = (
                player.locations[position]
                if position < len(player.locations) else None
            )
            values.extend((
                location.durability / 5.0 if location else 0.0,
                location.cooldown / 5.0 if location else 0.0,
            ))
    return tuple(values)


def _locate_entity(game: DragonMirrorGame, entity_id: int | None) -> tuple:
    if entity_id is None:
        return "none", None, None, None
    for player in game.players:
        for zone_name in ("hand", "board"):
            zone = getattr(player, zone_name)
            for position, card in enumerate(zone):
                if card.entity_id == entity_id:
                    return zone_name, player.index, position, card.card_id
        for position, location in enumerate(player.locations):
            if location.entity_id == entity_id:
                return "location", player.index, position, location.card_id
    if game.pending_choice:
        for position, option in enumerate(game.pending_choice.get("options", ())):
            if getattr(option, "entity_id", None) == entity_id:
                return "choice", game.current, position, option.card_id
    return "literal", None, entity_id, None


def encode_action(game: DragonMirrorGame, action: Action) -> tuple[float, ...]:
    """Encode a legal action without depending on raw entity-number magnitude."""
    kind_index = ACTION_KINDS.index(action.kind)
    source_zone, source_player, source_position, source_card = _locate_entity(
        game, action.source
    )
    if action.kind in {"AMMUNITION_PICK", "CORPSE_SPEND"}:
        source_zone, source_position = "literal", action.source
    if action.target_player is not None and action.target_entity is None:
        target_kind = "hero"
        target_player, target_position, target_card = action.target_player, None, None
    else:
        target_zone, target_player, target_position, target_card = _locate_entity(
            game, action.target_entity
        )
        target_kind = "none" if target_zone == "none" else (
            "literal" if target_zone == "literal" else "card"
        )
    values = _one_hot(kind_index, len(ACTION_KINDS))
    values += _one_hot(ZONE_NAMES.index(source_zone), len(ZONE_NAMES))
    values += _one_hot(source_player, 2)
    values += _one_hot(CARD_INDEX.get(source_card), len(CARD_VOCAB))
    values += _one_hot(
        source_position if isinstance(source_position, int) else None,
        MAX_HAND_SLOTS,
    )
    values += _one_hot(TARGET_KINDS.index(target_kind), len(TARGET_KINDS))
    values += _one_hot(target_player, 2)
    values += _one_hot(CARD_INDEX.get(target_card), len(CARD_VOCAB))
    values += _one_hot(
        target_position if isinstance(target_position, int) else None,
        MAX_HAND_SLOTS,
    )
    values.append(
        float(source_position) / 10.0
        if source_zone == "literal" and isinstance(source_position, int)
        else 0.0
    )
    return tuple(values)


@dataclass(frozen=True)
class EncodedDecision:
    state: tuple[float, ...]
    actions: tuple[tuple[float, ...], ...]
    action_keys: tuple[tuple, ...]


def encode_decision(game: DragonMirrorGame) -> EncodedDecision:
    legal = game.legal_actions()
    return EncodedDecision(
        state=encode_state(game, game.current),
        actions=tuple(encode_action(game, action) for action in legal),
        action_keys=tuple(action.key() for action in legal),
    )


def feature_schema(
    schema_version: int = STATE_SCHEMA_VERSION,
) -> dict[str, object]:
    if schema_version not in {LEGACY_STATE_SCHEMA_VERSION, STATE_SCHEMA_VERSION}:
        raise ValueError(f"unsupported state schema version: {schema_version}")
    vocab_json = json.dumps(CARD_VOCAB, separators=(",", ":"))
    legacy_state_size = 24 + 3 * len(CARD_VOCAB)
    dynamic_state_size = 16 + MAX_HAND_SLOTS * 4 + 2 * MAX_BOARD_SLOTS * 19 + 2 * MAX_BOARD_SLOTS * 2
    return {
        "schema_version": schema_version,
        "card_vocab_size": len(CARD_VOCAB),
        "card_vocab_sha256": hashlib.sha256(vocab_json.encode()).hexdigest(),
        "state_size": (
            legacy_state_size
            if schema_version == LEGACY_STATE_SCHEMA_VERSION
            else legacy_state_size + dynamic_state_size
        ),
        "action_size": (
            len(ACTION_KINDS) + len(ZONE_NAMES) + 2 + len(CARD_VOCAB)
            + MAX_HAND_SLOTS + len(TARGET_KINDS) + 2 + len(CARD_VOCAB)
            + MAX_HAND_SLOTS + 1
        ),
        "action_kinds": list(ACTION_KINDS),
    }
