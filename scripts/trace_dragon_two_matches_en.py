#!/usr/bin/env python3
"""Generate detailed English traces for two Dragon Warrior matchups."""
from __future__ import annotations
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
          "RULE_CHOICE_PICK":"Pick rule choice", "MULLIGAN_TOGGLE":"Mulligan",
          "MULLIGAN_CONFIRM":"Confirm mulligan"}

def trace(opponent: str, seed: int, filename: str) -> Path:
    config = ROOT / "config" / "decks_20260923_standard40.json"
    (a, ca), (b, cb) = matchup_deck_counts(config, "dragon_warrior", opponent)
    game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", seed,
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
        if definition is not None: return definition.name
        return game.card_defs[card.card_id].name if card.card_id in game.card_defs else card.card_id

    def pending_name(entity_id):
        for option in (game.pending_choice or {}).get("options", []):
            if getattr(option, "entity_id", None) == entity_id:
                return option.definition.name
        return name(entity_id)

    def summary(player):
        hand = ", ".join(name(c.entity_id) for c in player.hand) or "empty"
        board = ", ".join(
            f"{name(c.entity_id)} ({c.attack}/{c.max_health - c.damage}, damage {c.damage}"
            + (f", dormant {c.dormant_turns}" if c.dormant_turns else "") + ")"
            for c in player.board) or "empty"
        weapon = player.weapon.name if player.weapon is not None else "none"
        locations = ", ".join(
            f"{name(x.entity_id)} (durability {x.durability}, cooldown {x.cooldown})"
            for x in player.locations) or "none"
        return (f"P{player.index + 1}: HP {player.health}/{player.max_health}, Armor {player.armor}, "
                f"Mana {player.mana}/{player.max_mana}, Hand {len(player.hand)} [{hand}], "
                f"Deck {len(player.deck)}, Board [{board}], Weapon [{weapon}], Locations [{locations}]")

    opp_name = next((r.get("name_zh", opponent) for r in __import__("json").loads(config.read_text())["decks"] if r["id"] == opponent), opponent)
    lines = [f"# Dragon Warrior vs {opponent}: Full Action Trace", "", f"Opponent label: {opp_name}", f"Fixed seed: {seed}", ""]
    number = 0
    while not game.finished and number < 300:
        action = policies[game.current].choose(game)
        source = pending_name(action.source) if action.kind.endswith("PICK") else name(action.source)
        text = LABELS.get(action.kind, action.kind) + (f" [{source}]" if source else "")
        if action.target_entity is not None: text += f" -> [{name(action.target_entity)}]"
        elif action.target_player is not None and action.kind in {"HERO_ATTACK", "HERO_POWER"}:
            text += f" -> [Player {action.target_player + 1} hero]"
        lines.append(f"{number + 1}. Player {game.current + 1}: {text}")
        game.step(action); number += 1
        if action.kind == "END_TURN":
            lines.append("   Global state after turn:")
            lines.append(f"   - {summary(game.players[0])}")
            lines.append(f"   - {summary(game.players[1])}")
    winner = f"Player {game.winner + 1}" if game.winner is not None else "none"
    lines += ["", f"Result: {number} actions, {game.turn} turns; winner: {winner}; invalid actions: {game.invalid_actions}."]
    output = ROOT / "reports" / filename
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output

if __name__ == "__main__":
    for opponent, seed, filename in (("dirty_priest", 202609240101, "dragon-vs-dirty-priest-trace.en.md"),
                                     ("aggro_druid", 202609240102, "dragon-vs-aggro-druid-trace.en.md")):
        print(trace(opponent, seed, filename))
