#!/usr/bin/env python3
"""Direct policy/value training from columnar tensor shards."""
from __future__ import annotations

import argparse
import json
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from train_policy_value import choose_device
from hsa.encoding import compatible_feature_schema
from hsa.torch_model import StructuredResidualPolicyValueNet


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--data", nargs="+", type=Path, required=True)
    p.add_argument(
        "--priority-data", nargs="*", type=Path, default=(),
        help=("Optional higher-quality shards to mix into every epoch. "
              "They are repeated according to --priority-repeat rather than "
              "used as a post-hoc fine-tuning-only dataset."),
    )
    p.add_argument(
        "--priority-repeat", type=int, default=1,
        help="How many times each --priority-data shard appears per epoch (>= 1).",
    )
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--init-checkpoint", type=Path,
                   help="Resume model weights from a compatible columnar checkpoint.")
    p.add_argument("--device", choices=("cpu", "npu"), default="npu")
    p.add_argument("--epochs", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=256)
    p.add_argument("--hidden-size", type=int, default=1024)
    p.add_argument("--action-hidden-size", type=int, default=512)
    p.add_argument("--residual-blocks", type=int, default=8)
    p.add_argument("--card-embedding-size", type=int, default=256)
    p.add_argument("--learning-rate", type=float, default=2e-4)
    p.add_argument("--value-weight", type=float, default=.15)
    p.add_argument("--checkpoint-every", type=int, default=0,
                   help="Write an epoch checkpoint every N epochs (0 disables).")
    p.add_argument("--max-shards", type=int)
    p.add_argument("--exclude-mod", type=int)
    p.add_argument("--exclude-rem", type=int, default=0)
    p.add_argument("--seed", type=int, default=1)
    args = p.parse_args()

    if args.priority_repeat < 1:
        p.error("--priority-repeat must be at least 1")
    base_files = sorted(args.data)
    if args.max_shards is not None:
        base_files = base_files[:args.max_shards]
    priority_files = sorted(args.priority_data)
    files = base_files + priority_files * args.priority_repeat
    if not files:
        p.error("at least one training shard is required")
    random.Random(args.seed).shuffle(files)
    first = torch.load(files[0], map_location="cpu", weights_only=False)
    schema = first["header"]["feature_schema"]
    model = StructuredResidualPolicyValueNet(
        int(schema["state_size"]), int(schema["action_size"]), args.hidden_size,
        args.action_hidden_size, args.residual_blocks,
        int(schema["card_vocab_size"]), args.card_embedding_size,
    )
    resumed_from = None
    if args.init_checkpoint is not None:
        checkpoint = torch.load(args.init_checkpoint, map_location="cpu", weights_only=False)
        previous = checkpoint.get("report", {})
        previous_schema = previous.get("feature_schema")
        if previous_schema is not None and not compatible_feature_schema(previous_schema, schema):
            raise ValueError(
                "checkpoint feature schema differs from the input shards; "
                "run a vocabulary/schema migration before incremental training"
            )
        model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        resumed_from = str(args.init_checkpoint)
    device = choose_device(args.device)
    model.to(device)
    opt = torch.optim.AdamW(model.parameters(), lr=args.learning_rate, weight_decay=1e-2)
    started = time.perf_counter(); history = []; total_rows = 0

    def checkpoint(path: Path, *, final: bool) -> None:
        report = {"records": total_rows, "epochs": len(history), "history": history,
                  "elapsed_seconds": time.perf_counter() - started, "device": str(device),
                  "feature_schema": schema, "model": model.metadata(),
                  "resumed_from": resumed_from, "final": final,
                  "base_shards": len(base_files), "priority_shards": len(priority_files),
                  "priority_repeat": args.priority_repeat}
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"model_state_dict": model.state_dict(), "report": report}, path)
        path.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")

    for epoch in range(1, args.epochs + 1):
        model.train(); loss_sum = 0.; batches = 0
        random.Random(args.seed + epoch).shuffle(files)
        for path in files:
            shard = torch.load(path, map_location="cpu", weights_only=False)
            n = int(shard["count"])
            eligible = torch.arange(n)
            if args.exclude_mod is not None:
                eligible = eligible[(shard["game_seed"].abs() % args.exclude_mod) != args.exclude_rem]
            if not len(eligible):
                continue
            total_rows += len(eligible) if epoch == 1 else 0
            order = eligible[torch.randperm(len(eligible))]
            for start in range(0, n, args.batch_size):
                ix = order[start:start + args.batch_size]
                states = shard["states"][ix].to(device)
                actions = shard["actions"][ix].to(device)
                mask = shard["mask"][ix].to(device)
                targets = shard["values"][ix].to(device)
                policy_targets = shard["policy_targets"][ix].to(device)
                chosen = shard["chosen"][ix].to(device)
                # Older decisions can contain shortened/zero policy targets.
                # Restore a one-hot teacher target and skip malformed empty
                # action rows so one record cannot poison the full run.
                valid = mask.any(dim=1)
                if not bool(valid.any().item()):
                    continue
                states, actions, mask = states[valid], actions[valid], mask[valid]
                targets, policy_targets, chosen = (
                    targets[valid], policy_targets[valid], chosen[valid]
                )
                policy_targets = torch.nan_to_num(policy_targets)
                sums = policy_targets.sum(dim=1, keepdim=True)
                missing = sums.squeeze(1) <= 0
                if bool(missing.any().item()):
                    policy_targets[missing] = 0
                    policy_targets[missing, chosen[missing]] = 1
                    sums = policy_targets.sum(dim=1, keepdim=True)
                policy_targets = policy_targets / sums.clamp_min(1e-12)
                logits, values = model(states, actions, mask)
                rows = -(policy_targets * F.log_softmax(logits, dim=1)).sum(dim=1)
                nontrivial = mask.sum(dim=1) > 1
                policy = rows[nontrivial].mean() if bool(nontrivial.any()) else rows.sum() * 0
                loss = policy + args.value_weight * F.mse_loss(values, targets)
                opt.zero_grad(set_to_none=True); loss.backward()
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                opt.step()
                loss_sum += float(loss.detach()); batches += 1
        history.append({"epoch": epoch, "loss": loss_sum / max(1, batches)})
        print(json.dumps(history[-1]), flush=True)
        if args.checkpoint_every and epoch % args.checkpoint_every == 0:
            suffix = args.output.suffix
            checkpoint(args.output.with_name(f"{args.output.stem}.epoch{epoch}{suffix}"), final=False)
    if device.type == "npu": torch.npu.synchronize()
    checkpoint(args.output, final=True)

if __name__ == "__main__": main()
