#!/usr/bin/env python3
"""Flatten grouped archetype variants into tournament/training deck config."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    decks = []
    for group in data["archetypes"]:
        name = group["name"]
        safe = "".join(ch.lower() if ch.isalnum() else "_" for ch in name).strip("_")
        for index, code in enumerate(group["variants"], 1):
            decks.append({"id": f"{safe}_{index:02d}", "name_zh": name,
                          "archetype": name, "variant_index": index,
                          "frequency_weight": 1.0, "deckstring": code})
    result = {"snapshot_date": data.get("snapshot_date"), "region": "CN",
              "format": "STANDARD", "client_version": "2026-09-24",
              "frequency_prior": {"method": "archetype_balanced"}, "decks": decks}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"decks": len(decks), "archetypes": len(data["archetypes"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
