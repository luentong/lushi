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
CHOICE_HEADER = re.compile(r"\bChoices\s*-\s*id=(\d+).*?ChoiceType=(\w+)", re.IGNORECASE)
CHOICE_SOURCE = re.compile(r"\bChoices\s*-\s*Source=.*?\bid=(\d+).*?\bcardId=([^\s\]]*)", re.IGNORECASE)
CHOICE_ENTITIES = re.compile(r"\bChoices\s*-\s*Entities\[\d+\]=(\[.+\])", re.IGNORECASE)
CHOICE_ENTITY = re.compile(r"\bid=(\d+).*?cardId=([^\s\]]*)", re.IGNORECASE)
CHOICE_RESOLVED = re.compile(r"\b(?:SendChoices|ChosenEntities)\s*-\s*id=(\d+)", re.IGNORECASE)


@dataclass
class LiveSnapshot:
    entities: dict[str, str] = field(default_factory=dict)
    tags: dict[str, dict[str, str]] = field(default_factory=dict)
    lines_seen: int = 0
    last_line: str = ""
    decision_boundary: bool = False
    unsupported: list[str] = field(default_factory=list)
    events: list[dict[str, str]] = field(default_factory=list)
    open_choice: dict[str, object] | None = None

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
            "open_choice": self.open_choice,
        }


class PowerLogStateAdapter:
    """Extract stable public entities/tags and fail closed on unknown events."""

    def __init__(self) -> None:
        self.snapshot = LiveSnapshot()

    def consume(self, line: str) -> LiveSnapshot:
        s = self.snapshot
        s.lines_seen += 1
        s.last_line = line
        # A Discover/Choose prompt is itself a player decision boundary. It
        # need not be followed by BLOCK_END before the user clicks an option.
        s.decision_boundary = any(
            token in line
            for token in ("TURN_START", "ACTION_END", "BLOCK_END")
        ) or "choices" in line.lower()
        header = CHOICE_HEADER.search(line)
        if header:
            choice_id, choice_type = header.groups()
            s.open_choice = {
                "id": int(choice_id),
                "choice_type": choice_type.upper(),
                "source_entity": None,
                "source_card": None,
                "options": [],
            }
        source = CHOICE_SOURCE.search(line)
        if source and s.open_choice is not None:
            source_entity, source_card = source.groups()
            s.open_choice["source_entity"] = int(source_entity)
            s.open_choice["source_card"] = source_card or None
        entities = CHOICE_ENTITIES.search(line)
        if entities and s.open_choice is not None:
            options = []
            for entity, card_id in CHOICE_ENTITY.findall(entities.group(1)):
                options.append({"entity": int(entity), "card_id": card_id or None})
            if options:
                s.open_choice["options"] = options
        resolved = CHOICE_RESOLVED.search(line)
        if resolved and s.open_choice is not None:
            if int(resolved.group(1)) == s.open_choice.get("id"):
                s.open_choice = None
        match = FULL_ENTITY.search(line) or SHOW_ENTITY.search(line)
        if match:
            entity, card_id = match.groups()
            if card_id:
                s.entities[entity] = card_id
        match = TAG_CHANGE.search(line)
        if match:
            entity, tag, value = match.groups()
            if entity.isdecimal() or entity == "GameEntity":
                s.tags.setdefault(entity, {})[tag] = value
            if entity.isdecimal() and tag in {"TURN_START", "TURN_END", "CURRENT_PLAYER"}:
                s.events.append({"kind": tag, "entity": entity, "value": value})
        match = BLOCK.search(line)
        if match:
            entity, effect = match.groups()
            s.events.append({"kind": effect, "entity": entity})
        if "UNKNOWN" in line or "UNSUPPORTED" in line:
            s.unsupported.append("unknown_or_unsupported_log_transition")
        return s
