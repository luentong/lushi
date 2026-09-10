from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.training import (
    temperature_scale_probabilities,
    value_weighted_policy_target,
)


class TrainingDataTests(unittest.TestCase):
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
