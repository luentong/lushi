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
    from hsa.torch_model import TorchPolicyValueModel, load_checkpoint

    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--allow-legacy-checkpoint", action="store_true",
                        help="Allow a checkpoint created before ruleset provenance was recorded; report it as legacy.")
    args = parser.parse_args()

    if args.device.startswith("cuda") and not torch.cuda.is_available():
        raise RuntimeError(
            "CUDA is unavailable. Install a CUDA-enabled PyTorch wheel and "
            "confirm the NVIDIA driver with nvidia-smi."
        )
    checkpoint = load_checkpoint(str(args.checkpoint))
    report = checkpoint.get("report", {})
    manifest = ruleset_manifest(ROOT)
    checkpoint_ruleset = report.get("ruleset")
    checkpoint_fingerprint = report.get("ruleset_fingerprint")
    legacy = not checkpoint_ruleset or not checkpoint_fingerprint
    if legacy and not args.allow_legacy_checkpoint:
        raise RuntimeError(
            "checkpoint predates ruleset provenance; rerun with "
            "--allow-legacy-checkpoint only for advisory inference"
        )
    if not legacy and checkpoint_ruleset != manifest["ruleset"]:
        raise RuntimeError(
            f"checkpoint ruleset {checkpoint_ruleset!r} does not match "
            f"local source {manifest['ruleset']!r}"
        )
    if not legacy and checkpoint_fingerprint != manifest["fingerprint_sha256"]:
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
        "provenance_status": "legacy_allowed" if legacy else "exact_match",
        "checkpoint": str(args.checkpoint),
        "legal_actions": len(game.legal_actions()),
        "prior_count": len(output.priors),
        "value": output.value,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
