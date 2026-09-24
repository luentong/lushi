#!/usr/bin/env python3
"""Convert a deckstring manifest into Windows live-companion deck configs.

The live companion deliberately consumes stable internal card IDs rather than
deckstrings.  This tool converts a dated meta manifest once, preserving every
candidate deck in its original ordering.  The own deck is selected by manifest
``id``; the other entries become opponent belief hypotheses.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps"))

from hearthstone.deckstrings import Deck  # noqa: E402
from hsa.deck_metadata import apply_deck_metadata_overrides  # noqa: E402


def decode_counts(deckstring: str, by_dbf: dict[int, dict]) -> dict[str, int]:
    decoded = Deck.from_deckstring(deckstring)
    counts: dict[str, int] = {}
    for dbf_id, count in decoded.cards:
        card = by_dbf.get(int(dbf_id))
        if card is None:
            raise ValueError(f"deck contains unknown dbfId {dbf_id}")
        card_id = str(card["id"])
        counts[card_id] = counts.get(card_id, 0) + int(count)
    return counts


def get_deck_class(deckstring: str, by_dbf: dict[int, dict]) -> str:
    """Return the playable class encoded by a deckstring's hero DBF id."""
    decoded = Deck.from_deckstring(deckstring)
    if not decoded.heroes:
        return ""
    hero = by_dbf.get(int(decoded.heroes[0]), {})
    return str(hero.get("cardClass", "")).upper()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--self-deck-id", required=True,
                        help="Manifest deck id for the player controlled locally, e.g. 龙战_01")
    parser.add_argument("--self-controller", choices=("1", "2"), default="1")
    parser.add_argument("--known-output", type=Path, required=True)
    parser.add_argument("--candidates-output", type=Path, required=True)
    parser.add_argument("--candidate-class", default=None,
                        help="Optional Hearthstone class filter, e.g. PRIEST. Defaults to all other decks.")
    args = parser.parse_args()

    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    cards = json.loads(args.cards.read_text(encoding="utf-8"))
    by_dbf = {int(card["dbfId"]): card for card in cards if "dbfId" in card}
    apply_deck_metadata_overrides(by_dbf)
    entries = list(manifest.get("decks", ()))
    own_entry = next((entry for entry in entries if entry.get("id") == args.self_deck_id), None)
    if own_entry is None:
        known_ids = ", ".join(str(entry.get("id")) for entry in entries[:12])
        raise SystemExit(f"unknown --self-deck-id {args.self_deck_id!r}; examples: {known_ids}")

    self_controller = args.self_controller
    opponent_controller = str(3 - int(self_controller))
    known = {self_controller: decode_counts(own_entry["deckstring"], by_dbf)}
    candidates: list[dict[str, int]] = []
    candidate_meta: list[dict[str, str]] = []
    for entry in entries:
        if entry.get("id") == own_entry.get("id"):
            continue
        deck_class = get_deck_class(entry["deckstring"], by_dbf)
        if args.candidate_class and deck_class != args.candidate_class.upper():
            continue
        candidates.append(decode_counts(entry["deckstring"], by_dbf))
        candidate_meta.append({"id": str(entry.get("id", "")),
                               "name_zh": str(entry.get("name_zh", "")),
                               "archetype": str(entry.get("archetype", "")),
                               "class": deck_class})
    args.known_output.parent.mkdir(parents=True, exist_ok=True)
    args.candidates_output.parent.mkdir(parents=True, exist_ok=True)
    args.known_output.write_text(json.dumps(known, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.candidates_output.write_text(json.dumps({opponent_controller: candidates}, ensure_ascii=False, indent=2) + "\n",
                                      encoding="utf-8")
    args.candidates_output.with_suffix(".meta.json").write_text(
        json.dumps({"self_deck": {"id": own_entry.get("id"), "name_zh": own_entry.get("name_zh"),
                                   "archetype": own_entry.get("archetype")},
                    "candidate_count": len(candidate_meta), "candidates": candidate_meta},
                   ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"known_output": str(args.known_output),
                      "candidates_output": str(args.candidates_output),
                      "candidate_metadata": str(args.candidates_output.with_suffix(".meta.json")),
                      "self_deck": own_entry.get("id"), "candidate_count": len(candidates)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
