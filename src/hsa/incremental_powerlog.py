"""Incremental, local-only Power.log normalization for the live companion.

``hslog.LogParser`` keeps a packet tree while it receives lines. Keeping one
parser per rotating Power.log lets the recommender normalize the current game
without repeatedly re-reading the complete raw log or launching a subprocess.
Only the existing privacy-safe normalized structure leaves this module.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Iterable

try:  # Windows live companion dependency; NPU training does not need it.
    from hslog import LogParser
    from hslog import parser as hslog_parser
    from hslog.exceptions import NoSuchEnum
    from hslog import tokens as hslog_tokens
except ModuleNotFoundError:  # pragma: no cover - exercised on minimal NPU images
    LogParser = None
    hslog_parser = None
    hslog_tokens = None
    NoSuchEnum = ValueError

from .powerlog_import import normalize_packet_tree


def _allow_unknown_tags() -> None:
    """Keep a newer noncritical client tag from stopping live observation."""
    if hslog_parser is None:
        return
    original = hslog_parser.parse_tag
    if getattr(original, "_lushi_allows_unknown", False):
        return

    def parse_tag(tag: str, value: str):
        try:
            return original(tag, value)
        except (NoSuchEnum, NotImplementedError):
            return tag, int(value) if value.isdecimal() else value

    parse_tag._lushi_allows_unknown = True  # type: ignore[attr-defined]
    hslog_parser.parse_tag = parse_tag


def _enable_current_client_subspell_compatibility() -> None:
    if hslog_tokens is None:
        return
    hslog_tokens.SUB_SPELL_START_RE = re.compile(
        r"SUB_SPELL_START(?: -)? SpellPrefabGUID=(.*?) Source=(\d+) TargetCount=(\d+)$"
    )


class IncrementalPowerLogImporter:
    """Keep parser state for one append-only Power.log file."""

    def __init__(self) -> None:
        if LogParser is None:
            raise RuntimeError(
                "Power.log parsing requires hslog. Install requirements-live.txt "
                "on the Windows advisory machine."
            )
        _allow_unknown_tags()
        _enable_current_client_subspell_compatibility()
        self._parser = LogParser()

    def reset(self) -> None:
        """Discard state when the watcher switches to a new log file."""
        if LogParser is None:
            raise RuntimeError("Power.log parsing requires hslog")
        self._parser = LogParser()

    def consume(self, lines: Iterable[str]) -> None:
        for line in lines:
            # The tailer strips the newline; hslog accepts complete text lines.
            self._parser.read_line(line + "\n")

    def payload(self) -> dict[str, Any]:
        """Return the same sanitized shape as ``scripts/import_power_log.py``."""
        games = []
        for index, packet_tree in enumerate(self._parser.games):
            game = normalize_packet_tree(packet_tree)
            game["game_index"] = index
            games.append(game)
        digest = hashlib.sha256(
            json.dumps(games, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()
        return {
            "schema_version": 1,
            "source_sha256": digest,
            "game_count": len(games),
            "games": games,
        }
