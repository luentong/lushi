#!/usr/bin/env python3
"""Replay one policy-prior PUCT versus ISMCTS game with an action trace."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame, InformationSetMCTSPolicy
from hsa.torch_model import TorchPolicyValueModel


def compact_state(snapshot: dict) -> dict:
    players = []
    for player in snapshot["players"]:
        players.append({
            "player": player["player"],
            "health": player["health"],
            "armor": player["armor"],
            "mana": [player["mana"], player["max_mana"]],
            "deck_count": player["deck_count"],
            "weapon": player["weapon"],
            "hand": [
                {"id": card["id"], "name": card["name"], "cost": card["cost"]}
                for card in player["hand"]
            ],
            "board": [
                {
                    "id": card["id"], "entity": card["entity"],
                    "name": card["name"], "attack": card["attack"],
                    "health": card["health"], "keywords": card["keywords"],
                }
                for card in player["board"]
            ],
            "locations": player["locations"],
        })
    return {
        "turn": snapshot["turn"],
        "active_player": snapshot["active_player"],
        "finished": snapshot["finished"],
        "winner": snapshot["winner"],
        "pending_choice": snapshot["pending_choice"],
        "players": players,
    }


def player_line(player: dict) -> str:
    weapon = player["weapon"]
    weapon_text = (
        "none" if weapon is None
        else f'{weapon["name"]} {weapon["attack"]}/{weapon["durability"]}'
    )
    board = ", ".join(
        f'{card["name"]}#{card["entity"]} {card["attack"]}/{card["health"]}'
        for card in player["board"]
    ) or "empty"
    hand = ", ".join(
        f'{card["name"]}({card["cost"]})' for card in player["hand"]
    ) or "empty"
    return (
        f'P{player["player"]}: HP={player["health"]} Armor={player["armor"]} '
        f'Mana={player["mana"][0]}/{player["mana"][1]} '
        f'Deck={player["deck_count"]}; Weapon={weapon_text}; '
        f'Board={board}; Hand={hand}'
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--candidate-seat", type=int, choices=(0, 1), required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--tree-depth", type=int, default=4)
    parser.add_argument("--rollout-depth", type=int, default=3)
    parser.add_argument("--search-seed", type=int, default=20260909)
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--output-prefix", type=Path)
    args = parser.parse_args()

    prefix = args.output_prefix or (
        ROOT / "reports" / f"search-trace-{args.seed}-seat{args.candidate_seat}"
    )
    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    candidate = InformationSetMCTSPolicy(
        samples=args.samples,
        iterations_per_sample=args.iterations,
        tree_depth=args.tree_depth,
        rollout_depth=args.rollout_depth,
        seed=args.search_seed + args.seed * 2 + args.candidate_seat,
        policy_value_model=model,
        use_model_value=False,
    )
    baseline_seat = 1 - args.candidate_seat
    baseline = InformationSetMCTSPolicy(
        samples=args.samples,
        iterations_per_sample=args.iterations,
        tree_depth=args.tree_depth,
        rollout_depth=args.rollout_depth,
        seed=args.search_seed + args.seed * 2 + baseline_seat,
    )
    policies = [baseline, baseline]
    policies[args.candidate_seat] = candidate

    game = DragonMirrorGame(args.cards, args.seed)
    initial_state = compact_state(game.snapshot())
    steps = []
    while not game.finished and len(steps) < args.max_actions:
        actor = game.current
        policy = policies[actor]
        legal = game.legal_actions()
        legal_descriptions = [game.describe_action(action) for action in legal]
        action = policy.choose(game)
        description = game.describe_action(action)
        search = dict(policy.last_search)
        root_policy = search.pop("root_policy", [])
        root_action_stats = search.pop("root_action_stats", None)
        if root_action_stats is None:
            root_action_stats = [
                {"visit_share": probability}
                for probability in root_policy
            ]
        alternatives = sorted(
            [
                {"action": text, **stats}
                for text, stats in zip(
                    legal_descriptions, root_action_stats, strict=True
                )
            ],
            key=lambda item: (
                item.get("visits", 0), item.get("mean_value", 0.0),
                item.get("selected", False),
            ),
            reverse=True,
        )
        event_offset = len(game.events)
        game.step(action)
        steps.append({
            "step": len(steps) + 1,
            "actor": actor + 1,
            "agent": "policy-prior-puct-v1" if actor == args.candidate_seat else "shared-tree-ismcts-v1",
            "description": description,
            "legal_action_count": len(legal),
            "ranked_alternatives": alternatives,
            "search": search,
            "events": game.events[event_offset:],
            "state_after": compact_state(game.snapshot()),
        })

    document = {
        "schema_version": 1,
        "seed": args.seed,
        "candidate_seat": args.candidate_seat,
        "winner": game.winner,
        "candidate_win": game.winner == args.candidate_seat,
        "invalid_actions": game.invalid_actions,
        "parameters": {
            "samples": args.samples,
            "iterations": args.iterations,
            "tree_depth": args.tree_depth,
            "rollout_depth": args.rollout_depth,
            "search_seed": args.search_seed,
            "checkpoint": args.checkpoint.as_posix(),
            "device": args.device,
        },
        "initial_state": initial_state,
        "steps": steps,
    }
    json_path = prefix.with_suffix(".json")
    markdown_path = prefix.with_suffix(".md")
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(
        json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    lines = [
        "# Policy-prior PUCT vs ISMCTS detailed trace", "",
        f"- Seed: `{args.seed}`", f"- Candidate: `P{args.candidate_seat + 1}`",
        f"- Winner: `P{game.winner + 1 if game.winner is not None else 'draw'}`",
        f"- Candidate win: `{game.winner == args.candidate_seat}`",
        f"- Actions: `{len(steps)}`", f"- Illegal actions: `{game.invalid_actions}`", "",
    ]
    previous_turn = None
    for step in steps:
        state = step["state_after"]
        if state["turn"] != previous_turn:
            lines.extend([f'## Turn {state["turn"]}', ""])
            previous_turn = state["turn"]
        lines.extend([
            f'### Step {step["step"]}: {step["agent"]}', "",
            f'**{step["description"]}**', "",
            f'Legal actions: {step["legal_action_count"]}; '
            f'Searched nodes: {step["search"].get("nodes", 0)}; '
            f'Selected value: {step["search"].get("selected_value", 0):.4f}', "",
        ])
        if step["ranked_alternatives"]:
            lines.append("Top choices by root visit share:")
            lines.append("")
            for option in step["ranked_alternatives"][:5]:
                selected = " [SELECTED]" if option.get("selected") else ""
                lines.append(
                    f'- `{option["visit_share"]:.3f}` — {option["action"]}{selected}; '
                    f'Q={option.get("mean_value", 0):.4f}; '
                    f'prior={option.get("prior", 0):.4f}'
                )
            lines.append("")
        if step["events"]:
            lines.append("Resolved events:")
            lines.append("")
            for event in step["events"]:
                lines.append(
                    f'- `{json.dumps(event, ensure_ascii=False, sort_keys=True)}`'
                )
            lines.append("")
        lines.extend([f'- {player_line(player)}' for player in state["players"]])
        lines.append("")
    markdown_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "seed": args.seed,
        "candidate_seat": args.candidate_seat,
        "winner": game.winner,
        "candidate_win": game.winner == args.candidate_seat,
        "actions": len(steps),
        "invalid_actions": game.invalid_actions,
        "json": str(json_path),
        "markdown": str(markdown_path),
    }, indent=2))
    return 0 if game.finished and game.invalid_actions == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
