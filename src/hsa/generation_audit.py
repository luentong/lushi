"""Audit transitive generation pools for the pinned Dragon Warrior slice."""

from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path
from typing import Any

from .dragon_mirror import (
    ADDITIONAL_GENERATED_MINION_IDS,
    ADDITIONAL_PLAYABLE_CARD_IDS,
    ADDITIONAL_PLAYABLE_SPELL_IDS,
    ADDITIONAL_PLAYABLE_MINION_IDS,
    DISCOVER_BANNED_IDS,
    DIRECT_IDS,
    EXECUTABLE_CARD_IDS,
    GENERATED_MINION_IDS,
    SUPPORTED_ONE_COST_SUMMON_IDS,
    SUPPORTED_DEMON_PLAY_IDS,
    SUPPORTED_STADIUM_WEAPONS,
    SUPPORTED_VOID_SOUL_DEMON_IDS,
)
from .standard_catalog import STANDARD_SETS_BUILD_251332
from .rules import STANDARD_DECLARATIVE_IDS


# Standard on the supplied 2026-09-08 CN snapshot: Core plus the 2025 and
# released 2026 sets. Keeping this explicit makes rotation assumptions auditable.
# The nested pools opened by generated weapons and class Discover effects are
# audited separately from the flat generation rows below.  This prevents a
# card from appearing closed merely because its outer rule exists.
# The three previously tracked nested generators are now closed by explicit
# runtime pool filters.  Keep their candidate definitions here as an audit
# contract so a future catalogue refresh cannot silently reopen them.
NESTED_POOL_CLOSURE = {
    "JAIL_458": {
        "name": "Tiny Pal",
        "pools": ("three_cost_minion", "battlecry_minion"),
    },
    "JAIL_875": {
        "name": "Staff of Trickery",
        "pools": ("druid_collectible",),
    },
    "CATA_614": {
        "name": "Shadowed Informant",
        "pools": ("class_spell_collectible",),
    },
}
NESTED_POOL_BACKLOG: dict[str, dict[str, object]] = {}

# Kept as a compatibility export for consumers that report direct closure
# blockers.  It is intentionally empty now that the first tranche is closed.
PRIORITY_CLOSURE_BACKLOG = {}
WEAPON_CLOSURE_BACKLOG = {}


def _classes(card: dict[str, Any]) -> set[str]:
    result = {card.get("cardClass", "")}
    result.update(card.get("classes", ()))
    return result - {""}


def _races(card: dict[str, Any]) -> set[str]:
    result = {card.get("race", "")}
    result.update(card.get("races", ()))
    return result - {""}


def _eligible_for_warrior(card: dict[str, Any]) -> bool:
    return bool(_classes(card) & {"WARRIOR", "NEUTRAL"})


def nested_pool_candidates(cards: list[dict[str, Any]], pool_name: str) -> set[str]:
    """Return the complete collectible Standard candidate set for a nested pool."""
    def standard_collectible(card: dict[str, Any]) -> bool:
        return bool(
            card.get("collectible")
            and card.get("set") in STANDARD_SETS_BUILD_251332
        )

    if pool_name == "three_cost_minion":
        return {
            card["id"] for card in cards
            if standard_collectible(card)
            and card.get("type") == "MINION" and card.get("cost") == 3
        }
    if pool_name == "battlecry_minion":
        return {
            card["id"] for card in cards
            if standard_collectible(card)
            and card.get("type") == "MINION"
            and "BATTLECRY" in (card.get("mechanics") or ())
        }
    if pool_name == "druid_collectible":
        return {
            card["id"] for card in cards
            if standard_collectible(card)
            and (
                "DRUID" in _classes(card)
                and card.get("type") in {"MINION", "SPELL", "WEAPON"}
            )
        }
    if pool_name == "class_spell_collectible":
        # Shadowed Informant rotates through every class.  The candidate
        # universe is all collectible class spells, not only Druid spells.
        return {
            card["id"] for card in cards
            if standard_collectible(card)
            and card.get("type") == "SPELL"
            and _classes(card) - {"NEUTRAL"}
        }
    raise ValueError(f"unknown nested pool: {pool_name}")


