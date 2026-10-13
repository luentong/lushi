#!/usr/bin/env python3
"""Linearly interpolate compatible policy/value checkpoints.

The base checkpoint remains the metadata/schema authority. Floating-point model
parameters and buffers are blended as ``base + alpha * (candidate - base)``;
non-floating tensors must be identical and are copied from the base model.
"""

from __future__ import annotations

import argparse
import copy
from pathlib import Path

import torch


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--alpha", required=True, type=float)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    if not 0.0 <= args.alpha <= 1.0:
        parser.error("--alpha must be between 0 and 1")

    base = torch.load(args.base, map_location="cpu", weights_only=False)
    candidate = torch.load(args.candidate, map_location="cpu", weights_only=False)
    base_state = base["model_state_dict"]
    candidate_state = candidate["model_state_dict"]
    if base_state.keys() != candidate_state.keys():
        missing = sorted(base_state.keys() - candidate_state.keys())
        extra = sorted(candidate_state.keys() - base_state.keys())
        raise SystemExit(f"incompatible state dictionaries: missing={missing}, extra={extra}")

    blended = {}
    for name, base_tensor in base_state.items():
        candidate_tensor = candidate_state[name]
        if base_tensor.shape != candidate_tensor.shape:
            raise SystemExit(
                f"shape mismatch for {name}: {tuple(base_tensor.shape)} != "
                f"{tuple(candidate_tensor.shape)}"
            )
        if torch.is_floating_point(base_tensor):
            blended[name] = torch.lerp(base_tensor, candidate_tensor, args.alpha)
        else:
            if not torch.equal(base_tensor, candidate_tensor):
                raise SystemExit(f"non-floating tensor differs: {name}")
            blended[name] = base_tensor.clone()

    output = copy.deepcopy(base)
    output["model_state_dict"] = blended
    report = output.setdefault("report", {})
    report["interpolation"] = {
        "base": str(args.base),
        "candidate": str(args.candidate),
        "alpha": args.alpha,
    }
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    torch.save(output, destination)
    print(f"saved {destination} ({destination.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
