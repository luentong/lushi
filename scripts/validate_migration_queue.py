#!/usr/bin/env python3
"""Validate the generated Standard migration queue before a PR is opened."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "card_id", "name", "implementation", "queue_status", "tranche",
    "text_sha256", "verification",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=Path, nargs="?", default=ROOT / "reports" / "standard_migration_queue.json")
    args = parser.parse_args()
    payload = json.loads(args.queue.read_text(encoding="utf-8"))
    rows = payload.get("cards", [])
    errors: list[str] = []
    ids = [row.get("card_id") for row in rows]
    for card_id, count in Counter(ids).items():
        if not card_id or count != 1:
            errors.append(f"duplicate_or_empty_card_id:{card_id}:{count}")
    for index, row in enumerate(rows, 1):
        missing = REQUIRED - row.keys()
        if missing:
            errors.append(f"row_{index}_missing:{','.join(sorted(missing))}")
        if row.get("queue_status") == "verified" and row.get("implementation") == "not_implemented":
            errors.append(f"unverified_card_marked_verified:{row.get('card_id')}")
        if row.get("queue_status") == "verified" and row.get("verification") in {"missing", ""}:
            errors.append(f"verified_card_missing_test:{row.get('card_id')}")
    summary = payload.get("summary", {})
    if summary.get("cards") != len(rows):
        errors.append("summary_cards_mismatch")
    if errors:
        print("migration queue invalid")
        print("\n".join(errors))
        return 1
    print(json.dumps({
        "valid": True,
        "cards": len(rows),
        "todo": summary.get("todo"),
        "verified": summary.get("verified"),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
