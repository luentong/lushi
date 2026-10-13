from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from hsa import DragonMirrorGame
from hsa.policy import HeuristicPolicy
from audit_paired_root_outcomes import (
    ModelGreedyPolicy, paired_comparisons, paired_outcomes,
)


class PairedRootOutcomeTests(unittest.TestCase):
    def test_paired_worlds_are_reproducible_and_root_is_unchanged(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 42)
        actions = game.legal_actions()
        original = game.snapshot()
        first = paired_outcomes(game, actions, replicates=2,
                                max_actions=20, seed=123)
        second = paired_outcomes(game, actions, replicates=2,
                                 max_actions=20, seed=123)
        self.assertEqual(first, second)
        self.assertEqual(game.snapshot(), original)
        self.assertTrue(all(row["invalid"] == 0 for row in first))
        self.assertTrue(all(len(row["outcomes"]) == 2 for row in first))

    def test_truncated_games_do_not_count_as_wins(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 42)
        result = paired_outcomes(game, game.legal_actions()[:1],
                                 replicates=2, max_actions=1, seed=123)
        self.assertEqual(result[0]["truncated"], 2)
        self.assertEqual(result[0]["decided_games"], 0)
        self.assertIsNone(result[0]["score_per_decided_game"])

    def test_comparison_uses_only_paired_decided_replicates(self):
        rows = [
            {"action_key": ["a"], "description": "selected",
             "outcomes": [
                 {"replicate": 0, "status": "losses"},
                 {"replicate": 1, "status": "wins"},
                 {"replicate": 2, "status": "truncated"}]},
            {"action_key": ["b"], "description": "alternative",
             "outcomes": [
                 {"replicate": 0, "status": "wins"},
                 {"replicate": 1, "status": "losses"},
                 {"replicate": 2, "status": "wins"}]},
        ]
        comparison = paired_comparisons(rows, ["a"])[0]
        self.assertEqual(comparison["paired_decided"], 2)
        self.assertEqual(comparison["alternative_better"], 1)
        self.assertEqual(comparison["selected_better"], 1)
        self.assertEqual(comparison["mean_score_difference"], 0.0)

    def test_rejects_invalid_audit_limits(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 42)
        with self.assertRaises(ValueError):
            paired_outcomes(game, game.legal_actions(),
                            replicates=0, max_actions=10, seed=1)

    def test_model_continuation_keeps_legal_action_alignment(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 42)
        actions = game.legal_actions()

        class FirstActionModel:
            def predict(self, state, choices):
                self.seen = tuple(choices)
                return type("Prediction", (), {
                    "priors": tuple(1.0 if index == 0 else 0.0
                                    for index in range(len(choices)))})()

        model = FirstActionModel()
        self.assertEqual(ModelGreedyPolicy(model).choose(game), actions[0])
        self.assertEqual(model.seen, tuple(actions))

    def test_batched_and_sequential_continuations_agree(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 42)
        actions = game.legal_actions()
        heuristic = HeuristicPolicy()

        class BatchHeuristic:
            def choose_batch(self, games):
                return [heuristic.choose(state) for state in games]

        sequential = paired_outcomes(game, actions, replicates=2,
                                     max_actions=60, seed=17,
                                     continuation_policy=heuristic)
        batched = paired_outcomes(game, actions, replicates=2,
                                  max_actions=60, seed=17,
                                  continuation_policy=BatchHeuristic())
        self.assertEqual(sequential, batched)


if __name__ == "__main__":
    unittest.main()
