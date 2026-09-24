#!/usr/bin/env python3
"""Audit every configured deck before expensive self-play.

Unlike the smoke preflight, this scans every deck at once and reports every
missing executable card.  It is deliberately static and completes in seconds,
so a newly supplied meta manifest does not require repeated long simulations
just to discover one missing ID at a time.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps"))

from hearthstone.deckstrings import Deck  # noqa: E402
from hsa.dragon_mirror import EXECUTABLE_CARD_IDS  # noqa: E402
from hsa.deck_metadata import apply_deck_metadata_overrides  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.zhCN.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    payload = json.loads(args.deck_config.read_text(encoding="utf-8"))
    cards = json.loads(args.cards.read_text(encoding="utf-8"))
    by_dbf = {int(card["dbfId"]): card for card in cards if "dbfId" in card}
    apply_deck_metadata_overrides(by_dbf)

    missing_by_id: dict[str, list[str]] = defaultdict(list)
    unknown_dbf: dict[int, list[str]] = defaultdict(list)
    deck_results = []
    for item in payload["decks"]:
        decoded = Deck.from_deckstring(item["deckstring"])
        missing = []
        for dbf_id, count in decoded.cards:
            card = by_dbf.get(dbf_id)
            if card is None:
                unknown_dbf[dbf_id].append(item["id"])
                missing.append({"dbf_id": dbf_id, "count": count, "id": None, "name": None})
                continue
            card_id = card["id"]
            if card_id not in EXECUTABLE_CARD_IDS:
                missing_by_id[card_id].append(item["id"])
                missing.append({"dbf_id": dbf_id, "count": count, "id": card_id,
                                "name": card.get("name", "")})
        deck_results.append({"id": item["id"], "archetype": item.get("archetype"),
                             "missing": missing, "status": "ready" if not missing else "blocked"})

    report = {
        "schema_version": 1,
        "deck_count": len(deck_results),
        "ready_decks": sum(row["status"] == "ready" for row in deck_results),
        "blocked_decks": sum(row["status"] == "blocked" for row in deck_results),
        "missing_card_count": len(missing_by_id),
        "missing_cards": [
            {"id": card_id, "name": next((c.get("name", "") for c in cards if c.get("id") == card_id), ""),
             "deck_count": len(deck_ids), "decks": sorted(deck_ids)}
            for card_id, deck_ids in sorted(missing_by_id.items())
        ],
        "unknown_dbf": [{"dbf_id": key, "decks": sorted(value)} for key, value in sorted(unknown_dbf.items())],
        "decks": deck_results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("deck_count", "ready_decks", "blocked_decks", "missing_card_count", "missing_cards", "unknown_dbf")}, ensure_ascii=False, indent=2))
    return 0 if not missing_by_id and not unknown_dbf else 2


if __name__ == "__main__":
    raise SystemExit(main())
