"""Versioned, framework-neutral state/action encoding for policy/value models."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .dragon_mirror import Action, DragonMirrorGame
from .legacy_vocab import LEGACY_CARD_VOCAB


STATE_SCHEMA_VERSION = 7
LEGACY_STATE_SCHEMA_VERSION = 1
ABSOLUTE_ACTION_PLAYER_SCHEMA_VERSION = 2
RELATIVE_ACTION_PLAYER_SCHEMA_VERSION = 3
ACTION_TARGET_ZONE_SCHEMA_VERSION = 4
ACTION_KINDS = (
    "END_TURN", "MULLIGAN_TOGGLE", "MULLIGAN_CONFIRM", "TRADE", "PLAY",
    "PREPARE", "ATTACK", "HERO_ATTACK", "LOCATION", "HERO_POWER",
    "DISCOVER_PICK", "REWIND_KEEP", "REWIND_RETRY", "AMMUNITION_PICK",
    "CORPSE_SPEND",
)
CARD_VOCAB_MODE = "legacy"
CARD_VOCAB = LEGACY_CARD_VOCAB
CARD_INDEX = {card_id: index for index, card_id in enumerate(CARD_VOCAB)}


def _load_frozen_vocabulary(path: Path) -> tuple[str, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    card_ids = tuple(payload["card_ids"])
    if len(card_ids) != len(set(card_ids)) or tuple(sorted(card_ids)) != card_ids:
        raise ValueError(f"{path}: card vocabulary must be sorted and unique")
    digest = hashlib.sha256(
        json.dumps(card_ids, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    if payload.get("card_vocab_sha256") not in (None, digest):
        raise ValueError(f"{path}: card vocabulary digest does not match contents")
    return card_ids


def configure_card_vocab(
    mode: str, *, vocabulary_file: Path | None = None,
    vocabulary: tuple[str, ...] | list[str] | None = None,
) -> None:
    """Select the frozen identity vocabulary used by a dataset/checkpoint.

    An expanded vocabulary must be frozen at data-generation time. Deriving it
    from the mutable runtime executable set would silently resize later model
    inputs after a new generated token is implemented.
    """
    global CARD_VOCAB_MODE, CARD_VOCAB, CARD_INDEX
    if vocabulary is not None and vocabulary_file is not None:
        raise ValueError("supply either vocabulary or vocabulary_file, not both")
    if vocabulary is not None:
        vocabulary = tuple(vocabulary)
        if tuple(sorted(vocabulary)) != vocabulary or len(set(vocabulary)) != len(vocabulary):
            raise ValueError("explicit card vocabulary must be sorted and unique")
    elif vocabulary_file is not None:
        vocabulary = _load_frozen_vocabulary(vocabulary_file)
    elif mode == "legacy":
        vocabulary = tuple(LEGACY_CARD_VOCAB)
    elif mode == "expanded-executable":
        # Backward-compatible v4 name. Its historical list is immutable, so
        # new runtime-only entities remain unknown to old checkpoints.
        vocabulary = _load_frozen_vocabulary(
            Path(__file__).resolve().parents[2]
            / "config" / "card_vocabs" / "expanded-executable-v1.json"
        )
    else:
        raise ValueError(
            "card vocabulary must be 'legacy', 'expanded-executable', or frozen"
        )
    CARD_VOCAB_MODE = mode
    CARD_VOCAB = vocabulary
    CARD_INDEX = {card_id: index for index, card_id in enumerate(CARD_VOCAB)}
ZONE_NAMES = ("none", "hand", "board", "location", "choice", "literal")
TARGET_KINDS = ("none", "hero", "card", "literal")
MAX_HAND_SLOTS = 10
MAX_BOARD_SLOTS = 7

# Schema v7 assigns an explicit card token to every card-bearing entity slot.
# Zero means an empty slot, one means a known runtime card outside the frozen
# vocabulary, and vocabulary rows start at two.  The layout is fixed so NPU
# batches retain static shapes as cards enter and leave play.
ENTITY_CARD_LAYOUT = (
    ("own_hand", MAX_HAND_SLOTS),
    ("own_board", MAX_BOARD_SLOTS),
    ("enemy_board", MAX_BOARD_SLOTS),
    ("own_locations", MAX_BOARD_SLOTS),
    ("enemy_locations", MAX_BOARD_SLOTS),
    ("weapons", 2),
    ("hero_powers", 2),
)
ENTITY_CARD_SLOT_COUNT = sum(width for _, width in ENTITY_CARD_LAYOUT)

# Card semantics are intentionally independent of the frozen card-ID
# vocabulary.  This lets an unseen-but-known card contribute type, class,
# tribe, cost, stats, rarity and keyword information instead of collapsing to
# an all-zero identity feature.
CARD_TYPES = ("MINION", "SPELL", "WEAPON", "LOCATION", "HERO")
CARD_CLASSES = (
    "NEUTRAL", "DEATHKNIGHT", "DEMONHUNTER", "DRUID", "HUNTER",
    "MAGE", "PALADIN", "PRIEST", "ROGUE", "SHAMAN", "WARLOCK",
    "WARRIOR",
)
CARD_RACES = (
    "BEAST", "DEMON", "DRAGON", "ELEMENTAL", "MECHANICAL", "MURLOC",
    "NAGA", "PIRATE", "QUILBOAR", "TOTEM", "UNDEAD", "ALL", "TREANT",
    "GNOLL", "GRONN", "OGRE", "TITAN", "PET", "DRAENEI", "CENTAUR",
)
CARD_MECHANICS = (
    "TAUNT", "RUSH", "CHARGE", "BATTLECRY", "DEATHRATTLE", "DIVINE_SHIELD",
    "REBORN", "WINDFURY", "MEGA_WINDFURY", "LIFESTEAL", "POISONOUS",
    "VENOMOUS", "STEALTH", "ELUSIVE", "FREEZE", "DISCOVER", "INSPIRE",
    "SPELLBURST", "OUTCAST", "OVERKILL", "FRENZY", "HONORABLE_KILL",
    "CORRUPT", "ECHO", "TRADEABLE", "MAGNETIC", "DORMANT", "COLOSSAL",
    "OVERLOAD", "TWINSPELL", "REWIND", "FINALE", "QUICKDRAW", "KINDRED",
)
CARD_RARITIES = ("FREE", "COMMON", "RARE", "EPIC", "LEGENDARY", "SPECIAL")
CARD_TEXT_EFFECT_PATTERNS = (
    r"\bdamage\b", r"\bdestroy\b", r"\bsilence\b", r"\bsummon\b",
    r"\bdraw\b", r"\bdiscover\b", r"\badd .{0,50} to (?:your )?hand\b|\bgenerate\b",
    r"\btransform\b|\bturn .{0,50} into\b", r"\bcopy\b",
    r"\breturn .{0,50} to (?:your )?hand\b", r"\bshuffle .{0,50} into .{0,30}deck\b",
    r"\bresurrect\b|\brevive\b", r"\breduce .{0,40}cost\b|\bcosts? (?:\([0-9]+\) )?less\b",
    r"\bincrease .{0,40}cost\b|\bcosts? (?:\([0-9]+\) )?more\b",
    r"\bgain .{0,30}mana\b|\brefresh .{0,30}mana\b|\bmana crystal\b",
    r"\barmor\b", r"\bheal\b|\brestore .{0,30}health\b",
    r"\bgive .{0,40}\+|\bgain .{0,30}\+", r"\breduce .{0,30}attack\b|\blose .{0,30}attack\b",
    r"\battack\b", r"\bweapon\b|\bequip\b", r"\bsecret\b",
    r"\bchoose one\b|\bchoose both\b", r"\brandom(?:ly)?\b",
    r"\benemy\b|\bopposing\b", r"\bfriendly\b|\byour minion\b|\byour character\b",
    r"\bbattlecry\b", r"\bdeathrattle\b|\bafter .{0,30}dies\b|\bwhen .{0,30}dies\b",
    r"\bend of your turn\b|\bat end of turn\b", r"\bstart of your turn\b",
    r"\bwhenever .{0,40}damage\b|\bafter .{0,30}takes damage\b|\bwhen .{0,30}damaged\b",
    r"\bafter you play\b|\bwhenever you play\b|\bwhen you play\b",
    r"\bif you\b|\bif your\b|\bwhile you\b|\bwhen you have\b",
    r"\bfor every\b|\beach time\b|\bprogress\b|\bquest\b",
    r"\bagain\b|\btwice\b|\brepeat\b", r"\blifesteal\b",
    r"\bthis turn\b|\buntil end of turn\b", r"\bboard\b|\bbattlefield\b",
    r"\bhand\b", r"\bdeck\b", r"\bhero\b", r"\bspell\b", r"\bminion\b",
    r"\battack your hero\b|\battack the enemy hero\b",
)
_CARD_TEXT_EFFECT_REGEXES = tuple(re.compile(pattern) for pattern in CARD_TEXT_EFFECT_PATTERNS)
CARD_SEMANTIC_FEATURE_SIZE = (
    len(CARD_TYPES) + len(CARD_CLASSES) + len(CARD_RACES)
    + len(CARD_MECHANICS) + 11 + 2 + len(CARD_RARITIES)
    + len(CARD_TEXT_EFFECT_PATTERNS)
)


def card_semantic_features(definition) -> tuple[float, ...]:
    """Return a stable, ID-free metadata vector for a card definition."""
    def attr(name, json_name=None, default=None):
        if isinstance(definition, dict):
            return definition.get(json_name or name, default)
        return getattr(definition, name, default)

    # Cache by the fields that affect the vector, not card ID or object
    # identity. Some runtime cards share an ID but have modified definitions.
    return _card_semantic_features_cached(
        attr("card_type", "type", ""),
        tuple(attr("classes", default=()) or ()),
        attr("card_class", "cardClass", "") or "",
        tuple(attr("races", default=()) or ()),
        attr("race", default=""),
        tuple(attr("mechanics", default=()) or ()),
        attr("cost", default=0), attr("attack", default=0),
        attr("health", default=0), attr("rarity", default="") or "SPECIAL",
        attr("text", default="") or "",
    )


@lru_cache(maxsize=8192)
def _card_semantic_features_cached(card_type, classes, card_class, races,
                                   race, mechanics, cost_raw, attack_raw,
                                   health_raw, rarity, text_raw):
    values = _one_hot(CARD_TYPES.index(card_type)
                      if card_type in CARD_TYPES else None,
                      len(CARD_TYPES))
    classes = set(classes)
    classes.add(card_class)
    values.extend(float(name in classes) for name in CARD_CLASSES)
    races = set(races)
    if race:
        races.add(race)
    values.extend(float(name in races) for name in CARD_RACES)
    mechanics = set(mechanics)
    values.extend(float(name in mechanics) for name in CARD_MECHANICS)
    cost = max(0, min(10, int(cost_raw)))
    values.extend(_one_hot(cost, 11))
    values.extend((min(max(float(attack_raw), 0.0), 20.0) / 20.0,
                   min(max(float(health_raw), 0.0), 20.0) / 20.0))
    values.extend(_one_hot(CARD_RARITIES.index(rarity)
                           if rarity in CARD_RARITIES else None,
                           len(CARD_RARITIES)))
    text = re.sub(r"\s+", " ", text_raw).lower()
    values.extend(float(bool(pattern.search(text)))
                  for pattern in _CARD_TEXT_EFFECT_REGEXES)
    if len(values) != CARD_SEMANTIC_FEATURE_SIZE:
        raise AssertionError("card semantic feature width drifted")
    return tuple(values)


def _semantic_summary(cards, divisor: float) -> list[float]:
    result = [0.0] * CARD_SEMANTIC_FEATURE_SIZE
    for card in cards:
        features = card_semantic_features(card.definition)
        for index, value in enumerate(features):
            result[index] += value / divisor
    return result


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


def _entity_card_token(card_id: str | None) -> float:
    if not card_id:
        return 0.0
    index = CARD_INDEX.get(card_id)
    return float(1 if index is None else index + 2)


def _entity_card_tokens(game: DragonMirrorGame, observer: int) -> list[float]:
    """Return aligned card identities for every visible card-bearing slot."""
    own = game.players[observer]
    enemy = game.players[1 - observer]

    def padded_ids(cards, width: int) -> list[str | None]:
        values = [getattr(card, "card_id", None) for card in cards[:width]]
        return values + [None] * (width - len(values))

    ids: list[str | None] = []
    ids.extend(padded_ids(own.hand, MAX_HAND_SLOTS))
    ids.extend(padded_ids(own.board, MAX_BOARD_SLOTS))
    ids.extend(padded_ids(enemy.board, MAX_BOARD_SLOTS))
    ids.extend(padded_ids(own.locations, MAX_BOARD_SLOTS))
    ids.extend(padded_ids(enemy.locations, MAX_BOARD_SLOTS))
    ids.extend((
        getattr(own.weapon, "card_id", None),
        getattr(enemy.weapon, "card_id", None),
        own.hero_power_id,
        enemy.hero_power_id,
    ))
    if len(ids) != ENTITY_CARD_SLOT_COUNT:
        raise AssertionError("entity card layout width drifted")
    return [_entity_card_token(card_id) for card_id in ids]


def card_semantic_lookup(card_definitions: dict[str, object]) -> list[list[float]]:
    """Build the shared v7 semantic table aligned with entity token IDs.

    The table is stored once in the dataset header/checkpoint, rather than
    repeating 134 semantic floats for every entity in every decision record.
    """
    table = [
        [0.0] * CARD_SEMANTIC_FEATURE_SIZE,  # empty
        [0.0] * CARD_SEMANTIC_FEATURE_SIZE,  # out-of-vocabulary
    ]
    for card_id in CARD_VOCAB:
        definition = card_definitions.get(card_id)
        table.append(list(card_semantic_features(definition)) if definition else
                     [0.0] * CARD_SEMANTIC_FEATURE_SIZE)
    return table


def encode_state(
    game: DragonMirrorGame,
    observer: int | None = None,
    *,
    schema_version: int = STATE_SCHEMA_VERSION,
) -> tuple[float, ...]:
    """Encode only information visible to ``observer`` into a fixed vector."""
    if schema_version not in {
        LEGACY_STATE_SCHEMA_VERSION,
        ABSOLUTE_ACTION_PLAYER_SCHEMA_VERSION,
        RELATIVE_ACTION_PLAYER_SCHEMA_VERSION,
        ACTION_TARGET_ZONE_SCHEMA_VERSION,
        5,
        6,
        STATE_SCHEMA_VERSION,
    }:
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
    if schema_version >= 5:
        # The acting player knows their deck list and which cards remain in
        # it. Keep this histogram contiguous with the other card roles so the
        # structured model can embed them with one shared identity table.
        # Never expose the opponent's hidden deck identities here.
        values.extend(_card_histogram(own.deck))
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

    if schema_version >= 5:
        # Conditional triggers such as Warptooth depend on distinct friendly
        # characters damaged during the active player's turn. Dead minions are
        # no longer on board, so this progress cannot be reconstructed from
        # the ordinary board slots. Only expose the active player's current
        # turn counter; the other player's retained prior-turn counter is not
        # actionable and would be misleading.
        values.extend((
            min(len(own.damaged_characters_this_turn), 4) / 4.0
            if game.current == own.index else 0.0,
            min(len(enemy.damaged_characters_this_turn), 4) / 4.0
            if game.current == enemy.index else 0.0,
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
    if schema_version >= 6:
        # Same four observable card roles as the ID histograms, but semantic
        # metadata is retained even for cards outside the frozen ID vocab.
        for cards, divisor in (
            (own.hand, 10.0), (own.board, 7.0),
            (enemy.board, 7.0), (own.deck, 30.0),
        ):
            values.extend(_semantic_summary(cards, divisor))
    if schema_version >= 7:
        values.extend(_entity_card_tokens(game, observer))
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


def encode_action(
    game: DragonMirrorGame,
    action: Action,
    *,
    schema_version: int = STATE_SCHEMA_VERSION,
) -> tuple[float, ...]:
    """Encode a legal action without depending on raw entity-number magnitude."""
    if schema_version not in {
        LEGACY_STATE_SCHEMA_VERSION,
        ABSOLUTE_ACTION_PLAYER_SCHEMA_VERSION,
        RELATIVE_ACTION_PLAYER_SCHEMA_VERSION,
        ACTION_TARGET_ZONE_SCHEMA_VERSION,
        5,
        6,
        STATE_SCHEMA_VERSION,
    }:
        raise ValueError(f"unsupported action schema version: {schema_version}")
    # Keep the fixed action schema backward-compatible when newer rule
    # modules introduce a choice action.  Choice picks have the same
    # source/target semantics as discover picks, so encode them through the
    # existing slot rather than changing model input dimensions.  HAND_PICK
    # and DISCARD_PICK are hand-selection choices, while the other aliases
    # are board/deck choice prompts; their source entity/position remains
    # available through the normal locator fields.
    encoded_kind = action.kind
    if encoded_kind not in ACTION_KINDS:
        if encoded_kind in {
            "RULE_CHOICE_PICK", "CATACLYSM_PICK", "EARTHEN_ROAR_PICK",
            "DISCARD_PICK", "HAND_PICK",
        }:
            encoded_kind = "DISCOVER_PICK"
        else:
            raise ValueError(f"unsupported action kind: {action.kind}")
    kind_index = ACTION_KINDS.index(encoded_kind)
    source_zone, source_player, source_position, source_card = _locate_entity(
        game, action.source
    )
    if action.kind in {"AMMUNITION_PICK", "CORPSE_SPEND"}:
        source_zone, source_position = "literal", action.source
    if action.target_player is not None and action.target_entity is None:
        target_zone = "none"
        target_kind = "hero"
        target_player, target_position, target_card = action.target_player, None, None
    else:
        target_zone, target_player, target_position, target_card = _locate_entity(
            game, action.target_entity
        )
        target_kind = "none" if target_zone == "none" else (
            "literal" if target_zone == "literal" else "card"
        )
    if schema_version >= RELATIVE_ACTION_PLAYER_SCHEMA_VERSION:
        source_player = (
            None if source_player is None
            else 0 if source_player == game.current else 1
        )
        target_player = (
            None if target_player is None
            else 0 if target_player == game.current else 1
        )
    values = _one_hot(kind_index, len(ACTION_KINDS))
    values += _one_hot(ZONE_NAMES.index(source_zone), len(ZONE_NAMES))
    values += _one_hot(source_player, 2)
    values += _one_hot(CARD_INDEX.get(source_card), len(CARD_VOCAB))
    values += _one_hot(
        source_position if isinstance(source_position, int) else None,
        MAX_HAND_SLOTS,
    )
    if schema_version >= ACTION_TARGET_ZONE_SCHEMA_VERSION:
        values += _one_hot(ZONE_NAMES.index(target_zone), len(ZONE_NAMES))
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
    if schema_version >= 6:
        source_definition = game.card_defs.get(source_card) if source_card else None
        target_definition = game.card_defs.get(target_card) if target_card else None
        values.extend(card_semantic_features(source_definition)
                      if source_definition else (0.0,) * CARD_SEMANTIC_FEATURE_SIZE)
        values.extend(card_semantic_features(target_definition)
                      if target_definition else (0.0,) * CARD_SEMANTIC_FEATURE_SIZE)
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
        actions=tuple(
            encode_action(game, action, schema_version=STATE_SCHEMA_VERSION)
            for action in legal
        ),
        action_keys=tuple(action.key() for action in legal),
    )


def feature_schema(
    schema_version: int = STATE_SCHEMA_VERSION,
    *,
    card_definitions: dict[str, object] | None = None,
) -> dict[str, object]:
    if schema_version not in {
        LEGACY_STATE_SCHEMA_VERSION,
        ABSOLUTE_ACTION_PLAYER_SCHEMA_VERSION,
        RELATIVE_ACTION_PLAYER_SCHEMA_VERSION,
        ACTION_TARGET_ZONE_SCHEMA_VERSION,
        5,
        6,
        STATE_SCHEMA_VERSION,
    }:
        raise ValueError(f"unsupported state schema version: {schema_version}")
    vocab_json = json.dumps(CARD_VOCAB, separators=(",", ":"))
    legacy_state_size = 24 + 3 * len(CARD_VOCAB)
    dynamic_state_size = 16 + MAX_HAND_SLOTS * 4 + 2 * MAX_BOARD_SLOTS * 19 + 2 * MAX_BOARD_SLOTS * 2
    semantic_state_size = 4 * CARD_SEMANTIC_FEATURE_SIZE if schema_version >= 6 else 0
    semantic_action_size = 2 * CARD_SEMANTIC_FEATURE_SIZE if schema_version >= 6 else 0
    entity_identity_size = ENTITY_CARD_SLOT_COUNT if schema_version >= 7 else 0
    result = {
        "schema_version": schema_version,
        "card_vocab_size": len(CARD_VOCAB),
        "card_vocab_mode": CARD_VOCAB_MODE,
        "card_vocab_sha256": hashlib.sha256(vocab_json.encode()).hexdigest(),
        "card_vocab_ids": list(CARD_VOCAB),
        "state_size": (
            legacy_state_size
            if schema_version == LEGACY_STATE_SCHEMA_VERSION
            else legacy_state_size + dynamic_state_size
            + (2 + len(CARD_VOCAB) if schema_version >= 5 else 0)
            + semantic_state_size + entity_identity_size
        ),
        "action_size": (
            len(ACTION_KINDS) + len(ZONE_NAMES) + 2 + len(CARD_VOCAB)
            + MAX_HAND_SLOTS
            + (len(ZONE_NAMES) if schema_version >= ACTION_TARGET_ZONE_SCHEMA_VERSION else 0)
            + len(TARGET_KINDS) + 2 + len(CARD_VOCAB)
            + MAX_HAND_SLOTS + 1 + semantic_action_size
        ),
        "action_kinds": list(ACTION_KINDS),
        "action_player_encoding": (
            "relative"
            if schema_version >= RELATIVE_ACTION_PLAYER_SCHEMA_VERSION
            else "absolute"
        ),
        "action_target_zone": schema_version >= ACTION_TARGET_ZONE_SCHEMA_VERSION,
        "card_semantic_feature_size": CARD_SEMANTIC_FEATURE_SIZE if schema_version >= 6 else 0,
        "card_semantics": (
            "type-class-race-mechanics-cost-stats-rarity-text-effect-v2"
            if schema_version >= 6 else "none"
        ),
        "entity_card_slot_count": entity_identity_size,
        "entity_card_layout": (
            [[name, width] for name, width in ENTITY_CARD_LAYOUT]
            if schema_version >= 7 else []
        ),
        "entity_card_token_rows": (
            len(CARD_VOCAB) + 2 if schema_version >= 7 else 0
        ),
    }
    if schema_version >= 7 and card_definitions is not None:
        semantic_lookup = card_semantic_lookup(card_definitions)
        semantic_json = json.dumps(semantic_lookup, separators=(",", ":"))
        result["entity_card_semantic_lookup"] = semantic_lookup
        result["entity_card_semantic_sha256"] = hashlib.sha256(
            semantic_json.encode()
        ).hexdigest()
    return result


def compatible_feature_schema(left: dict[str, object], right: dict[str, object]) -> bool:
    """Compare model-shaping schema fields across old and new artifacts.

    Pre-manifest v4 checkpoints did not embed ``card_vocab_ids``.  They remain
    compatible with a later artifact only when every tensor-shaping field and
    the vocabulary digest agree; the missing diagnostic list is not itself a
    schema migration.
    """
    fields = (
        "schema_version", "card_vocab_size", "card_vocab_mode",
        "card_vocab_sha256", "state_size", "action_size", "action_kinds",
        "action_player_encoding", "action_target_zone",
    )
    if not all(left.get(field) == right.get(field) for field in fields):
        return False
    if int(left.get("schema_version", 0) or 0) >= 6:
        if not all(left.get(field) == right.get(field) for field in (
            "card_semantic_feature_size", "card_semantics",
        )):
            return False
    if int(left.get("schema_version", 0) or 0) >= 7:
        return all(left.get(field) == right.get(field) for field in (
            "entity_card_slot_count", "entity_card_layout",
            "entity_card_token_rows", "entity_card_semantic_sha256",
        ))
    return True
