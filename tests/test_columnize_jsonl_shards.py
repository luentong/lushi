import tempfile
import unittest
from pathlib import Path

import torch

from scripts.columnize_jsonl_shards import _flush
from scripts.train_policy_value import collate_decisions, evaluate


class ColumnizeActionQTests(unittest.TestCase):
    def test_validation_scores_only_visited_action_q_and_restores_training_mode(self):
        class TinyActionQModel(torch.nn.Module):
            def forward_with_action_values(self, states, actions, mask):
                return (
                    torch.tensor([[1.0, 0.0]]),
                    torch.tensor([0.0]),
                    torch.tensor([[0.2, 0.9]]),
                )

        model = TinyActionQModel()
        model.train()
        batch = (
            torch.zeros((1, 1)),
            torch.zeros((1, 2, 1)),
            torch.tensor([[True, True]]),
            torch.tensor([0]),
            torch.tensor([1.0]),
            torch.tensor([[1.0, 0.0]]),
            torch.tensor([[0.5, -1.0]]),
            torch.tensor([[True, False]]),
        )
        metrics = evaluate(model, [batch], torch.device("cpu"))
        self.assertTrue(model.training)
        self.assertEqual(1, metrics["action_q_count"])
        self.assertAlmostEqual(0.3, metrics["action_q_mae"], places=6)
        self.assertAlmostEqual(0.09, metrics["action_q_mse"], places=6)

    def test_validation_without_action_q_keeps_eval_mode(self):
        class TinyPolicyValueModel(torch.nn.Module):
            def forward(self, states, actions, mask):
                return torch.tensor([[0.0, 1.0]]), torch.tensor([0.0])

        model = TinyPolicyValueModel()
        model.eval()
        batch = (
            torch.zeros((1, 1)),
            torch.zeros((1, 2, 1)),
            torch.tensor([[True, True]]),
            torch.tensor([1]),
            torch.tensor([0.0]),
            torch.tensor([[0.0, 1.0]]),
        )
        metrics = evaluate(model, [batch], torch.device("cpu"))
        self.assertFalse(model.training)
        self.assertEqual(0, metrics["action_q_count"])
        self.assertIsNone(metrics["action_q_mse"])

    def test_unvisited_search_action_is_not_an_action_q_label(self):
        record = {
            "state": [0.0, 1.0],
            "actions": [[1.0], [2.0]],
            "chosen_action": 0,
            "value_target": 1.0,
            "teacher_action_values": [0.25, 0.0],
            "teacher_action_visits": [3, 0],
            "game_seed": 1,
            "actor": 0,
            "winner": 0,
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "shard.pt"
            _flush([record], path)
            payload = torch.load(path, weights_only=True)
        self.assertEqual([[True, False]], payload["teacher_action_value_mask"].tolist())

    def test_explicit_action_q_mask_has_priority(self):
        record = {
            "state": [0.0],
            "actions": [[1.0], [2.0]],
            "chosen_action": 1,
            "value_target": -1.0,
            "teacher_action_values": [0.0, 0.25],
            "teacher_action_visits": [1, 0],
            "teacher_action_value_mask": [False, True],
        }
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "shard.pt"
            _flush([record], path)
            payload = torch.load(path, weights_only=True)
        self.assertEqual([[False, True]], payload["teacher_action_value_mask"].tolist())

    def test_tensor_training_collator_respects_visit_fallback(self):
        record = {
            "state": torch.tensor([0.0]),
            "actions": torch.tensor([[1.0], [2.0]]),
            "chosen_action": 0,
            "value_target": 1.0,
            "policy_target": torch.tensor([0.75, 0.25]),
            "teacher_action_values": torch.tensor([0.25, 0.0]),
            "teacher_action_visits": [3, 0],
        }
        batch = collate_decisions([record], include_action_values=True)
        self.assertEqual([[True, False]], batch[7].tolist())


if __name__ == "__main__":
    unittest.main()
