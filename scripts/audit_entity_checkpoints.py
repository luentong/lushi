#!/usr/bin/env python3
"""Evaluate frozen entity checkpoints on the original game-level holdout.

No resplitting, training, or promotion. Cache CPU batches once across checkpoints.
Terminal labels measure calibration under the teacher's continuation, not strength.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def summarize_predictions(rows, training_win_probability):
    if not rows:
        raise ValueError("empty evaluation split")
    games = defaultdict(list)
    for row in rows:
        games[row["seed"]].append(row)
    mean = lambda values: sum(values) / len(values)
    return {
        "rows": len(rows), "games": len(games),
        "brier": mean([r["brier"] for r in rows]),
        "game_macro_brier": mean([mean([r["brier"] for r in g]) for g in games.values()]),
        "policy_ce": mean([r["policy_ce"] for r in rows]),
        "policy_accuracy": mean([r["policy_correct"] for r in rows]),
        "target_win_probability": mean([r["target"] for r in rows]),
        "predicted_win_probability": mean([r["prediction"] for r in rows]),
        "neutral_brier": mean([(0.5 - r["target"]) ** 2 for r in rows]),
        "train_constant_brier": mean([(training_win_probability - r["target"]) ** 2 for r in rows]),
        "confident_wrong_fraction": mean([float(abs(r["prediction"] - r["target"]) > 0.9) for r in rows]),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--checkpoints", type=Path, nargs="+", required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--holdout-mod", type=int, default=5)
    p.add_argument("--holdout-rem", type=int, default=0)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        p.error("output exists")
    import torch
    from audit_entity_dataset import committed_paths
    from train_entity_selfplay import load_observer_records, select_device, file_digest
    from hsa.entity_model import EntityPolicyValueNet, collate_views
    torch.set_num_threads(2)
    device = select_device(args.device)
    paths = committed_paths(json.loads(args.manifest.read_text()))
    rows, seen = load_observer_records(paths, 100000, 0)
    if seen != len(rows):
        raise ValueError("audit requires full dataset, not a reservoir subset")
    train = [r for r in rows if r["seed"] % args.holdout_mod != args.holdout_rem]
    if not train:
        raise ValueError("empty training split")
    base_rate = sum((r["value"] + 1) / 2 for r in train) / len(train)
    first = EntityPolicyValueNet.from_payload(torch.load(args.checkpoints[0], map_location="cpu", weights_only=False))
    vocabulary = first.card_ids
    del first
    batches = []
    for i in range(0, len(rows), args.batch_size):
        batch_rows = rows[i:i + args.batch_size]
        batches.append((batch_rows, collate_views([r["view"] for r in batch_rows], vocabulary)))
    report = {"status": "running", "split": "original_game_seed_modulo", "holdout_mod": args.holdout_mod,
              "holdout_rem": args.holdout_rem, "data_sha256": {str(p): file_digest(p) for p in paths},
              "train_constant_probability": base_rate, "checkpoints": [], "strength_validated": False}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for path in args.checkpoints:
        model = EntityPolicyValueNet.from_payload(torch.load(path, map_location="cpu", weights_only=False))
        if model.card_ids != vocabulary:
            raise ValueError("cannot reuse encoded batches with a different vocabulary")
        model.to(device).eval()
        results = []
        with torch.no_grad():
            for batch_rows, batch in batches:
                logits, values = model({k: v.to(device) for k, v in batch.items()})
                logp, value = logits.log_softmax(-1).cpu(), values.cpu().tolist()
                for i, row in enumerate(batch_rows):
                    target = torch.tensor(row["target"], dtype=torch.float32)
                    target = target / target.sum()
                    probability = (value[i] + 1) / 2
                    truth = (row["value"] + 1) / 2
                    results.append({"seed": row["seed"], "turn": row["view"]["turn"],
                                    "class": row["view"]["players"][0]["tags"]["card_class"],
                                    "target": truth, "prediction": probability, "brier": (probability - truth) ** 2,
                                    "policy_ce": float(-(target * logp[i, :len(target)]).sum()),
                                    "policy_correct": float(int(logp[i].argmax()) == int(target.argmax()))})
        item = {"path": str(path), "sha256": file_digest(path)}
        for split in ("train", "validation"):
            subset = [r for r in results if (r["seed"] % args.holdout_mod == args.holdout_rem) == (split == "validation")]
            item[split] = summarize_predictions(subset, base_rate)
            item[split + "_by_game"] = {str(seed): summarize_predictions([r for r in subset if r["seed"] == seed], base_rate)
                                              for seed in sorted({r["seed"] for r in subset})}
            item[split + "_by_phase"] = {
                phase: summarize_predictions(part, base_rate)
                for phase, part in (("opening", [r for r in subset if r["turn"] <= 6]),
                                    ("later", [r for r in subset if r["turn"] > 6])) if part}
        report["checkpoints"].append(item)
        args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps({"checkpoint": str(path), "train": item["train"], "validation": item["validation"]}), flush=True)
        del model
    report["status"] = "complete"
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
