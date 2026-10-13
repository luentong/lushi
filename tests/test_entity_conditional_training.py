import copy
import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from hsa import DragonMirrorGame
from hsa.observer_view import observer_view
from train_entity_corrective import conditional_rows


class ConditionalTrainingTests(unittest.TestCase):
    def setUp(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 17)
        actions = game.legal_actions()
        self.row = {"record_type": "decision", "conditional": True,
                    "game_seed": 17, "observer_view": observer_view(game, actions=actions),
                    "policy_target": [1 / len(actions)] * len(actions),
                    "legal_action_count": len(actions), "chosen_action": 0,
                    "executed_action": 0, "actor": 0, "winner": 0,
                    "value_target_valid": False, "value_target": None,
                    "conditional_target_source": "independent_public_belief_search",
                    "conditional_target_top_action_agreement": 1.0}

    def write_shard(self, directory, name, rows):
        path = Path(directory) / name
        with gzip.open(path, "wt", encoding="utf-8") as output:
            for row in rows:
                output.write(json.dumps(row) + "\n")
        return path

    def test_agreement_filter_keeps_only_independent_policy_labels(self):
        with tempfile.TemporaryDirectory() as directory:
            low = copy.deepcopy(self.row)
            low["conditional_target_top_action_agreement"] = 0.5
            path = self.write_shard(directory, "first.gz", [self.row, low])
            rows, rejected = conditional_rows([path], 0.75, {path: "dragon__druid"})
            self.assertEqual(1, len(rows))
            self.assertEqual(1, rejected["low_agreement"])
            self.assertNotIn("value", rows[0])
            self.assertEqual("dragon__druid", rows[0]["matchup"])

    def test_fabricated_terminal_value_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            wrong = copy.deepcopy(self.row)
            wrong["value_target"] = 1.0
            path = self.write_shard(directory, "first.gz", [wrong])
            with self.assertRaisesRegex(ValueError, "no terminal"):
                conditional_rows([path], 0.75)

    def test_games_with_no_accepted_branches_remain_auditable(self):
        with tempfile.TemporaryDirectory() as directory:
            low = copy.deepcopy(self.row)
            low["conditional_target_top_action_agreement"] = 0.5
            first = self.write_shard(directory, "first.gz", [low])
            second = copy.deepcopy(self.row)
            second["game_seed"] = 18
            other = self.write_shard(directory, "second.gz", [second])
            rows, rejected = conditional_rows([first, other], 0.75)
            self.assertEqual([18], [row["seed"] for row in rows])
            self.assertEqual(1, rejected["games_without_accepted_rows"])

    def test_duplicate_game_seed_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            first = self.write_shard(directory, "first.gz", [self.row])
            second = self.write_shard(directory, "second.gz", [self.row])
            with self.assertRaisesRegex(ValueError, "distinct game seed"):
                conditional_rows([first, second], 0.75)


if __name__ == "__main__":
    unittest.main()
