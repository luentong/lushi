"""Fail-closed Power.log shadow-mode coverage and divergence analysis.

This module intentionally does *not* drive a Hearthstone client.  A Power.log
can reveal that a live game has diverged from our executable rules, but it
does not expose the local player's full decision state in a form that is safe
to replay for arbitrary Standard matchups.  We therefore emit actionable
engineering tasks and an explicit confidence gate, never invented moves.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Any, Iterable

from .lineage import ruleset_manifest
from .rules import build_rule_registry


DIRECT_BLOCKS = frozenset({"PLAY", "POWER", "TRIGGER", "ATTACK"})
# These entities are client presentation or engine-state records rather than
# independent decisions.  Hero skins use the same underlying class/hero power
# as their base hero; enchantments are represented by the owning entity's
# attack, health, cost, or temporary-effect fields in the simulator.
COSMETIC_HERO_IDS = frozenset({
    "HERO_06e", "HERO_06ebp", "HERO_07d", "HERO_07dbp",
    "HERO_09aj_EliseStarseeker", "HERO_09ajhp", "HERO_09bl", "HERO_09blhp",
    "HERO_10a", "HERO_10cbp", "HERO_11l", "HERO_11lbp",
    # Hero/card skins observed in sanitized live logs.  These IDs do not
    # change the underlying hero power or simulator rules.
    "HERO_10bc", "HERO_10bchp", "HERO_01w", "HERO_01wbp",
    "HERO_01n", "HERO_01dbp", "HERO_03dbp", "HERO_03cd",
})
KNOWN_AUXILIARY_READY = frozenset({
    "ETC_COIN2", "AV_COIN1", "DFT_ALEX_COIN1", "CS2_082",
})
KNOWN_ENGINE_STATE_IDS = frozenset({
    "GBL_002e", "GBL_003e", "GBL_999e", "CS2_017o", "RLK_707e2", "UNG_999t2e",
    "TSC_650a", "TSC_650d", "VAN_CS2_222o",
    "GBL_001e", "BT_035e", "NEW_1308e", "YOP_001e", "ICC_314t1e",
    "SCH_158e2", "EX1_145o", "REV_990e",
    "EX1_145e",
})
# The coverage export intentionally contains pinned-Standard metadata only,
# while a real Power.log can also expose an EVENT printing or a generated
# token.  A rule already present in the executable registry is still ready
# even when that non-collectible entity is absent from the catalog export.
RULE_READY_IDS = frozenset(
    row["card_id"] for row in build_rule_registry().manifest()
)
SEVERITY = {
    "played_card_missing_rule": "red",
    "trigger_source_missing_rule": "red",
    "unknown_card_id": "red",
    "observed_entity_not_executable": "amber",
}


@dataclass(frozen=True)
class Divergence:
    card_id: str
    reason: str
    severity: str
    name: str | None
    card_class: str | None
    card_type: str | None
    collectible: bool | None
    first_packet_id: int | None
    occurrences: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "card_id": self.card_id,
            "reason": self.reason,
            "severity": self.severity,
            "name": self.name,
            "class": self.card_class,
            "type": self.card_type,
            "collectible": self.collectible,
            "first_packet_id": self.first_packet_id,
            "occurrences": self.occurrences,
        }


def _coverage_index(coverage: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {card["card_id"]: card for card in coverage.get("cards", ())}


def _record(
    pending: dict[tuple[str, str], Divergence], *, card_id: str,
    reason: str, card: dict[str, Any] | None, packet_id: int | None,
) -> None:
    key = (card_id, reason)
    old = pending.get(key)
    if old is not None:
        pending[key] = Divergence(**{**old.__dict__, "occurrences": old.occurrences + 1})
        return
    pending[key] = Divergence(
        card_id=card_id,
        reason=reason,
        severity=SEVERITY[reason],
        name=card.get("name") if card else None,
        card_class=card.get("class") if card else None,
        card_type=card.get("type") if card else None,
        collectible=card.get("collectible") if card else None,
        first_packet_id=packet_id,
        occurrences=1,
    )


def _unready_reason(
    card: dict[str, Any] | None, direct_kind: str | None,
    *, card_id: str | None = None,
) -> str | None:
    card_id = card_id or (card.get("card_id") if card else None)
    if card_id in COSMETIC_HERO_IDS or (card and card.get("set") == "HERO_SKINS"):
        return None
    if card_id in KNOWN_AUXILIARY_READY:
        return None
    if card_id in KNOWN_ENGINE_STATE_IDS:
        return None
    if card_id in RULE_READY_IDS:
        return None
    if card is None:
        return "unknown_card_id"
    if card.get("type") == "ENCHANTMENT":
        return None
    if card.get("playable_ready"):
        return None
    if direct_kind == "PLAY":
        return "played_card_missing_rule"
    if direct_kind in {"POWER", "TRIGGER", "ATTACK"}:
        return "trigger_source_missing_rule"
    return "observed_entity_not_executable"


def analyze_game(game: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    """Analyze public card identities in one sanitized game, fail-closed."""
    cards = _coverage_index(coverage)
    pending: dict[tuple[str, str], Divergence] = {}
    observed = Counter(str(card_id) for card_id in game.get("revealed_cards", ()))
    direct = Counter()

    for block in game.get("blocks", ()):
        kind = block.get("block_type")
        if kind not in DIRECT_BLOCKS:
            continue
        card_id = block.get("source_card")
        if not card_id:
            continue
        card_id = str(card_id)
        direct[card_id] += 1
        card = cards.get(card_id)
        reason = _unready_reason(card, kind, card_id=card_id)
        if reason:
            _record(
                pending, card_id=card_id, reason=reason, card=card,
                packet_id=block.get("packet_id"),
            )

    # A revealed entity can be a generated card, enchantment, or a direct deck
    # card.  It is lower priority than an executed effect but still tells us
    # which closure branch blocks faithful replay.
    for card_id, count in observed.items():
        card = cards.get(card_id)
        reason = _unready_reason(card, None, card_id=card_id)
        if reason:
            _record(
                pending, card_id=card_id, reason=reason, card=card,
                packet_id=None,
            )

    divergences = sorted(
        (entry.as_dict() for entry in pending.values()),
        key=lambda entry: (
            0 if entry["severity"] == "red" else 1,
            -entry["occurrences"], entry["card_id"], entry["reason"],
        ),
    )
    red_count = sum(entry["severity"] == "red" for entry in divergences)
    return {
        "game_index": game.get("game_index"),
        "revealed_card_count": len(observed),
        "direct_event_card_count": len(direct),
        "direct_event_cards": dict(sorted(direct.items())),
        "confidence": "red" if red_count else "amber",
        "action_recommendation": {
            "available": False,
            "reason": (
                "Power.log coverage analysis is advisory-only; an arbitrary "
                "Standard state is not yet replayable by this closed Dragon "
                "Warrior simulator."
            ),
        },
        "divergences": divergences,
    }


def analyze_payload(payload: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    games = [analyze_game(game, coverage) for game in payload.get("games", ())]
    all_tasks: dict[tuple[str, str], dict[str, Any]] = {}
    for game in games:
        for task in game["divergences"]:
            key = (task["card_id"], task["reason"])
            merged = all_tasks.get(key)
            if merged is None:
                all_tasks[key] = {**task, "game_indices": [game["game_index"]]}
            else:
                merged["occurrences"] += task["occurrences"]
                merged["game_indices"].append(game["game_index"])
    tasks = sorted(
        all_tasks.values(),
        key=lambda task: (
            0 if task["severity"] == "red" else 1,
            -task["occurrences"], task["card_id"], task["reason"],
        ),
    )
    return {
        "schema_version": 1,
        "mode": "shadow-advisory-only",
        "source_sha256": payload.get("source_sha256"),
        "ruleset_manifest": ruleset_manifest(),
        "coverage_build": coverage.get("cards_build"),
        "game_count": len(games),
        "summary": {
            "red_divergence_count": sum(task["severity"] == "red" for task in tasks),
            "amber_divergence_count": sum(task["severity"] == "amber" for task in tasks),
            "action_recommendations_emitted": 0,
        },
        "games": games,
        "backlog": tasks,
    }


def jsonl_backlog(entries: Iterable[dict[str, Any]]) -> str:
    """Serialize only engineering tasks, so teams can append/import safely."""
    import json
    return "".join(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n" for entry in entries)
