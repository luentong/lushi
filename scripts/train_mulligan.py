#!/usr/bin/env python3
"""Train/evaluate the standalone mulligan head; no in-game checkpoint changes."""

from __future__ import annotations

import argparse
from collections import defaultdict
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.mulligan import FEATURE_SCHEMA, FEATURE_WIDTH, TEACHER_VERSION, new_mulligan_network


def _metrics(rows: list[dict], predictions: list[int]) -> dict:
    if not rows:
        return {"records": 0}
    teacher_matches = 0
    model_regret = auto_regret = 0.0
    by_deck = defaultdict(lambda: [0, 0.0, 0.0])
    for row, choice in zip(rows, predictions, strict=True):
        label = row["teacher_mask"]
        scores = row["teacher_scores"]
        teacher_matches += choice == label
        regret = max(scores) - scores[choice]
        baseline = max(scores) - scores[row["automatic_mask"]]
        model_regret += regret
        auto_regret += baseline
        group = by_deck[row["deck_id"]]
        group[0] += 1
        group[1] += regret
        group[2] += baseline
    return {
        "records": len(rows),
        "teacher_agreement": teacher_matches / len(rows),
        "mean_proxy_regret": model_regret / len(rows),
        "automatic_mean_proxy_regret": auto_regret / len(rows),
        "by_deck": {
            deck: {"n": v[0], "model_regret": v[1] / v[0],
                   "automatic_regret": v[2] / v[0]}
            for deck, v in sorted(by_deck.items())
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--learning-rate", type=float, default=3e-4)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=20261013)
    args = parser.parse_args()
    if args.epochs < 1 or args.batch_size < 1:
        parser.error("epochs and batch size must be positive")
    import torch
    if args.device.startswith("npu"):
        import torch_npu  # noqa: F401

    rows = [json.loads(line) for line in args.data.read_text(encoding="utf-8").splitlines() if line]
    if not rows or any(
        row["schema"] != FEATURE_SCHEMA
        or row.get("teacher_version") != TEACHER_VERSION
        or len(row["features"]) != FEATURE_WIDTH
        for row in rows
    ):
        raise ValueError("empty or incompatible mulligan data")
    # Both seats of one game stay in the same split; validation seeds are never
    # used by the optimizer. This metric checks teacher imitation, not wins.
    train = [row for row in rows if row["seed"] % 5 != 0]
    valid = [row for row in rows if row["seed"] % 5 == 0]
    if not train or not valid:
        raise ValueError("need nonempty game-seed train and validation splits")
    torch.manual_seed(args.seed)
    model = new_mulligan_network().to(args.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    features = torch.tensor([r["features"] for r in train], dtype=torch.float32)
    labels = torch.tensor([r["teacher_mask"] for r in train], dtype=torch.long)
    legal_counts = torch.tensor([1 << len(r["offered"]) for r in train], dtype=torch.long)
    v_features = torch.tensor([r["features"] for r in valid], dtype=torch.float32, device=args.device)
    v_legal = torch.tensor([1 << len(r["offered"]) for r in valid], dtype=torch.long, device=args.device)
    indexes = torch.arange(16, device=args.device)
    best = None
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(1, args.epochs + 1):
        model.train()
        order = torch.randperm(len(train))
        losses = []
        for group in order.split(args.batch_size):
            batch_x = features[group].to(args.device)
            batch_y = labels[group].to(args.device)
            batch_n = legal_counts[group].to(args.device)
            logits = model(batch_x).masked_fill(indexes[None, :] >= batch_n[:, None], -1e9)
            loss = torch.nn.functional.cross_entropy(logits, batch_y)
            optimizer.zero_grad(set_to_none=True)
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        model.eval()
        with torch.no_grad():
            logits = model(v_features).masked_fill(indexes[None, :] >= v_legal[:, None], -1e9)
            predicted = logits.argmax(dim=1).cpu().tolist()
        metrics = _metrics(valid, predicted)
        print(json.dumps({"epoch": epoch, "train_loss": sum(losses) / len(losses),
                          "validation": {k: v for k, v in metrics.items() if k != "by_deck"}},
                         ensure_ascii=False), flush=True)
        rank = (metrics["mean_proxy_regret"], -metrics["teacher_agreement"])
        if best is None or rank < best:
            best = rank
            torch.save({"schema": FEATURE_SCHEMA, "teacher_version": TEACHER_VERSION,
                        "feature_width": FEATURE_WIDTH,
                        "model": {key: value.detach().cpu() for key, value in model.state_dict().items()},
                        "epoch": epoch,
                        "proxy_gate_passed": (
                            metrics["mean_proxy_regret"]
                            < metrics["automatic_mean_proxy_regret"]
                        ),
                        "validation": metrics}, args.output)
    best_payload = torch.load(args.output, map_location="cpu", weights_only=False)
    report = {"checkpoint": str(args.output), "best_epoch": best_payload["epoch"],
              "proxy_gate_passed": best_payload["proxy_gate_passed"],
              "validation": best_payload["validation"]}
    report_path = args.output.with_suffix(".metrics.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"checkpoint": str(args.output), "report": str(report_path),
                      "best_epoch": report["best_epoch"],
                      "proxy_gate_passed": report["proxy_gate_passed"],
                      "validation": {key: value for key, value in report["validation"].items()
                                     if key != "by_deck"}}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
