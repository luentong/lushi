from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from columnize_pt_shards import columnize
from hsa.encoding import CARD_SEMANTIC_FEATURE_SIZE, CARD_VOCAB, feature_schema
from hsa.torch_model import StructuredResidualPolicyValueNet
from train_columnar_policy_value import _is_held_out_deck_shard, _load_checkpoint_weights
from reindex_columnar_vocab import reindex_shard


class ActionValueTargetTests(unittest.TestCase):
    def test_deck_variant_holdout_matches_exact_matchup_id(self):
        held_out = {"dragon_hunter_user_02"}
        self.assertTrue(_is_held_out_deck_shard(
            Path("dragon_warrior__dragon_hunter_user_02.jsonl.part00000.pt"),
            held_out,
        ))
        self.assertFalse(_is_held_out_deck_shard(
            Path("dragon_warrior__dragon_hunter.jsonl.part00000.pt"), held_out,
        ))
        self.assertFalse(_is_held_out_deck_shard(
            Path("dragon_warrior__dragon_warrior.jsonl.part00000.pt"), held_out,
        ))

    def test_semantic_shard_vocab_reindex_preserves_dynamic_features_and_labels(self):
        source_schema = feature_schema(6)
        source_ids = list(source_schema["card_vocab_ids"])
        target_schema = dict(source_schema)
        target_ids = source_ids + ["TEST_EXTRA_A", "TEST_EXTRA_B"]
        target_vocab = len(target_ids)
        target_schema["card_vocab_ids"] = target_ids
        target_schema["card_vocab_size"] = target_vocab
        target_schema["state_size"] += 4 * 2
        target_schema["action_size"] += 2 * 2
        count, legal = 2, 3
        source_states = torch.arange(
            count * int(source_schema["state_size"]), dtype=torch.float32
        ).reshape(count, int(source_schema["state_size"]))
        source_actions = torch.arange(
            count * legal * int(source_schema["action_size"]), dtype=torch.float32
        ).reshape(count, legal, int(source_schema["action_size"]))
        source = {
            "header": {"feature_schema": source_schema},
            "count": count,
            "states": source_states,
            "actions": source_actions,
            "values": torch.tensor([0.25, -0.5]),
            "chosen": torch.tensor([1, 2]),
        }
        result = reindex_shard(source, target_schema)
        self.assertEqual((count, int(target_schema["state_size"])),
                         tuple(result["states"].shape))
        self.assertEqual((count, legal, int(target_schema["action_size"])),
                         tuple(result["actions"].shape))
        self.assertTrue(torch.equal(source["states"][:, :24], result["states"][:, :24]))
        self.assertTrue(torch.equal(source["actions"][..., :23], result["actions"][..., :23]))
        self.assertTrue(torch.equal(source["values"], result["values"]))
        self.assertTrue(torch.equal(source["chosen"], result["chosen"]))
        self.assertTrue(torch.equal(
            source["states"][:, 24 + 4 * len(source_ids):],
            result["states"][:, 24 + 4 * len(target_ids):],
        ))

    def test_columnizer_keeps_q_estimates_aligned_and_masks_unvisited(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pt"
            target = root / "columnar" / "source.pt"
            torch.save({"records": [{
                "state": [0.0, 1.0],
                "actions": [[1.0], [2.0], [3.0]],
                "chosen_action": 1,
                "value_target": 0.0,
                "teacher_action_values": [-0.5, 0.25, 0.9],
                "teacher_action_visits": [4, 0, 9],
            }]}, source)
            self.assertEqual(1, columnize(source, target))
            shard = torch.load(target, map_location="cpu", weights_only=False)
            self.assertEqual([-0.5, 0.25], shard["action_values"][0, :2].tolist())
            self.assertAlmostEqual(0.9, float(shard["action_values"][0, 2]), places=6)
            self.assertEqual([4, 0, 9], shard["action_value_visits"][0].tolist())
            self.assertEqual([True, False, True], shard["action_value_mask"][0].tolist())

    def test_columnizer_preserves_opponent_view_for_value_training(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, target = root / "source.pt", root / "out" / "source.pt"
            torch.save({"records": [{
                "state": [0.0, 1.0],
                "opponent_value_state": [1.0, 0.0],
                "actions": [[1.0]], "chosen_action": 0,
                "value_target": 1.0, "opponent_value_target": -1.0,
            }, {
                "state": [1.0, 0.0], "actions": [[1.0]],
                "chosen_action": 0, "value_target": None,
                "value_target_valid": False,
            }]}, source)
            self.assertEqual(2, columnize(source, target))
            shard = torch.load(target, map_location="cpu", weights_only=False)
            self.assertEqual([1.0, 0.0], shard["opponent_value_states"][0].tolist())
            self.assertEqual([True, False], shard["opponent_value_valid"].tolist())

    def test_action_value_head_is_bounded_and_masks_padding(self):
        vocab = len(CARD_VOCAB)
        model = StructuredResidualPolicyValueNet(
            374 + 3 * vocab, 56 + 2 * vocab,
            hidden_size=32, action_hidden_size=16, residual_blocks=1,
            card_vocab_size=vocab, card_embedding_size=8,
        )
        states = torch.zeros((2, model.state_size))
        actions = torch.zeros((2, 3, model.action_size))
        mask = torch.tensor([[True, True, False], [True, False, False]])
        logits, values, q_values = model.forward_with_action_values(states, actions, mask)
        self.assertEqual((2, 3), tuple(logits.shape))
        self.assertEqual((2,), tuple(values.shape))
        self.assertEqual((2, 3), tuple(q_values.shape))
        self.assertTrue(bool((q_values.abs() <= 1).all()))
        self.assertEqual(0.0, float(q_values[0, 2].detach()))
        self.assertEqual(0.0, float(q_values[1, 1].detach()))

    def test_old_structured_checkpoint_loads_with_new_head_left_trainable(self):
        vocab = len(CARD_VOCAB)
        model = StructuredResidualPolicyValueNet(
            374 + 3 * vocab, 56 + 2 * vocab,
            hidden_size=32, action_hidden_size=16, residual_blocks=1,
            card_vocab_size=vocab, card_embedding_size=8,
        )
        old_state = {
            key: value for key, value in model.state_dict().items()
            if not key.startswith("action_value_head.")
        }
        migration = _load_checkpoint_weights(
            model,
            {"model_state_dict": old_state, "report": {}},
            {"schema_version": 5},
        )
        self.assertEqual("exact+new-action-value-head", migration)
        self.assertTrue(all(p.requires_grad for p in model.action_value_head.parameters()))

    def test_v4_checkpoint_migrates_to_semantic_v6_without_shape_drift(self):
        vocab = len(CARD_VOCAB)
        old_model = StructuredResidualPolicyValueNet(
            374 + 3 * vocab, 56 + 2 * vocab,
            hidden_size=32, action_hidden_size=16, residual_blocks=1,
            card_vocab_size=vocab, card_embedding_size=8,
        )
        target_schema = feature_schema(6)
        model = StructuredResidualPolicyValueNet(
            int(target_schema["state_size"]), int(target_schema["action_size"]),
            hidden_size=32, action_hidden_size=16, residual_blocks=1,
            card_vocab_size=vocab, card_embedding_size=8,
        )
        old_state = {
            key: value for key, value in old_model.state_dict().items()
            if not key.startswith("action_value_head.")
        }
        migration = _load_checkpoint_weights(
            model,
            {"model_state_dict": old_state,
             "report": {"feature_schema": feature_schema(4)}},
            target_schema,
        )
        self.assertIn("v4-to-v6", migration)
        self.assertEqual(CARD_SEMANTIC_FEATURE_SIZE,
                         target_schema["card_semantic_feature_size"])
        states = torch.zeros((1, model.state_size))
        actions = torch.zeros((1, 1, model.action_size))
        logits, values, q = model.forward_with_action_values(states, actions)
        self.assertEqual((1, 1), tuple(logits.shape))
        self.assertEqual((1,), tuple(values.shape))
        self.assertEqual((1, 1), tuple(q.shape))

    def test_v6_checkpoint_widens_semantics_without_changing_old_features(self):
        vocab = len(CARD_VOCAB)
        embed, hidden, action_hidden = 8, 32, 16
        old_semantics = 90
        old_schema = dict(feature_schema(6))
        new_schema = feature_schema(6)
        old_schema["card_semantic_feature_size"] = old_semantics
        old_schema["card_semantics"] = "type-class-race-mechanics-cost-stats-rarity-v1"
        old_schema["state_size"] += 4 * (old_semantics - int(new_schema["card_semantic_feature_size"]))
        old_schema["action_size"] += 2 * (old_semantics - int(new_schema["card_semantic_feature_size"]))
        old_model = StructuredResidualPolicyValueNet(
            int(old_schema["state_size"]), int(old_schema["action_size"]),
            hidden_size=hidden, action_hidden_size=action_hidden,
            residual_blocks=1, card_vocab_size=vocab,
            card_embedding_size=embed,
        )
        model = StructuredResidualPolicyValueNet(
            int(new_schema["state_size"]), int(new_schema["action_size"]),
            hidden_size=hidden, action_hidden_size=action_hidden,
            residual_blocks=1, card_vocab_size=vocab,
            card_embedding_size=embed,
        )
        migration = _load_checkpoint_weights(
            model,
            {"model_state_dict": old_model.state_dict(),
             "report": {"feature_schema": old_schema}},
            new_schema,
        )
        self.assertTrue(migration.startswith("v6-semantic-widening"))
        self.assertTrue(torch.equal(
            model.semantic_state_projection[0].weight[:, :4 * old_semantics],
            old_model.semantic_state_projection[0].weight,
        ))
        self.assertTrue(torch.equal(
            model.semantic_state_projection[0].weight[:, 4 * old_semantics:],
            torch.zeros_like(model.semantic_state_projection[0].weight[:, 4 * old_semantics:]),
        ))
        states = torch.zeros((1, model.state_size))
        actions = torch.zeros((1, 2, model.action_size))
        logits, values, q = model.forward_with_action_values(states, actions)
        self.assertEqual((1, 2), tuple(logits.shape))
        self.assertEqual((1,), tuple(values.shape))
        self.assertEqual((1, 2), tuple(q.shape))


if __name__ == "__main__":
    unittest.main()
