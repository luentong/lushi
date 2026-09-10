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
from hsa.policy_value import HeuristicPolicyValueModel, PolicyValueOutput


CARDS = ROOT / "cards.251332.enUS.json"


class _EndTurnPrior:
    name = "end-turn-prior-test"

    def predict(self, game, actions):
        weights = tuple(1.0 if action.kind == "END_TURN" else 0.0 for action in actions)
        total = sum(weights)
        return PolicyValueOutput(
            tuple(weight / total for weight in weights),
            0.0,
        )


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
        root_stats = left.last_search["root_action_stats"]
        self.assertEqual(len(first.legal_actions()), len(root_stats))
        self.assertEqual(1, sum(bool(item["selected"]) for item in root_stats))
        self.assertEqual(
            left.last_search["selected_visits"],
            next(item["visits"] for item in root_stats if item["selected"]),
        )
        self.assertAlmostEqual(
            left.last_search["selected_value"],
            next(item["mean_value"] for item in root_stats if item["selected"]),
        )

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

    def test_low_budget_puct_does_not_force_one_visit_per_legal_action(self):
        game = DragonMirrorGame(CARDS, 141)
        policy = InformationSetMCTSPolicy(
            samples=1, iterations_per_sample=4, tree_depth=3,
            rollout_depth=0, exploration=100.0,
            policy_value_model=_EndTurnPrior(), use_model_value=False,
            force_uniform_expansion=False,
        )
        action = policy.choose(game)
        legal = game.legal_actions()
        stats = policy.last_search["root_action_stats"]
        end_turn = next(
            item for candidate, item in zip(legal, stats, strict=True)
            if candidate.kind == "END_TURN"
        )
        self.assertEqual("END_TURN", action.kind)
        self.assertEqual(4, end_turn["visits"])
        self.assertTrue(any(item["visits"] == 0 for item in stats))
        self.assertEqual("puct_prior", policy.last_search["expansion_mode"])

    def test_legacy_puct_expansion_remains_available_for_ab_comparison(self):
        game = DragonMirrorGame(CARDS, 143)
        policy = InformationSetMCTSPolicy(
            samples=1, iterations_per_sample=len(game.legal_actions()),
            tree_depth=3, rollout_depth=0, exploration=100.0,
            policy_value_model=_EndTurnPrior(), use_model_value=False,
            force_uniform_expansion=True,
        )
        policy.choose(game)
        stats = policy.last_search["root_action_stats"]
        self.assertTrue(all(item["visits"] == 1 for item in stats))
        self.assertEqual(
            "force_unvisited", policy.last_search["expansion_mode"]
        )

    def test_adaptive_budget_scales_with_root_branching_and_honors_cap(self):
        game = DragonMirrorGame(CARDS, 145)
        root_actions = len(game.legal_actions())
        policy = InformationSetMCTSPolicy(
            samples=1, iterations_per_sample=2, tree_depth=3,
            rollout_depth=0, min_simulations_per_root_action=3,
            max_total_iterations=4,
        )
        policy.choose(game)
        self.assertEqual(2, policy.last_search["configured_iterations"])
        self.assertEqual(min(root_actions * 3, 4), policy.last_search["iterations"])
        self.assertEqual(
            policy.last_search["iterations"] - 2,
            policy.last_search["adaptive_iterations"],
        )

    def test_root_coverage_gives_each_action_requested_repeated_samples(self):
        game = DragonMirrorGame(CARDS, 146)
        policy = InformationSetMCTSPolicy(
            samples=1, iterations_per_sample=2, tree_depth=3,
            rollout_depth=0, min_simulations_per_root_action=2,
        )
        policy.choose(game)
        self.assertEqual(
            2, policy.last_search["minimum_root_action_visits_achieved"]
        )
        self.assertTrue(
            all(
                item["visits"] >= 2
                for item in policy.last_search["root_action_stats"]
            )
        )


if __name__ == "__main__":
    unittest.main()
