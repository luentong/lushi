#!/usr/bin/env python3
"""Cross-reference a sanitized Power.log with metadata and rule coverage."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import SUPPORTED_IDS
from hsa.rules import build_rule_registry
from hsa.standard_catalog import STANDARD_SETS_BUILD_251332


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument(
        "--cards", type=Path, default=ROOT / "cards.251332.enUS.json"
    )
    parser.add_argument("--json", type=Path, required=True)
    parser.add_argument("--markdown", type=Path, required=True)
    args = parser.parse_args()

    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    metadata = {
        row["id"]: row
        for row in json.loads(args.cards.read_text(encoding="utf-8"))
    }
    declarative = {
        row["card_id"] for row in build_rule_registry().manifest()
    }
    source_blocks = Counter()
    played = Counter()
    triggered = Counter()
    for game in trace["games"]:
        for block in game["blocks"]:
            card_id = block.get("source_card")
            if not card_id:
                continue
            source_blocks[card_id] += 1
            if block["block_type"] == "PLAY":
                played[card_id] += 1
            if block["block_type"] == "TRIGGER":
                triggered[card_id] += 1

    revealed = sorted({
        card_id
        for game in trace["games"]
        for card_id in game["revealed_cards"]
    })
    rows = []
    for card_id in revealed:
        card = metadata.get(card_id, {})
        standard = card.get("set") in STANDARD_SETS_BUILD_251332
        implementation = (
            "declarative" if card_id in declarative
            else "legacy_compatibility" if card_id in SUPPORTED_IDS
            else "not_implemented"
        )
        rows.append({
            "card_id": card_id,
            "name": card.get("name", ""),
            "set": card.get("set", ""),
            "class": card.get("cardClass", ""),
            "type": card.get("type", ""),
            "collectible": bool(card.get("collectible", False)),
            "standard_entity": standard,
            "implementation": implementation,
            "source_blocks": source_blocks[card_id],
            "play_blocks": played[card_id],
            "trigger_blocks": triggered[card_id],
            "text": card.get("text", "") or "",
        })

    observed_standard = [row for row in rows if row["standard_entity"]]
    played_standard = [
        row for row in observed_standard if row["play_blocks"] > 0
    ]
    priority = [
        row for row in played_standard
        if row["implementation"] == "not_implemented"
    ]
    payload = {
        "schema_version": 1,
        "source_sha256": trace["source_sha256"],
        "summary": {
            "games": trace["game_count"],
            "revealed_entities": len(rows),
            "standard_entities": len(observed_standard),
            "standard_played_cards": len(played_standard),
            "unimplemented_standard_played_cards": len(priority),
        },
        "priority_from_real_play": priority,
        "cards": rows,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )

    lines = [
        "# Power.log rules evidence — 2026-09-11",
        "",
        f"Source SHA-256: `{trace['source_sha256']}`.",
        "The raw log is kept out of Git because it contains player/account identifiers.",
        "The importer strips those identifiers before analysis.",
        "",
        "## Coverage",
        "",
        f"- Parsed games: {trace['game_count']}",
        f"- Revealed card/enchantment entities: {len(rows)}",
        f"- Entities belonging to the pinned Standard sets: {len(observed_standard)}",
        f"- Standard cards observed in PLAY blocks: {len(played_standard)}",
        f"- Played Standard cards still lacking executable rules: {len(priority)}",
        "",
        "## Real-play implementation priority",
        "",
        "| Card ID | Name | Class | Type | Plays | Triggers |",
        "|---|---|---|---|---:|---:|",
    ]
    lines.extend(
        f"| `{row['card_id']}` | {row['name']} | {row['class']} | "
        f"{row['type']} | {row['play_blocks']} | {row['trigger_blocks']} |"
        for row in priority
    )
    lines.extend([
        "",
        "This report proves observed packet ordering and state/tag changes only. "
        "It does not by itself prove hidden candidate pools or server-side random logic.",
        "",
    ])
    args.markdown.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
