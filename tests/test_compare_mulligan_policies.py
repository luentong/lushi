import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_mulligan_policies import compare


class MulliganPolicyComparisonTests(unittest.TestCase):
    def fixture(self, opening, winners):
        return {
            "checkpoint_sha256": {"candidate": "a", "opponent": "b"},
            "source_sha256": {"rules": "c"},
            "deck_config_sha256": "d",
            "parameters": {
                "seed": 7, "pairs_per_matchup": 1, "deck_config": "decks.json",
                "cards": "cards.json", "max_actions": 350,
                "max_game_seconds": 300, "candidate_search_budget": 0,
                "manual_mulligan": True, "opponent_mulligan_policy": "baseline",
                "candidate_mulligan_policy": opening,
            },
            "games": [
                {"pair_id": 0, "seed": 7, "candidate_deck": "dragon",
                 "opponent_deck": "priest", "candidate_seat": seat,
                 "winner": winner, "status": "complete"}
                for seat, winner in enumerate(winners)
            ],
        }

    def test_matched_openings_report_seat_paired_delta(self):
        result = compare(self.fixture("model", [0, 1]),
                         self.fixture("baseline", [1, 1]))
        self.assertEqual(2, result["games"])
        self.assertEqual(1.0, result["model_opening_score"])
        self.assertEqual(0.5, result["baseline_opening_score"])
        self.assertEqual(0.5, result["paired_delta"]["mean"])

    def test_opponent_mulligan_must_be_held_fixed(self):
        opponent_changed = self.fixture("baseline", [1, 1])
        opponent_changed["parameters"]["opponent_mulligan_policy"] = "model"
        with self.assertRaises(ValueError):
            compare(self.fixture("model", [0, 1]), opponent_changed)


if __name__ == "__main__":
    unittest.main()
