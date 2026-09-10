from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame
from hsa.dragon_mirror import Action
from hsa.encoding import encode_action, encode_decision, encode_state, feature_schema
from hsa.policy_value import HeuristicPolicyValueModel


CARDS = ROOT / "cards.251332.enUS.json"


class EncodingTests(unittest.TestCase):
    def test_state_encoding_does_not_read_opponent_hidden_identity(self):
        first = DragonMirrorGame(CARDS, 301)
        second = first.clone(include_history=True)
        second.players[1].hand[0] = second._entity("CORE_CS2_065")
        self.assertEqual(encode_state(first, 0), encode_state(second, 0))

    def test_state_and_action_sizes_match_versioned_schema(self):
        game = DragonMirrorGame(CARDS, 303)
        decision = encode_decision(game)
        schema = feature_schema()
        self.assertEqual(schema["state_size"], len(decision.state))
        self.assertTrue(decision.actions)
        self.assertTrue(all(
            len(action) == schema["action_size"] for action in decision.actions
        ))
        self.assertEqual(4, schema["schema_version"])
        self.assertEqual(867, len(encode_state(game, schema_version=1)))
        self.assertEqual(1217, len(encode_state(game, schema_version=2)))
        self.assertEqual(1217, len(encode_state(game, schema_version=3)))
        self.assertEqual(
            feature_schema(3)["action_size"] + 6,
            schema["action_size"],
        )

    def test_v3_action_players_are_relative_to_the_actor(self):
        game = DragonMirrorGame(CARDS, 3031)
        game.current = 0
        first = encode_action(
            game, Action("HERO_ATTACK", target_player=1), schema_version=3
        )
        first_legacy = encode_action(
            game, Action("HERO_ATTACK", target_player=1), schema_version=2
        )
        game.current = 1
        second = encode_action(
            game, Action("HERO_ATTACK", target_player=0), schema_version=3
        )
        second_legacy = encode_action(
            game, Action("HERO_ATTACK", target_player=0), schema_version=2
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first_legacy, second_legacy)

    def test_v4_action_identifies_target_zone(self):
        game = DragonMirrorGame(CARDS, 3032)
        own = game.players[game.current]
        hand_action = Action("PLAY", target_entity=own.hand[0].entity_id)
        board_card = game._entity(own.hand[0].card_id)
        own.board.append(board_card)
        board_action = Action("PLAY", target_entity=board_card.entity_id)
        self.assertEqual(
            encode_action(game, hand_action, schema_version=3),
            encode_action(game, board_action, schema_version=3),
        )
        self.assertNotEqual(
            encode_action(game, hand_action, schema_version=4),
            encode_action(game, board_action, schema_version=4),
        )

    def test_v2_observes_temporary_hero_attack_missing_from_v1(self):
        first = DragonMirrorGame(CARDS, 304)
        second = first.clone(include_history=True)
        second.players[second.current].hero_attack_bonus = 3
        self.assertEqual(
            encode_state(first, schema_version=1),
            encode_state(second, schema_version=1),
        )
        self.assertNotEqual(encode_state(first), encode_state(second))

    def test_legal_action_encodings_are_distinct(self):
        game = DragonMirrorGame(CARDS, 305)
        decision = encode_decision(game)
        self.assertEqual(len(decision.actions), len(set(decision.actions)))

    def test_heuristic_policy_value_output_is_normalized_and_bounded(self):
        game = DragonMirrorGame(CARDS, 307)
        legal = game.legal_actions()
        output = HeuristicPolicyValueModel().predict(game, legal)
        self.assertAlmostEqual(1.0, sum(output.priors))
        self.assertEqual(len(legal), len(output.priors))
        self.assertLessEqual(abs(output.value), 1.0)


if __name__ == "__main__":
    unittest.main()
