import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_entity_rollouts import audit


class EntityRolloutAuditTests(unittest.TestCase):
    def test_reports_game_macro_not_row_weighted_brier(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl.gz"
            rows = [
                {"game_seed": 1, "deck_a": "a", "deck_b": "b", "actor": 0,
                 "return": 1, "old_value": 1, "opponent_version": "bootstrap"},
                {"game_seed": 2, "deck_a": "a", "deck_b": "b", "actor": 0,
                 "return": -1, "old_value": 1, "opponent_version": "round1"},
                {"game_seed": 2, "deck_a": "a", "deck_b": "b", "actor": 0,
                 "return": -1, "old_value": 1, "opponent_version": "round1"},
            ]
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row) + "\n")
            result = audit([path])
            self.assertEqual(2, result["overall"]["games"])
            self.assertEqual(3, result["overall"]["decisions"])
            self.assertAlmostEqual(0.5, result["overall"]["game_macro_brier"])
            self.assertEqual(2, result["by_deck"]["a"]["games"])


if __name__ == "__main__":
    unittest.main()
