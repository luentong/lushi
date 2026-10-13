#!/usr/bin/env python3
"""Small policy-only conditional fine-tune with a frozen-policy replay anchor.

No terminal value is fabricated for a searched hypothetical branch. This is
an experiment; selection is by held-out games and an anchor-drift limit.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
from pathlib import Path
import random
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from audit_entity_dataset import check_decision
from train_entity_selfplay import load_observer_records, save, select_device


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def conditional_rows(paths, min_agreement, path_matchups=None):
    rows = []
    rejected = {"low_agreement": 0, "wrong_source": 0, "games_without_accepted_rows": 0}
    seen_seeds = set()
    for path in paths:
        path_seeds = set()
        accepted_here = 0
        with gzip.open(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                item = json.loads(line)
                if item.get("record_type") == "decision":
                    path_seeds.add(item["game_seed"])
                if not item.get("conditional"):
                    continue
                if item.get("conditional_target_source") not in (
                        "independent_public_belief_search",
                        "independent_public_belief_action_values"):
                    rejected["wrong_source"] += 1
                    continue
                agreement = item.get("conditional_target_top_action_agreement")
                if not isinstance(agreement, (int, float)) or agreement < min_agreement:
                    rejected["low_agreement"] += 1
                    continue
                check_decision(item, policy_only=True)
                rows.append({"view": item["observer_view"], "target": item["policy_target"],
                             "seed": item["game_seed"], "agreement": agreement,
                             "source": item["conditional_target_source"],
                             "matchup": (path_matchups or {}).get(Path(path), "unknown")})
                accepted_here += 1
        if len(path_seeds) != 1 or seen_seeds.intersection(path_seeds):
            raise ValueError("each conditional shard must have one distinct game seed")
        seen_seeds.update(path_seeds)
        if not accepted_here:
            rejected["games_without_accepted_rows"] += 1
    return rows, rejected


def policy_ce(model, rows, device):
    import torch
    from hsa.entity_model import collate_views
    logits, _ = model(collate_views([r["view"] for r in rows], model.card_ids, device))
    target = torch.zeros_like(logits)
    for index, row in enumerate(rows):
        values = row["target"]
        if len(values) != len(row["view"]["actions"]):
            raise ValueError("conditional action and label counts differ")
        target[index, :len(values)] = torch.tensor(values, device=device)
    return -(target * logits.log_softmax(-1)).sum(-1).mean()


def policy_top1_agreement(model, rows, device):
    from hsa.entity_model import collate_views
    logits, _ = model(collate_views([r["view"] for r in rows], model.card_ids, device))
    return sum(int(int(logits[i].argmax()) == max(
        range(len(row["target"])), key=row["target"].__getitem__))
        for i, row in enumerate(rows))


def anchor_drift(model, frozen, rows, device):
    import torch
    from hsa.entity_model import collate_views
    batch = collate_views([r["view"] for r in rows], model.card_ids, device)
    new_logits, new_value = model(batch)
    with torch.no_grad():
        old_logits, old_value = frozen(batch)
    old_prob = old_logits.softmax(-1)
    kl = (old_prob * (old_logits.log_softmax(-1) - new_logits.log_softmax(-1))).sum(-1).mean()
    value_mse = (new_value - old_value).square().mean()
    return kl, value_mse


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--init-checkpoint", type=Path, required=True)
    p.add_argument("--conditional-manifest", type=Path, required=True)
    p.add_argument("--root-manifest", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--epochs", type=int, default=3)
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--learning-rate", type=float, default=2e-6)
    p.add_argument("--min-agreement", type=float, default=0.75)
    p.add_argument("--anchor-records", type=int, default=256)
    p.add_argument("--anchor-kl-weight", type=float, default=0.5)
    p.add_argument("--anchor-value-weight", type=float, default=0.5)
    p.add_argument("--max-anchor-kl", type=float, default=0.02)
    p.add_argument("--max-anchor-value-mse", type=float, default=0.01)
    p.add_argument("--max-matchup-ce-increase", type=float, default=0.1)
    p.add_argument("--holdout-mod", type=int, default=5)
    p.add_argument("--holdout-rem", type=int, default=0)
    p.add_argument("--seed", type=int, default=20261003)
    args = p.parse_args()
    if (args.epochs < 1 or args.batch_size < 1 or args.anchor_records < 1
            or args.learning_rate <= 0 or args.holdout_mod < 2
            or not 0 <= args.holdout_rem < args.holdout_mod
            or not 0.5 <= args.min_agreement <= 1
            or min(args.anchor_kl_weight, args.anchor_value_weight,
                   args.max_anchor_kl, args.max_anchor_value_mse,
                   args.max_matchup_ce_increase) < 0):
        p.error("invalid corrective training configuration")
    if args.output.exists() or args.output.with_suffix(".report.json").exists():
        p.error("output exists; choose a new experiment name")
    conditional_manifest = json.loads(args.conditional_manifest.read_text())
    root_manifest = json.loads(args.root_manifest.read_text())
    conditional_jobs = sorted(conditional_manifest["jobs"], key=lambda j: j["index"])
    root_jobs = sorted(root_manifest["jobs"], key=lambda j: j["index"])
    if any(j["exit_code"] for j in conditional_jobs + root_jobs):
        raise ValueError("manifests must reference completed games only")
    conditional_paths = [Path(j["data"]) for j in conditional_jobs]
    root_paths = [Path(j["data"]) for j in root_jobs]
    matchup_by_path = {Path(j["data"]): f"{j['deck_a']}__{j['deck_b']}"
                       for j in conditional_jobs}
    conditional, rejected = conditional_rows(
        conditional_paths, args.min_agreement, matchup_by_path)
    train = [row for row in conditional if row["seed"] % args.holdout_mod != args.holdout_rem]
    valid = [row for row in conditional if row["seed"] % args.holdout_mod == args.holdout_rem]
    if len(train) < 16 or len(valid) < 4 or len({r["seed"] for r in train}) < 2:
        raise ValueError(f"insufficient independent conditional data: train={len(train)}, valid={len(valid)}")
    anchor, seen = load_observer_records(root_paths, args.anchor_records, args.seed)
    if len(anchor) < 16:
        raise ValueError("too few ordinary roots for policy-preservation anchor")

    import torch
    from hsa.entity_model import EntityPolicyValueNet
    torch.set_num_threads(2)
    torch.manual_seed(args.seed)
    device = select_device(args.device)
    payload = torch.load(args.init_checkpoint, map_location="cpu", weights_only=False)
    model = EntityPolicyValueNet.from_payload(payload).to(device).eval()
    frozen = copy.deepcopy(model).eval()
    for parameter in frozen.parameters():
        parameter.requires_grad_(False)
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report_path = args.output.with_suffix(".report.json")
    report = {"status": "running", "mode": "policy_only_conditional_correction",
              "started_at": time.time(), "history": [], "selected_epoch": 0,
              "train_rows": len(train), "validation_rows": len(valid),
              "train_games": len({r["seed"] for r in train}),
              "validation_games": len({r["seed"] for r in valid}),
              "train_rows_by_matchup": dict(Counter(r["matchup"] for r in train)),
              "validation_rows_by_matchup": dict(Counter(r["matchup"] for r in valid)),
              "anchor_rows": len(anchor), "anchor_seen": seen,
              "rejected_conditional": rejected, "strength_validated": False,
              "lineage_sha256": {"init": digest(args.init_checkpoint),
                                 "conditional_manifest": digest(args.conditional_manifest),
                                 "root_manifest": digest(args.root_manifest),
                                 "script": digest(Path(__file__))},
              "settings": {k: str(v) if isinstance(v, Path) else v
                           for k, v in vars(args).items()}}

    def progress():
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False))

    def validate():
        with torch.no_grad():
            def mean_ce(rows):
                sums = [(float(policy_ce(model, rows[i:i + args.batch_size], device)),
                         len(rows[i:i + args.batch_size]))
                        for i in range(0, len(rows), args.batch_size)]
                return sum(value * count for value, count in sums) / len(rows)
            validation_ce = mean_ce(valid)
            by_matchup = {
                matchup: mean_ce([row for row in valid if row["matchup"] == matchup])
                for matchup in sorted({row["matchup"] for row in valid})}
            top1_matches = sum(policy_top1_agreement(
                model, valid[i:i + args.batch_size], device)
                for i in range(0, len(valid), args.batch_size))
            drift = [anchor_drift(model, frozen, anchor[i:i + args.batch_size], device)
                     for i in range(0, len(anchor), args.batch_size)]
            def weighted(index):
                return sum(float(pair[index]) * min(args.batch_size, len(anchor) - i * args.batch_size)
                           for i, pair in enumerate(drift)) / len(anchor)
            return {"conditional_ce": validation_ce,
                    "conditional_top1_agreement": top1_matches / len(valid),
                    "conditional_ce_by_matchup": by_matchup,
                    "anchor_kl": weighted(0), "anchor_value_mse": weighted(1)}

    initial = validate()
    report["initial_validation"] = initial
    best_ce = initial["conditional_ce"]
    best_path = args.output.with_suffix(".best.pt")
    save(model, optimizer, best_path, report)
    progress()
    stale = 0
    rng = random.Random(args.seed)
    for epoch in range(1, args.epochs + 1):
        rng.shuffle(train)
        losses = []
        for start in range(0, len(train), args.batch_size):
            batch = train[start:start + args.batch_size]
            replay = rng.sample(anchor, min(len(anchor), len(batch)))
            optimizer.zero_grad(set_to_none=True)
            loss = policy_ce(model, batch, device)
            kl, value_mse = anchor_drift(model, frozen, replay, device)
            objective = loss + args.anchor_kl_weight * kl + args.anchor_value_weight * value_mse
            if not torch.isfinite(objective):
                raise ValueError("non-finite corrective loss")
            objective.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            losses.append(float(objective.detach()))
        metrics = validate()
        accepted = (metrics["conditional_ce"] < best_ce - 1e-5
                    and metrics["anchor_kl"] <= args.max_anchor_kl
                    and metrics["anchor_value_mse"] <= args.max_anchor_value_mse
                    and all(
                        value <= initial["conditional_ce_by_matchup"][matchup]
                        + args.max_matchup_ce_increase
                        for matchup, value in metrics["conditional_ce_by_matchup"].items()
                    ))
        report["history"].append({"epoch": epoch, "train_objective": sum(losses) / len(losses),
                                  "validation": metrics, "accepted": accepted})
        if accepted:
            best_ce, stale = metrics["conditional_ce"], 0
            report["selected_epoch"] = epoch
            save(model, optimizer, best_path, report)
        else:
            stale += 1
        save(model, optimizer, args.output.with_suffix(f".epoch{epoch}.pt"), report)
        progress()
        print(json.dumps({"epoch": epoch, "validation": metrics,
                          "selected_epoch": report["selected_epoch"]}), flush=True)
        if stale >= 2:
            report["early_stopped"] = True
            break
    report.update(status="complete", elapsed_seconds=time.time() - report["started_at"],
                  policy_holdout_improved=report["selected_epoch"] > 0,
                  selected_checkpoint=str(best_path))
    progress()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
