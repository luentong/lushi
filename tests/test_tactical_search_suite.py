from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from audit_search_tactics import make_case
from hsa.dragon_mirror import LOW_COST_DRAGON_IDS


class TacticalSearchSuiteTests(unittest.TestCase):
    def test_information_order_fixture_has_no_mana_for_generated_dragon_after_both(self):
        game, _, _ = make_case("information_before_commitment")
        self.assertEqual(2, game.players[0].mana)
        self.assertTrue(all(game.card_defs[card_id].cost >= 1
                            for card_id in LOW_COST_DRAGON_IDS))
        for order in (("CATA_556", "CAP_107"), ("CAP_107", "CATA_556")):
            state = game.clone()
            for card_id in order:
                card = next(card for card in state.players[0].hand
                            if card.card_id == card_id)
                action = next(action for action in state.legal_actions()
                              if action.kind == "PLAY" and action.source == card.entity_id)
                state.step(action)
            self.assertEqual(0, state.players[0].mana)
            self.assertFalse(any(action.kind == "PLAY" for action in state.legal_actions()))

    def test_warrior_hero_power_prevents_known_counterattack_lethal(self):
        game, expected, _ = make_case("spend_remaining_mana_hero_power")
        actions = game.legal_actions()
        hero_power = next(action for action in actions if action.kind == "HERO_POWER")
        end_turn = next(action for action in actions if action.kind == "END_TURN")
        self.assertTrue(expected(hero_power))

        passed = game.clone(include_history=False, record_events=False)
        passed.step(end_turn)
        enemy_attack = next(
            action for action in passed.legal_actions()
            if action.kind == "ATTACK" and action.target_player == 0
            and action.target_entity is None
        )
        passed.step(enemy_attack)
        self.assertTrue(passed.finished)
        self.assertEqual(1, passed.winner)

        defended = game.clone(include_history=False, record_events=False)
        defended.step(hero_power)
        self.assertEqual(2, defended.players[0].armor)
        end_turn = next(action for action in defended.legal_actions()
                        if action.kind == "END_TURN")
        defended.step(end_turn)
        enemy_attack = next(
            action for action in defended.legal_actions()
            if action.kind == "ATTACK" and action.target_player == 0
            and action.target_entity is None
        )
        defended.step(enemy_attack)
        self.assertFalse(defended.finished)
        self.assertEqual(1, defended.players[0].health)
        self.assertEqual(0, defended.players[0].armor)


if __name__ == "__main__":
    unittest.main()
