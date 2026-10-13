"""Opening-hand decisions, kept separate from the in-game policy/value net.

Only the player's offered cards, declared own deck and opponent class enter
the feature vector. In particular, shuffled deck order and the opponent's
opening hand are never features.
"""

from __future__ import annotations

import random
from pathlib import Path

from .dragon_mirror import Action, CardDef, DragonMirrorGame


MAX_OPENING_CARDS = 4
CLASSES = (
    "DEATHKNIGHT", "DEMONHUNTER", "DRUID", "HUNTER", "MAGE",
    "PALADIN", "PRIEST", "ROGUE", "SHAMAN", "WARLOCK", "WARRIOR",
)
FEATURE_SCHEMA = "mulligan-semantic-v2"
TEACHER_VERSION = "opening-curve-v3"


def opening_cards(game: DragonMirrorGame, actor: int) -> list:
    pending = game.pending_choice
    if pending is None or pending["kind"] != "MULLIGAN" or pending["player"] != actor:
        raise ValueError("not this player's mulligan phase")
    offered = set(pending["options"])
    return [card for card in game.players[actor].hand if card.entity_id in offered]


def _card_features(definition: CardDef) -> list[float]:
    mechanics = set(definition.mechanics)
    text = definition.text.casefold()
    return [
        min(10, definition.cost) / 10,
        min(15, definition.attack) / 15,
        min(15, definition.health) / 15,
        float(definition.card_type == "MINION"),
        float(definition.card_type == "SPELL"),
        float(definition.card_type == "WEAPON"),
        float("BATTLECRY" in mechanics),
        float("DEATHRATTLE" in mechanics),
        float("RUSH" in mechanics or "CHARGE" in mechanics),
        float("TAUNT" in mechanics),
        float("draw" in text),
        float("discover" in text),
        float("summon" in text),
        float(definition.race == "DRAGON" or "DRAGON" in definition.races),
        float(definition.race == "PIRATE" or "PIRATE" in definition.races),
        float("mana" in text or "refresh" in text),
    ]


CARD_FEATURE_WIDTH = 16
FEATURE_WIDTH = MAX_OPENING_CARDS * CARD_FEATURE_WIDTH + 11 + 2 * len(CLASSES) + 1


def encode_mulligan(game: DragonMirrorGame, actor: int) -> list[float]:
    cards = opening_cards(game, actor)
    if len(cards) > MAX_OPENING_CARDS:
        raise ValueError("opening hand exceeds fixed four-card schema")
    result = []
    for index in range(MAX_OPENING_CARDS):
        result.extend(
            _card_features(cards[index].definition)
            if index < len(cards) else [0.0] * CARD_FEATURE_WIDTH
        )
    # A histogram of the declared own deck is stable across deck order and
    # extends naturally to new cards without changing checkpoint dimensions.
    counts = game.deck_counts[actor]
    curve = [0.0] * 11
    for card_id, count in counts.items():
        curve[min(10, game.card_defs[card_id].cost)] += count
    result.extend(value / max(1, sum(counts.values())) for value in curve)
    for seat in (actor, 1 - actor):
        result.extend(float(game.players[seat].card_class == name) for name in CLASSES)
    result.append(float(actor == 1))
    assert len(result) == FEATURE_WIDTH
    return result


def automatic_mask(game: DragonMirrorGame, actor: int) -> int:
    """The legacy simulator baseline: replace every printed 4+ cost card."""
    return sum(
        1 << index for index, card in enumerate(opening_cards(game, actor))
        if card.definition.cost >= 4
    )


def _curve_score(cards: list[CardDef]) -> float:
    available = list(cards)
    score = 0.0
    for mana in (1, 2, 3, 4, 5):
        # Zero-cost utility cards do not consume the turn's normal play. In
        # particular, treating a mana spell as the only card played on turn 1
        # makes the teacher incorrectly throw away cards such as Innervate.
        effective_mana = mana
        for card in list(available):
            if card.cost != 0:
                continue
            text = card.text.casefold()
            if "mana" in text or "refresh" in text:
                # Hold ramp until it actually unlocks an otherwise unplayable
                # card, rather than spending Innervate on turn one for no gain.
                if any(other.cost == effective_mana + 1 for other in available):
                    available.remove(card)
                    effective_mana += 1
                    score += 0.5
            elif "draw" in text or "discover" in text:
                available.remove(card)
                score += 0.4
            else:
                available.remove(card)
                score += 0.2
        affordable = [card for card in available if card.cost <= effective_mana]
        if not affordable:
            score -= 0.35
            continue
        chosen = max(affordable, key=lambda card: (
            card.cost,
            "draw" in card.text.casefold() or "discover" in card.text.casefold(),
            card.attack + card.health,
        ))
        available.remove(chosen)
        score += 0.9 + 0.5 * chosen.cost / effective_mana
        if mana <= 3 and (
            "draw" in chosen.text.casefold() or "discover" in chosen.text.casefold()
        ):
            score += 0.13
    # Unused ramp is worth a little flexibility but less than a played card.
    score += 0.15 * sum(
        card.cost == 0 and ("mana" in card.text.casefold() or "refresh" in card.text.casefold())
        for card in available
    )
    return score


