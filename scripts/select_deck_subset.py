#!/usr/bin/env python3
"""Write a reproducible, ordered subset of a reviewed deck manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--ids", required=True,
                        help="Comma-separated manifest deck IDs in desired order.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = json.loads(args.source.read_text(encoding="utf-8"))
    entries = {str(entry["id"]): entry for entry in payload.get("decks", ())}
    ids = [item.strip() for item in args.ids.split(",") if item.strip()]
    if len(ids) < 2:
        raise SystemExit("select at least two deck IDs")
    unknown = [item for item in ids if item not in entries]
    duplicate = len(ids) != len(set(ids))
    if unknown or duplicate:
        raise SystemExit(f"unknown IDs: {unknown}; duplicate IDs: {duplicate}")
    result = {key: value for key, value in payload.items() if key != "decks"}
    result["source_manifest"] = args.source.name
    result["decks"] = [entries[item] for item in ids]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "deck_count": len(ids), "ids": ids}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
