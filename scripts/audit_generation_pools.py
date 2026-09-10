#!/usr/bin/env python3
"""Write the pinned Standard generation-closure audit."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.generation_audit import write_audit


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--json", type=Path, default=ROOT / "reports" / "generation_pool_audit.json")
    parser.add_argument("--csv", type=Path, default=ROOT / "reports" / "generation_pool_cards.csv")
    args = parser.parse_args()
    summary = write_audit(args.cards, args.json, args.csv)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
