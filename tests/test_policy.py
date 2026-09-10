from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import Action, DragonMirrorGame
from hsa.policy import HeuristicPolicy


CARDS = ROOT / "cards.251332.enUS.json"


class HeuristicPolicyTests(unittest.TestCase):
    def test_policy_only_selects_legal_actions(self):
        game = DragonMirrorGame(CARDS, 202609090001)
        policy = HeuristicPolicy()
        for _ in range(500):
            if game.finished:
                break
            action = policy.choose(game)
            self.assertIn(action.key(), {candidate.key() for candidate in game.legal_actions()})
            game.step(action)
        self.assertEqual(0, game.invalid_actions)

    def test_policy_takes_available_lethal(self):
        game = DragonMirrorGame(CARDS, 17)
        player, enemy = game.players
        player.hand.clear()
        player.board.clear()
        enemy.board.clear()
        enemy.health = 3
        attacker = game._entity("JAIL_421")
        attacker.summoned_turn = game.turn - 1
        player.board.append(attacker)
        action = HeuristicPolicy().choose(game)
        self.assertEqual(Action("ATTACK", attacker.entity_id, 1, None), action)

    def test_policy_is_deterministic_without_consuming_rng(self):
        first = DragonMirrorGame(CARDS, 19)
        second = DragonMirrorGame(CARDS, 19)
        policy = HeuristicPolicy()
        self.assertEqual(policy.choose(first), policy.choose(second))
        self.assertEqual(first.rng.getstate(), second.rng.getstate())

    def test_hand_target_battlecries_are_scored_as_hand_cards(self):
        for card_id in ("CATA_200", "CATA_490"):
            with self.subTest(card_id=card_id):
                game = DragonMirrorGame(CARDS, 23)
                player = game.players[0]
                player.hand.clear()
                player.mana = 10
                cheap = game._entity("GAME_005")
                expensive = game._entity("EDR_421")
                source = game._entity(card_id)
                player.hand.extend([cheap, expensive, source])
                policy = HeuristicPolicy()
                candidates = [
                    action for action in game.legal_actions()
                    if action.kind == "PLAY" and action.source == source.entity_id
                ]
                action = max(
                    candidates,
                    key=lambda candidate: policy.score(game, candidate),
                )
                self.assertEqual(cheap.entity_id, action.target_entity)


if __name__ == "__main__":
    unittest.main()
