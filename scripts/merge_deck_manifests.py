#!/usr/bin/env python3
"""Build a dated, de-duplicated Standard deck manifest from reviewed inputs.

The merge is intentionally deckstring-based: the same list with a different
local label is one training distribution, while a one-card variant remains a
separate candidate.  This keeps both the live belief library and teacher-data
manifest auditable.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", type=Path, required=True)
    parser.add_argument("--append", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot-date", required=True)
    args = parser.parse_args()

    base = json.loads(args.base.read_text(encoding="utf-8"))
    supplemental = json.loads(args.append.read_text(encoding="utf-8"))
    if not isinstance(base.get("decks"), list) or not isinstance(supplemental.get("decks"), list):
        raise SystemExit("both manifests must contain a decks list")

    merged: list[dict] = []
    seen_strings: set[str] = set()
    seen_ids: set[str] = set()
    for source_name, payload in ((args.base.name, base), (args.append.name, supplemental)):
        for raw in payload["decks"]:
            entry = dict(raw)
            deckstring = str(entry.get("deckstring", ""))
            deck_id = str(entry.get("id", ""))
            if not deckstring or not deck_id:
                raise SystemExit(f"invalid deck entry in {source_name}: {entry!r}")
            if deckstring in seen_strings:
                continue
            if deck_id in seen_ids:
                suffix = 2
                candidate = f"{deck_id}_supplement_{suffix}"
                while candidate in seen_ids:
                    suffix += 1
                    candidate = f"{deck_id}_supplement_{suffix}"
                entry["id"] = candidate
            seen_strings.add(deckstring)
            seen_ids.add(str(entry["id"]))
            merged.append(entry)

    output = {
        "snapshot_date": args.snapshot_date,
        "region": base.get("region", "CN"),
        "format": "STANDARD",
        "client_version": base.get("client_version", args.snapshot_date),
        "frequency_prior": base.get("frequency_prior", {"method": "archetype_balanced"}),
        "sources": [args.base.name, args.append.name],
        "decks": merged,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "deck_count": len(merged),
                      "deduplicated": len(base["decks"]) + len(supplemental["decks"]) - len(merged)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
