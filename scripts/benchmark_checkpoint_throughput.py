#!/usr/bin/env python3
"""Measure fixed-shape checkpoint forward throughput on CPU or Ascend NPU.

This deliberately benchmarks the model only, separating network throughput
from the much slower Python rules engine and MCTS expansion loop.
"""
from __future__ import annotations
import argparse, json, time
from pathlib import Path
import torch
from hsa.torch_model import TorchPolicyValueModel

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--batch-sizes", type=int, nargs="+", default=[1, 16, 64, 256])
    p.add_argument("--legal-actions", type=int, nargs="+", default=[32, 64])
    p.add_argument("--warmup", type=int, default=5)
    p.add_argument("--iterations", type=int, default=50)
    args = p.parse_args()
    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    model.model.eval()
    state_size, action_size = model.model.state_size, model.model.action_size
    rows = []
    for batch in args.batch_sizes:
        for legal in args.legal_actions:
            states = torch.randn(batch, state_size, device=args.device)
            actions = torch.randn(batch, legal, action_size, device=args.device)
            mask = torch.ones(batch, legal, dtype=torch.bool, device=args.device)
            with torch.no_grad():
                for _ in range(args.warmup):
                    model.model.forward_with_action_values(states, actions, mask)
                if args.device.startswith("npu"):
                    torch.npu.synchronize()
                start = time.perf_counter()
                for _ in range(args.iterations):
                    model.model.forward_with_action_values(states, actions, mask)
                if args.device.startswith("npu"):
                    torch.npu.synchronize()
            elapsed = time.perf_counter() - start
            rows.append({"batch": batch, "legal_actions": legal,
                         "calls_per_second": args.iterations / elapsed,
                         "states_per_second": args.iterations * batch / elapsed,
                         "milliseconds_per_call": elapsed * 1000 / args.iterations})
    print(json.dumps({"checkpoint": str(args.checkpoint), "device": args.device,
                      "state_size": state_size, "action_size": action_size,
                      "results": rows}, indent=2))

if __name__ == "__main__":
    main()
