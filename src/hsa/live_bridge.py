"""Conservative Power.log snapshot -> simulator belief bridge.

This module intentionally distinguishes a *snapshot-verified hypothesis* from
an omniscient replay.  Power.log does not reveal the opponent's hand/deck
order, so every candidate deck becomes one deterministic hypothesis.  The
caller may emit the plurality action immediately and exposes its support as a
confidence signal; it can also request a stricter consensus threshold.

The bridge is deliberately narrow: public hand/board entities, hero health,
mana and ordinary stat enchantments are hydrated; unresolved locations,
secrets, weapons and pending choices fail closed rather than being guessed.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
import json
from pathlib import Path
import re
from typing import Any

from .dragon_mirror import CardDef, DragonMirrorGame, Location, Weapon
from .live_compare import compare_public_state
from .live_replay import EntityIdMapper
from .live_special_zones import (broxigar_reserves, godfrey_public_copies,
                                 generated_hidden_hand_card)


_IMPLICIT_HERO_POWER_ID = re.compile(r"^HERO_\d+[a-z]*bp\d*$", re.IGNORECASE)
_EXECUTABLE_CARD_ALIASES = {
    # These client variants are all 0-cost "Gain 1 Mana Crystal this turn only".
    # Clients emit different second-player Coin variants by game version;
    # the engine implements the canonical GAME_005 form.
    "AV_COIN1": "GAME_005",
    "DFT_ALEX_COIN1": "GAME_005",
    "TTN_COIN2": "GAME_005",
    "VAC_COIN2": "GAME_005",
}
_NON_BOARD_ENTITY_TYPES = {
    "HERO", "PLAYER", "GAME", "HERO_POWER", "WEAPON", "LOCATION",
    "ENCHANTMENT", "COUNTER",
}
_STATIC_PUBLIC_MINION_MECHANICS = frozenset({
    "TAUNT", "RUSH", "CHARGE", "LIFESTEAL", "ELUSIVE", "STEALTH",
    "DIVINE_SHIELD", "WINDFURY", "REBORN", "POISONOUS", "CANT_ATTACK",
})
_STATIC_KEYWORD_TEXT = frozenset({
    "taunt", "rush", "charge", "lifesteal", "elusive", "stealth",
    "divine shield", "windfury", "reborn", "poisonous", "can't attack",
})
_PUBLIC_STATIC_DEF_CACHE: dict[tuple[str, int, int], dict[str, CardDef]] = {}


def _is_hero_power(entity: Any) -> bool:
    """Recognise client hero-power IDs when the CARDTYPE tag is omitted.

    Some Power.log snapshots put the ordinary class power in PLAY but leave
    out ``CARDTYPE=HERO_POWER``.  ``HERO_01wbp`` is one such Warrior spelling.
    Tokens such as ``HERO_11bpt`` do not match and remain ordinary minions.
    """
    if entity.card_type == "HERO_POWER":
        return True
    return bool(_IMPLICIT_HERO_POWER_ID.fullmatch(str(entity.card_id or "")))


def _tag_is_true(entity: Any, tag: str) -> bool:
    """Read Hearthstone's integer/boolean public tags without guessing."""
    value = entity.tags.get(tag)
    try:
        return bool(int(value))
    except (TypeError, ValueError):
        return str(value).upper() in {"TRUE", "YES"}


def _public_remaining_durability(entity: Any) -> int | None:
    """Read remaining weapon/location durability from public Power.log tags."""
    explicit = entity.tags.get("DURABILITY")
    try:
        if explicit is not None:
            remaining = int(explicit)
        elif entity.health is not None:
            remaining = int(entity.health) - int(entity.damage)
        else:
            return None
    except (TypeError, ValueError):
        return None
    return remaining if remaining > 0 else None


def _executable_card_id(game: DragonMirrorGame, card_id: str | None) -> str | None:
    """Resolve audited runtime aliases without inventing card behavior."""
    if not card_id:
        return None
    resolved = _EXECUTABLE_CARD_ALIASES.get(card_id, card_id)
    return resolved if resolved in game.card_defs else None


def _has_only_static_keyword_text(text: str) -> bool:
    """Accept only a blank rules box or a list of engine-supported keywords."""
    plain = re.sub(r"<[^>]+>", "", (text or "").replace("<br/>", "\n"))
    plain = plain.replace("\xa0", " ")
    lines = [line.strip().rstrip(".").lower()
             for line in plain.replace("<br/>", "\n").splitlines() if line.strip()]
    return not lines or all(line in _STATIC_KEYWORD_TEXT for line in lines)


def _public_static_minion_defs(cards_path: str | Path) -> dict[str, CardDef]:
    """Load safe public-only minion definitions without expanding play pools.

    The simulator's executable catalog intentionally excludes most Standard
    cards.  A visible enemy whiteboard minion is still needed to calculate
    legal targets and combat.  This cache admits only minions whose complete
    printed behavior is base stats plus keywords that the simulator already
    implements.  They are *not* added to ``executable_card_ids`` and therefore
    cannot leak into Discover/random generation/search-created hidden zones.
    """
    path = Path(cards_path)
    stat = path.stat()
    key = (str(path.resolve()), stat.st_mtime_ns, stat.st_size)
    cached = _PUBLIC_STATIC_DEF_CACHE.get(key)
    if cached is not None:
        return cached

    result: dict[str, CardDef] = {}
    for card in json.loads(path.read_text(encoding="utf-8")):
        card_id = str(card.get("id") or "")
        mechanics = tuple(card.get("mechanics", ()) or ())
        if (not card_id or card.get("type") != "MINION"
                or not set(mechanics).issubset(_STATIC_PUBLIC_MINION_MECHANICS)
                or not _has_only_static_keyword_text(str(card.get("text") or ""))):
            continue
        result[card_id] = CardDef(
            card_id=card_id,
            name=str(card.get("name") or card_id),
            card_type="MINION",
            cost=int(card.get("cost", 0)),
            attack=int(card.get("attack", 0)),
            health=int(card.get("health", 0)),
            race=str(card.get("race") or ""),
            mechanics=mechanics,
            card_class=str(card.get("cardClass") or ""),
            races=tuple(card.get("races", ()) or ()),
            card_set=str(card.get("set") or ""),
            text=str(card.get("text") or ""),
        )
    _PUBLIC_STATIC_DEF_CACHE[key] = result
    return result


