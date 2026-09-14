#!/usr/bin/env python3
"""Scan pinned upstream trees for references to every Standard entity."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from audit_card_rules import scan_upstreams  # noqa: E402
from hsa.standard_catalog import CARDS_BUILD, StandardCatalog  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--json", type=Path, default=ROOT / "reports" / "standard_upstream_scan.json")
    args = parser.parse_args()
    catalog = StandardCatalog.load(args.cards)
    card_ids = {card.card_id for card in catalog.all()}
    matches = scan_upstreams(card_ids)
    rows = []
    for card in catalog.all():
        hits = matches.get(card.card_id, [])
        rows.append({
            "card_id": card.card_id,
            "name": card.name,
            "collectible": card.collectible,
            "matches": hits,
            "repositories": sorted({hit["repository"] for hit in hits}),
            "match_count": len(hits),
        })
    payload = {
        "schema_version": 1,
        "cards_build": CARDS_BUILD,
        "policy": "upstream references are evidence for review, never executable rules by themselves",
        "summary": {
            "standard_entities": len(rows),
            "entities_with_match": sum(bool(row["matches"]) for row in rows),
            "collectible_with_match": sum(row["collectible"] and bool(row["matches"]) for row in rows),
            "rosettastone_matches": sum("RosettaStone" in row["repositories"] for row in rows),
            "fireplace_matches": sum("fireplace" in row["repositories"] for row in rows),
        },
        "cards": rows,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
