"""Conservative opponent hidden-card belief state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class OpponentBelief:
    controller: str
    known_deck: dict[str, int] = field(default_factory=dict)
    unknown_slots: int = 0
    seen_played: dict[str, int] = field(default_factory=dict)
    candidate_decks: list[dict[str, int]] = field(default_factory=list)

    def observe_played(self, card_id: str) -> None:
        self.seen_played[card_id] = self.seen_played.get(card_id, 0) + 1
        self.candidate_decks = [
            deck for deck in self.candidate_decks
            if self.seen_played[card_id] <= int(deck.get(card_id, 0))
        ]

    def compatible(self) -> bool:
        return self.unknown_slots >= 0 and all(
            self.seen_played.get(card, 0) <= count
            for card, count in self.known_deck.items()
        )

    def summary(self) -> dict[str, object]:
        return {"controller": self.controller, "known_deck": dict(self.known_deck),
                "unknown_slots": self.unknown_slots, "seen_played": dict(self.seen_played),
                "candidate_count": len(self.candidate_decks), "compatible": self.compatible()}


def build_beliefs(deck_counts: dict[str, dict[str, int]], unknown_slots: dict[str, int], *,
                  candidate_decks: dict[str, Iterable[dict[str, int]]] | None = None):
    candidate_decks = candidate_decks or {}
    return {controller: OpponentBelief(
        controller, dict(cards), int(unknown_slots.get(controller, 0)),
        candidate_decks=[dict(x) for x in candidate_decks.get(controller, ())],
    ) for controller, cards in deck_counts.items()}


def filter_candidates(belief: OpponentBelief) -> list[dict[str, int]]:
    """Return candidates compatible with every observed played card."""
    return [deck for deck in belief.candidate_decks if all(
        int(deck.get(card, 0)) >= count
        for card, count in belief.seen_played.items()
    )]
