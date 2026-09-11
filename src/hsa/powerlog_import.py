"""Privacy-safe normalization of python-hslog packet trees.

The raw client log contains BattleTags and account identifiers.  Normalized
records retain numeric entity/player IDs, card IDs, tags, choices and block
ordering, but deliberately never serialize player names or GameAccountId.
"""

from __future__ import annotations

from collections import Counter
from datetime import date, datetime, time
from enum import Enum
from typing import Any, Iterable


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


def card_identity_map(packet_tree: Any) -> dict[int | str, str]:
    identities: dict[int | str, str] = {}
    for _, packet in walk_packets(packet_tree.packets):
        card_id = getattr(packet, "card_id", None)
        entity = public_entity_id(getattr(packet, "entity", None))
        if entity is not None and card_id:
            identities[entity] = card_id
        block_entity = getattr(packet, "entity", None)
        embedded_card = getattr(block_entity, "card_id", None)
        if entity is not None and embedded_card:
            identities[entity] = embedded_card
    return identities


def _normalize_leaf(packet: Any, identities: dict) -> dict[str, Any]:
    kind = type(packet).__name__
    row: dict[str, Any] = {"kind": kind}
    entity = public_entity_id(getattr(packet, "entity", None))
    if entity is not None:
        row["entity"] = entity
        if entity in identities:
            row["card_id"] = identities[entity]
    for attribute in (
        "packet_id", "ts", "card_id", "tag", "value", "zone", "meta",
        "data", "count", "id", "tasklist", "type", "min", "max",
        "source", "option", "suboption", "target", "position",
    ):
        value = getattr(packet, attribute, None)
        if value is not None:
            row[attribute] = json_value(value)
    tags = getattr(packet, "tags", None)
    if tags:
        row["tags"] = _tags(tags)
    for attribute in ("info", "choices"):
        value = getattr(packet, attribute, None)
        if value is not None:
            row[attribute] = [public_entity_id(item) for item in value]
    return row


def normalize_packet_tree(packet_tree: Any) -> dict[str, Any]:
    identities = card_identity_map(packet_tree)
    all_packets = list(walk_packets(packet_tree.packets))
    counts = Counter(type(packet).__name__ for _, packet in all_packets)
    blocks = []
    preamble = []
    for depth, packet in all_packets:
        if type(packet).__name__ != "Block":
            if depth == 0:
                preamble.append(_normalize_leaf(packet, identities))
            continue
        entity = public_entity_id(getattr(packet, "entity", None))
        direct_effects = [
            _normalize_leaf(child, identities)
            for child in getattr(packet, "packets", ())
            if type(child).__name__ != "Block"
        ]
        blocks.append({
            "packet_id": getattr(packet, "packet_id", None),
            "timestamp": json_value(getattr(packet, "ts", None)),
            "depth": depth,
            "block_type": json_value(getattr(packet, "type", None)),
            "source_entity": entity,
            "source_card": identities.get(entity),
            "target_entity": public_entity_id(getattr(packet, "target", None)),
            "target_card": identities.get(
                public_entity_id(getattr(packet, "target", None))
            ),
            "trigger_keyword": json_value(
                getattr(packet, "trigger_keyword", None)
            ),
            "effects": direct_effects,
        })
    return {
        "schema_version": 1,
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

