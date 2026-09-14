#!/usr/bin/env python3
"""Build an auditable, deterministic migration queue for Standard cards.

This tool deliberately does *not* turn card text into executable rules.  It
joins the pinned HearthstoneJSON coverage report with the upstream source
scan, then assigns a review tranche so contributors can work in parallel
without duplicating effort or silently accepting an unsafe implementation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

_TAG_RE = re.compile(r"<[^>]+>|\[[^]]*]")
_SIMPLE_PATTERNS = (
    ("vanilla_or_keyword", re.compile(r"^(?:$|[A-Za-z ]*(?:Taunt|Rush|Windfury|Divine Shield|Lifesteal|Reborn|Poisonous|Stealth|Charge|Magnetic|Tradeable|Elusive|Titan))$", re.I)),
    ("draw_or_discard", re.compile(r"\b(draw|discard|overdraw|fatigue)\b", re.I)),
    ("damage_or_heal", re.compile(r"\b(damage|deal|heal|restore|lifesteal|destroy)\b", re.I)),
    ("summon_or_buff", re.compile(r"\b(summon|buff|give|gain|lose|increase|decrease)\b", re.I)),
    ("targeted_choice", re.compile(r"\b(choose one|discover|choose|random|adapt|secret|rewind|dark gift)\b", re.I)),
    ("persistent_or_triggered", re.compile(r"\b(while|after|whenever|start of|end of|aura|quest|location|battlecry|deathrattle)\b", re.I)),
)


def clean_text(value: str) -> str:
    return " ".join(_TAG_RE.sub("", value or "").split())


def tranche(text: str, mechanics: str, card_type: str) -> str:
    normalized = clean_text(text)
    if _SIMPLE_PATTERNS[0][1].fullmatch(normalized):
        return "A0_vanilla_and_keywords"
    for name, pattern in _SIMPLE_PATTERNS[1:]:
        if pattern.search(normalized):
            return {
                "draw_or_discard": "A1_draw_discard",
                "damage_or_heal": "A2_damage_heal",
                "summon_or_buff": "A3_summon_buff",
                "targeted_choice": "B1_choice_random",
                "persistent_or_triggered": "B2_triggers_aura_quest",
            }[name]
    if card_type in {"MINION", "WEAPON", "LOCATION"} and not normalized:
        return "A0_vanilla_and_keywords"
    return "C_manual_spec"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--coverage", type=Path, default=ROOT / "reports" / "standard_rule_coverage.json")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports" / "card_rule_manifest.json")
    parser.add_argument("--json", type=Path, default=ROOT / "reports" / "standard_migration_queue.json")
    parser.add_argument("--csv", type=Path, default=ROOT / "reports" / "standard_migration_queue.csv")
    args = parser.parse_args()

    coverage = load_json(args.coverage)
    manifest = load_json(args.manifest)
    by_id = {row["card_id"]: row for row in manifest.get("cards", [])}
    rows: list[dict] = []
    for card in coverage.get("cards", []):
        source = by_id.get(card["card_id"], {})
        upstream = source.get("upstream_matches", [])
        status = card["implementation"]
        text = clean_text(card.get("text", ""))
        queue_status = "verified" if status != "not_implemented" else "todo"
        if queue_status == "todo" and upstream:
            queue_status = "upstream_reference_review"
        rows.append({
            "card_id": card["card_id"],
            "dbf_id": card.get("dbf_id"),
            "name": card.get("name", ""),
            "set": card.get("set", ""),
            "class": card.get("class", ""),
            "type": card.get("type", ""),
            "collectible": bool(card.get("collectible", False)),
            "mechanics": card.get("mechanics", ""),
            "text": text,
            "text_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "implementation": status,
            "queue_status": queue_status,
            "tranche": tranche(text, card.get("mechanics", ""), card.get("type", "")),
            "upstream_repositories": sorted({hit.get("repository", "") for hit in upstream}),
            "upstream_match_count": len(upstream),
            "verification": card.get("verification", "missing"),
        })
    rows.sort(key=lambda row: (row["queue_status"] == "verified", row["tranche"], not row["collectible"], row["class"], row["card_id"]))
    payload = {
        "schema_version": 1,
        "cards_build": coverage.get("cards_build"),
        "policy": "reference_matches require human review; only focused tests may promote a card to executable",
        "summary": {
            "cards": len(rows),
            "todo": sum(row["queue_status"] == "todo" for row in rows),
            "upstream_reference_review": sum(row["queue_status"] == "upstream_reference_review" for row in rows),
            "verified": sum(row["queue_status"] == "verified" for row in rows),
            "by_tranche": dict(sorted(Counter(row["tranche"] for row in rows).items())),
        },
        "cards": rows,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    fields = tuple(rows[0]) if rows else ()
    with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
