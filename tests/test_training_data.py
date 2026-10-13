from __future__ import annotations

import importlib.util
import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from hsa.training import (
    temperature_scale_probabilities,
    value_weighted_policy_target,
)

GENERATOR_PATH = ROOT / "scripts" / "generate_policy_value_data.py"
GENERATOR_SPEC = importlib.util.spec_from_file_location(
    "generate_policy_value_data", GENERATOR_PATH
)
assert GENERATOR_SPEC is not None and GENERATOR_SPEC.loader is not None
GENERATOR = importlib.util.module_from_spec(GENERATOR_SPEC)
GENERATOR_SPEC.loader.exec_module(GENERATOR)
from compact_decision_shards import compact
from train_columnar_policy_value import turn_band_sample_weights


class TrainingDataTests(unittest.TestCase):
    def test_turn_band_sample_weights(self):
        import torch

        states = torch.zeros((4, 1))
        states[:, 0] = torch.tensor([0.03, 0.04, 0.07, 0.12])
        weights = turn_band_sample_weights(states, (1.5, 1.25, 0.75))
        self.assertEqual([1.5, 1.25, 0.75, 0.75], weights.tolist())
        self.assertEqual(
            [1.0, 1.0, 1.0, 1.0],
            turn_band_sample_weights(states, (1.0, 1.0, 1.0)).tolist(),
        )

    def test_action_value_target_masks_unvisited_actions(self):
        target = GENERATOR.action_value_policy_target(
            [0.2, 0.8, 99.0], [3, 4, 0], 0.1
        )
        self.assertEqual(0.0, target[2])
        self.assertGreater(target[1], 0.99)
        self.assertAlmostEqual(1.0, sum(target))

    def test_action_value_target_is_stable_for_extreme_values(self):
        target = GENERATOR.action_value_policy_target(
            [-1e6, 1e6], [1, 1], 0.01
        )
        self.assertLess(target[0], 1e-30)
        self.assertAlmostEqual(1.0, target[1])

    def test_action_value_target_returns_zero_when_all_actions_unvisited(self):
        self.assertEqual(
            [0.0, 0.0],
            GENERATOR.action_value_policy_target([0.1, -0.2], [0, 0], 0.15),
        )

    def test_action_value_target_rejects_bad_inputs(self):
        with self.assertRaises(ValueError):
            GENERATOR.action_value_policy_target([0.0], [1], 0.0)
        with self.assertRaises(ValueError):
            GENERATOR.action_value_policy_target([0.0], [1, 2], 0.1)
        with self.assertRaises(ValueError):
            GENERATOR.action_value_policy_target([float("nan")], [1], 0.1)

    def test_compaction_preserves_conditional_branch_depth(self):
        record = {
            "record_type": "decision",
            "state": [0.0],
            "actions": [[1.0]],
            "chosen_action": 0,
            "conditional": True,
            "conditional_trigger_depth": 3,
            "value_target": None,
            "value_target_valid": False,
        }
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "raw.jsonl.gz"
            dst = Path(directory) / "compact.jsonl.gz"
            with gzip.open(src, "wt", encoding="utf-8") as stream:
                stream.write(json.dumps({"record_type": "header"}) + "\n")
                stream.write(json.dumps(record) + "\n")
            self.assertEqual(1, compact(src, dst))
            with gzip.open(dst, "rt", encoding="utf-8") as stream:
                next(stream)
                compact_record = json.loads(next(stream))
        self.assertEqual(3, compact_record["conditional_trigger_depth"])

    def test_compaction_preserves_action_value_visits(self):
        record = {
            "record_type": "decision",
            "state": [0.0],
            "actions": [[1.0], [0.0]],
            "chosen_action": 0,
            "teacher_action_values": [0.25, -0.5],
            "teacher_action_visits": [7, 9],
            "value_target": 1.0,
        }
        with tempfile.TemporaryDirectory() as directory:
            src = Path(directory) / "raw.jsonl.gz"
            dst = Path(directory) / "compact.jsonl.gz"
            with gzip.open(src, "wt", encoding="utf-8") as stream:
                stream.write(json.dumps({"record_type": "header"}) + "\n")
                stream.write(json.dumps(record) + "\n")
            self.assertEqual(1, compact(src, dst))
            with gzip.open(dst, "rt", encoding="utf-8") as stream:
                next(stream)
                compact_record = json.loads(next(stream))
        self.assertEqual([7, 9], compact_record["teacher_action_visits"])

    def test_conditional_records_do_not_inflate_gameplay_or_teacher_budget(self):
        records = [{
            "winner": 0,
            "legal_action_count": 2,
            "chosen_action": 0,
            "executed_action": 0,
            "policy_target": [0.6, 0.4],
            "teacher_simulations": 64,
            "teacher_adaptive_simulations": 0,
            "teacher_action_values": [0.2, -0.1],
        }, {
            "winner": 0,
            "legal_action_count": 2,
            "chosen_action": 1,
            "executed_action": 1,
            "policy_target": [0.1, 0.9],
            "teacher_simulations": 64,
            "teacher_adaptive_simulations": 0,
            "teacher_action_values": [0.0, 0.1],
            "conditional": True,
            "conditional_trigger_depth": 3,
            "value_target": None,
            "value_target_valid": False,
            "conditional_target_top_action_agreement": 2 / 3,
            "conditional_target_mean_value_std": 0.12,
        }]
        statistics = GENERATOR.DatasetStatistics()
        statistics.add_game(records)

        result = statistics.result()
        self.assertEqual(2, result["training_decision_records"])
        self.assertEqual(1, result["conditional_decision_records"])
        self.assertEqual({"3": 1}, result["conditional_trigger_depth_counts"])
        self.assertEqual(1.0, result["mean_decisions_per_game"])
        self.assertEqual(64.0, result["teacher_policy"]["mean_simulations"])
        quality = result["conditional_target_quality"]
        self.assertEqual(1, quality["records_with_repeat_metrics"])
        self.assertAlmostEqual(2 / 3, quality["mean_top_action_agreement"])
        self.assertAlmostEqual(0.12, quality["mean_action_value_std"])

    def test_streaming_statistics_do_not_require_retaining_all_games(self):
        games = [
            [{
                "winner": 0,
                "legal_action_count": 2,
                "chosen_action": 0,
                "executed_action": 1,
                "policy_target": [0.75, 0.25],
                "teacher_simulations": 4,
                "teacher_adaptive_simulations": 0,
                "teacher_action_values": [0.5, -0.5],
            }],
            [{
                "winner": 1,
                "legal_action_count": 1,
                "chosen_action": 0,
                "executed_action": 0,
                "policy_target": None,
                "teacher_simulations": 0,
                "teacher_adaptive_simulations": 0,
                "teacher_action_values": [0.0],
            }],
        ]
        statistics = GENERATOR.DatasetStatistics()
        for game in games:
            statistics.add_game(game)

        result = statistics.result()
        self.assertEqual(2, statistics.records)
        self.assertEqual(
            {"player_0": 1, "player_1": 1, "draw": 0},
            result["winner_counts"],
        )
        self.assertEqual(1.0, result["mean_decisions_per_game"])
        self.assertEqual(1.5, result["mean_legal_actions"])
        self.assertEqual(0.5, result["forced_action_fraction"])
        self.assertEqual(1.0, result["teacher_behavior_disagreement_fraction"])
        self.assertEqual(4.0, result["teacher_policy"]["mean_simulations"])
        self.assertEqual(1.0, result["teacher_policy"]["mean_visited_value_range"])

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
