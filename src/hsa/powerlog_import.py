"""Privacy-safe normalization of python-hslog packet trees.

The raw client log contains BattleTags and account identifiers.  Normalized
records retain numeric entity/player IDs, card IDs, tags, choices and block
ordering, but deliberately never serialize player names or GameAccountId.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time
from enum import Enum
import re
from typing import Any, Iterable


_EXPLICIT_BLOCK_CARD = re.compile(
    r"^D (?P<time>\d\d:\d\d:\d\d\.\d{6})\d* "
    r"GameState\.DebugPrintPower\(\) -\s+BLOCK_START "
    r"BlockType=(?P<kind>\w+) Entity=(?P<source>.*?) EffectCardId="
)
_SOURCE_ENTITY_ID = re.compile(r"\bid=(\d+)\b")
_SOURCE_CARD_ID = re.compile(r"\bcardId=([A-Za-z0-9_]+)(?=\s|\])")


def record_explicit_block_card(line: str, hints: dict[tuple[str, str, int], str]) -> None:
    """Keep only a card ID explicitly visible on this raw action line.

    hslog's entity objects may be mutated by a later reveal. Reading their
    final ``card_id`` would leak future knowledge into an earlier packet.
    This narrow raw-line hint is safe for a local player's already-visible
    card; opponent hidden hand cards have an empty ``cardId=`` and do not
    match. Names and account data are never retained.
    """
    match = _EXPLICIT_BLOCK_CARD.search(line)
    if match:
        entity = _SOURCE_ENTITY_ID.search(match["source"])
        card = _SOURCE_CARD_ID.search(match["source"])
        if entity and card:
            hints[(match["time"], match["kind"], int(entity[1]))] = card[1]


def walk_packets(packets: Iterable[Any], depth: int = 0):
    for packet in packets:
        yield depth, packet
        children = getattr(packet, "packets", None)
        if children is not None:
            yield from walk_packets(children, depth + 1)


def public_entity_id(entity: Any) -> int | str | None:
    """Return a stable public reference without leaking a BattleTag."""
    if entity is None:
        return None
    if isinstance(entity, (int, str)):
        return entity
    for attribute in ("entity_id", "id"):
        value = getattr(entity, attribute, None)
        if value is not None:
            return value
    return None


def json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.name
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return public_entity_id(value)


def _tags(tags: Iterable[tuple[Any, Any]]) -> list[dict[str, Any]]:
    return [
        {"tag": json_value(tag), "value": json_value(value)}
        for tag, value in tags
    ]


def _option(option: Any) -> dict[str, Any]:
    """Keep only public, non-name fields of a client legal-action option."""
    return {
        "id": json_value(getattr(option, "id", None)),
        "type": json_value(getattr(option, "type", None)),
        "entity": public_entity_id(getattr(option, "entity", None)),
        "error": json_value(getattr(option, "error", None)),
        "error_param": json_value(getattr(option, "error_param", None)),
        "options": [_option(child) for child in getattr(option, "options", ())],
    }


def _normalize_leaf(packet: Any, identities: dict) -> dict[str, Any]:
    kind = type(packet).__name__
    row: dict[str, Any] = {"kind": kind}
    entity = public_entity_id(getattr(packet, "entity", None))
    if entity is not None:
        row["entity"] = entity
        if entity in identities:
            row["card_id"] = identities[entity]
    for attribute in (
        "packet_id", "ts", "tag", "value", "zone", "meta",
        "data", "count", "id", "tasklist", "type", "min", "max",
        "source", "option", "suboption", "target", "position",
    ):
        value = getattr(packet, attribute, None)
        if value is not None:
            row[attribute] = json_value(value)
    if kind in {"FullEntity", "ShowEntity", "ChangeEntity"}:
        revealed_card = getattr(packet, "card_id", None)
        if revealed_card:
            row["card_id"] = revealed_card
    tags = getattr(packet, "tags", None)
    if tags:
        row["tags"] = _tags(tags)
    for attribute in ("info", "choices"):
        value = getattr(packet, attribute, None)
        if value is not None:
            row[attribute] = [public_entity_id(item) for item in value]
    if kind == "Options":
        row["options"] = [_option(option) for option in getattr(packet, "options", ())]
    return row


def normalize_packet_tree(
    packet_tree: Any,
    explicit_block_cards: dict[tuple[str, str, int], str] | None = None,
) -> dict[str, Any]:
    # Build identities as packets arrive. A full-tree index would backfill a
    # card revealed on turn N into earlier hidden TagChanges, silently giving
    # offline replay and imitation training future information.
    identities: dict[int | str, str] = {}
    all_packets = list(walk_packets(packet_tree.packets))
    counts = Counter(type(packet).__name__ for _, packet in all_packets)
    blocks: list[dict[str, Any]] = []
    preamble: list[dict[str, Any]] = []

    def visit(packets: Iterable[Any], depth: int = 0,
              parent: dict[str, Any] | None = None) -> None:
        for packet in packets:
            entity = public_entity_id(getattr(packet, "entity", None))
            # Only an identity explicitly carried by this packet (or its
            # embedded entity) is a new revelation. Never infer it from a
            # later packet in the same completed game.
            card_id = (getattr(packet, "card_id", None)
                       if type(packet).__name__ in {
                           "FullEntity", "ShowEntity", "ChangeEntity"
                       } else None)
            if entity is not None and card_id:
                identities[entity] = card_id
            if type(packet).__name__ == "Block":
                timestamp = json_value(getattr(packet, "ts", None))
                block_type = json_value(getattr(packet, "type", None))
                explicit_card = (explicit_block_cards or {}).get(
                    (timestamp, block_type, entity))
                if entity is not None and explicit_card:
                    identities[entity] = explicit_card
                block = {
                    "packet_id": getattr(packet, "packet_id", None),
                    "timestamp": timestamp,
                    "depth": depth,
                    "block_type": block_type,
                    "source_entity": entity,
                    "source_card": identities.get(entity),
                    "target_entity": public_entity_id(getattr(packet, "target", None)),
                    "target_card": identities.get(
                        public_entity_id(getattr(packet, "target", None))
                    ),
                    "trigger_keyword": json_value(
                        getattr(packet, "trigger_keyword", None)
                    ),
                    "effects": [],
                }
                blocks.append(block)
                visit(getattr(packet, "packets", ()), depth + 1, block)
            else:
                row = _normalize_leaf(packet, identities)
                (parent["effects"] if parent is not None else preamble).append(row)
                # SubSpell and a few other non-Block hslog containers can
                # themselves contain Block packets. The old flat walk saw
                # those blocks; stopping recursion here silently drops them.
                children = getattr(packet, "packets", None)
                if children is not None:
                    visit(children, depth + 1, parent)

    visit(packet_tree.packets)
    return {
        "schema_version": 1,
        "identity_timing": "causal_reveal_only",
        "privacy": (
            "player names and account identifiers omitted; numeric public "
            "entity/player references retained"
        ),
        "summary": {
            "packet_counts": dict(sorted(counts.items())),
            "block_counts": dict(sorted(Counter(
                block["block_type"] for block in blocks
            ).items())),
            "revealed_card_count": len(set(identities.values())),
        },
        "revealed_cards": sorted(set(identities.values())),
        "preamble": preamble,
        "blocks": blocks,
    }