def teacher_scores(game: DragonMirrorGame, actor: int, samples: int = 16) -> list[float]:
    """Small counterfactual opening-curve teacher, not a win-rate oracle."""
    offered = opening_cards(game, actor)
    if samples < 1:
        raise ValueError("samples must be positive")
    bag = sorted((card.definition for card in game.players[actor].deck),
                 key=lambda definition: definition.card_id)
    rng = random.Random(game.seed * 1009 + actor * 9176 + 29)
    permutations = [rng.sample(bag, len(bag)) for _ in range(samples)]
    values = []
    for mask in range(1 << len(offered)):
        kept = [card.definition for index, card in enumerate(offered)
                if not mask & (1 << index)]
        replaced = mask.bit_count()
        values.append(sum(
            _curve_score(kept + order[:replaced])
            for order in permutations
        ) / samples)
    return values


def teacher_mask(game: DragonMirrorGame, actor: int, samples: int = 16) -> int:
    scores = teacher_scores(game, actor, samples)
    return max(range(len(scores)), key=lambda mask: (
        scores[mask], -mask.bit_count(), -mask,
    ))


def next_mulligan_action(game: DragonMirrorGame, mask: int) -> Action:
    """Turn a whole-hand mask into the engine's explicit toggle/confirm steps."""
    actor = game.current
    cards = opening_cards(game, actor)
    if mask < 0 or mask >= 1 << len(cards):
        raise ValueError("mulligan mask is outside the offered hand")
    selected = game.pending_choice["selected"]
    for index, card in enumerate(cards):
        if (card.entity_id in selected) != bool(mask & (1 << index)):
            return Action("MULLIGAN_TOGGLE", card.entity_id)
    return Action("MULLIGAN_CONFIRM")


def new_mulligan_network():
    from torch import nn

    return nn.Sequential(
        nn.Linear(FEATURE_WIDTH, 256), nn.ReLU(),
        nn.Linear(256, 256), nn.ReLU(), nn.Linear(256, 16),
    )


class MulliganModel:
    """Small standalone head; PyTorch is imported only when a model is used."""

    def __init__(self, checkpoint: str | Path, device: str = "cpu") -> None:
        import torch
        self.torch = torch
        self.device = device
        payload = torch.load(checkpoint, map_location="cpu", weights_only=False)
        if (payload["schema"] != FEATURE_SCHEMA
                or payload.get("teacher_version") != TEACHER_VERSION
                or payload["feature_width"] != FEATURE_WIDTH):
            raise ValueError("incompatible mulligan checkpoint schema")
        if not payload.get("proxy_gate_passed", False):
            raise ValueError("mulligan checkpoint did not beat the automatic baseline")
        self.network = new_mulligan_network().to(device)
        self.network.load_state_dict(payload["model"])
        self.network.eval()

    def raw_mask(self, game: DragonMirrorGame, actor: int) -> int:
        count = len(opening_cards(game, actor))
        features = self.torch.tensor(
            [encode_mulligan(game, actor)], dtype=self.torch.float32,
            device=self.device,
        )
        with self.torch.no_grad():
            logits = self.network(features)[0, :1 << count]
        return int(logits.argmax().item())

    def choose_mask(self, game: DragonMirrorGame, actor: int) -> int:
        """Reject a model choice that loses to the old rule on its own proxy.

        This is an opening-curve safeguard, not a claim that either choice has
        higher actual win rate. The model remains the first-choice policy.
        """
        choice = self.raw_mask(game, actor)
        baseline = automatic_mask(game, actor)
        if choice == baseline:
            return choice
        scores = teacher_scores(game, actor)
        return choice if scores[choice] >= scores[baseline] else baseline
