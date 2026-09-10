#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=202609080001)
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "dragon_mirror.jsonl")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    results = []
    for offset in range(args.games):
        game = DragonMirrorGame(args.cards, args.seed + offset)
        results.append(game.run_random())
    # Write bytes explicitly so Windows and Linux produce identical artifacts.
    payload = "".join(json.dumps(x, sort_keys=True) + "\n" for x in results)
    args.output.write_bytes(payload.encode("utf-8"))
    print(json.dumps(results, indent=2))
    return 0 if all(x["finished"] and x["invalid_actions"] == 0 for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
