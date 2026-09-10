"""Baseline policies for the deterministic Hearthstone environment.

The heuristic deliberately uses only information visible to the acting player:
their own hand and both public boards/heroes.  It never reads the opponent's
hand contents or deck order.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dragon_mirror import Action, CardInstance, DragonMirrorGame


def _card_value(card: CardInstance) -> float:
    definition = card.definition
    value = float(definition.cost)
    if definition.card_type == "MINION":
        value += 1.6 * max(0, card.attack) + max(0, card.health)
        value += 1.5 * sum((card.taunt, card.divine_shield, card.rush, card.lifesteal))
        value += 1.0 * sum((card.windfury, card.poisonous, card.reborn))
    elif definition.card_type == "WEAPON":
        value += 1.5 * definition.attack * max(1, definition.health)
    return value


@dataclass(frozen=True)
class RandomPolicy:
    name: str = "random-v1"

    def choose(self, game: DragonMirrorGame) -> Action:
        return game.choose_random_action()


@dataclass(frozen=True)
class HeuristicPolicy:
    """A transparent tempo-oriented baseline, not a learned policy."""

    name: str = "heuristic-tempo-v1"

    def choose(self, game: DragonMirrorGame) -> Action:
        legal = game.legal_actions()
        if not legal:
            raise RuntimeError("policy requested an action in a terminal state")
        if game.pending_choice:
            return self._choose_pending(game, legal)
        # Deterministic key tie-breaks make policy evaluation reproducible and
        # avoid consuming the environment's random-event stream.
        return max(legal, key=lambda action: (self.score(game, action), action.key()))

    def _choose_pending(
        self, game: DragonMirrorGame, legal: list[Action]
    ) -> Action:
        kind = game.pending_choice["kind"]
        if kind == "MULLIGAN":
            player = game.players[game.current]
            desired = {
                card.entity_id for card in player.hand
                if card.entity_id in game.pending_choice["options"]
                and card.definition.cost >= 4
            }
            selected = game.pending_choice["selected"]
            mismatch = sorted(desired ^ selected)
            return (
                Action("MULLIGAN_TOGGLE", mismatch[0])
                if mismatch else Action("MULLIGAN_CONFIRM")
            )
        if kind in {"DISCOVER", "GEDDON_DRAW", "DECK_DISCOVER"}:
            options = {card.entity_id: card for card in game.pending_choice["options"]}
            return max(
                legal,
                key=lambda action: (_card_value(options[action.source]), action.key()),
            )
        if kind == "REWIND":
            return Action("REWIND_KEEP")
        if kind in {"AMMUNITION", "CORPSE_SPEND"}:
            return max(legal, key=lambda action: (action.source or 0, action.key()))
        return legal[0]

    def score(self, game: DragonMirrorGame, action: Action) -> float:
        player = game.players[game.current]
        enemy = game.players[1 - game.current]
        if action.kind == "END_TURN":
            return -1000.0
        if action.kind == "HERO_POWER":
            return 15.0
        if action.kind == "PREPARE":
            return 8.0
        if action.kind == "TRADE":
            card = next(c for c in player.hand if c.entity_id == action.source)
            return 4.0 + max(0, game._effective_cost(player, card) - player.mana)
        if action.kind == "LOCATION":
            return self._location_score(game, action)
        if action.kind in {"ATTACK", "HERO_ATTACK"}:
            return self._attack_score(game, action)
        if action.kind == "PLAY":
            card = next(c for c in player.hand if c.entity_id == action.source)
            score = 100.0 + 4.0 * game._effective_cost(player, card) + _card_value(card)
            return score + self._play_target_score(game, card, action)
        return 0.0

    def _attack_score(self, game: DragonMirrorGame, action: Action) -> float:
        player = game.players[game.current]
        enemy = game.players[1 - game.current]
        if action.kind == "HERO_ATTACK":
            attack = player.attack
            source_health = player.health + player.armor
        else:
            source = next(m for m in player.board if m.entity_id == action.source)
            attack = source.attack
            source_health = source.health
        if action.target_entity is None:
            lethal = attack >= enemy.health + enemy.armor
            return (10000.0 if lethal else 210.0) + 2.0 * attack
        target = game._find_minion(action.target_player, action.target_entity)
        kills_target = attack >= target.health
        loses_source = target.attack >= source_health
        trade = 2.2 * target.attack + 1.4 * target.health
        if kills_target:
            trade += 45.0
        if loses_source:
            trade -= 1.2 * source_health
        if target.taunt:
            trade += 12.0
        return 230.0 + trade

    def _play_target_score(
        self, game: DragonMirrorGame, card: CardInstance, action: Action
    ) -> float:
        if action.target_player is None:
            return 0.0
        friendly = action.target_player == game.current
        if action.target_entity is None:
            return -20.0 if friendly else 20.0
        if card.card_id in {"CATA_200", "CATA_490"}:
            # These Battlecries explicitly target another card in our hand,
            # not a board minion. Prefer sacrificing the least valuable card.
            target = next(
                held for held in game.players[game.current].hand
                if held.entity_id == action.target_entity
            )
            return 30.0 - _card_value(target)
        target = game._find_minion(action.target_player, action.target_entity)
        if card.card_id == "CORE_SW_066":
            bonuses = abs(target.attack_delta) + abs(target.health_delta)
            keywords = sum((target.taunt, target.divine_shield, target.windfury,
                            target.lifesteal, target.poisonous, target.stealth))
            return (-80.0 if friendly else 25.0) + 5.0 * bonuses + 8.0 * keywords
        if card.card_id == "CATA_585":
            return -200.0 if friendly else 80.0 + 4.0 * target.attack
        # Windpeak Wyrm can damage either side; prefer useful enemy targets.
        if card.card_id == "TLC_600":
            return -100.0 if friendly else 35.0 + 3.0 * target.attack
        return -12.0 if friendly else 18.0 + 2.0 * target.attack

    def _location_score(self, game: DragonMirrorGame, action: Action) -> float:
        if action.target_player is None:
            return 90.0
        target = game._find_minion(action.target_player, action.target_entity)
        if action.target_player == game.current:
            # Sanguine Depths is best used on a friendly minion that survives.
            return 125.0 + (25.0 if target.health > 1 else -80.0) + target.attack
        return 120.0 + (35.0 if target.health <= 1 else 0.0) + 2.0 * target.attack
