#!/usr/bin/env python3
"""Parse ### archetype/deckstring text into a grouped training manifest."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse(path: Path) -> dict:
    groups: dict[str, list[str]] = {}
    current = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if line.startswith("###"):
            current = line[3:].strip()
            groups.setdefault(current, [])
        elif current and line and not line.startswith("#"):
            if line not in groups[current]:
                groups[current].append(line)
    variants = sum(len(x) for x in groups.values())
    return {
        "snapshot_date": "2026-09-24",
        "format": "STANDARD",
        "source": str(path),
        "archetypes": [{"name": name, "variants": codes}
                       for name, codes in groups.items()],
        "summary": {"archetypes": len(groups), "variants": variants},
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = parse(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
