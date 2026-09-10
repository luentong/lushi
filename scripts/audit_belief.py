#!/usr/bin/env python3
"""Audit public-belief coverage across complete Dragon Warrior mirrors."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame, HeuristicPolicy, PublicBelief


def play(cards: Path, seed: int) -> dict[str, object]:
    game = DragonMirrorGame(cards, seed)
    policy = HeuristicPolicy()
    decisions = 0
    unresolved_decisions = 0
    max_unresolved = 0
    first_unresolved_context: list[dict[str, object]] = []
    source_counts: Counter[str] = Counter()
    modifier_counts: Counter[str] = Counter()
    while not game.finished and decisions < 2000:
        belief = PublicBelief.from_game(game, game.current)
        unresolved = belief.unresolved_hidden_slots
        unresolved_decisions += int(unresolved > 0)
        max_unresolved = max(max_unresolved, unresolved)
        if unresolved and not first_unresolved_context:
            first_unresolved_context = [
                {
                    key: event[key] for key in ("turn", "kind", "source")
                    if key in event
                }
                for event in game.events[-12:]
            ]
        source_counts.update(slot.source_card_id for slot in belief.generated_cards)
        modifier_counts.update(
            modifier.source_card_id for modifier in belief.hand_modifiers
        )
        game.step(policy.choose(game))
        decisions += 1
    return {
        "seed": seed,
        "finished": game.finished,
        "decisions": decisions,
        "unresolved_decisions": unresolved_decisions,
        "max_unresolved": max_unresolved,
        "first_unresolved_context": first_unresolved_context,
        "generated_source_observations": dict(sorted(source_counts.items())),
        "hand_modifier_observations": dict(sorted(modifier_counts.items())),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--games", type=int, default=50)
    parser.add_argument("--seed", type=int, default=202609090000)
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "public-belief-audit.json",
    )
    args = parser.parse_args()
    rows = [play(args.cards, args.seed + offset) for offset in range(args.games)]
    source_counts: Counter[str] = Counter()
    modifier_counts: Counter[str] = Counter()
    for row in rows:
        source_counts.update(row["generated_source_observations"])
        modifier_counts.update(row["hand_modifier_observations"])
    report = {
        "schema_version": 1,
        "belief_model": "public_dragon_mirror_v3",
        "games": len(rows),
        "finished": sum(bool(row["finished"]) for row in rows),
        "decisions": sum(int(row["decisions"]) for row in rows),
        "unresolved_decisions": sum(
            int(row["unresolved_decisions"]) for row in rows
        ),
        "games_with_unresolved_slots": sum(
            int(row["max_unresolved"] > 0) for row in rows
        ),
        "max_unresolved_slots": max(
            (int(row["max_unresolved"]) for row in rows), default=0
        ),
        "generated_source_observations": dict(sorted(source_counts.items())),
        "hand_modifier_observations": dict(sorted(modifier_counts.items())),
        "runs": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in report.items() if k != "runs"}, indent=2))


if __name__ == "__main__":
    main()