@dataclass
class BridgeResult:
    game: DragonMirrorGame | None = None
    mapper: EntityIdMapper = field(default_factory=EntityIdMapper)
    reason: str | None = None
    public_match: dict[str, Any] | None = None
    hypothesis_notes: list[str] = field(default_factory=list)

    @property
    def available(self) -> bool:
        return self.game is not None and self.reason is None


def _supported_bridge_deck_sizes(own_deck: dict[str, int],
                                 opponent_deck: dict[str, int]) -> tuple[bool, bool]:
    """Return (supported, short-format-opponent) for live hydration."""
    own_size = sum(map(int, own_deck.values()))
    opponent_size = sum(map(int, opponent_deck.values()))
    short_format = opponent_size == 20 and int(opponent_deck.get("JAIL_430", 0)) > 0
    return own_size >= 30 and (opponent_size >= 30 or short_format), short_format

def _controller_entities(state: Any, controller: int, zone: str) -> list[Any]:
    return [entity for entity in state.entities.values()
            if entity.controller == controller and entity.zone == zone]


def _classes(value: tuple[str, str] | list[str] | None) -> tuple[str, str]:
    if not value or len(value) != 2:
        return ("WARRIOR", "WARRIOR")
    return (str(value[0]).upper(), str(value[1]).upper())


def _visible_card_counts(state: Any, controller: int) -> Counter[str]:
    """Count unique visible non-generated entities currently outside DECK.

    PLAY and ATTACK history describe actions, not additional card copies.
    Counting that history double-subtracted living minions and subtracted
    them again on every attack. Current zones also let a shuffled-back card
    rejoin the candidate bag. When provenance is absent, membership in the
    supplied deck remains a hypothesis; transformations/theft need additional
    origin information to fully reconstruct the remaining list.
    """
    result: Counter[str] = Counter()
    seen = set()
    for entity in state.entities.values():
        original_deck = bool(entity.zone_history and entity.zone_history[0][1] == "DECK"
                             and not any(entity.tags.get(tag) not in (None, 0, "0", "")
                                         for tag in ("CREATOR", "COPIED_FROM_ENTITY_ID")))
        owner = (entity.initial_controller or entity.controller) if original_deck else entity.controller
        if (entity.entity_id in seen or owner != controller
                or not entity.card_id or entity.zone not in {
                    "HAND", "PLAY", "SECRET", "GRAVEYARD", "REMOVEDFROMGAME", "SETASIDE"}
                or (entity.zone == "SETASIDE" and not original_deck)
                or (entity.card_type == "HERO" and not original_deck)
                or entity.card_type in {"PLAYER", "GAME", "HERO_POWER",
                                        "ENCHANTMENT", "COUNTER"}
                or _is_hero_power(entity)):
            continue
        seen.add(entity.entity_id)
        if any(entity.tags.get(tag) not in (None, 0, "0", "")
               for tag in ("CREATOR", "COPIED_FROM_ENTITY_ID")):
            continue
        original_id = entity.identity_history[0][1] if original_deck and entity.identity_history else entity.card_id
        result[original_id] += 1
    return result


def _self_controller_looks_reversed(state: Any, self_controller: int) -> bool:
    """Detect the public-hand pattern that proves a controller swap.

    The local client identifies its own hand, while an opponent hand normally
    contains anonymous entities.  This is only a diagnostic: deck ownership
    is user-supplied, so the bridge must not silently swap the two decks.
    """
    other = 1 if self_controller == 2 else 2
    own_hand = _controller_entities(state, self_controller, "HAND")
    other_hand = _controller_entities(state, other, "HAND")
    own_unknown = sum(not entity.card_id for entity in own_hand)
    other_known = sum(bool(entity.card_id) for entity in other_hand)
    return bool(own_unknown and other_known)


def _inert_setaside_entities(
    state: Any,
    open_choice_entities: tuple[int, ...],
    *,
    policy: str = "strict",
) -> set[str]:
    """Identify unlinked SETASIDE entities outside the decision surface.

    Power.log uses SETASIDE for completed-effect debris as well as for live
    choices.  Advisory mode may omit it only when it is not a choice, has no
    public reference, and is not an intrinsically active object such as a
    secret, weapon, or location.  The registry still retains it for audit.
    """
    if policy != "advisory":
        return set()
    projection = state.public_decision_projection(open_choice_entities)
    return set(projection["inert_setaside"])


