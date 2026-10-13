#!/usr/bin/env python3
"""Show counterfactual opening-mask scores without opponent hidden information."""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from benchmark_mcts import matchup_deck_counts
from hsa.dragon_mirror import Action, DragonMirrorGame
from hsa.mulligan import automatic_mask, opening_cards, teacher_scores


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--deck-a", required=True)
    parser.add_argument("--deck-b", required=True)
    parser.add_argument("--actor", type=int, choices=(0, 1), default=0)
    parser.add_argument("--samples", type=int, default=16)
    parser.add_argument("--config", type=Path, default=ROOT / "config/decks_20260924_flat.json")
    args = parser.parse_args()
    pair = matchup_deck_counts(args.config, args.deck_a, args.deck_b)
    game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", args.seed,
                            manual_mulligan=True,
                            deck_counts=(pair[0][0], pair[1][0]),
                            player_classes=(pair[0][1], pair[1][1]))
    if args.actor:
        game.step(Action("MULLIGAN_CONFIRM"))
    cards = opening_cards(game, args.actor)
    scores = teacher_scores(game, args.actor, args.samples)
    result = {
        "offered": [{"id": card.card_id, "name": card.definition.name,
                     "cost": card.cost} for card in cards],
        "automatic_mask": automatic_mask(game, args.actor),
        "candidates": sorted(
            [{"mask": mask, "score": round(score, 5),
              "replace": [card.definition.name for index, card in enumerate(cards)
                          if mask & (1 << index)]}
             for mask, score in enumerate(scores)],
            key=lambda row: (-row["score"], len(row["replace"]), row["mask"]),
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
