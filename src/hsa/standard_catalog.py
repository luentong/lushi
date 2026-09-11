"""Pinned Standard-format card catalogue and coverage primitives.

HearthstoneJSON is authoritative for card identity and printed metadata, but it
does not contain executable effects.  This module deliberately keeps metadata
coverage separate from rules coverage so an imported card can never be
silently treated as a vanilla body.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


CARDS_BUILD = 251332
STANDARD_SETS_BUILD_251332 = frozenset({
    "CORE",
    "EMERALD_DREAM",
    "THE_LOST_CITY",
    "TIME_TRAVEL",
    "CATACLYSM",
    "ESCAPEFROM_VIOLET_HOLD",
})


@dataclass(frozen=True)
class StandardCard:
    card_id: str
    dbf_id: int
    name: str
    card_type: str
    card_set: str
    card_class: str
    classes: tuple[str, ...]
    collectible: bool
    cost: int
    attack: int
    health: int
    durability: int
    rarity: str
    race: str
    races: tuple[str, ...]
    mechanics: tuple[str, ...]
    text: str
    collection_text: str
    spell_school: str

    @property
    def effective_classes(self) -> tuple[str, ...]:
        return tuple(
            card_class for card_class in dict.fromkeys(
                (self.card_class, *self.classes)
            )
            if card_class
        )

    @property
    def has_rules_text(self) -> bool:
        return bool(self.text.strip())


class StandardCatalog:
    """All collectible cards and related entities in one pinned Standard build."""

    def __init__(self, cards: Iterable[StandardCard]):
        cards = tuple(cards)
        self._cards = {card.card_id: card for card in cards}
        if len(self._cards) != len(cards):
            raise ValueError("duplicate card id in Standard catalogue")

    @classmethod
    def load(cls, path: str | Path) -> "StandardCatalog":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        cards = []
        for row in raw:
            if row.get("set") not in STANDARD_SETS_BUILD_251332:
                continue
            cards.append(StandardCard(
                card_id=row["id"],
                dbf_id=int(row.get("dbfId", 0)),
                name=row.get("name", "") or "",
                card_type=row.get("type", "") or "",
                card_set=row.get("set", "") or "",
                card_class=row.get("cardClass", "") or "",
                classes=tuple(row.get("classes", ())),
                collectible=bool(row.get("collectible", False)),
                cost=int(row.get("cost", 0)),
                attack=int(row.get("attack", 0)),
                health=int(row.get("health", 0)),
                durability=int(row.get("durability", 0)),
                rarity=row.get("rarity", "") or "",
                race=row.get("race", "") or "",
                races=tuple(row.get("races", ())),
                mechanics=tuple(row.get("mechanics", ())),
                text=row.get("text", "") or "",
                collection_text=row.get("collectionText", "") or "",
                spell_school=row.get("spellSchool", "") or "",
            ))
        return cls(cards)

    def __len__(self) -> int:
        return len(self._cards)

    def __contains__(self, card_id: str) -> bool:
        return card_id in self._cards

    def __getitem__(self, card_id: str) -> StandardCard:
        return self._cards[card_id]

    def all(self) -> tuple[StandardCard, ...]:
        return tuple(self._cards[card_id] for card_id in sorted(self._cards))

    def collectible(self) -> tuple[StandardCard, ...]:
        return tuple(card for card in self.all() if card.collectible)

    def generated_entities(self) -> tuple[StandardCard, ...]:
        return tuple(card for card in self.all() if not card.collectible)

    def eligible_for_class(self, card_id: str, card_class: str) -> bool:
        card = self[card_id]
        return bool(set(card.effective_classes) & {card_class, "NEUTRAL"})