def generation_pool(card: dict[str, Any], pool_name: str) -> bool:
    if not card.get("collectible") or card.get("set") not in STANDARD_SETS_BUILD_251332:
        return False
    if pool_name != "weapon" and card.get("id") in DISCOVER_BANNED_IDS:
        return False
    if pool_name == "dragon":
        return (
            card.get("type") == "MINION"
            and "DRAGON" in _races(card)
            and _eligible_for_warrior(card)
        )
    if pool_name == "warrior_minion":
        return card.get("type") == "MINION" and "WARRIOR" in _classes(card)
    if pool_name == "pirate":
        return (
            card.get("type") == "MINION"
            and "PIRATE" in _races(card)
            and _eligible_for_warrior(card)
        )
    if pool_name == "fire_spell":
        # Fyrakk is Neutral and does not restrict the text to a class. The
        # candidate universe is therefore every collectible Standard Fire
        # spell, irrespective of class; target feasibility is tracked through
        # each spell's own rule rather than guessed from card text.
        return (
            card.get("type") == "SPELL"
            and card.get("spellSchool") == "FIRE"
        )
    if pool_name == "weapon":
        # Unlike default Discover, Stadium Announcer's random equip is not
        # restricted to the Warrior/Neutral class pool.
        return card.get("type") == "WEAPON"
    if pool_name == "one_cost_minion":
        return card.get("type") == "MINION" and card.get("cost") == 1
    if pool_name == "tortotem_multi_type_minion":
        return card.get("type") == "MINION" and len(_races(card)) > 1
    if pool_name == "demon_play":
        return card.get("type") == "MINION" and "DEMON" in _races(card)
    if pool_name == "mech_play":
        return card.get("type") == "MINION" and "MECHANICAL" in _races(card)
    if pool_name == "five_cost_minion_play":
        return card.get("type") == "MINION" and card.get("cost") == 5
    if pool_name == "legendary_minion_play":
        return (
            card.get("type") == "MINION"
            and card.get("rarity") == "LEGENDARY"
            and _eligible_for_warrior(card)
        )
    if pool_name == "rewind_card_play":
        return "<b>Rewind</b>" in (card.get("text") or "")
    if pool_name == "aura_card_play":
        return "AURA" in (card.get("mechanics") or ())
    if pool_name in {"two_cost_minion_play", "four_cost_minion_play"}:
        cost = 2 if pool_name.startswith("two_") else 4
        return card.get("type") == "MINION" and card.get("cost") == cost
    if pool_name.startswith("void_soul_demon_"):
        cost = int(pool_name.rsplit("_", 1)[1])
        return (
            card.get("type") == "MINION"
            and card.get("cost") == cost
            and "DEMON" in _races(card)
        )
    raise ValueError(f"unknown generation pool: {pool_name}")


def support_status(card: dict[str, Any], pool_name: str) -> str:
    if pool_name == "demon_play":
        return (
            "generated_supported"
            if (
                card["id"] in SUPPORTED_DEMON_PLAY_IDS
                or card["id"] in ADDITIONAL_PLAYABLE_MINION_IDS
            )
            else "needs_rule"
        )
    if card["id"] in DIRECT_IDS:
        return "direct_supported"
    if pool_name == "fire_spell" and card["id"] in STANDARD_DECLARATIVE_IDS:
        return "generated_supported"
    if (
        pool_name == "one_cost_minion"
        and card["id"] in SUPPORTED_ONE_COST_SUMMON_IDS
    ):
        return "generated_supported"
    if (
        pool_name.startswith("void_soul_demon_")
        and card["id"] in SUPPORTED_VOID_SOUL_DEMON_IDS
    ):
        return "generated_supported"
    if (
        card["id"] in GENERATED_MINION_IDS
        or card["id"] in ADDITIONAL_GENERATED_MINION_IDS
        or card["id"] in ADDITIONAL_PLAYABLE_CARD_IDS
        or card["id"] in ADDITIONAL_PLAYABLE_SPELL_IDS
        or card["id"] in ADDITIONAL_PLAYABLE_MINION_IDS
        or card["id"] in SUPPORTED_STADIUM_WEAPONS
    ):
        return "generated_supported"
    if not (card.get("text") or "").strip():
        return "metadata_only"
    return "needs_rule"


