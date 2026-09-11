#!/usr/bin/env python3
"""Export fail-closed rules coverage for every entity in pinned Standard."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import SUPPORTED_IDS
from hsa.rules import build_rule_registry
from hsa.standard_catalog import CARDS_BUILD, StandardCatalog


TAG_RE = re.compile(r"<[^>]+>|\[[^]]*]")


def normalized_text(text: str) -> str:
    return " ".join(TAG_RE.sub("", text).split())


def implementation_status(card_id: str, declarative: set[str]) -> str:
    if card_id in declarative:
        return "declarative"
    if card_id in SUPPORTED_IDS:
        return "legacy_compatibility"
    return "not_implemented"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cards", type=Path, default=ROOT / "cards.251332.enUS.json"
    )
    parser.add_argument(
        "--json", type=Path,
        default=ROOT / "reports" / "standard_rule_coverage.json",
    )
    parser.add_argument(
        "--csv", type=Path,
        default=ROOT / "reports" / "standard_rule_coverage.csv",
    )
    args = parser.parse_args()

    catalog = StandardCatalog.load(args.cards)
    declarative = {
        row["card_id"] for row in build_rule_registry().manifest()
    }
    rows = []
    for card in catalog.all():
        status = implementation_status(card.card_id, declarative)
        text = normalized_text(card.text)
        rows.append({
            "card_id": card.card_id,
            "dbf_id": card.dbf_id,
            "name": card.name,
            "set": card.card_set,
            "class": ",".join(card.effective_classes),
            "type": card.card_type,
            "collectible": card.collectible,
            "mechanics": ",".join(card.mechanics),
            "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "implementation": status,
            "playable_ready": status != "not_implemented",
            "verification": (
                "focused_or_regression_tests"
                if status != "not_implemented" else "missing"
            ),
        })

    counts = Counter(row["implementation"] for row in rows)
    collectible = [row for row in rows if row["collectible"]]
    collectible_counts = Counter(row["implementation"] for row in collectible)
    payload = {
        "schema_version": 1,
        "cards_build": CARDS_BUILD,
        "completion_policy": (
            "fail_closed: metadata import never implies executable rules"
        ),
        "summary": {
            "standard_entities": len(rows),
            "collectible_cards": len(collectible),
            "generated_or_auxiliary_entities": len(rows) - len(collectible),
            "implementation": dict(sorted(counts.items())),
            "collectible_implementation": dict(
                sorted(collectible_counts.items())
            ),
            "fully_implemented": counts["not_implemented"] == 0,
        },
        "cards": rows,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=tuple(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
