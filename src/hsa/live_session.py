"""Initialization gate for a log-backed DragonMirrorGame session."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class SessionGate:
    ready: bool
    reason: str | None = None
    missing_slots: dict[str, int] = field(default_factory=dict)
    unsupported_cards: dict[str, list[str]] = field(default_factory=dict)


def check_initial_decks(
    deck_counts: dict[str, dict[str, int]],
    *,
    required_cards: set[str] | None = None,
) -> SessionGate:
    missing = {}
    for controller in ("1", "2"):
        count = sum(deck_counts.get(controller, {}).values())
        if count < 30:
            missing[controller] = 30 - count
    unsupported: dict[str, list[str]] = {}
    if required_cards is not None:
        for controller, cards in deck_counts.items():
            bad = sorted(set(cards) - required_cards)
            if bad:
                unsupported[controller] = bad
    if missing:
        return SessionGate(False, "initial deck is only partially visible", missing, unsupported)
    if unsupported:
        return SessionGate(False, "deck contains cards without executable rules", missing, unsupported)
    return SessionGate(True)


def build_verified_session(*args: Any, **kwargs: Any):
    """Construct a game only after the caller has passed the initialization gate."""
    from .dragon_mirror import DragonMirrorGame
    deck_counts = kwargs.pop("deck_counts")
    gate = check_initial_decks(deck_counts, required_cards=kwargs.pop("required_cards", None))
    if not gate.ready:
        raise ValueError(gate.reason)
    game = DragonMirrorGame(*args, deck_counts=(deck_counts["1"], deck_counts["2"]), **kwargs)
    game._live_replay_verified = False
    return game
