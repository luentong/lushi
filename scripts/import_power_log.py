#!/usr/bin/env python3
"""Import a real Hearthstone Power.log into a sanitized evidence record."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor" / "python-hearthstone"))
sys.path.insert(0, str(ROOT / "vendor" / "python-hslog"))

from hslog import LogParser

from hsa.powerlog_import import normalize_packet_tree


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("power_log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.power_log.read_bytes()
    log_parser = LogParser()
    with args.power_log.open(encoding="utf-8") as handle:
        log_parser.read(handle)
    log_parser.flush()
    if not log_parser.games:
        raise RuntimeError("no CREATE_GAME packet found")

    games = []
    for index, packet_tree in enumerate(log_parser.games):
        game = normalize_packet_tree(packet_tree)
        game["game_index"] = index
        games.append(game)
    payload = {
        "schema_version": 1,
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "game_count": len(games),
        "games": games,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(
        (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    print(json.dumps({
        "source_sha256": payload["source_sha256"],
        "game_count": len(games),
        "summaries": [game["summary"] for game in games],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

