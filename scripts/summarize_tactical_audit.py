#!/usr/bin/env python3
"""Summarize fixed tactical audit pass counts without scoring N/A cases as misses."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reports", nargs="+", type=Path)
    args = parser.parse_args()
    for path in args.reports:
        payload = json.loads(path.read_text(encoding="utf-8"))
        groups = defaultdict(list)
        for row in payload.get("rows", ()):
            groups[row["case"]].append(row)
        print(path.name)
        for case, rows in sorted(groups.items()):
            print(json.dumps({
                "case": case,
                "passed": sum(row.get("passed") is True for row in rows),
                "failed": sum(row.get("passed") is False for row in rows),
                "not_applicable": sum(row.get("passed") is None for row in rows),
                "n": len(rows),
                "conditional_order": {
                    status: sum(row.get("conditional_order_status") == status for row in rows)
                    for status in ("preferred_order_observed", "reverse_order_observed",
                                   "matched", "needs_review", "not_applicable", "not_audited")
                },
            }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
