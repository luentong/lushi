"""Compatibility metadata for deckstrings newer than our pinned card snapshot.

The simulator keeps HearthstoneJSON immutable for reproducibility.  A current
client can, however, encode a reprinted card with a DBF ID not yet present in
that snapshot.  Keep each such translation narrow, documented, and shared by
the deck audit, teacher generator, and benchmark runner.
"""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import Any


DECK_DBF_METADATA_OVERRIDES: dict[int, dict[str, Any]] = {
    # The supplied September 2026 deckstrings already contain M.O.T.H.E.R.,
    # whereas the pinned build 251332 predates its metadata.
    128132: {
        "dbfId": 128132, "id": "BE_036", "name": "M.O.T.H.E.R.",
        "cardClass": "NEUTRAL", "collectible": True, "set": "BE",
        "type": "MINION", "cost": 9, "attack": 9, "health": 7,
    },
    # The Companion Hunter deckstring has two DBF 130677 entries.  They are
    # the then-current Core printing of Call of the Wild: 8 mana, summon
    # Misha/Leokk/Huffer.  The simulator already implements the canonical
    # CORE_OG_211 rule, so retain that canonical identity rather than making a
    # duplicate card rule merely for a client printing ID.
    130677: {
        "dbfId": 130677, "id": "CORE_OG_211", "name": "Call of the Wild",
        "cardClass": "HUNTER", "collectible": True, "set": "CORE",
        "type": "SPELL", "cost": 8,
        "text": "Summon all three Animal Companions.",
    },
}


def apply_deck_metadata_overrides(cards_by_dbf: MutableMapping[int, dict[str, Any]]) -> None:
    """Add only missing current-client printing metadata to a card lookup."""
    for dbf_id, metadata in DECK_DBF_METADATA_OVERRIDES.items():
        cards_by_dbf.setdefault(dbf_id, dict(metadata))
