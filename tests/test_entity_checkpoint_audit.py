import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_entity_checkpoints import summarize_predictions


class CheckpointAuditTests(unittest.TestCase):
    def test_game_macro_differs_from_row_weighting(self):
        rows = [{"seed": 1, "brier": 1, "policy_ce": 1, "policy_correct": 0,
                 "target": 0, "prediction": 1}]
        rows += [{"seed": 2, "brier": 0, "policy_ce": 0, "policy_correct": 1,
                  "target": 1, "prediction": 1} for _ in range(3)]
        result = summarize_predictions(rows, 0.5)
        self.assertEqual(0.25, result["brier"])
        self.assertEqual(0.5, result["game_macro_brier"])
        self.assertEqual(0.25, result["train_constant_brier"])
        self.assertEqual(0.25, result["confident_wrong_fraction"])

    def test_empty_split_rejected(self):
        with self.assertRaises(ValueError):
            summarize_predictions([], 0.5)


if __name__ == "__main__":
    unittest.main()