def build_audit(cards_path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    nested_closure = {
        card_id: {
            "name": entry["name"],
            "pools": {
                pool_name: {
                    "candidate_count": len(candidates := nested_pool_candidates(cards, pool_name)),
                    "missing_executable": sorted(candidates - EXECUTABLE_CARD_IDS),
                }
                for pool_name in entry["pools"]
            },
        }
        for card_id, entry in NESTED_POOL_CLOSURE.items()
    }
    nested_missing = [
        (card_id, pool_name, missing)
        for card_id, entry in nested_closure.items()
        for pool_name, pool in entry["pools"].items()
        for missing in [pool["missing_executable"]]
        if missing
    ]
    if nested_missing:
        raise ValueError(f"nested generation pool is not executable: {nested_missing}")
    details: list[dict[str, Any]] = []
    summaries = {}
    for pool_name in (
        "dragon", "warrior_minion", "pirate", "weapon", "one_cost_minion",
        "fire_spell",
        "tortotem_multi_type_minion",
        "demon_play", "mech_play", "five_cost_minion_play",
        "two_cost_minion_play", "four_cost_minion_play",
        "legendary_minion_play",
        "rewind_card_play", "aura_card_play",
        "void_soul_demon_1", "void_soul_demon_2", "void_soul_demon_3",
        "void_soul_demon_4", "void_soul_demon_5",
        "void_soul_demon_6", "void_soul_demon_7",
        "void_soul_demon_8", "void_soul_demon_9", "void_soul_demon_10",
    ):
        candidates = sorted(
            (card for card in cards if generation_pool(card, pool_name)),
            key=lambda card: card["id"],
        )
        statuses = Counter(support_status(card, pool_name) for card in candidates)
        summaries[pool_name] = {
            "candidate_count": len(candidates),
            "direct_supported": statuses["direct_supported"],
            "generated_supported": statuses["generated_supported"],
            "metadata_only": statuses["metadata_only"],
            "needs_rule": statuses["needs_rule"],
            "unimplemented": (
                len(candidates)
                - statuses["direct_supported"]
                - statuses["generated_supported"]
            ),
        }
        for card in candidates:
            details.append({
                "pool": pool_name,
                "card_id": card["id"],
                "name": card.get("name", ""),
                "card_class": ",".join(sorted(_classes(card))),
                "set": card.get("set", ""),
                "type": card.get("type", ""),
                "cost": card.get("cost", 0),
                "attack": card.get("attack", 0),
                "health_or_durability": card.get("health", card.get("durability", 0)),
                "races": ",".join(sorted(_races(card))),
                "mechanics": ",".join(card.get("mechanics", ())),
                "text": (card.get("text") or "").replace("\n", " "),
                "status": support_status(card, pool_name),
            })
    return {
        "schema_version": 7,
        "cards_build": 251332,
        "standard_sets": sorted(STANDARD_SETS_BUILD_251332),
        "pool_semantics": (
            "Discover uses the fixed deck's eligible Warrior/Neutral pool and "
            "excludes Fabled plus conditionally banned Herald cards; Stadium "
            "random equip uses all collectible Standard weapons; Undefeated "
            "Champion uses all collectible Standard 1-Cost minions; Champion "
            "and Void Soul pools are evaluated in summon context where "
            "Battlecries do not execute; Void Soul tiers 1-10 are closed; "
            "Demon, Mech, 5-Cost, 2-Cost, and 4-Cost play-from-hand pools "
            "plus Warrior/Neutral Legendary minions are closed; nested Tiny "
            "Pal, Staff of Trickery, and Shadowed Informant pools are checked "
            "against the executable Standard catalogue"
        ),
        "summary": summaries,
        "nested_pool_backlog": [
            {"card_id": card_id, **entry}
            for card_id, entry in NESTED_POOL_BACKLOG.items()
        ],
        "nested_pool_closure": nested_closure,
        # Compatibility field for older report readers; direct outer-weapon
        # blockers are closed, so this list is intentionally empty.
        "weapon_closure_backlog": [],
        "priority_closure_backlog": [
            {"card_id": card_id, **entry}
            for card_id, entry in PRIORITY_CLOSURE_BACKLOG.items()
        ],
    }, details


def write_audit(cards_path: Path, json_path: Path, csv_path: Path) -> dict[str, Any]:
    summary, details = build_audit(cards_path)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    # Explicit bytes keep the audit artifact identical on Windows and Linux.
    json_path.write_bytes(
        (json.dumps(summary, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )
    with csv_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(details[0]))
        writer.writeheader()
        writer.writerows(details)
    return summary