def _inert_play_artifacts(state: Any, *, policy: str) -> set[str]:
    """Return zero-information internal objects temporarily exposed in PLAY.

    Some effects materialize an internal entity by moving it from SETASIDE to
    PLAY without a card identity, type, stats, cost, or public reference. It
    cannot be a legal target or a playable card from the information exposed
    to the client. Advisory mode excludes only this exact shape and records a
    risk note; any opaque entity with stats, a type, or a reference remains
    fail-closed.
    """
    if policy != "advisory":
        return set()
    referenced = {
        str(reference)
        for entity in state.entities.values()
        for reference in getattr(entity, "references", set())
    }
    result = set()
    for entity in state.entities.values():
        history = [zone for _, zone in getattr(entity, "zone_history", ())]
        is_setaside_play_artifact = (
            entity.controller in (1, 2)
            and entity.zone == "PLAY"
            and not entity.card_id
            and not entity.card_type
            and entity.attack is None
            and entity.health is None
            and entity.cost is None
            and str(entity.entity_id) not in referenced
            and "SETASIDE" in history
        )
        if is_setaside_play_artifact:
            result.add(str(entity.entity_id))
    return result


def _modeled_corpse_rebirth_proxies(state: Any, game: DragonMirrorGame) -> dict[str, int]:
    """Find TIME_618's public player enchantment and its SETASIDE spell proxy.

    The proxy is not a pending choice: the engine represents the same effect
    with ``corpse_rebirth_pending``. Require a public corpse count and a
    verified attachment to the owning PLAYER entity before substituting it.
    """
    if "TIME_618t" not in game.card_defs:
        return {}
    players = [entity for entity in state.entities.values()
               if entity.card_type == "PLAYER"
               or "MULLIGAN_STATE" in entity.tags
               or "PLAYSTATE" in entity.tags]
    players.sort(key=lambda entity: int(entity.entity_id)
                 if entity.entity_id.lstrip("-").isdigit() else 10**9)
    if len(players) != 2:
        return {}
    owner_by_entity = {entity.entity_id: index
                       for index, entity in enumerate(players, start=1)}
    meta = state.visible().get("player_meta", {})
    result: dict[str, int] = {}
    for enchant in state.entities.values():
        if (enchant.card_id != "TIME_618e" or enchant.zone != "PLAY"
                or enchant.card_type != "ENCHANTMENT"):
            continue
        controller = owner_by_entity.get(str(enchant.tags.get("ATTACHED")))
        proxy_id = str(enchant.tags.get("TAG_SCRIPT_DATA_NUM_1"))
        proxy = state.entities.get(proxy_id)
        if (controller not in (1, 2) or enchant.controller != controller
                or proxy is None or proxy.card_id != "TIME_618t"
                or proxy.zone != "SETASIDE" or proxy.controller != controller
                or meta.get(str(controller), {}).get("corpses") is None):
            continue
        result[proxy_id] = controller
    return result


def _retired_deathwing_hero_entities(state: Any, game: DragonMirrorGame) -> set[str]:
    """Recognise the old hero/power archived by permanent CATA_190h replacement.

    This is not a general rule for every hero transformation. Require the
    replacement hero and its executable power to be public, plus the exact
    PLAY -> SETASIDE transition and linkage to the old hero.
    """
    if "CATA_190p" not in game.card_defs:
        return set()
    result: set[str] = set()
    for hero in state.entities.values():
        if not (hero.card_id == "CATA_190h" and hero.zone == "PLAY"
                and hero.card_type == "HERO" and hero.controller in (1, 2)):
            continue
        old_id = str(hero.tags.get("LINKED_ENTITY"))
        old_hero = state.entities.get(old_id)
        if (old_hero is None or old_hero.card_type != "HERO"
                or old_hero.controller != hero.controller
                or old_hero.zone != "SETASIDE"
                or "PLAY" not in [zone for _, zone in old_hero.zone_history]):
            continue
        new_power = any(
            entity.card_id == "CATA_190p" and entity.zone == "PLAY"
            and entity.card_type == "HERO_POWER"
            and entity.controller == hero.controller
            and str(entity.tags.get("CREATOR")) == hero.entity_id
            for entity in state.entities.values()
        )
        if not new_power:
            continue
        result.add(old_id)
        for entity in state.entities.values():
            if (entity.card_type == "HERO_POWER" and entity.zone == "SETASIDE"
                    and entity.controller == hero.controller
                    and str(entity.tags.get("CREATOR")) == old_id
                    and "PLAY" in [zone for _, zone in entity.zone_history]):
                result.add(entity.entity_id)
    return result


def _retired_linked_hero_powers(state: Any) -> set[str]:
    """Recognise a replaced hero power archived by its active successor.

    The link alone is insufficient: both objects must be hero powers owned by
    the same player, with the successor in PLAY and the predecessor having
    visibly moved PLAY -> SETASIDE. This only omits the retired action source
    from hydration; it never discards the currently usable power.
    """
    result: set[str] = set()
    for current in state.entities.values():
        if (current.card_type != "HERO_POWER" or current.zone != "PLAY"
                or current.controller not in (1, 2)):
            continue
        previous_id = str(current.tags.get("LINKED_ENTITY"))
        previous = state.entities.get(previous_id)
        if (previous is None or previous.card_type != "HERO_POWER"
                or previous.zone != "SETASIDE"
                or previous.controller != current.controller
                or "PLAY" not in [zone for _, zone in previous.zone_history]):
            continue
        result.add(previous_id)
    return result


