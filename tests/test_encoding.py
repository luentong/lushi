from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame
from hsa.encoding import encode_decision, encode_state, feature_schema
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
