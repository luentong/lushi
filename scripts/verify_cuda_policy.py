#!/usr/bin/env python3
"""Verify that a local policy checkpoint can safely run on CUDA."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.lineage import ruleset_manifest


def main() -> int:
    # Keep module import independent from a machine's optional accelerator
    # plugins. In particular, a Windows CUDA user must not need torch_npu.
    import torch

    from hsa import DragonMirrorGame
    from hsa.torch_model import TorchPolicyValueModel

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    args = parser.parse_args()

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is unavailable. Install a CUDA-enabled PyTorch wheel and "
            "confirm the NVIDIA driver with nvidia-smi."
        )
    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=False)
    report = checkpoint.get("report", {})
    manifest = ruleset_manifest(ROOT)
    if report.get("ruleset") != manifest["ruleset"]:
        raise RuntimeError(
            f"checkpoint ruleset {report.get('ruleset')!r} does not match "
            f"local source {manifest['ruleset']!r}"
        )
    if report.get("ruleset_fingerprint") != manifest["fingerprint_sha256"]:
        raise RuntimeError(
            "checkpoint source fingerprint does not match this checkout; "
            "use the matching commit or retrain the checkpoint"
        )

    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    game = DragonMirrorGame(args.cards, seed=202609112501)
    output = model.predict(game, game.legal_actions())
    print(json.dumps({
        "status": "ok",
        "device": str(model.device),
        "cuda_device_name": (
            torch.cuda.get_device_name(torch.device(args.device))
            if args.device.startswith("cuda") else None
        ),
        "ruleset": manifest["ruleset"],
        "ruleset_fingerprint": manifest["fingerprint_sha256"],
        "checkpoint": str(args.checkpoint),
        "legal_actions": len(game.legal_actions()),
        "prior_count": len(output.priors),
        "value": output.value,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
