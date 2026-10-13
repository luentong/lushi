#!/usr/bin/env python3
"""Generate auditable, information-safe opening-hand labels for a separate head."""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from benchmark_mcts import _decoded_decks
from hsa.dragon_mirror import Action, DragonMirrorGame
from hsa.mulligan import (
    FEATURE_SCHEMA, TEACHER_VERSION, automatic_mask, encode_mulligan, opening_cards,
    teacher_mask, teacher_scores,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config/decks_20260924_flat.json")
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--games", type=int, default=512)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--seed", type=int, default=2026101301)
    parser.add_argument("--output", type=Path, default=ROOT / "reports/mulligan-v1/openings.jsonl")
    args = parser.parse_args()
    if args.games < 1:
        parser.error("--games must be positive")
    decks = _decoded_decks(args.config)
    deck_ids = sorted(decks)
    chooser = random.Random(args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as out:
        for index in range(args.games):
            left, right = chooser.choices(deck_ids, k=2)
            game_seed = args.seed + index * 1009
            game = DragonMirrorGame(
                args.cards, game_seed, manual_mulligan=True,
                deck_counts=(decks[left][0], decks[right][0]),
                player_classes=(decks[left][1], decks[right][1]),
            )
            for actor, deck_id, opponent_id in ((0, left, right), (1, right, left)):
                if actor == 1:
                    game.step(Action("MULLIGAN_CONFIRM"))
                cards = opening_cards(game, actor)
                scores = teacher_scores(game, actor, args.samples)
                best = max(range(len(scores)), key=lambda mask: (
                    scores[mask], -mask.bit_count(), -mask,
                ))
                assert best == teacher_mask(game, actor, args.samples)
                row = {
                    "schema": FEATURE_SCHEMA, "teacher_version": TEACHER_VERSION,
                    "seed": game_seed,
                    "deck_id": deck_id, "opponent_deck_id_for_audit_only": opponent_id,
                    "actor": actor, "own_class": game.players[actor].card_class,
                    "opponent_class": game.players[1 - actor].card_class,
                    "offered": [card.card_id for card in cards],
                    "features": encode_mulligan(game, actor),
                    "teacher_mask": best, "teacher_scores": scores,
                    "automatic_mask": automatic_mask(game, actor),
                    "teacher_samples": args.samples,
                }
                out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"games": args.games, "records": args.games * 2,
                      "output": str(args.output), "schema": FEATURE_SCHEMA,
                      "teacher_version": TEACHER_VERSION}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
