import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa import DragonMirrorGame
from hsa.observer_view import observer_view
from audit_entity_dataset import check_decision, committed_paths


class EntityDatasetAuditTests(unittest.TestCase):
    def setUp(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 2)
        actions = game.legal_actions()
        self.row = {"observer_view": observer_view(game, actions=actions),
                    "policy_target": [1 / len(actions)] * len(actions),
                    "legal_action_count": len(actions), "chosen_action": 0,
                    "executed_action": 0, "actor": 0, "winner": 0, "value_target": 1.0}

    def test_fresh_view_passes(self):
        self.assertEqual(self.row["legal_action_count"], check_decision(self.row))

    def test_conditional_labels_have_policy_but_no_fabricated_terminal_value(self):
        row = copy.deepcopy(self.row)
        row.update(conditional=True, value_target=None, value_target_valid=False)
        self.assertEqual(row["legal_action_count"], check_decision(row, policy_only=True))
        row["value_target"] = 1.0
        with self.assertRaisesRegex(ValueError, "no terminal"):
            check_decision(row, policy_only=True)

    def test_optional_parallel_arrays_must_align(self):
        for field in ("actions", "teacher_action_values", "teacher_action_visits", "action_keys"):
            row = copy.deepcopy(self.row)
            row[field] = []
            with self.assertRaises(ValueError):
                check_decision(row)

    def test_duplicate_concrete_action_keys_rejected(self):
        self.row["action_keys"] = ["duplicate"] * self.row["legal_action_count"]
        self.assertGreater(self.row["legal_action_count"], 1)
        with self.assertRaises(ValueError):
            check_decision(self.row)

    def test_inverted_terminal_reward_rejected(self):
        self.row["value_target"] = -1
        with self.assertRaisesRegex(ValueError, "perspective"):
            check_decision(self.row)

    def test_enemy_hand_identity_rejected(self):
        card = copy.deepcopy(next(e for e in self.row["observer_view"]["entities"] if e["zone"] == "hand"))
        card["owner"] = 1
        self.row["observer_view"]["entities"].append(card)
        with self.assertRaisesRegex(ValueError, "private opponent"):
            check_decision(self.row)

    def test_bad_action_reference_rejected(self):
        self.row["observer_view"]["actions"][0]["source"] = 100000
        with self.assertRaisesRegex(ValueError, "reference"):
            check_decision(self.row)

    def test_only_committed_successful_shards_are_selected(self):
        jobs = [{"index": 2, "exit_code": 1, "data": "failed.jsonl.gz"},
                {"index": 1, "exit_code": 0, "data": "good1.jsonl.gz"},
                {"index": 0, "exit_code": 0, "data": "good0.jsonl.gz"}]
        self.assertEqual([Path("good0.jsonl.gz"), Path("good1.jsonl.gz")], committed_paths({"jobs": jobs}))


if __name__ == "__main__":
    unittest.main()
