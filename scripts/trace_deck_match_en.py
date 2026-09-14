#!/usr/bin/env python3
"""Replay the fixed Dragon Warrior vs Dirty Priest match in English."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from benchmark_mcts import matchup_deck_counts
from hsa.dragon_mirror import DragonMirrorGame
from hsa.policy import HeuristicPolicy

LABELS = {"PLAY":"Play", "ATTACK":"Minion attack", "HERO_ATTACK":"Hero attack",
          "HERO_POWER":"Use hero power", "END_TURN":"End turn", "LOCATION":"Use location",
          "PREPARE":"Prepare", "TRADE":"Trade", "DISCOVER_PICK":"Pick Discover",
          "RULE_CHOICE_PICK":"Pick rule choice", "MULLIGAN_TOGGLE":"Mulligan", "MULLIGAN_CONFIRM":"Confirm mulligan"}

def main() -> int:
    (a, ca), (b, cb) = matchup_deck_counts(ROOT / "config" / "decks.json", "dragon_warrior", "dirty_priest")
    game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 202609140001,
                            deck_counts=(a, b), player_classes=(ca, cb))
    policies = [HeuristicPolicy(), HeuristicPolicy()]

    def find(entity_id):
        if entity_id is None: return None
        for player in game.players:
            for zone in (player.hand, player.board, player.deck, player.locations):
                for card in zone:
                    if card.entity_id == entity_id: return card
        return None

    def name(entity_id):
        card = find(entity_id)
        if card is None: return str(entity_id) if entity_id is not None else ""
        definition = getattr(card, "definition", None)
        return definition.name if definition is not None else card.card_id

    def pending_name(entity_id):
        for option in (game.pending_choice or {}).get("options", []):
            if getattr(option, "entity_id", None) == entity_id:
                return option.definition.name
        return name(entity_id)

    lines = ["# Dragon Warrior vs Dirty Priest: Full Action Trace", "", "Fixed seed: 202609140001", ""]
    number = 0
    while not game.finished and number < 300:
        action = policies[game.current].choose(game)
        source = pending_name(action.source) if action.kind.endswith("PICK") else name(action.source)
        text = LABELS.get(action.kind, action.kind) + (f" [{source}]" if source else "")
        if action.target_entity is not None: text += f" -> [{name(action.target_entity)}]"
        lines.append(f"{number + 1}. Player {game.current + 1}: {text}")
        game.step(action); number += 1
    winner = f"Player {game.winner + 1}" if game.winner is not None else "none"
    lines += ["", f"Result: {number} actions, {game.turn} turns; winner: {winner}; invalid actions: {game.invalid_actions}."]
    output = ROOT / "reports" / "dragon-vs-dirty-priest-one-game.en.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
