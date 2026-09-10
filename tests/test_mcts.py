from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import (
    DeterminizedMCTSPolicy,
    DragonMirrorGame,
    InformationSetMCTSPolicy,
    MCTSPolicy,
)
from hsa.policy_value import HeuristicPolicyValueModel


CARDS = ROOT / "cards.251332.enUS.json"


class MCTSPolicyTests(unittest.TestCase):
    def test_mcts_returns_legal_action_and_does_not_mutate_root(self):
        game = DragonMirrorGame(CARDS, 101)
        before = game.snapshot()
        policy = MCTSPolicy(iterations=8, rollout_depth=4)
        action = policy.choose(game)
        self.assertIn(action.key(), {candidate.key() for candidate in game.legal_actions()})
        self.assertEqual(before, game.snapshot())
        self.assertGreater(policy.last_search["nodes"], 1)

    def test_mcts_is_reproducible_for_same_state(self):
        first = DragonMirrorGame(CARDS, 103)
        second = DragonMirrorGame(CARDS, 103)
        left = MCTSPolicy(iterations=8, rollout_depth=4)
        right = MCTSPolicy(iterations=8, rollout_depth=4)
        self.assertEqual(left.choose(first), right.choose(second))
        self.assertEqual(left.last_search, right.last_search)

    def test_terminal_state_is_rejected(self):
        game = DragonMirrorGame(CARDS, 107)
        game.finished = True
        with self.assertRaises(RuntimeError):
            MCTSPolicy().choose(game)

    def test_terminal_node_with_stale_pending_choice_has_no_actions(self):
        game = DragonMirrorGame(CARDS, 109)
        game.finished = True
        game.pending_choice = {"kind": "REWIND"}
        policy = MCTSPolicy()
        self.assertEqual([], policy._ordered_actions(game, []))

    def test_determinized_mcts_is_legal_reproducible_and_root_safe(self):
        first = DragonMirrorGame(CARDS, 113)
        second = DragonMirrorGame(CARDS, 113)
        before = first.snapshot()
        left = DeterminizedMCTSPolicy(samples=2, iterations_per_sample=4, rollout_depth=3)
        right = DeterminizedMCTSPolicy(samples=2, iterations_per_sample=4, rollout_depth=3)
        action = left.choose(first)
        self.assertEqual(action, right.choose(second))
        self.assertIn(action.key(), {candidate.key() for candidate in first.legal_actions()})
        self.assertEqual(before, first.snapshot())
        self.assertEqual("public_dragon_mirror_v3", left.information_mode)

    def test_shared_tree_ismcts_is_legal_reproducible_and_root_safe(self):
        first = DragonMirrorGame(CARDS, 127)
        second = DragonMirrorGame(CARDS, 127)
        before = first.snapshot()
        left = InformationSetMCTSPolicy(
            samples=2, iterations_per_sample=4, tree_depth=4,
            rollout_depth=3,
        )
        right = InformationSetMCTSPolicy(
            samples=2, iterations_per_sample=4, tree_depth=4,
            rollout_depth=3,
        )
        action = left.choose(first)
        self.assertEqual(action, right.choose(second))
        self.assertIn(action.key(), {item.key() for item in first.legal_actions()})
        self.assertEqual(before, first.snapshot())
        self.assertEqual(8, left.last_search["determinizations"])
        self.assertGreater(left.last_search["root_children"], 1)
        self.assertEqual(len(first.legal_actions()), len(left.last_search["root_policy"]))
        self.assertAlmostEqual(1.0, sum(left.last_search["root_policy"]))

    def test_shared_tree_does_not_read_true_opponent_hidden_identity(self):
        first = DragonMirrorGame(CARDS, 131)
        second = first.clone(include_history=True)
        second.players[1].hand[0] = second._entity("CORE_CS2_065")
        left = InformationSetMCTSPolicy(
            samples=2, iterations_per_sample=3, tree_depth=3,
            rollout_depth=2,
        )
        right = InformationSetMCTSPolicy(
            samples=2, iterations_per_sample=3, tree_depth=3,
            rollout_depth=2,
        )
        self.assertEqual(left.choose(first), right.choose(second))

    def test_policy_value_guided_ismcts_uses_shared_model_contract(self):
        game = DragonMirrorGame(CARDS, 137)
        policy = InformationSetMCTSPolicy(
            samples=2, iterations_per_sample=3, tree_depth=3,
            rollout_depth=0,
            policy_value_model=HeuristicPolicyValueModel(),
        )
        action = policy.choose(game)
        self.assertIn(action.key(), {item.key() for item in game.legal_actions()})
        self.assertEqual(
            "heuristic-policy-value-v1",
            policy.last_search["policy_value_model"],
        )

    def test_policy_prior_can_keep_heuristic_leaf_rollout(self):
        game = DragonMirrorGame(CARDS, 139)
        policy = InformationSetMCTSPolicy(
            samples=2, iterations_per_sample=3, tree_depth=3,
            rollout_depth=2,
            policy_value_model=HeuristicPolicyValueModel(),
            use_model_value=False,
        )
        action = policy.choose(game)
        self.assertIn(action.key(), {item.key() for item in game.legal_actions()})
        self.assertEqual("heuristic_rollout", policy.last_search["leaf_value_source"])


if __name__ == "__main__":
    unittest.main()
