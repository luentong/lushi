#!/usr/bin/env python3
"""Bounded one-shot entity pilot; isolated artifacts, no daemon or scheduler."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import itertools
import json
from pathlib import Path
import subprocess
import sys
import time
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]


def jobs_for(decks, repetitions, seed):
    return [(i, a, b, seed + i) for i, (a, b) in enumerate(
        pair for _ in range(repetitions) for pair in itertools.product(decks, repeat=2))]


def validated_reused_jobs(manifest, schedule):
    jobs = manifest["jobs"]
    actual = [(j["index"], j["deck_a"], j["deck_b"], j["seed"]) for j in jobs]
    if sorted(actual) != sorted(schedule) or any(j["exit_code"] != 0 for j in jobs):
        raise ValueError("reused data does not match the complete requested schedule")
    return [dict(job) for job in jobs]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--teacher-checkpoint", type=Path, required=True)
    parser.add_argument("--entity-init", type=Path, required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--devices", nargs="+", required=True)
    parser.add_argument("--repetitions", type=int, default=8)
    parser.add_argument("--seed", type=int, default=202609291000)
    parser.add_argument("--reset-value-head", action="store_true")
    parser.add_argument("--bootstrap-learning-rate", type=float, default=1e-5)
    parser.add_argument("--bootstrap-epochs", type=int, default=6)
    parser.add_argument("--ppo-rounds", type=int, default=8)
    parser.add_argument("--ppo-games-per-round", type=int, default=32)
    parser.add_argument("--reuse-teacher-manifest", type=Path,
                        help="Resume audited existing shards into a NEW output directory; never regenerate all games")
    args = parser.parse_args()
    if args.repetitions < 1 or len(args.devices) != len(set(args.devices)):
        parser.error("positive repetitions and unique devices required")
    if min(args.bootstrap_epochs, args.ppo_rounds, args.ppo_games_per_round) < 1 or args.bootstrap_learning_rate <= 0:
        parser.error("invalid training configuration")
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    decks = [item["id"] for item in json.loads(args.deck_config.read_text(encoding="utf-8"))["decks"]]
    jobs = jobs_for(decks, args.repetitions, args.seed)
    report = {"stage": "teacher", "started_at": time.time(), "jobs": [],
              "config": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              "teacher_games_requested": len(jobs), "strength_validated": False,
              "devices": args.devices, "source_sha256": {
                  str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                  for directory in (ROOT / "src/hsa", ROOT / "scripts")
                  for p in directory.rglob("*.py")}}
    manifest = args.output_dir / "pipeline.json"
    report_lock = Lock()

    def progress():
        temporary = manifest.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(manifest)

    def invoke(command, log, timeout=3600):
        with log.open("xb") as output:
            try:
                return subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                      stdout=output, stderr=subprocess.STDOUT,
                                      timeout=timeout).returncode
            except subprocess.TimeoutExpired:
                output.write(b"\nENGINEERING TIMEOUT: excluded, not a draw or loss.\n")
                return 124

    def worker(device, assigned):
        completed = []
        for index, a, b, seed in assigned:
            stem = args.output_dir / f"teacher-{index:04d}"
            data, log = stem.with_suffix(".jsonl.gz"), stem.with_suffix(".log")
            command = [sys.executable, "-u", str(ROOT / "scripts/generate_policy_value_data.py"),
                       "--games", "1", "--seed", str(seed), "--teacher", "ismcts",
                       "--samples", "2", "--iterations", "32", "--rollout-depth", "3",
                       "--teacher-checkpoint", str(args.teacher_checkpoint.resolve()),
                       "--teacher-device", device, "--teacher-value-mode", "prior-only",
                       "--export-observer-view", "--card-vocab", "expanded-executable",
                       "--workers", "1", "--max-actions", "400", "--deck-config",
                       str(args.deck_config.resolve()), "--deck-a", a, "--deck-b", b,
                       "--output", str(data), "--ruleset-label", "entity-v1-frozen-pilot"]
            code = invoke(command, log, timeout=900)
            result = {"index": index, "deck_a": a, "deck_b": b, "seed": seed,
                      "device": device, "exit_code": code, "data": str(data), "log": str(log)}
            completed.append(result)
            with report_lock:
                report["jobs"].append(result)
                progress()
            print(json.dumps({"stage": "teacher_game", **result}), flush=True)
        return completed

    progress()
    # Exactly one generator per selected NPU; each game is an independent shard.
    # A later failure cannot delete earlier completed games.
    if args.reuse_teacher_manifest:
        imported = json.loads(args.reuse_teacher_manifest.read_text(encoding="utf-8"))
        report["jobs"] = validated_reused_jobs(imported, jobs)
        report["reused_manifest_sha256"] = hashlib.sha256(args.reuse_teacher_manifest.read_bytes()).hexdigest()
        report["reused_teacher_provenance"] = {k: v for k, v in imported.items() if k != "jobs"}
        if not all(Path(j["data"]).is_file() for j in report["jobs"]):
            raise ValueError("missing reused shard")
        progress()
    else:
        with ThreadPoolExecutor(max_workers=len(args.devices)) as executor:
            futures = [executor.submit(worker, device, jobs[i::len(args.devices)])
                       for i, device in enumerate(args.devices)]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as exc:
                    with report_lock:
                        report.setdefault("worker_errors", []).append(f"{type(exc).__name__}: {exc}")
                        progress()
    successful = [j for j in report["jobs"] if j["exit_code"] == 0 and Path(j["data"]).exists()]
    if (len(successful) < (len(jobs) + 1) // 2 or
            {(j["deck_a"], j["deck_b"]) for j in successful} != set(itertools.product(decks, repeat=2))):
        report.update(stage="blocked", error="too few complete games or a missing ordered matchup")
        progress()
        return 1
    report.update(stage="dataset_audit", completed_teacher_games=len(successful))
    progress()
    from audit_entity_dataset import audit
    data_audit = audit([Path(j["data"]) for j in sorted(successful, key=lambda j: j["index"])])
    (args.output_dir / "dataset-audit.json").write_text(json.dumps(data_audit, indent=2), encoding="utf-8")
    if data_audit["status"] != "passed":
        report.update(stage="dataset_rejected", error="structural data audit failed; no training launched")
        progress()
        return 3
    report["stage"] = "bootstrap"
    progress()
    bootstrap = args.output_dir / "entity-bootstrap.pt"
    common = [sys.executable, "-u", str(ROOT / "scripts/train_entity_selfplay.py")]
    code = invoke(common + ["--mode", "bootstrap", "--data"] +
                  [j["data"] for j in sorted(successful, key=lambda j: j["index"])] +
                  ["--init-checkpoint", str(args.entity_init.resolve()), "--output", str(bootstrap),
                   "--device", args.devices[-1], "--epochs", str(args.bootstrap_epochs), "--batch-size", "8",
                   "--max-records", "50000", "--learning-rate", str(args.bootstrap_learning_rate), "--seed", str(args.seed),
                   "--deck-config", str(args.deck_config.resolve())] +
                  (["--reset-value-head"] if args.reset_value_head else []), args.output_dir / "bootstrap.log", timeout=14400)
    if code:
        report.update(stage="failed", failed_stage="bootstrap", exit_code=code)
        progress()
        return code
    training = json.loads(bootstrap.with_suffix(".report.json").read_text())
    if not training.get("bootstrap_gate", {}).get("passed"):
        report.update(stage="validation_rejected", bootstrap_gate=training.get("bootstrap_gate"),
                      error="bootstrap failed calibration/policy gate; no automatic PPO launch")
        progress()
        return 2
    selected = Path(training["selection"]["path"])
    if not selected.is_file():
        raise ValueError("selected bootstrap checkpoint is missing")
    report["selected_bootstrap"] = str(selected)
    report["selected_bootstrap_epoch"] = training["selection"]["epoch"]
    report["selected_value_status"] = training["selected_value_status"]
    report["stage"] = "ppo"
    progress()
    code = invoke(common + ["--mode", "ppo", "--init-checkpoint", str(selected),
                  "--output", str(args.output_dir / "entity-ppo.pt"),
                  "--device", args.devices[-1], "--rounds", str(args.ppo_rounds),
                  "--games-per-round", str(args.ppo_games_per_round),
                  "--epochs", "2", "--batch-size", "8", "--learning-rate", "2e-5",
                  "--max-actions", "400", "--seed", str(args.seed + 1000000),
                  "--deck-config", str(args.deck_config.resolve())], args.output_dir / "ppo.log", timeout=14400)
    report.update(stage="complete" if code == 0 else "failed", exit_code=code,
                  elapsed_seconds=time.time() - report["started_at"])
    progress()
    return code


if __name__ == "__main__":
    raise SystemExit(main())
