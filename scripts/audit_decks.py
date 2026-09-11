#!/usr/bin/env python3
"""Audit decks against pinned metadata, upstream code, and this runtime."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import EXECUTABLE_CARD_IDS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "decks.json")
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.zhCN.json")
    parser.add_argument(
        "--rosetta",
        type=Path,
        default=ROOT / "vendor" / "RosettaStone",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "reports")
    return parser.parse_args()


def load_deck_class():
    try:
        from hearthstone.deckstrings import Deck
    except ImportError:
        sys.path.insert(0, str(ROOT / ".deps"))
        from hearthstone.deckstrings import Deck
    return Deck


def implemented_card_ids(rosetta: Path) -> set[str]:
    result: set[str] = set()
    for path in (rosetta / "Sources" / "Rosetta" / "PlayMode" / "CardSets").glob("*CardsGen.cpp"):
        text = path.read_text(encoding="utf-8", errors="ignore")
        marker = 'cards.emplace("'
        for line in text.splitlines():
            if marker in line:
                result.add(line.split(marker, 1)[1].split('"', 1)[0])
    return result


def main() -> int:
    args = parse_args()
    Deck = load_deck_class()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    cards = json.loads(args.cards.read_text(encoding="utf-8"))
    cards_by_dbf = {card["dbfId"]: card for card in cards if "dbfId" in card}
    rosetta_ids = implemented_card_ids(args.rosetta)
    rows: list[dict] = []
    summaries: list[dict] = []

    for deck_cfg in config["decks"]:
        deck = Deck.from_deckstring(deck_cfg["deckstring"])
        rosetta_unique = rosetta_copies = 0
        runtime_unique = runtime_copies = 0
        validated_unique = validated_copies = 0
        for dbf_id, count in deck.cards:
            card = cards_by_dbf.get(dbf_id, {})
            card_id = card.get("id", "")
            in_rosetta = card_id in rosetta_ids
            # ``SUPPORTED_IDS`` is a historical, hand-maintained subset for
            # the original Dragon Warrior vertical slice.  It deliberately
            # excludes rules that are declared in ``STANDARD_DECLARATIVE_IDS``
            # even though the engine loads and dispatches them.  Using it here
            # made the coverage report stale and under-counted current support.
            # A deck is runnable when every card is inside the executable
            # closure, not merely when it belongs to the initial deck list.
            in_runtime = card_id in EXECUTABLE_CARD_IDS
            deck_validated = in_runtime
            rosetta_unique += int(in_rosetta)
            rosetta_copies += count if in_rosetta else 0
            runtime_unique += int(in_runtime)
            runtime_copies += count if in_runtime else 0
            validated_unique += int(deck_validated)
            validated_copies += count if deck_validated else 0
            rows.append(
                {
                    "deck_id": deck_cfg["id"],
                    "deck_name_zh": deck_cfg["name_zh"],
                    "dbf_id": dbf_id,
                    "card_id": card_id,
                    "name_zh": card.get("name", "<missing metadata>"),
                    "count": count,
                    "collectible": card.get("collectible", False),
                    "set": card.get("set", ""),
                    "type": card.get("type", ""),
                    "rosetta_implemented": in_rosetta,
                    "project_runtime_supported": in_runtime,
                    "project_deck_validated": deck_validated,
                }
            )
        summaries.append(
            {
                "deck_id": deck_cfg["id"],
                "deck_name_zh": deck_cfg["name_zh"],
                "format": deck.format.name,
                "hero_dbf_ids": deck.heroes,
                "encoded_entries": sum(count for _, count in deck.cards),
                "unique_entities": len(deck.cards),
                "sideboards": len(deck.sideboards),
                "rosetta_implemented_unique": rosetta_unique,
                "rosetta_implemented_copies": rosetta_copies,
                "rosetta_coverage_unique_pct": round(
                    100 * rosetta_unique / len(deck.cards), 2
                ),
                "project_runtime_supported_unique": runtime_unique,
                "project_runtime_supported_copies": runtime_copies,
                "project_runtime_coverage_unique_pct": round(
                    100 * runtime_unique / len(deck.cards), 2
                ),
                "project_deck_validated_unique": validated_unique,
                "project_deck_validated_copies": validated_copies,
                "project_deck_validated_unique_pct": round(
                    100 * validated_unique / len(deck.cards), 2
                ),
                "project_deck_validated_copies_pct": round(
                    100 * validated_copies
                    / sum(count for _, count in deck.cards), 2
                ),
                "deck_ready": validated_unique == len(deck.cards),
            }
        )

    all_dbf_ids = {row["dbf_id"] for row in rows}
    rosetta_dbf_ids = {
        row["dbf_id"] for row in rows if row["rosetta_implemented"]
    }
    runtime_dbf_ids = {
        row["dbf_id"] for row in rows if row["project_runtime_supported"]
    }
    validated_dbf_ids = {
        row["dbf_id"] for row in rows if row["project_deck_validated"]
    }
    overall = {
        "deck_count": len(summaries),
        "unique_entities": len(all_dbf_ids),
        "rosetta_implemented_unique": len(rosetta_dbf_ids),
        "rosetta_coverage_unique_pct": round(
            100 * len(rosetta_dbf_ids) / len(all_dbf_ids), 2
        ),
        "project_runtime_supported_unique": len(runtime_dbf_ids),
        "project_runtime_coverage_unique_pct": round(
            100 * len(runtime_dbf_ids) / len(all_dbf_ids), 2
        ),
        "project_deck_validated_unique": len(validated_dbf_ids),
        "project_deck_validated_unique_pct": round(
            100 * len(validated_dbf_ids) / len(all_dbf_ids), 2
        ),
    }

    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "deck_audit.json").write_text(
        json.dumps(
            {
                "snapshot": config,
                "overall": overall,
                "summaries": summaries,
                "cards": rows,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    for filename, data in (("deck_summary.csv", summaries), ("card_coverage.csv", rows)):
        with (args.output / filename).open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    print(json.dumps({"overall": overall, "decks": summaries}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
