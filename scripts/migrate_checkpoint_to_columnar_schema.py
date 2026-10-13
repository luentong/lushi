#!/usr/bin/env python3
"""Widen a structured checkpoint to match a target columnar schema."""
from __future__ import annotations

import argparse
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from train_columnar_policy_value import _load_checkpoint_weights  # noqa: E402
from hsa.torch_model import StructuredResidualPolicyValueNet  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--target-shard", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    shard = torch.load(args.target_shard, map_location="cpu", weights_only=False)
    schema = shard["header"]["feature_schema"]
    metadata = checkpoint["report"]["model"]
    model = StructuredResidualPolicyValueNet(
        int(schema["state_size"]), int(schema["action_size"]),
        int(metadata["hidden_size"]), int(metadata["action_hidden_size"]),
        int(metadata.get("residual_blocks", 8)),
        int(schema["card_vocab_size"]),
        int(metadata.get("card_embedding_size", 256)),
    )
    migration = _load_checkpoint_weights(model, checkpoint, schema)
    report = dict(checkpoint["report"])
    report["feature_schema"] = schema
    report["model"] = model.metadata()
    report["checkpoint_migration"] = migration
    report["migrated_from"] = str(args.checkpoint)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save({"model_state_dict": model.state_dict(), "report": report}, args.output)
    print({"migration": migration, "output": str(args.output),
           "state_size": model.state_size, "action_size": model.action_size})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
