from __future__ import annotations

import unittest
from pathlib import Path
from unittest.mock import patch

from hsa.dragon_mirror import CardDef, DragonMirrorGame
from hsa.mulligan import (
    FEATURE_WIDTH, MulliganModel, _curve_score, automatic_mask, encode_mulligan, next_mulligan_action,
    opening_cards, teacher_mask, teacher_scores,
)


CARDS = Path(__file__).resolve().parents[1] / "cards.251332.enUS.json"


class MulliganPipelineTests(unittest.TestCase):
    def test_explicit_phase_records_both_players_before_turn_one(self):
        game = DragonMirrorGame(CARDS, 91, manual_mulligan=True)
        self.assertEqual(0, game.turn)
        self.assertEqual(0, game.current)
        for actor in (0, 1):
            mask = teacher_mask(game, actor, samples=4)
            while game.pending_choice and game.pending_choice["player"] == actor:
                game.step(next_mulligan_action(game, mask))
        self.assertIsNone(game.pending_choice)
        self.assertEqual(1, game.turn)
        events = [row["kind"] for row in game.events]
        self.assertEqual(2, events.count("mulligan_offer"))
        self.assertEqual(2, events.count("mulligan_result"))

    def test_features_hide_deck_order_and_opponent_hand(self):
        game = DragonMirrorGame(CARDS, 92, manual_mulligan=True)
        before = encode_mulligan(game, 0)
        self.assertEqual(FEATURE_WIDTH, len(before))
        game.players[0].deck.reverse()
        game.players[1].hand.clear()
        self.assertEqual(before, encode_mulligan(game, 0))
        self.assertEqual(teacher_scores(game, 0, samples=4),
                         teacher_scores(game, 0, samples=4))

    def test_masks_never_select_unoffered_card(self):
        game = DragonMirrorGame(CARDS, 93, manual_mulligan=True)
        count = len(opening_cards(game, 0))
        self.assertLess(automatic_mask(game, 0), 1 << count)
        self.assertLess(teacher_mask(game, 0, samples=4), 1 << count)
        with self.assertRaises(ValueError):
            next_mulligan_action(game, 1 << count)

    def test_zero_cost_mana_spell_does_not_consume_normal_play(self):
        ramp = CardDef("FREE_MANA", "Free Mana", "SPELL", 0,
                       text="Gain 1 Mana Crystal this turn only.")
        two_drop = CardDef("TWO", "Two Drop", "MINION", 2, 2, 2)
        self.assertGreater(_curve_score([ramp, two_drop]),
                           _curve_score([two_drop]))

    def test_model_choice_worse_than_legacy_proxy_falls_back(self):
        model = MulliganModel.__new__(MulliganModel)
        with patch.object(MulliganModel, "raw_mask", return_value=0), \
                patch("hsa.mulligan.automatic_mask", return_value=3), \
                patch("hsa.mulligan.teacher_scores", return_value=[0.0, 0.5, 0.8, 1.0]):
            self.assertEqual(3, model.choose_mask(object(), 0))
        with patch.object(MulliganModel, "raw_mask", return_value=0), \
                patch("hsa.mulligan.automatic_mask", return_value=3), \
                patch("hsa.mulligan.teacher_scores", return_value=[1.0, 0.5, 0.8, 0.0]):
            self.assertEqual(0, model.choose_mask(object(), 0))


if __name__ == "__main__":
    unittest.main()
