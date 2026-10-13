#!/usr/bin/env python3
"""Reindex schema-v6 columnar tensors into a shared frozen card vocabulary."""
from __future__ import annotations

import argparse
from pathlib import Path

import torch


def _copy_histogram(source: torch.Tensor, target: torch.Tensor,
                    source_ids: list[str], target_ids: list[str]) -> None:
    index = {card_id: i for i, card_id in enumerate(target_ids)}
    for source_index, card_id in enumerate(source_ids):
        target_index = index.get(card_id)
        if target_index is not None:
            target[..., target_index] = source[..., source_index]


def reindex_shard(shard: dict, target_schema: dict) -> dict:
    header = shard["header"]
    source_schema = header["feature_schema"]
    if int(source_schema.get("schema_version", -1)) != 6:
        raise ValueError("only schema-v6 shards are supported")
    if int(target_schema.get("schema_version", -1)) != 6:
        raise ValueError("target schema must be version 6")
    for field in ("action_kinds", "action_player_encoding", "action_target_zone",
                  "card_semantics", "card_semantic_feature_size"):
        if source_schema.get(field) != target_schema.get(field):
            raise ValueError(f"incompatible schema field: {field}")

    source_ids = list(source_schema["card_vocab_ids"])
    target_ids = list(target_schema["card_vocab_ids"])
    source_vocab, target_vocab = len(source_ids), len(target_ids)
    source_state = shard["states"]
    source_actions = shard["actions"]
    semantic_width = 4 * int(source_schema["card_semantic_feature_size"])
    state_dynamic_width = source_state.shape[1] - 24 - 4 * source_vocab - semantic_width
    target_dynamic_width = int(target_schema["state_size"]) - 24 - 4 * target_vocab - semantic_width
    if state_dynamic_width != target_dynamic_width:
        raise ValueError("dynamic state feature width differs")
    if source_actions.shape[-1] != 56 + 2 * source_vocab + 2 * int(source_schema["card_semantic_feature_size"]):
        raise ValueError("source action tensor width differs from its schema")
    if int(target_schema["action_size"]) != 56 + 2 * target_vocab + 2 * int(target_schema["card_semantic_feature_size"]):
        raise ValueError("target action tensor width differs from its schema")

    target_states = source_state.new_zeros((len(source_state), int(target_schema["state_size"])))
    target_states[:, :24] = source_state[:, :24]
    source_semantic_start = 24 + 4 * source_vocab + state_dynamic_width
    target_semantic_start = 24 + 4 * target_vocab + target_dynamic_width
    for role in range(4):
        src = source_state[:, 24 + role * source_vocab:24 + (role + 1) * source_vocab]
        dst = target_states[:, 24 + role * target_vocab:24 + (role + 1) * target_vocab]
        _copy_histogram(src, dst, source_ids, target_ids)
    source_dynamic_start = 24 + 4 * source_vocab
    target_dynamic_start = 24 + 4 * target_vocab
    target_states[:, target_dynamic_start:target_dynamic_start + state_dynamic_width] = (
        source_state[:, source_dynamic_start:source_dynamic_start + state_dynamic_width]
    )
    target_states[:, target_semantic_start:] = source_state[:, source_semantic_start:]

    target_actions = source_actions.new_zeros(
        (*source_actions.shape[:-1], int(target_schema["action_size"]))
    )
    target_actions[..., :23] = source_actions[..., :23]
    src_pos_start = 23 + source_vocab
    dst_pos_start = 23 + target_vocab
    _copy_histogram(source_actions[..., 23:src_pos_start],
                    target_actions[..., 23:dst_pos_start], source_ids, target_ids)
    target_actions[..., dst_pos_start:dst_pos_start + 10] = (
        source_actions[..., src_pos_start:src_pos_start + 10]
    )
    src_target_prefix = src_pos_start + 10
    dst_target_prefix = dst_pos_start + 10
    target_actions[..., dst_target_prefix:dst_target_prefix + 12] = (
        source_actions[..., src_target_prefix:src_target_prefix + 12]
    )
    src_target_card = src_target_prefix + 12
    dst_target_card = dst_target_prefix + 12
    _copy_histogram(source_actions[..., src_target_card:src_target_card + source_vocab],
                    target_actions[..., dst_target_card:dst_target_card + target_vocab],
                    source_ids, target_ids)
    source_tail = src_target_card + source_vocab
    target_tail = dst_target_card + target_vocab
    target_actions[..., target_tail:] = source_actions[..., source_tail:]

    result = dict(shard)
    result["states"] = target_states.contiguous()
    result["actions"] = target_actions.contiguous()
    result_header = dict(header)
    result_header["feature_schema"] = target_schema
    result_header["vocabulary_reindex"] = {
        "source_size": source_vocab,
        "target_size": target_vocab,
        "preserved_card_ids": sum(card_id in set(target_ids) for card_id in source_ids),
    }
    result["header"] = result_header
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--target-shard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    source = torch.load(args.input, map_location="cpu", weights_only=False)
    target = torch.load(args.target_shard, map_location="cpu", weights_only=False)
    upgraded = reindex_shard(source, target["header"]["feature_schema"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(upgraded, args.output)
    print({"records": int(upgraded["count"]),
           "source_vocab": upgraded["header"]["vocabulary_reindex"]["source_size"],
           "target_vocab": upgraded["header"]["vocabulary_reindex"]["target_size"],
           "state_shape": list(upgraded["states"].shape),
           "action_shape": list(upgraded["actions"].shape)})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
