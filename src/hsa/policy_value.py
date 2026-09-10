"""Framework-neutral policy/value contract and transparent baseline adapter."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol, Sequence

from .dragon_mirror import Action, DragonMirrorGame
from .policy import HeuristicPolicy, _card_value


@dataclass(frozen=True)
class PolicyValueOutput:
    priors: tuple[float, ...]
    value: float


class PolicyValueModel(Protocol):
    name: str

    def predict(
        self, game: DragonMirrorGame, actions: Sequence[Action]
    ) -> PolicyValueOutput: ...


def public_value(game: DragonMirrorGame, observer: int) -> float:
    """Bounded public-state value; never inspects opposing hidden identities."""
    if game.finished:
        if game.winner is None:
            return 0.0
        return 1.0 if game.winner == observer else -1.0
    own, enemy = game.players[observer], game.players[1 - observer]
    board = sum(_card_value(card) for card in own.board) - sum(
        _card_value(card) for card in enemy.board
    )
    weapons = (
        (own.weapon.attack * own.weapon.durability if own.weapon else 0)
        - (enemy.weapon.attack * enemy.weapon.durability if enemy.weapon else 0)
    )
    raw = (
        2.0 * ((own.health + own.armor) - (enemy.health + enemy.armor))
        + 1.2 * board + 0.8 * weapons
        + 0.7 * (len(own.hand) - len(enemy.hand))
    )
    return math.tanh(raw / 35.0)


@dataclass(frozen=True)
class HeuristicPolicyValueModel:
    """Reference implementation used before a learned 910C model is trained."""

    name: str = "heuristic-policy-value-v1"
    temperature: float = 20.0

    def predict(
        self, game: DragonMirrorGame, actions: Sequence[Action]
    ) -> PolicyValueOutput:
        if not actions:
            return PolicyValueOutput((), public_value(game, game.current))
        policy = HeuristicPolicy()
        scores = [policy.score(game, action) for action in actions]
        maximum = max(scores)
        weights = [math.exp((score - maximum) / self.temperature) for score in scores]
        total = sum(weights)
        return PolicyValueOutput(
            tuple(weight / total for weight in weights),
            public_value(game, game.current),
        )
