#!/usr/bin/env python3
"""Copy an epoch checkpoint with the inference flags used by its trained heads.

Older epoch checkpoint reports omitted these flags even though the complete
policy/value/action-Q tensors were saved.  Never change the original weights.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("output must differ from input; keep the original checkpoint")
    payload = torch.load(args.input, map_location="cpu", weights_only=False)
    report = payload["report"]
    architecture = report["model"]["architecture"]
    if "action-q" not in architecture:
        parser.error(f"checkpoint does not have an action-Q architecture: {architecture}")
    if not any(key.startswith("action_value_head.") for key in payload["model_state_dict"]):
        parser.error("checkpoint does not contain trained action-Q tensors")
    if report.get("value_trained") is False or report.get("action_value_trained") is False:
        parser.error("checkpoint explicitly marks a head as untrained")
    report["value_trained"] = True
    report["action_value_trained"] = True
    report["inference_flags_restored_from_epoch_checkpoint"] = True
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(payload, args.output)
    print(f"saved evaluation checkpoint: {args.output}")


if __name__ == "__main__":
    main()
