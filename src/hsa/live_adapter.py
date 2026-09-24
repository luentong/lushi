"""Conservative Power.log line adapter for live shadow mode.

This is intentionally a *coverage/state observation* layer, not a complete
Hearthstone replay engine.  Unknown entities and unsupported transitions keep
the gate closed instead of producing a guessed move.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

FULL_ENTITY = re.compile(r"FULL_ENTITY\s+-\s+Creating ID=(\d+) CardID=([^ ]*)")
SHOW_ENTITY = re.compile(r"SHOW_ENTITY\s+-\s+Updating Entity=([^ ]+) CardID=([^ ]*)")
TAG_CHANGE = re.compile(r"TAG_CHANGE\s+Entity=([^ ]+)\s+tag=([^ ]+)\s+value=([^ ]+)")
BLOCK = re.compile(r"BLOCK_START\s+Entity=(\d+)\s+Effect=(\w+)")


@dataclass
class LiveSnapshot:
    entities: dict[str, str] = field(default_factory=dict)
    tags: dict[str, dict[str, str]] = field(default_factory=dict)
    lines_seen: int = 0
    last_line: str = ""
    decision_boundary: bool = False
    unsupported: list[str] = field(default_factory=list)
    events: list[dict[str, str]] = field(default_factory=list)

    @property
    def confidence(self) -> str:
        return "red" if self.unsupported else "amber"

    def as_dict(self) -> dict[str, object]:
        return {
            "confidence": self.confidence,
            "lines_seen": self.lines_seen,
            "entities": dict(self.entities),
            "tags": self.tags,
            "decision_boundary": self.decision_boundary,
            "unsupported": list(dict.fromkeys(self.unsupported)),
            "events": list(self.events[-200:]),
        }


class PowerLogStateAdapter:
    """Extract stable public entities/tags and fail closed on unknown events."""

    def __init__(self) -> None:
        self.snapshot = LiveSnapshot()

    def consume(self, line: str) -> LiveSnapshot:
        s = self.snapshot
        s.lines_seen += 1
        s.last_line = line
        s.decision_boundary = any(token in line for token in ("TURN_START", "ACTION_END", "BLOCK_END"))
        match = FULL_ENTITY.search(line) or SHOW_ENTITY.search(line)
        if match:
            entity, card_id = match.groups()
            if card_id:
                s.entities[entity] = card_id
        match = TAG_CHANGE.search(line)
        if match:
            entity, tag, value = match.groups()
            s.tags.setdefault(entity, {})[tag] = value
            if tag in {"TURN_START", "TURN_END", "CURRENT_PLAYER"}:
                s.events.append({"kind": tag, "entity": entity, "value": value})
        match = BLOCK.search(line)
        if match:
            entity, effect = match.groups()
            s.events.append({"kind": effect, "entity": entity})
        if "UNKNOWN" in line or "UNSUPPORTED" in line:
            s.unsupported.append(line[-240:])
        return s
