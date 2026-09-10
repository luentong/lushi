from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.training import temperature_scale_probabilities


class TrainingDataTests(unittest.TestCase):
    def test_policy_target_temperature_sharpens_visit_distribution(self):
        targets = temperature_scale_probabilities([0.25, 0.75], 0.5)
        self.assertAlmostEqual(0.1, targets[0], places=6)
        self.assertAlmostEqual(0.9, targets[1], places=6)

    def test_policy_target_temperature_must_be_positive(self):
        with self.assertRaises(ValueError):
            temperature_scale_probabilities([0.25, 0.75], 0.0)


if __name__ == "__main__":
    unittest.main()
