#!/usr/bin/env python3
"""Smoke-test a policy/value checkpoint on Ascend NPU.

This deliberately exercises the complete path: catalog -> game state ->
legal actions -> checkpoint-backed policy/value inference.  It is intended for
the 910B/910C training host, not for gameplay automation.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--device", default="npu:0")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=2026100500)
    args = parser.parse_args()

    import torch

    from hsa.dragon_mirror import DragonMirrorGame
    from hsa.torch_model import TorchPolicyValueModel

    if not args.device.startswith("npu"):
        raise RuntimeError("this smoke test is for an Ascend device, e.g. npu:0")
    if not getattr(torch, "npu", None) or not torch.npu.is_available():
        raise RuntimeError("torch.npu is unavailable; source the CANN environment first")

    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    rows: list[dict[str, object]] = []
    for offset in range(args.runs):
        game = DragonMirrorGame(args.cards, seed=args.seed + offset)
        actions = game.legal_actions()
        started = time.perf_counter()
        output = model.predict(game, actions)
        elapsed = time.perf_counter() - started
        rows.append({
            "seed": args.seed + offset,
            "legal_actions": len(actions),
            "prior_count": len(output.priors),
            "value": float(output.value),
            "seconds": elapsed,
        })

    print(json.dumps({
        "status": "ok",
        "device": str(model.device),
        "runs": rows,
        "mean_seconds": sum(float(row["seconds"]) for row in rows) / len(rows),
        "steady_state_seconds": (
            sum(float(row["seconds"]) for row in rows[1:]) / max(1, len(rows) - 1)
        ),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
