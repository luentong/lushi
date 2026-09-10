#!/usr/bin/env python3
"""Generate a machine-readable and human-readable single-game trace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import GENERATION_PROFILE, DragonMirrorGame


def compact_player(player: dict) -> str:
    weapon = player["weapon"]
    weapon_text = "none" if weapon is None else f'{weapon["name"]} {weapon["attack"]}/{weapon["durability"]}'
    board = ", ".join(
        f'{card["name"]}#{card["entity"]} {card["attack"]}/{card["health"]}'
        for card in player["board"]
    ) or "empty"
    locations = ", ".join(
        f'{loc["id"]}#{loc["entity"]} durability={loc["durability"]} cooldown={loc["cooldown"]}'
        for loc in player["locations"]
    ) or "none"
    hand = ", ".join(f'{card["name"]}({card["cost"]})' for card in player["hand"]) or "empty"
    return (
        f'HP={player["health"]} Armor={player["armor"]} '
        f'Mana={player["mana"]}/{player["max_mana"]} Deck={player["deck_count"]}; '
        f'Weapon={weapon_text}; Board={board}; Locations={locations}; Hand={hand}'
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=202609080001)
    parser.add_argument("--max-actions", type=int, default=5000)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--json", type=Path, default=ROOT / "reports" / "dragon_mirror_trace.json")
    parser.add_argument("--markdown", type=Path, default=ROOT / "reports" / "dragon_mirror_trace.md")
    args = parser.parse_args()

    # Manual mode makes both players' mulligan decisions visible as ordinary
    # trace steps before turn one.
    game = DragonMirrorGame(args.cards, args.seed, manual_mulligan=True)
    steps = []
    while not game.finished and len(steps) < args.max_actions:
        legal = game.legal_actions()
        action = game.choose_random_action()
        description = game.describe_action(action)
        before = game.snapshot()
        event_offset = len(game.events)
        game.step(action)
        steps.append({
            "step": len(steps) + 1,
            "description": description,
            "chosen_action": {
                "kind": action.kind,
                "source": action.source,
                "target_player": action.target_player,
                "target_entity": action.target_entity,
            },
            "legal_action_count": len(legal),
            "new_events": game.events[event_offset:],
            "before": before,
            "after": game.snapshot(),
        })

    document = {
        "schema_version": 1,
        "seed": args.seed,
        "generation_profile": GENERATION_PROFILE,
        "finished": game.finished,
        "winner": None if game.winner is None else game.winner + 1,
        "invalid_actions": game.invalid_actions,
        "steps": steps,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_bytes((json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    lines = [
        "# Dragon Warrior mirror trace",
        "",
        f"- Seed: `{args.seed}`",
        f"- Profile: `{GENERATION_PROFILE}`",
        f"- Winner: `P{game.winner + 1 if game.winner is not None else 'draw'}`",
        f"- Actions: `{len(steps)}`",
        f"- Illegal actions: `{game.invalid_actions}`",
        "",
    ]
    for step in steps:
        after = step["after"]
        lines.extend([
            f'## Step {step["step"]} — turn {after["turn"]}',
            "",
            f'`{step["description"]}`',
            "",
            f'Legal choices before action: {step["legal_action_count"]}',
            "",
        ])
        if step["new_events"]:
            lines.append("Events:")
            lines.append("")
            for event in step["new_events"]:
                lines.append(f"- `{json.dumps(event, ensure_ascii=False, sort_keys=True)}`")
            lines.append("")
        for player in after["players"]:
            lines.append(f'- P{player["player"]}: {compact_player(player)}')
        if after["pending_choice"]:
            lines.append(
                f'- Pending decision: `{json.dumps(after["pending_choice"], ensure_ascii=False, sort_keys=True)}`'
            )
        lines.append("")
    args.markdown.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    print(json.dumps({
        "seed": args.seed,
        "winner": document["winner"],
        "actions": len(steps),
        "invalid_actions": game.invalid_actions,
        "json": str(args.json),
        "markdown": str(args.markdown),
    }, ensure_ascii=False, indent=2))
    return 0 if game.finished and game.invalid_actions == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
