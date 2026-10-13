#!/usr/bin/env python3
"""Bounded, resumable multi-deck PPO run with frozen development/confirmation.

Each round uses fresh on-policy games. Historical models are training opponents,
not deployment approvals. Low development scores do not truncate the budget.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "src")]


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_json(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")
    temporary.replace(path)


def training_command(args, checkpoints, output):
    offset = len(checkpoints)
    command = [sys.executable, "-u", str(ROOT / "scripts/train_entity_selfplay.py"),
        "--mode", "ppo", "--init-checkpoint", str(checkpoints[-1] if checkpoints else args.init_checkpoint),
        "--output", str(output), "--device", args.device, "--deck-config", str(args.deck_config),
        "--seed", str(args.seed), "--rounds", "1", "--games-per-round", str(args.games_per_round),
        "--rollout-workers", str(args.workers), "--inference-batch-size", str(args.inference_batch_size),
        "--batch-size", str(args.batch_size), "--epochs", str(args.epochs),
        "--learning-rate", str(args.learning_rate), "--max-actions", str(args.max_actions),
        "--opponent-pool-size", str(args.opponent_pool_size), "--advantage-mode", "terminal"]
    command += ["--kl-guard", getattr(args, "kl_guard", "minibatch"),
                "--kl-probe-size", str(getattr(args, "kl_probe_size", 256)),
                "--kl-check-interval", str(getattr(args, "kl_check_interval", 100))]
    if offset:
        command += ["--round-offset", str(offset), "--anchor-checkpoint", str(args.init_checkpoint),
                    "--history-checkpoint"] + [str(p) for p in checkpoints]
    return command


def disjoint_seed_ranges(seed, rounds, dev_seed, confirm_seed, deck_count, development_pairs):
    return (seed + rounds * 100003 < dev_seed and
            dev_seed + deck_count * deck_count * max(1, development_pairs) < confirm_seed)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--init-checkpoint", type=Path, required=True)
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--device", default="npu:2")
    p.add_argument("--eval-device", default="npu:3")
    p.add_argument("--rounds", type=int, default=32)
    p.add_argument("--games-per-round", type=int, default=1024)
    p.add_argument("--workers", type=int, default=16)
    p.add_argument("--inference-batch-size", type=int, default=32)
    p.add_argument("--batch-size", type=int, default=32)
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--learning-rate", type=float, default=1e-5)
    p.add_argument("--kl-guard", choices=("minibatch", "probe"), default="minibatch")
    p.add_argument("--kl-probe-size", type=int, default=256)
    p.add_argument("--kl-check-interval", type=int, default=100)
    p.add_argument("--opponent-pool-size", type=int, default=8)
    p.add_argument("--max-actions", type=int, default=400)
    p.add_argument("--seed", type=int, default=202703010000)
    p.add_argument("--dev-seed", type=int, default=202801010000)
    p.add_argument("--confirm-seed", type=int, default=202901010000)
    p.add_argument("--evaluate-every", type=int, default=8)
    p.add_argument("--development-pairs", type=int, default=2)
    p.add_argument("--confirmation-pairs", type=int, default=8)
    p.add_argument("--resume", action="store_true")
    args = p.parse_args()
    if args.kl_probe_size < 1 or args.kl_check_interval < 1:
        p.error("KL probe settings must be positive")
    if min(args.rounds, args.games_per_round, args.workers, args.batch_size, args.epochs,
           args.inference_batch_size, args.opponent_pool_size, args.max_actions, args.evaluate_every) < 1:
        p.error("counts must be positive")
    if min(args.development_pairs, args.confirmation_pairs) < 0:
        p.error("evaluation counts cannot be negative")
    if not 0 < args.learning_rate < 1 or args.games_per_round * 3 >= 100003:
        p.error("invalid learning rate or overlapping round seeds")
    for field in ("init_checkpoint", "deck_config", "output_dir"):
        setattr(args, field, getattr(args, field).resolve())
    deck_count = len(json.loads(args.deck_config.read_text(encoding="utf-8"))["decks"])
    if not disjoint_seed_ranges(args.seed, args.rounds, args.dev_seed, args.confirm_seed,
                                deck_count, args.development_pairs):
        p.error("training/development/confirmation seed ranges must be disjoint and ordered")
    config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items() if k != "resume"}
    sources = list((ROOT / "src/hsa").rglob("*.py")) + [ROOT / "scripts" / name for name in (
        "run_entity_scale.py", "train_entity_selfplay.py", "entity_parallel_rollout.py",
        "evaluate_entity_policy.py", "compare_entity_evaluations.py", "benchmark_mcts.py", "ppo_kl_probe.py")]
    provenance = {str(path): digest(path) for path in sources + [args.deck_config, args.init_checkpoint,
                                                              ROOT / "cards.251332.enUS.json"]}
    args.output_dir.mkdir(parents=True, exist_ok=True)
    # Linux training host: OS releases this lock even after a process crash.
    import fcntl
    lock = (args.output_dir / "pipeline.lock").open("a")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        p.error("this run already has an active coordinator")
    manifest = args.output_dir / "pipeline.json"
    if manifest.exists():
        if not args.resume:
            p.error("run exists; use --resume with the original configuration")
        report = json.loads(manifest.read_text(encoding="utf-8"))
        if report["config"] != config or report["provenance"] != provenance:
            p.error("configuration/source/input changed; use a new run directory")
    else:
        report = {"config": config, "provenance": provenance, "started_at": time.time(),
                  "rounds": [], "evaluations": [], "attempts": [], "strength_validated": False,
                  "planned_training_games": args.rounds * args.games_per_round,
                  "deck_count": deck_count, "status": "starting"}

    def progress(**updates):
        report.update(updates, updated_at=time.time())
        atomic_json(manifest, report)

    def invoke(command, log):
        if any(digest(path) != expected for path, expected in provenance.items()):
            raise ValueError("frozen source/input changed while coordinator was running")
        with log.open("xb") as output:
            child = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                     stdout=output, stderr=subprocess.STDOUT,
                                     env={**os.environ, "PYTHONHASHSEED": "0", "OMP_NUM_THREADS": "2",
                                          "MKL_NUM_THREADS": "2"})
            progress(child_pid=child.pid, current_log=str(log), current_command=command)
            try:
                code = child.wait()
            except BaseException:
                child.terminate()
                child.wait()
                raise
        progress(child_pid=None)
        if code:
            raise RuntimeError(f"child exit {code}; inspect {log}")

    def evaluate(checkpoint, label, split, pairs, seed):
        old = next((e for e in report["evaluations"] if e["label"] == label), None)
        if old:
            if digest(old["path"]) != old["sha256"]:
                raise ValueError("saved evaluation changed")
            return Path(old["path"])
        attempt = 1
        while (args.output_dir / f"{label}-attempt{attempt}").exists():
            attempt += 1
        directory = args.output_dir / f"{label}-attempt{attempt}"
        progress(status="evaluating", evaluation_label=label)
        invoke([sys.executable, "-u", str(ROOT / "scripts/evaluate_entity_policy.py"),
                "--candidate", str(checkpoint), "--opponent-kind", "entity",
                "--opponent", str(args.init_checkpoint), "--device", args.eval_device,
                "--deck-config", str(args.deck_config), "--pairs-per-matchup", str(pairs),
                "--seed", str(seed), "--max-actions", str(args.max_actions), "--split", split,
                "--output", str(directory)], args.output_dir / f"{label}-attempt{attempt}.log")
        path = directory / "evaluation.json"
        result = json.loads(path.read_text(encoding="utf-8"))
        if result["status"] != "complete":
            raise ValueError("incomplete evaluation; excluded from candidate selection")
        report["evaluations"].append({"label": label, "path": str(path), "sha256": digest(path)})
        progress()
        return path

    def compare_at(checkpoint, label, split, pairs, seed):
        from compare_entity_evaluations import compare
        baseline = evaluate(args.init_checkpoint, f"{split}-baseline", split, pairs, seed)
        candidate = evaluate(checkpoint, label, split, pairs, seed)
        delta = compare(json.loads(candidate.read_text(encoding="utf-8")),
                        json.loads(baseline.read_text(encoding="utf-8")))
        atomic_json(args.output_dir / f"{label}-comparison.json", delta)
        return delta

    try:
        progress(status="running", coordinator_pid=os.getpid())
        checkpoints = []
        for item in report["rounds"]:
            if item["round"] != len(checkpoints) + 1 or digest(item["checkpoint"]) != item["sha256"]:
                raise ValueError("round checkpoint sequence/hash changed")
            checkpoints.append(Path(item["checkpoint"]))
        for round_number in range(1, args.rounds + 1):
            if round_number > len(checkpoints):
                attempt = 1
                stem = f"round-{round_number:03d}-attempt{attempt}"
                while (args.output_dir / f"{stem}.log").exists():
                    attempt += 1
                    stem = f"round-{round_number:03d}-attempt{attempt}"
                output = args.output_dir / f"{stem}.pt"
                command = training_command(args, checkpoints, output)
                report["attempts"].append({"round": round_number, "attempt": attempt, "output": str(output)})
                progress(status="training", current_round=round_number)
                invoke(command, args.output_dir / f"{stem}.log")
                child_report = json.loads(output.with_suffix(".report.json").read_text(encoding="utf-8"))
                history = child_report["history"]
                if (child_report["status"] != "complete" or len(history) != 1 or
                        history[0]["round"] != round_number or
                        len(history[0]["games"]) != args.games_per_round):
                    raise ValueError("round report does not contain the required complete collection/update")
                item = {"round": round_number, "checkpoint": str(output), "sha256": digest(output),
                        "report": str(output.with_suffix(".report.json")), "rows": history[0]["rows"],
                        "failures": len(child_report["failures"]), "seconds": child_report["elapsed_seconds"],
                        "collection": history[0].get("collection"),
                        "kl_early_stopped": history[0]["kl_early_stopped"]}
                report["rounds"].append(item)
                checkpoints.append(output)
                progress(completed_training_games=len(checkpoints) * args.games_per_round)
                print(json.dumps({"completed_round": round_number, "planned_rounds": args.rounds,
                                  "training_games": len(checkpoints) * args.games_per_round}), flush=True)
            item = report["rounds"][round_number - 1]
            if args.development_pairs and (round_number % args.evaluate_every == 0 or round_number == args.rounds):
                delta = compare_at(checkpoints[round_number - 1], f"dev-round{round_number}",
                                   "development", args.development_pairs, args.dev_seed)
                item["development_delta"] = delta["mean_score_delta"]
                progress()
        candidates = [r for r in report["rounds"] if "development_delta" in r]
        selected = max(candidates, key=lambda r: (r["development_delta"], -r["round"])) if candidates else report["rounds"][-1]
        progress(selected_round=selected["round"], selected_checkpoint=selected["checkpoint"],
                 selection="development_score_delta" if candidates else "fixed_final_round")
        if args.confirmation_pairs:
            delta = compare_at(Path(selected["checkpoint"]), "confirmation-selected", "confirmation",
                               args.confirmation_pairs, args.confirm_seed)
            report["confirmation"] = {k: v for k, v in delta.items() if k != "paired_games"}
        progress(status="complete", automatic_promotion=False, elapsed_seconds=time.time() - report["started_at"])
        return 0
    except BaseException as exc:
        progress(status="failed", error=f"{type(exc).__name__}: {exc}")
        raise
    finally:
        lock.close()


if __name__ == "__main__":
    raise SystemExit(main())
