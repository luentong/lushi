"""Print compact checkpoint metadata without dumping tensor weights."""

from __future__ import annotations

import argparse
import pprint
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    args = parser.parse_args()
    payload = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    report = payload.get("report") if isinstance(payload.get("report"), dict) else payload
    feature_schema = report.get("feature_schema") or {}
    compact = {
        "model": report.get("model") or report.get("model_config"),
        "epoch": report.get("epoch"),
        "best_epoch": report.get("best_epoch"),
        "ruleset": report.get("ruleset"),
        "records": report.get("records"),
        "train_games": report.get("train_games"),
        "validation_games": report.get("validation_games"),
        "validation_metrics": report.get("validation_metrics") or report.get("validation"),
        "schema_version": feature_schema.get("schema_version"),
        "card_vocab_size": feature_schema.get("card_vocab_size"),
        "card_vocab_sha256": feature_schema.get("card_vocab_sha256"),
        "init_checkpoint": report.get("init_checkpoint"),
        "value_trained": report.get("value_trained"),
        "action_value_trained": report.get("action_value_trained"),
        "anchor_checkpoint": report.get("anchor_checkpoint"),
    }
    pprint.pp(compact)
    print("checkpoint_keys:", sorted(payload))


if __name__ == "__main__":
    main()