def _unplayed_unlinked_setaside_heroes(
    state: Any, open_choice_entities: tuple[int, ...],
) -> set[str]:
    """Exclude an unactivated hero candidate from the current action surface.

    A generated hero can be staged in SETASIDE before a later effect uses it.
    It is not the *current* hero if it has never entered PLAY, no live object
    references it, and it is not an open choice. Any one of those signals keeps
    the normal fail-closed behavior.
    """
    selected = {str(entity_id) for entity_id in open_choice_entities}
    selected.update(str(entity_id) for choices in state.open_choice_candidates.values()
                    for entity_id in choices)
    referenced = {str(reference) for source in state.entities.values()
                  for reference in source.references}
    return {
        entity.entity_id for entity in state.entities.values()
        if entity.card_type == "HERO" and entity.zone == "SETASIDE"
        and entity.controller in (1, 2)
        and "PLAY" not in [zone for _, zone in entity.zone_history]
        and entity.entity_id not in selected
        and entity.entity_id not in referenced
    }


def _remaining_deck(deck: dict[str, int], observed: Counter[str]) -> list[str]:
    remaining: list[str] = []
    for card_id, count in deck.items():
        remaining.extend([card_id] * max(0, int(count) - observed.get(card_id, 0)))
    return remaining


def build_snapshot_hypothesis(
    *,
    cards_path: str | Path,
    state: Any,
    own_deck: dict[str, int],
    opponent_deck: dict[str, int],
    player_classes: tuple[str, str] | list[str] | None = None,
    self_controller: int = 1,
    seed: int = 1,
    open_choice_kind: str | None = None,
    open_choice_entities: tuple[int, ...] = (),
    setaside_policy: str = "strict",
) -> BridgeResult:
    """Build one hidden-state hypothesis from a public Power.log snapshot.

    ``own_deck`` and ``opponent_deck`` must be full lists.  The current public
    state is authoritative; unknown opponent hand slots are deterministically
    filled from the candidate's remaining cards solely for scoring that
    hypothesis.
    """
    # JAIL_430 (Azalina/Special Dirty Priest format) starts from a legal
    # 20-card list and copies 20 cards from the opponent before the opening
    # draw.  DragonMirror already applies that pre-game rule, so rejecting the
    # 20-card source list here would make the live belief path unable to model
    # an otherwise supported archetype.
    supported_sizes, opponent_short_format = _supported_bridge_deck_sizes(
        own_deck, opponent_deck)
    if not supported_sizes:
        return BridgeResult(reason="known deck must contain at least 30 cards; candidate must contain 30/40 cards or supported 20-card JAIL_430 format")
    classes = _classes(player_classes)
    decks = (dict(own_deck), dict(opponent_deck)) if self_controller == 1 else (dict(opponent_deck), dict(own_deck))
    classes = classes if self_controller == 1 else (classes[1], classes[0])
    try:
        game = DragonMirrorGame(str(cards_path), seed=seed, deck_counts=decks,
                                player_classes=classes)
    except Exception as exc:  # unsupported candidate cards must stay closed.
        return BridgeResult(reason=f"cannot initialise candidate: {exc}")
    # Constructor opening deals/Coin/start effects are synthetic, not events
    # observed in this live match. They must not update the hydrated belief.
    game.events.clear()
    # Keep public whiteboard minions available for combat hydration without
    # making them playable candidates or random-generation outcomes.
    static_public_defs = _public_static_minion_defs(cards_path)
    if static_public_defs:
        game.card_defs = {**game.card_defs, **static_public_defs}

    # These zones carry state that cannot be reconstructed safely yet. A
    # GAME_RESET may include inert completed-effect debris in SETASIDE; it is
    # excluded only by the narrowly defined public checks above.
    if setaside_policy not in {"strict", "advisory"}:
        return BridgeResult(reason=f"unknown SETASIDE policy: {setaside_policy}")
    if _self_controller_looks_reversed(state, self_controller):
        return BridgeResult(
            reason="self-controller likely reversed: configured local hand has hidden cards",
        )
    inert_setaside = _inert_setaside_entities(
        state, open_choice_entities, policy=setaside_policy)
    modeled_rebirth = (_modeled_corpse_rebirth_proxies(state, game)
                       if setaside_policy == "advisory" else {})
    retired_heroes = (_retired_deathwing_hero_entities(state, game)
                      if setaside_policy == "advisory" else set())
    retired_powers = (_retired_linked_hero_powers(state)
                      if setaside_policy == "advisory" else set())
    staged_heroes = (_unplayed_unlinked_setaside_heroes(state, open_choice_entities)
                     if setaside_policy == "advisory" else set())
    reserves = broxigar_reserves(state)
    atlas_copies = godfrey_public_copies(state)
    inert_play_artifacts = _inert_play_artifacts(state, policy=setaside_policy)
    projection = state.public_decision_projection(open_choice_entities)
    active_setaside = set(projection["active_setaside"])
    open_setaside = {str(entity_id) for entity_id in open_choice_entities}
    blocked_setaside = (active_setaside if setaside_policy == "advisory"
                        else {entity.entity_id for entity in state.entities.values()
                              if entity.zone == "SETASIDE"})
    blocked_setaside -= open_setaside
    blocked_setaside -= modeled_rebirth.keys()
    blocked_setaside -= retired_heroes
    blocked_setaside -= retired_powers
    blocked_setaside -= staged_heroes
    blocked_setaside -= reserves.keys()
    blocked_setaside -= atlas_copies.keys()
    for entity in state.entities.values():
        if (entity.controller in (1, 2) and entity.zone == "SETASIDE"
                and str(entity.entity_id) not in inert_setaside
                and str(entity.entity_id) in blocked_setaside):
            return BridgeResult(reason=f"unsupported live zone: {entity.zone}")

    visible_before_hydration = state.visible()
    current_turn = visible_before_hydration.get("turn")
    played_from_hand_this_turn = {
        int(action["source_entity"])
        for action in state.action_history
        if (action.get("kind") == "PLAY"
            and action.get("turn") == current_turn
            and str(action.get("source_entity")).lstrip("-").isdigit())
    }

    # The engine's constructor has already allocated opening-hand/deck entity
    # ids.  Public Power.log ids can be much larger, and a hydrated public id
    # must never collide with an unobserved card created for the remaining
    # deck.  Allocate all new hidden cards strictly above every live id.
    live_ids = [int(entity.entity_id) for entity in state.entities.values()
                if str(entity.entity_id).lstrip("-").isdigit()]
    if live_ids:
        game.next_entity_id = max(game.next_entity_id, max(live_ids) + 1)

    mapper = EntityIdMapper()
    notes: list[str] = []
    if opponent_short_format:
        notes.append("advisory: expanded supported 20-card JAIL_430 deck to 40 cards at game start")
    if inert_setaside:
        notes.append(f"advisory: ignored {len(inert_setaside)} inert SETASIDE entities")
    if modeled_rebirth:
        notes.append("advisory: hydrated Husk corpse rebirth player enchantment")
    if retired_heroes:
        notes.append(f"advisory: ignored {len(retired_heroes)} retired Deathwing hero entities")
    if inert_play_artifacts:
        notes.append(
            f"advisory: ignored {len(inert_play_artifacts)} inert opaque PLAY artifacts")
    for live_controller in (1, 2):
        engine_index = live_controller - 1
        player = game.players[engine_index]
        player.hand.clear()
        player.board.clear()
        player.locations.clear()
        player.secrets.clear()
        player.weapon = None
        player.overdrawn_cards.clear()
        player.broxigar_removed_from_game = any(owner == live_controller for owner, _ in reserves.values())
        player.broxigar_return_used = any(owner == live_controller and used for owner, used in reserves.values())
        raw_hand = [atlas_copies.get(e.entity_id, e)
                    for e in _controller_entities(state, live_controller, "HAND")]
        recovered = [e for e in atlas_copies.values() if e.controller == live_controller]
        if recovered:
            notes.append(f"controller {live_controller}: inferred {len(recovered)} Godfrey copies from public proxies")
        for live in recovered:
            if live.zone != "SETASIDE":
                continue
            card_id = _executable_card_id(game, live.card_id)
            if card_id is None:
                return BridgeResult(reason=f"non-executable Godfrey reserve: {live.card_id}")
            card = game._entity(card_id)
            card.entity_id = int(live.entity_id)
            card.cost_delta = (live.cost - card.definition.cost) if live.cost is not None else -1
            player.overdrawn_cards.append(card)
        # Creation order does not establish recovery order in the public log.
        # Sample one queue hypothesis rather than assert chronological order.
        game.rng.shuffle(player.overdrawn_cards)
        public_hand = [x for x in raw_hand if x.card_id]
        hidden_hand = [x for x in raw_hand if not x.card_id]
        public_board = _controller_entities(state, live_controller, "PLAY")
        public_board = [x for x in public_board
                        if x.card_type not in _NON_BOARD_ENTITY_TYPES
                        and not _is_hero_power(x)
                        and str(x.entity_id) not in inert_play_artifacts]
        if (live_controller == self_controller and hidden_hand) or any(not x.card_id for x in public_board):
            return BridgeResult(reason=f"controller {live_controller} has hidden public card identity")
        observed = _visible_card_counts(state, live_controller)
        deck_source = decks[engine_index]
        remaining = _remaining_deck(deck_source, observed)
        # Revealed/returned cards known to still be in DECK are not eligible
        # for hidden hand sampling. Preserve their identities and live costs.
        pinned_deck = []
        for live in _controller_entities(state, live_controller, "DECK"):
            if not live.card_id:
                continue
            generated = any(live.tags.get(tag) not in (None, 0, "0", "")
                            for tag in ("CREATOR", "COPIED_FROM_ENTITY_ID"))
            if not generated and live.card_id in remaining:
                remaining.remove(live.card_id)
                pinned_deck.append(live)
        # Hand cards may be generated, so construct from metadata even if not
        # in the candidate deck.  Hidden opponents are filled deterministically
        # below only when the log exposes an actual unknown hand entity.
        for zone, destination, entities in (("HAND", player.hand, public_hand), ("PLAY", player.board, public_board)):
            for live in entities:
                executable_id = _executable_card_id(game, live.card_id)
                if executable_id is None:
                    return BridgeResult(reason=f"non-executable visible card: {live.card_id}")
                if executable_id != live.card_id:
                    notes.append(f"normalised runtime alias {live.card_id} -> {executable_id}")
                elif executable_id in static_public_defs:
                    notes.append(f"hydrated static public minion {executable_id}")
                card = game._entity(executable_id)
                card.entity_id = int(live.entity_id)
                card.attack_delta = (int(live.attack) - card.definition.attack) if live.attack is not None else 0
                if live.health is not None:
                    card.health_delta = int(live.health) + int(live.damage or 0) - card.definition.health
                card.damage = int(live.damage or 0)
                card.cost_delta = (int(live.cost) - card.definition.cost) if live.cost is not None else 0
                if zone == "PLAY":
                    # A direct PLAY block exposes the live entity id. Preserve
                    # summoning sickness for that entity; otherwise the old
                    # fallback made every visible board minion look as though
                    # it had survived a prior turn.
                    live_entity_id = (
                        int(live.entity_id)
                        if str(live.entity_id).lstrip("-").isdigit() else None
                    )
                    card.summoned_turn = (
                        int(current_turn) if current_turn is not None
                        and live_entity_id in played_from_hand_this_turn
                        else -99
                    )
                    # A public attack/exhaustion tag is more authoritative
                    # than inferred summon age. Without it, the recommender
                    # can repeat an attack that the live client has consumed.
                    attacks = live.tags.get("NUM_ATTACKS_THIS_TURN")
                    try:
                        card.attacks_this_turn = max(0, int(attacks))
                    except (TypeError, ValueError):
                        card.attacks_this_turn = 1 if _tag_is_true(live, "EXHAUSTED") else 0
                destination.append(card)
                mapper.bind(int(live.entity_id), card.entity_id)
        # Remove cards already visible / played, retaining a deterministic
        # possible deck for future draws.  This does not assert its order.
        player.deck = [game._entity(card_id, started_in_deck=True) for card_id in remaining]
        game.rng.shuffle(player.deck)
        for live in hidden_hand:
            generated_hypothesis = generated_hidden_hand_card(game, live)
            if generated_hypothesis is not None:
                card, explanation = generated_hypothesis
                card.entity_id = int(live.entity_id)
                player.hand.append(card)
                mapper.bind(int(live.entity_id), card.entity_id)
                notes.append(f"controller {live_controller}: {explanation}")
                continue
            if live.zone_history and live.zone_history[0][1] != "DECK":
                return BridgeResult(reason=f"unsupported hidden generated hand entity: {live.entity_id}")
            if not player.deck:
                return BridgeResult(reason=f"candidate deck cannot fill hidden hand for controller {live_controller}")
            card = player.deck.pop()
            card.entity_id = int(live.entity_id)
            player.hand.append(card)
            mapper.bind(int(live.entity_id), card.entity_id)
            notes.append(f"controller {live_controller} hidden hand determinised")
        # Public generated cards still in DECK cannot fill hidden hand slots.
        # They are extra cards, not copies of starting candidate deck entries.
        for live in _controller_entities(state, live_controller, "DECK"):
            if not live.card_id or not any(live.tags.get(tag) not in (None, 0, "0", "")
                                          for tag in ("CREATOR", "COPIED_FROM_ENTITY_ID")):
                continue
            card_id = _executable_card_id(game, live.card_id)
            if card_id is None:
                return BridgeResult(reason=f"non-executable generated deck card: {live.card_id}")
            card = game._entity(card_id)
            card.entity_id = int(live.entity_id)
            card.cost_delta = live.cost - card.definition.cost if live.cost is not None else 0
            player.deck.append(card)
        for live in pinned_deck:
            card_id = _executable_card_id(game, live.card_id)
            if card_id is None:
                return BridgeResult(reason=f"non-executable known deck card: {live.card_id}")
            card = game._entity(card_id, started_in_deck=True)
            card.entity_id = int(live.entity_id)
            card.cost_delta = live.cost - card.definition.cost if live.cost is not None else 0
            player.deck.append(card)
        game.rng.shuffle(player.deck)
        hand_positions = {int(e.entity_id): int(e.tags.get("ZONE_POSITION", pos + 1))
                          for pos, e in enumerate(raw_hand)}
        player.hand.sort(key=lambda card: hand_positions.get(card.entity_id, 9999))
        raw_secrets = _controller_entities(state, live_controller, "SECRET")
        known_secrets = [x for x in raw_secrets if x.card_id]
        hidden_secrets = [x for x in raw_secrets if not x.card_id]
        if live_controller == self_controller and hidden_secrets:
            return BridgeResult(reason="local secret identity is hidden")
        for live_secret in known_secrets:
            executable_id = _executable_card_id(game, live_secret.card_id)
            if executable_id is None:
                return BridgeResult(reason=f"non-executable visible secret: {live_secret.card_id}")
            secret = game._entity(executable_id)
            secret.entity_id = int(live_secret.entity_id)
            player.secrets.append(secret)
            mapper.bind(int(live_secret.entity_id), secret.entity_id)
        for live_secret in hidden_secrets:
            candidates = [card for card in player.deck
                          if "SECRET" in card.definition.mechanics]
            if not candidates:
                return BridgeResult(reason=f"candidate has no secret for controller {live_controller}")
            secret = candidates[0]
            player.deck.remove(secret)
            secret.entity_id = int(live_secret.entity_id)
            player.secrets.append(secret)
            mapper.bind(int(live_secret.entity_id), secret.entity_id)
            notes.append(f"controller {live_controller} secret determinised as {secret.card_id}")
        hero = next((x for x in _controller_entities(state, live_controller, "PLAY")
                     if x.card_type == "HERO"), None)
        meta = state.visible().get("player_meta", {}).get(str(live_controller), {})
        if hero is not None and hero.health is not None:
            player.max_health = int(hero.health)
            player.health = max(0, int(hero.health) - int(hero.damage or 0))
            player.armor = int(hero.tags.get("ARMOR", 0) or 0)
        if meta.get("mana") is not None:
            player.mana = int(meta["mana"])
        if meta.get("max_mana") is not None:
            player.max_mana = int(meta["max_mana"])
        if meta.get("corpses") is not None:
            player.corpses = max(0, int(meta["corpses"]))
        if live_controller in modeled_rebirth.values():
            player.corpse_rebirth_pending = True
        # A transformed/imbued Hero Power is a public entity in Power.log.
        # Preserve it when the engine has executable metadata; ordinary class
        # powers intentionally retain the simulator's class fallback.
        powers = [x for x in _controller_entities(state, live_controller, "PLAY")
                  if _is_hero_power(x) and x.card_id]
        if len(powers) > 1:
            return BridgeResult(reason=f"controller {live_controller} has multiple active hero powers")
        if powers and powers[0].card_id in game.card_defs:
            power_id = powers[0].card_id
            if game.card_defs[power_id].card_type == "HERO_POWER":
                player.hero_power_id = power_id
                mapper.bind(int(powers[0].entity_id), int(powers[0].entity_id))
        elif powers:
            notes.append(f"controller {live_controller} ordinary hero power uses class fallback")
        # Weapon stats and durability are public and do not require a hidden
        # determinisation.  They are safe to hydrate when the log exposes both
        # values. Current Power.log versions commonly encode weapon maximum
        # durability as HEALTH and spent durability as DAMAGE, without a
        # separate DURABILITY tag. Never guess if neither representation is
        # present: durability changes Hero attack legality after combat.
        weapons = [x for x in _controller_entities(state, live_controller, "PLAY")
                   if x.card_type == "WEAPON"]
        if len(weapons) > 1:
            return BridgeResult(reason=f"controller {live_controller} has multiple live weapons")
        if weapons:
            live_weapon = weapons[0]
            durability = _public_remaining_durability(live_weapon)
            if not live_weapon.card_id or durability is None:
                return BridgeResult(reason="live weapon lacks identity or durability")
            definition = game.card_defs.get(live_weapon.card_id)
            if definition is None:
                return BridgeResult(reason=f"non-executable visible weapon: {live_weapon.card_id}")
            attack = int(live_weapon.attack) if live_weapon.attack is not None else definition.attack
            player.weapon = Weapon(live_weapon.card_id, definition.name, attack, int(durability))
            mapper.bind(int(live_weapon.entity_id), int(live_weapon.entity_id))
        if hero is not None:
            # The Hero's ATK tag is the client-authoritative total, including
            # generated weapons whose entity was not exposed as CARDTYPE=WEAPON.
            # Preserve it for legal hero attacks while avoiding double-counting
            # a separately hydrated weapon.
            if hero.attack is not None:
                weapon_attack = player.weapon.attack if player.weapon else 0
                player.hero_attack_bonus = max(
                    0, int(hero.attack) - weapon_attack - player.hero_board_attack_bonus)
            hero_attacks = hero.tags.get("NUM_ATTACKS_THIS_TURN")
            try:
                player.hero_attacks_this_turn = max(0, int(hero_attacks))
            except (TypeError, ValueError):
                player.hero_attacks_this_turn = 1 if _tag_is_true(hero, "EXHAUSTED") else 0
        locations = [x for x in _controller_entities(state, live_controller, "PLAY")
                     if x.card_type == "LOCATION"]
        for live_location in locations:
            durability = _public_remaining_durability(live_location)
            exhausted = live_location.tags.get("EXHAUSTED")
            if not live_location.card_id or durability is None:
                return BridgeResult(reason="live location lacks identity or durability")
            if live_location.card_id not in game.card_defs:
                return BridgeResult(reason=f"non-executable visible location: {live_location.card_id}")
            # The client exposes LOCATION_ACTION_COOLDOWN directly on newer
            # logs. EXHAUSTED can remain 1 while that counter is 0, so the
            # explicit location counter takes precedence for present-action
            # legality. Older logs retain the conservative inference below.
            cooldown = 0
            public_cooldown = live_location.tags.get("LOCATION_ACTION_COOLDOWN")
            try:
                public_cooldown = max(0, int(public_cooldown)) if public_cooldown is not None else None
            except (TypeError, ValueError):
                public_cooldown = None
            if public_cooldown is not None:
                cooldown = public_cooldown
            elif exhausted is None:
                # Older log clients do not emit EXHAUSTED for every Location.
                # Keeping it unavailable for two owner turns is conservative:
                # it cannot fabricate an illegal Location use.
                cooldown = 2
                notes.append(f"location {live_location.card_id} cooldown conservatively inferred")
            elif int(exhausted):
                used_now = any(
                    action.get("kind") == "LOCATION"
                    and str(action.get("source_entity")) == str(live_location.entity_id)
                    and action.get("turn") == state.visible().get("turn")
                    for action in state.action_history
                )
                cooldown = 2 if used_now or state.visible().get("active_player") != live_controller else 1
            player.locations.append(Location(int(live_location.entity_id), live_location.card_id,
                                             int(durability), cooldown))
            mapper.bind(int(live_location.entity_id), int(live_location.entity_id))

    # Restore only the current-turn parts of action legality.  Without this,
    # an advisory search could recommend a second attack or a second Hero
    # Power merely because the public snapshot itself does not contain those
    # engine counters.
    for action in state.action_history:
        if current_turn is None or action.get("turn") != current_turn:
            continue
        source = action.get("source_entity")
        source_entity = state.entities.get(str(source))
        # Normalized Block packets often omit ``controller``. The public
        # source entity is authoritative for PLAY/POWER/ATTACK ownership and
        # is required to restore one-turn action limits.
        controller = action.get("controller")
        if controller not in (1, 2) and source_entity is not None:
            controller = source_entity.controller
        if controller not in (1, 2):
            continue
        player = game.players[int(controller) - 1]
        source_id = int(source) if str(source).lstrip("-").isdigit() else None
        kind = action.get("kind")
        if kind == "ATTACK":
            if source_id is not None:
                card = next((x for x in player.board if x.entity_id == source_id), None)
                if card is not None:
                    # The current public NUM_ATTACKS_THIS_TURN tag already
                    # includes every earlier attack. History is a fallback
                    # only when the client omitted that tag entirely.
                    if (source_entity is None or
                            source_entity.tags.get("NUM_ATTACKS_THIS_TURN") is None):
                        card.attacks_this_turn += 1
                else:
                    hero = next((x for x in _controller_entities(
                        state, int(controller), "PLAY") if x.card_type == "HERO"), None)
                    if hero is None or hero.tags.get("NUM_ATTACKS_THIS_TURN") is None:
                        player.hero_attacks_this_turn += 1
        elif kind == "POWER":
            if source_entity is not None and _is_hero_power(source_entity):
                player.hero_power_used = True
        elif kind == "PLAY":
            if source_entity is not None and _is_hero_power(source_entity):
                player.hero_power_used = True
                continue
            player.cards_played_this_turn += 1
            source_card = action.get("source_card")
            definition = game.card_defs.get(source_card)
            if definition is not None and definition.card_type == "SPELL":
                player.spells_cast_this_turn += 1

    # A refresh can follow an earlier use in the same turn. Current explicit
    # EXHAUSTED beats historical usage; otherwise refreshed powers disappear
    # from the legal-action list for the remainder of the turn.
    for controller in (1, 2):
        player = game.players[controller - 1]
        powers = [e for e in _controller_entities(state, controller, "PLAY") if _is_hero_power(e)]
        if len(powers) != 1:
            continue
        power = powers[0]
        if power.tags.get("EXHAUSTED") in (0, 1, "0", "1"):
            player.hero_power_used = _tag_is_true(power, "EXHAUSTED")
        if power.card_id == "JAIL_EVENT_101hp":
            amount = power.tags.get("TAG_SCRIPT_DATA_NUM_1")
            if str(amount).isdigit() and int(amount) >= 2:
                player.collapsing_star_damage = int(amount)

    game.next_entity_id = max([game.next_entity_id] + list(mapper.sim_to_live)) + 1
    visible = state.visible()
    if visible.get("game_phase") in {"FINAL_GAMEOVER", "FINAL_WRAPUP"}:
        return BridgeResult(reason="game has ended", hypothesis_notes=notes)
    if visible.get("active_player") not in (1, 2):
        return BridgeResult(reason="active player is not known")
    game.current = int(visible["active_player"]) - 1
    if visible.get("turn") is not None:
        game.turn = int(visible["turn"])
    # Schema v5 consumes damage progress for effects whose conditions count
    # distinct friendly characters damaged during the active player's turn.
    # Rebuild it from explicit DAMAGE TagChanges, not the snapshot's cumulative
    # DAMAGE values (which may include earlier turns). Entity registry entries
    # survive deaths, so lethal damage still contributes to the count.
    for event in state.damage_history:
        if (event.get("turn") != current_turn
                or event.get("active_player") != event.get("controller")):
            continue
        controller = event.get("controller")
        if controller not in (1, 2):
            continue
        live = (state.entity_registry.get(str(event.get("entity")))
                or state.entities.get(str(event.get("entity"))))
        if live is None:
            continue
        player = game.players[int(controller) - 1]
        if live.card_type == "HERO" or str(live.card_id or "").startswith("HERO_"):
            player.damaged_characters_this_turn.add(f"hero:{player.index}")
        elif live.card_type == "MINION" or (
                live.card_id in game.card_defs
                and game.card_defs[live.card_id].card_type == "MINION"):
            if str(event.get("entity")).lstrip("-").isdigit():
                player.damaged_characters_this_turn.add(
                    f"minion:{int(event['entity'])}")
    if game.current != self_controller - 1:
        return BridgeResult(reason="waiting for local player's decision")
    if open_choice_entities:
        if open_choice_kind not in {"DISCOVER", "CHOOSE_ONE"}:
            return BridgeResult(reason=f"unsupported open choice: {open_choice_kind}")
        options = []
        for entity_id in open_choice_entities:
            live_option = state.entities.get(str(entity_id))
            card_id = _executable_card_id(
                game, live_option.card_id if live_option is not None else None)
            if card_id is None:
                return BridgeResult(reason="open choice contains hidden or non-executable option")
            option = game._entity(card_id)
            option.entity_id = int(entity_id)
            options.append(option)
            mapper.bind(int(entity_id), option.entity_id)
        # The immediate decision surface is identical for Discover and Choose
        # One: select exactly one shown option.  The live watcher rebuilds the
        # public snapshot after the client resolves it, so we deliberately do
        # not simulate an unknown follow-up effect from a generic Choose One.
        game.pending_choice = {"kind": "DISCOVER", "player": game.current,
                               "options": options, "live_choice_kind": open_choice_kind}
        notes.append(f"open {open_choice_kind} hydrated with {len(options)} options")
    comparison = compare_public_state(
        game, visible, ignored_entity_ids=inert_play_artifacts)
    if not comparison.matches:
        return BridgeResult(reason="hydrated public state does not match Power.log",
                            public_match=comparison.as_dict(), hypothesis_notes=notes)
    game._live_replay_verified = True
    # This game represents one candidate chosen by the live belief caller;
    # preserve that hypothesis when PUCT resamples hidden hands internally.
    # Use the already-publicly-filtered remainder, since synthetic hydration
    # does not have an engine event history of all past plays.
    opponent_index = 1 - game.current
    from collections import Counter
    hidden = game.players[opponent_index]
    game.search_deck_hypotheses[game.current] = [
        (1.0, dict(Counter(c.card_id for c in hidden.hand + hidden.deck)))
    ]
    return BridgeResult(game=game, mapper=mapper, public_match=comparison.as_dict(), hypothesis_notes=notes)
