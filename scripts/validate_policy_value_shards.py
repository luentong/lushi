"""Validate compressed policy/value JSONL shards without loading them all at once."""

from __future__ import annotations

import argparse
import gzip
import json
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()

    files = sorted(args.directory.glob("*.jsonl.gz"))
    records = 0
    games: Counter[str] = Counter()
    empty: list[str] = []
    errors: list[dict[str, str]] = []
    fields: set[str] = set()

    for path in files:
        rows = 0
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line in handle:
                    if not line.strip():
                        continue
                    record = json.loads(line)
                    rows += 1
                    records += 1
                    fields.update(record)
                    games[str(record.get("game_id", record.get("game", "unknown")))] += 1
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append({"path": str(path), "error": repr(exc)})
        if rows == 0:
            empty.append(str(path))

    print(
        json.dumps(
            {
                "files": len(files),
                "records": records,
                "distinct_game_ids": len(games),
                "min_records_per_game": min(games.values(), default=0),
                "max_records_per_game": max(games.values(), default=0),
                "empty_files": empty,
                "errors": errors,
                "fields": sorted(fields),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if empty or errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
