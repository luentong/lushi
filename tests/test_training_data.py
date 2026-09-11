from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.training import (
    temperature_scale_probabilities,
    value_weighted_policy_target,
)

GENERATOR_PATH = ROOT / "scripts" / "generate_policy_value_data.py"
GENERATOR_SPEC = importlib.util.spec_from_file_location(
    "generate_policy_value_data", GENERATOR_PATH
)
assert GENERATOR_SPEC is not None and GENERATOR_SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(GENERATOR_SPEC)
GENERATOR_SPEC.loader.exec_module(GENERATOR)


class TrainingDataTests(unittest.TestCase):
    def test_streaming_statistics_do_not_require_retaining_all_games(self):
        games = [
            [{
                "winner": 0,
                "legal_action_count": 2,
                "chosen_action": 0,
                "executed_action": 1,
                "policy_target": [0.75, 0.25],
                "teacher_simulations": 4,
                "teacher_adaptive_simulations": 0,
                "teacher_action_values": [0.5, -0.5],
            }],
            [{
                "winner": 1,
                "legal_action_count": 1,
                "chosen_action": 0,
                "executed_action": 0,
                "policy_target": None,
                "teacher_simulations": 0,
                "teacher_adaptive_simulations": 0,
                "teacher_action_values": [0.0],
            }],
        ]
        statistics = GENERATOR.DatasetStatistics()
        for game in games:
            statistics.add_game(game)

        result = statistics.result()
        self.assertEqual(2, statistics.records)
        self.assertEqual(
            {"player_0": 1, "player_1": 1, "draw": 0},
            result["winner_counts"],
        )
        self.assertEqual(1.0, result["mean_decisions_per_game"])
        self.assertEqual(1.5, result["mean_legal_actions"])
        self.assertEqual(0.5, result["forced_action_fraction"])
        self.assertEqual(1.0, result["teacher_behavior_disagreement_fraction"])
        self.assertEqual(4.0, result["teacher_policy"]["mean_simulations"])
        self.assertEqual(1.0, result["teacher_policy"]["mean_visited_value_range"])

    def test_policy_target_temperature_sharpens_visit_distribution(self):
        targets = temperature_scale_probabilities([0.25, 0.75], 0.5)
        self.assertAlmostEqual(0.1, targets[0], places=6)
        self.assertAlmostEqual(0.9, targets[1], places=6)

    def test_policy_target_temperature_must_be_positive(self):
        with self.assertRaises(ValueError):
            temperature_scale_probabilities([0.25, 0.75], 0.0)

    def test_value_weighted_target_prefers_higher_q_at_equal_visits(self):
        targets = value_weighted_policy_target(
            [0.5, 0.5], [-0.5, 0.5], value_temperature=0.5
        )
        self.assertLess(targets[0], 0.2)
        self.assertGreater(targets[1], 0.8)
        self.assertAlmostEqual(1.0, sum(targets))

    def test_value_weighted_target_requires_aligned_values(self):
        with self.assertRaises(ValueError):
            value_weighted_policy_target([1.0], [0.0, 1.0], 0.5)


if __name__ == "__main__":
    unittest.main()
