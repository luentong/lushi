#!/usr/bin/env python3
"""Seat-swapped gameplay check for a guarded mulligan head versus auto-4+."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from benchmark_mcts import _decoded_decks
from hsa.dragon_mirror import DragonMirrorGame
from hsa.mulligan import MulliganModel, automatic_mask, next_mulligan_action
from hsa.policy import HeuristicPolicy


def play(cards: Path, seed: int, pair, model, model_seat: int, max_actions: int):
    game = DragonMirrorGame(
        cards, seed, manual_mulligan=True,
        deck_counts=(pair[0][0], pair[1][0]),
        player_classes=(pair[0][1], pair[1][1]),
    )
    opening = []
    guard_fallbacks = 0
    for actor in (0, 1):
        if actor == model_seat:
            raw = model.raw_mask(game, actor)
            mask = model.choose_mask(game, actor)
            guard_fallbacks += raw != mask
        else:
            mask = automatic_mask(game, actor)
        opening.append(mask)
        while game.pending_choice and game.pending_choice["kind"] == "MULLIGAN" \
                and game.pending_choice["player"] == actor:
            game.step(next_mulligan_action(game, mask))
    policies = (HeuristicPolicy(), HeuristicPolicy())
    steps = 0
    while not game.finished and steps < max_actions:
        game.step(policies[game.current].choose(game))
        steps += 1
    if not game.finished:
        return {"status": "incomplete", "steps": steps, "opening": opening,
                "guard_fallbacks": guard_fallbacks}
    return {"status": "complete", "steps": steps, "opening": opening,
            "winner": game.winner, "model_win": game.winner == model_seat,
            "draw": game.winner is None, "invalid_actions": game.invalid_actions,
            "guard_fallbacks": guard_fallbacks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=ROOT / "config/decks_20260924_flat.json")
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--pairs", type=int, default=40)
    parser.add_argument("--seed", type=int, default=20261013101)
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument("--deck-id", action="append", default=[])
    parser.add_argument("--output", type=Path, default=ROOT / "reports/mulligan-v3/paired-eval.json")
    args = parser.parse_args()
    decks = _decoded_decks(args.config)
    ids = sorted(args.deck_id or decks)
    if not ids or any(deck_id not in decks for deck_id in ids):
        parser.error("unknown or empty deck selection")
    model = MulliganModel(args.checkpoint)
    rng = random.Random(args.seed)
    games = []
    for index in range(args.pairs):
        left, right = rng.choices(ids, k=2)
        pair = (decks[left], decks[right])
        seed = args.seed + index * 1009
        for seat in (0, 1):
            result = play(args.cards, seed, pair, model, seat, args.max_actions)
            games.append({"seed": seed, "decks": [left, right],
                          "model_seat": seat, **result})
    complete = [row for row in games if row["status"] == "complete"]
    counts = Counter(
        "draw" if row["draw"] else "model_win" if row["model_win"] else "auto_win"
        for row in complete
    )
    summary = {"pairs": args.pairs, "complete": len(complete),
               "incomplete": len(games) - len(complete),
               "model_wins": counts["model_win"], "auto_wins": counts["auto_win"],
               "draws": counts["draw"],
               "invalid_actions": sum(row["invalid_actions"] for row in complete),
               "guard_fallbacks": sum(row["guard_fallbacks"] for row in games),
               "gameplay_policy": "heuristic-v1-both-seats",
               "note": "Paired gameplay diagnostic; the model uses a proxy-score fallback, not a proven stronger ladder mulligan."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({"summary": summary, "games": games},
                                      ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(args.output), **summary}, ensure_ascii=False))
    return 0 if summary["incomplete"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
