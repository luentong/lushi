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
from pathlib import Path
from typing import Any

from .dragon_mirror import DragonMirrorGame, Location, Weapon
from .live_compare import compare_public_state
from .live_replay import EntityIdMapper


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


def _controller_entities(state: Any, controller: int, zone: str) -> list[Any]:
    return [entity for entity in state.entities.values()
            if entity.controller == controller and entity.zone == zone]


def _classes(value: tuple[str, str] | list[str] | None) -> tuple[str, str]:
    if not value or len(value) != 2:
        return ("WARRIOR", "WARRIOR")
    return (str(value[0]).upper(), str(value[1]).upper())


def _visible_card_counts(state: Any, controller: int) -> Counter[str]:
    """Cards known to have left or be outside the starting deck.

    A card generated during the game may appear in the action history.  It is
    only removed from a candidate deck when that deck actually contains it.
    This is a safe lower-fidelity determinisation, not a claim about deck
    order.
    """
    result: Counter[str] = Counter()
    for entity in state.entities.values():
        if entity.controller == controller and entity.card_id and entity.zone in {"HAND", "PLAY", "SECRET"}:
            if entity.card_type not in {"HERO", "PLAYER", "GAME"}:
                result[entity.card_id] += 1
    for action in state.action_history:
        if action.get("controller") == controller and action.get("source_card"):
            result[str(action["source_card"])] += 1
    return result


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
) -> BridgeResult:
    """Build one hidden-state hypothesis from a public Power.log snapshot.

    ``own_deck`` and ``opponent_deck`` must be full lists.  The current public
    state is authoritative; unknown opponent hand slots are deterministically
    filled from the candidate's remaining cards solely for scoring that
    hypothesis.
    """
    if sum(map(int, own_deck.values())) < 30 or sum(map(int, opponent_deck.values())) < 30:
        return BridgeResult(reason="known and candidate decks must each contain at least 30 cards")
    classes = _classes(player_classes)
    decks = (dict(own_deck), dict(opponent_deck)) if self_controller == 1 else (dict(opponent_deck), dict(own_deck))
    classes = classes if self_controller == 1 else (classes[1], classes[0])
    try:
        game = DragonMirrorGame(str(cards_path), seed=seed, deck_counts=decks,
                                player_classes=classes)
    except Exception as exc:  # unsupported candidate cards must stay closed.
        return BridgeResult(reason=f"cannot initialise candidate: {exc}")

    # These zones carry state that cannot be reconstructed safely yet.
    for entity in state.entities.values():
        if (entity.controller in (1, 2) and entity.zone == "SETASIDE"
                and int(entity.entity_id) not in set(open_choice_entities)):
            return BridgeResult(reason=f"unsupported live zone: {entity.zone}")

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
    for live_controller in (1, 2):
        engine_index = live_controller - 1
        player = game.players[engine_index]
        player.hand.clear()
        player.board.clear()
        player.locations.clear()
        player.secrets.clear()
        player.weapon = None
        raw_hand = _controller_entities(state, live_controller, "HAND")
        public_hand = [x for x in raw_hand if x.card_id]
        hidden_hand = [x for x in raw_hand if not x.card_id]
        public_board = _controller_entities(state, live_controller, "PLAY")
        public_board = [x for x in public_board if x.card_type not in {"HERO", "PLAYER", "GAME"}]
        if (live_controller == self_controller and hidden_hand) or any(not x.card_id for x in public_board):
            return BridgeResult(reason=f"controller {live_controller} has hidden public card identity")
        observed = _visible_card_counts(state, live_controller)
        deck_source = decks[engine_index]
        remaining = _remaining_deck(deck_source, observed)
        # Hand cards may be generated, so construct from metadata even if not
        # in the candidate deck.  Hidden opponents are filled deterministically
        # below only when the log exposes an actual unknown hand entity.
        for zone, destination, entities in (("HAND", player.hand, public_hand), ("PLAY", player.board, public_board)):
            for live in entities:
                if live.card_id not in game.card_defs:
                    return BridgeResult(reason=f"non-executable visible card: {live.card_id}")
                card = game._entity(live.card_id)
                card.entity_id = int(live.entity_id)
                card.attack_delta = (int(live.attack) - card.definition.attack) if live.attack is not None else 0
                if live.health is not None:
                    card.health_delta = int(live.health) + int(live.damage or 0) - card.definition.health
                card.damage = int(live.damage or 0)
                card.cost_delta = (int(live.cost) - card.definition.cost) if live.cost is not None else 0
                if zone == "PLAY":
                    card.summoned_turn = -99  # existing board cards can act if log permits it.
                destination.append(card)
                mapper.bind(int(live.entity_id), card.entity_id)
        # Remove cards already visible / played, retaining a deterministic
        # possible deck for future draws.  This does not assert its order.
        player.deck = [game._entity(card_id, started_in_deck=True) for card_id in remaining]
        for _ in hidden_hand:
            if not player.deck:
                return BridgeResult(reason=f"candidate deck cannot fill hidden hand for controller {live_controller}")
            player.hand.append(player.deck.pop())
            notes.append(f"controller {live_controller} hidden hand determinised")
        raw_secrets = _controller_entities(state, live_controller, "SECRET")
        known_secrets = [x for x in raw_secrets if x.card_id]
        hidden_secrets = [x for x in raw_secrets if not x.card_id]
        if live_controller == self_controller and hidden_secrets:
            return BridgeResult(reason="local secret identity is hidden")
        for live_secret in known_secrets:
            if live_secret.card_id not in game.card_defs:
                return BridgeResult(reason=f"non-executable visible secret: {live_secret.card_id}")
            secret = game._entity(live_secret.card_id)
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
        # A transformed/imbued Hero Power is a public entity in Power.log.
        # Preserve it when the engine has executable metadata; ordinary class
        # powers intentionally retain the simulator's class fallback.
        powers = [x for x in _controller_entities(state, live_controller, "PLAY")
                  if x.card_type == "HERO_POWER" and x.card_id]
        if len(powers) > 1:
            return BridgeResult(reason=f"controller {live_controller} has multiple active hero powers")
        if powers and powers[0].card_id in game.card_defs:
            power_id = powers[0].card_id
            if game.card_defs[power_id].card_type == "HERO_POWER":
                player.hero_power_id = power_id
                mapper.bind(int(powers[0].entity_id), int(powers[0].entity_id))
        # Weapon stats and durability are public and do not require a hidden
        # determinisation.  They are safe to hydrate when the log exposes both
        # values.  A missing durability stays closed because it changes Hero
        # attack legality after combat.
        weapons = [x for x in _controller_entities(state, live_controller, "PLAY")
                   if x.card_type == "WEAPON"]
        if len(weapons) > 1:
            return BridgeResult(reason=f"controller {live_controller} has multiple live weapons")
        if weapons:
            live_weapon = weapons[0]
            durability = live_weapon.tags.get("DURABILITY")
            if not live_weapon.card_id or durability is None:
                return BridgeResult(reason="live weapon lacks identity or durability")
            definition = game.card_defs.get(live_weapon.card_id)
            if definition is None:
                return BridgeResult(reason=f"non-executable visible weapon: {live_weapon.card_id}")
            attack = int(live_weapon.attack) if live_weapon.attack is not None else definition.attack
            player.weapon = Weapon(live_weapon.card_id, definition.name, attack, int(durability))
            mapper.bind(int(live_weapon.entity_id), int(live_weapon.entity_id))
        locations = [x for x in _controller_entities(state, live_controller, "PLAY")
                     if x.card_type == "LOCATION"]
        for live_location in locations:
            durability = live_location.tags.get("DURABILITY")
            exhausted = live_location.tags.get("EXHAUSTED")
            if not live_location.card_id or durability is None:
                return BridgeResult(reason="live location lacks identity or durability")
            if live_location.card_id not in game.card_defs:
                return BridgeResult(reason=f"non-executable visible location: {live_location.card_id}")
            # A location used this turn has cooldown 2.  At the start of the
            # next owner turn it becomes 1 (still unusable); otherwise an
            # exhausted location seen off-turn is conservatively kept at 2.
            cooldown = 0
            if exhausted is None:
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
    current_turn = state.visible().get("turn")
    for action in state.action_history:
        if current_turn is None or action.get("turn") != current_turn:
            continue
        controller = action.get("controller")
        if controller not in (1, 2):
            continue
        player = game.players[int(controller) - 1]
        source = action.get("source_entity")
        source_id = int(source) if str(source).lstrip("-").isdigit() else None
        kind = action.get("kind")
        if kind == "ATTACK":
            if source_id is not None:
                card = next((x for x in player.board if x.entity_id == source_id), None)
                if card is not None:
                    card.attacks_this_turn += 1
                else:
                    player.hero_attacks_this_turn += 1
        elif kind == "POWER":
            entity = state.entities.get(str(source))
            if entity is not None and entity.card_type == "HERO_POWER":
                player.hero_power_used = True
        elif kind == "PLAY":
            player.cards_played_this_turn += 1
            source_card = action.get("source_card")
            definition = game.card_defs.get(source_card)
            if definition is not None and definition.card_type == "SPELL":
                player.spells_cast_this_turn += 1

    game.next_entity_id = max([game.next_entity_id] + list(mapper.sim_to_live)) + 1
    visible = state.visible()
    if visible.get("active_player") not in (1, 2):
        return BridgeResult(reason="active player is not known")
    game.current = int(visible["active_player"]) - 1
    if visible.get("turn") is not None:
        game.turn = int(visible["turn"])
    if game.current != self_controller - 1:
        return BridgeResult(reason="waiting for local player's decision")
    if open_choice_entities:
        if open_choice_kind not in {"DISCOVER", "CHOOSE_ONE"}:
            return BridgeResult(reason=f"unsupported open choice: {open_choice_kind}")
        options = []
        for entity_id in open_choice_entities:
            live_option = state.entities.get(str(entity_id))
            card_id = live_option.card_id if live_option is not None else None
            if not card_id or card_id not in game.card_defs:
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
    comparison = compare_public_state(game, visible)
    if not comparison.matches:
        return BridgeResult(reason="hydrated public state does not match Power.log",
                            public_match=comparison.as_dict(), hypothesis_notes=notes)
    game._live_replay_verified = True
    return BridgeResult(game=game, mapper=mapper, public_match=comparison.as_dict(), hypothesis_notes=notes)
