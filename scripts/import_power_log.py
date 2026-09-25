#!/usr/bin/env python3
"""Import a real Hearthstone Power.log into a sanitized evidence record."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "vendor" / "python-hearthstone"))
sys.path.insert(0, str(ROOT / "vendor" / "python-hslog"))

from hslog import LogParser
from hslog import parser as hslog_parser
from hslog.exceptions import NoSuchEnum
from hslog import tokens as hslog_tokens

# Hearthstone's newer visual sub-spells may contain spaces in
# ``SpellPrefabGUID`` (for example ``TIMEFX_ TachyonBarrage``).  Keep this
# compatibility shim in the tracked importer so a fresh checkout does not
# depend on an uncommitted vendor edit.
hslog_tokens.SUB_SPELL_START_RE = re.compile(
    r"SUB_SPELL_START(?: -)? SpellPrefabGUID=(.*?) Source=(\d+) TargetCount=(\d+)$"
)

from hsa.powerlog_import import normalize_packet_tree


def allow_unknown_tags() -> None:
    """Keep parsing when a newer client emits an unknown noncritical tag."""
    original = hslog_parser.parse_tag

    def parse_tag(tag: str, value: str):
        try:
            return original(tag, value)
        except (NoSuchEnum, NotImplementedError):
            return tag, int(value) if value.isdecimal() else value

    hslog_parser.parse_tag = parse_tag


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("power_log", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    raw = args.power_log.read_bytes()
    allow_unknown_tags()
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
