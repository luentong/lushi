#!/usr/bin/env python3
"""Paired-action outcome audit at a learner decision in a saved PPO game.

This provides review evidence only. A heuristic continuation is not an
optimal-play oracle and its outcome ranks must not automatically become labels.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import time

from audit_paired_root_outcomes import (EntityGreedyPolicy, HeuristicPolicy,
                                        paired_comparisons, paired_outcomes)
from replay_entity_rollout import replay_game_prefix, verify_report_inputs


def public_root_state(game):
    """Compact actor-visible review context; never expose the opponent's hand."""
    observer = game.current
    players = []
    for player in game.players:
        players.append({
            "player": player.index, "health": player.health,
            "max_health": player.max_health, "armor": player.armor,
            "mana": player.mana, "max_mana": player.max_mana,
            "hand_count": len(player.hand),
            "hand": [
                {"entity": card.entity_id, "card": card.card_id,
                 "name": card.definition.name,
                 "cost": game._effective_cost(player, card)}
                for card in player.hand
            ] if player.index == observer else None,
            "board": [
                {"entity": card.entity_id, "card": card.card_id,
                 "name": card.definition.name, "attack": card.attack,
                 "health": card.health}
                for card in player.board
            ],
            "weapon": player.weapon.card_id if player.weapon else None,
            "locations": [(location.card_id, location.durability, location.cooldown)
                          for location in player.locations],
        })
    return {"turn": game.turn, "actor": observer, "players": players}


def audit(record, cards, deck_config, *, step, replicates, max_actions, seed,
          max_root_actions, continuation, only_alternatives=()):
    trace = record.get("action_trace")
    if trace is None or not 0 <= step < len(trace):
        raise ValueError("recorded learner step unavailable")
    root = replay_game_prefix(record, cards, deck_config, until=step)
    if root.current != record["learner_seat"]:
        raise ValueError("selected root is an opponent decision, not a learner decision")
    actions = root.legal_actions()
    if len(actions) > max_root_actions:
        raise ValueError("root has too many actions; sample another root")
    selected_key = trace[step]["action"]
    if sum(list(action.key()) == selected_key for action in actions) != 1:
        raise ValueError("recorded learner action is not uniquely legal at the root")
    if only_alternatives:
        requested = set(only_alternatives)
        found = {root.describe_action(action) for action in actions
                 if root.describe_action(action) in requested}
        if found != requested:
            raise ValueError(f"requested alternative not legal: {sorted(requested - found)}")
        actions = [action for action in actions
                   if list(action.key()) == selected_key
                   or root.describe_action(action) in requested]
    started = time.perf_counter()
    results = paired_outcomes(root, actions, replicates=replicates,
                              max_actions=max_actions, seed=seed,
                              continuation_policy=continuation)
    return {"schema": "entity-rollout-paired-root-v1", "game_seed": record["seed"],
            "deck_a": record["deck_a"], "deck_b": record["deck_b"],
            "learner_seat": record["learner_seat"], "step_zero_based": step,
            "public_root_state": public_root_state(root),
            "selected_action_key": selected_key, "replicates": replicates,
            "future_seed": seed, "audit_seconds": round(time.perf_counter() - started, 3),
            "results": results,
            "paired_comparisons_to_selected": paired_comparisons(results, selected_key),
            "warning": "Outcome ranks depend on continuation policy and sampled belief; review before labeling."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--game-index", type=int, default=0)
    parser.add_argument("--step", type=int, required=True,
                        help="Zero-based action index; root is immediately before this action")
    parser.add_argument("--cards", type=Path, default=Path(__file__).resolve().parents[1]
                        / "cards.251332.enUS.json")
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=16)
    parser.add_argument("--max-actions", type=int, default=240)
    parser.add_argument("--max-root-actions", type=int, default=12)
    parser.add_argument("--only-alternative", action="append", default=[],
                        help="Restrict to the played action and this exact action description")
    parser.add_argument("--seed", type=int, default=202701060000)
    parser.add_argument("--continuation", choices=("heuristic", "entity-greedy"),
                        default="heuristic")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    verify_report_inputs(report, args.cards, args.deck_config)
    rounds = [row for row in report["history"] if row["round"] == args.round]
    if len(rounds) != 1 or not 0 <= args.game_index < len(rounds[0]["games"]):
        raise ValueError("round/game index unavailable")
    if args.continuation == "entity-greedy":
        if args.checkpoint is None:
            parser.error("entity-greedy requires --checkpoint")
        continuation = EntityGreedyPolicy(args.checkpoint, args.device)
    else:
        continuation = HeuristicPolicy()
    result = audit(rounds[0]["games"][args.game_index], args.cards, args.deck_config,
                   step=args.step, replicates=args.replicates,
                   max_actions=args.max_actions, seed=args.seed,
                   max_root_actions=args.max_root_actions, continuation=continuation,
                   only_alternatives=tuple(args.only_alternative))
    result.update(report=str(args.report), round=args.round, game_index=args.game_index,
                  continuation=args.continuation,
                  checkpoint=str(args.checkpoint) if args.checkpoint else None)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"selected": result["selected_action_key"],
                      "comparisons": result["paired_comparisons_to_selected"]},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
