from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.evaluation import (
    exact_two_sided_sign_p,
    paired_seed_summary,
    wilson_interval,
)


class EvaluationTests(unittest.TestCase):
    def test_wilson_interval_contains_observed_rate(self):
        low, high = wilson_interval(60, 100)
        self.assertLess(low, 0.6)
        self.assertGreater(high, 0.6)

    def test_sign_test_is_symmetric(self):
        self.assertEqual(
            exact_two_sided_sign_p(18, 8),
            exact_two_sided_sign_p(8, 18),
        )

    def test_paired_seed_summary(self):
        games = [
            {"seed": 1, "mcts_seat": 0, "mcts_win": True},
            {"seed": 1, "mcts_seat": 1, "mcts_win": True},
            {"seed": 2, "mcts_seat": 0, "mcts_win": True},
            {"seed": 2, "mcts_seat": 1, "mcts_win": False},
            {"seed": 3, "mcts_seat": 0, "mcts_win": False},
            {"seed": 3, "mcts_seat": 1, "mcts_win": False},
        ]
        summary = paired_seed_summary(games)
        self.assertEqual(1, summary["swept_pairs"])
        self.assertEqual(1, summary["split_pairs"])
        self.assertEqual(1, summary["lost_pairs"])
        self.assertEqual(1.0, summary["exact_two_sided_sign_p"])

    def test_incomplete_pair_is_rejected(self):
        with self.assertRaises(ValueError):
            paired_seed_summary([
                {"seed": 1, "mcts_seat": 0, "mcts_win": True},
            ])


if __name__ == "__main__":
    unittest.main()
