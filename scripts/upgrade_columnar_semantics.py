#!/usr/bin/env python3
"""Upgrade schema-v5 columnar shards with ID-independent card semantics.

This transformation is lossless for the existing labels and tensors.  The
new card descriptors are derived from the frozen identity histograms and the
card catalog, so old multi-deck shards can train the v6 semantic model without
re-running games.  Unknown runtime IDs remain represented by their numeric
card semantics whenever present in the source catalog/vocabulary.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "src"))
from hsa.encoding import (  # noqa: E402
    CARD_SEMANTIC_FEATURE_SIZE, card_semantic_features,
)


def _card_matrix(vocab_ids: list[str], cards_path: Path) -> tuple[torch.Tensor, dict]:
    cards = json.loads(cards_path.read_text(encoding="utf-8"))
    by_id = {str(item.get("id")): item for item in cards if item.get("id")}
    matrix = torch.zeros((len(vocab_ids), CARD_SEMANTIC_FEATURE_SIZE), dtype=torch.float32)
    known = 0
    for index, card_id in enumerate(vocab_ids):
        card = by_id.get(card_id)
        if card is None:
            continue
        matrix[index] = torch.tensor(card_semantic_features(card), dtype=torch.float32)
        known += 1
    return matrix, {"vocabulary_size": len(vocab_ids), "catalog_matches": known,
                    "catalog_match_fraction": known / max(1, len(vocab_ids))}


def upgrade_shard(source: Path, target: Path, card_matrix: torch.Tensor) -> dict:
    shard = torch.load(source, map_location="cpu", weights_only=False)
    header = shard.get("header", {})
    schema = header.get("feature_schema", {})
    version = int(schema.get("schema_version", -1))
    if version == 6:
        target.parent.mkdir(parents=True, exist_ok=True)
        torch.save(shard, target)
        return {"status": "already_v6", "count": int(shard.get("count", 0))}
    if version not in (4, 5):
        raise ValueError(f"{source}: expected schema v4/v5, got {version}")
    vocab = int(schema["card_vocab_size"])
    if card_matrix.shape != (vocab, CARD_SEMANTIC_FEATURE_SIZE):
        raise ValueError(f"{source}: vocabulary and semantic matrix differ")
    states = shard["states"].to(torch.float32)
    actions = shard["actions"].to(torch.float32)
    old_state_width = (374 + 3 * vocab) if version == 4 else (376 + 4 * vocab)
    old_action_width = 56 + 2 * vocab
    if states.shape[1] != old_state_width or actions.shape[2] != old_action_width:
        raise ValueError(f"{source}: tensor sizes do not match v5 feature schema")
    hist_start = 24
    histogram_count = 3 if version == 4 else 4
    histograms = [states[:, hist_start + i * vocab:hist_start + (i + 1) * vocab]
                  for i in range(histogram_count)]
    if version == 4:
        # v4 did not observe own remaining-deck identities or the two
        # turn-damage counters. Insert explicit zeros at their versioned
        # positions; never infer hidden/consumed cards from a partial state.
        dynamic_start = 24 + 3 * vocab
        dynamic = states[:, dynamic_start:]
        dynamic_prefix, locations = dynamic[:, :322], dynamic[:, 322:]
        if locations.shape[1] != 28:
            raise ValueError(f"{source}: unexpected v4 dynamic-state width")
        deck_zeros = states.new_zeros((len(states), vocab))
        progress_zeros = states.new_zeros((len(states), 2))
        states = torch.cat((
            states[:, :dynamic_start], deck_zeros, dynamic_prefix,
            progress_zeros, locations,
        ), dim=1)
        histograms.append(deck_zeros)
    else:
        dynamic_start = 24 + 4 * vocab
        dynamic_end = dynamic_start + 352
        if dynamic_end > states.shape[1]:
            raise ValueError(f"{source}: unexpected v5 dynamic-state width")
    divisors = (10.0, 7.0, 7.0, 30.0)
    semantic_state = torch.cat([
        torch.matmul(histogram, card_matrix) / divisor
        for histogram, divisor in zip(histograms, divisors, strict=True)
    ], dim=1)

    source_cards = actions[..., 23:23 + vocab]
    target_start = 45 + vocab
    target_cards = actions[..., target_start:target_start + vocab]
    semantic_actions = torch.cat((
        torch.matmul(source_cards, card_matrix),
        torch.matmul(target_cards, card_matrix),
    ), dim=2)
    shard["states"] = torch.cat((states, semantic_state), dim=1).contiguous()
    shard["actions"] = torch.cat((actions, semantic_actions), dim=2).contiguous()
    schema = dict(schema)
    source_version = version
    schema["schema_version"] = 6
    schema["state_size"] = 376 + 4 * vocab + 4 * CARD_SEMANTIC_FEATURE_SIZE
    schema["action_size"] = old_action_width + 2 * CARD_SEMANTIC_FEATURE_SIZE
    schema["card_semantic_feature_size"] = CARD_SEMANTIC_FEATURE_SIZE
    schema["card_semantics"] = "type-class-race-mechanics-cost-stats-rarity-text-effect-v2"
    header = dict(header)
    header["feature_schema"] = schema
    header["semantic_upgrade"] = f"v{source_version}-to-v6-catalog-derived-text-effects-v2"
    if source_version == 4:
        header["v5_features_missing_in_source"] = [
            "actor_remaining_deck_histogram", "turn_damage_progress",
        ]
    shard["header"] = header
    target.parent.mkdir(parents=True, exist_ok=True)
    torch.save(shard, target)
    return {"status": "upgraded", "count": int(shard.get("count", len(states))),
            "state_size": int(shard["states"].shape[1]),
            "action_size": int(shard["actions"].shape[2])}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--max-shards", type=int)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    files = sorted(args.input_dir.rglob("*.pt"))
    if args.max_shards is not None:
        files = files[:args.max_shards]
    if not files:
        parser.error("no .pt shards found")
    sample = torch.load(files[0], map_location="cpu", weights_only=False)
    vocab_ids = sample["header"]["feature_schema"]["card_vocab_ids"]
    card_matrix, catalog_report = _card_matrix(vocab_ids, args.cards)
    rows = []
    for index, source in enumerate(files, 1):
        relative = source.relative_to(args.input_dir)
        target = args.output_dir / relative
        row = upgrade_shard(source, target, card_matrix)
        row["source"] = str(relative)
        rows.append(row)
        if index % 16 == 0 or index == len(files):
            summary = {"complete": False, "processed": index, "total": len(files),
                       "catalog": catalog_report, "rows": rows}
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"processed": index, "total": len(files),
                              "status": row["status"], "count": row["count"]}), flush=True)
    result = {"complete": True, "processed": len(rows), "total_records": sum(r["count"] for r in rows),
              "catalog": catalog_report, "rows": rows}
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
