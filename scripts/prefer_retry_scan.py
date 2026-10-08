"""Remove superseded original trace candidates when a retry exists."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--retry-dir", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    d = json.loads(args.input.read_text(encoding="utf-8"))
    retry_ids = {int(m.group(1)) for x in args.retry_dir.glob("retry-*.json")
                 if (m := re.match(r"retry-(\d+)\.json$", x.name))}
    keep = []
    removed = 0
    for c in d.get("candidates", []):
        source = str(c.get("source", ""))
        m = re.search(r"match-(\d+)\.json$", source)
        if m and int(m.group(1)) in retry_ids:
            removed += 1
            continue
        keep.append(c)
    out = dict(d)
    out["candidates"] = keep
    out["candidate_count"] = len(keep)
    out["superseded_original_candidates_removed"] = removed
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"retry_ids": sorted(retry_ids), "removed": removed,
                      "remaining": len(keep)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
