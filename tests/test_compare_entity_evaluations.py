from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_entity_evaluations import compare


class MatchedEvaluationTests(unittest.TestCase):
    def evaluation(self, checkpoint, opponent, winners):
        games = []
        for i, winner in enumerate(winners):
            games.append({"pair_id": i // 2, "seed": 10 + i // 2,
                          "candidate_deck": "weak" if i < 2 else "strong",
                          "opponent_deck": "other", "candidate_seat": i % 2,
                          "status": "complete", "winner": winner})
        return {"parameters": {"candidate": checkpoint, "seed": 10,
                               "pairs_per_matchup": 1, "deck_config": "decks.json",
                               "cards": "cards.json", "max_actions": 400,
                               "max_game_seconds": 120},
                "checkpoint_sha256": {"candidate": checkpoint, "opponent": opponent},
                "games": games}

    def test_weak_deck_can_improve_despite_low_raw_win_rate(self):
        baseline = self.evaluation("old", "old", [1, 0, 0, 1])
        candidate = self.evaluation("new", "old", [1, 1, 0, 1])
        result = compare(candidate, baseline)
        self.assertEqual(4, result["games"])
        self.assertEqual(0, result["by_candidate_deck"]["weak"]["baseline_score"])
        self.assertEqual(.5, result["by_candidate_deck"]["weak"]["candidate_score"])
        self.assertEqual(.5, result["by_candidate_deck"]["weak"]["mean_score_delta"])

    def test_mismatched_seed_or_opponent_rejected(self):
        baseline = self.evaluation("old", "old", [1, 1])
        candidate = self.evaluation("new", "old", [1, 1])
        candidate["parameters"]["seed"] += 1
        with self.assertRaisesRegex(ValueError, "seed"):
            compare(candidate, baseline)
        candidate = self.evaluation("new", "different", [1, 1])
        with self.assertRaisesRegex(ValueError, "different frozen opponents"):
            compare(candidate, baseline)


if __name__ == "__main__":
    unittest.main()
