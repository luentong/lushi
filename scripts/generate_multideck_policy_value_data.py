#!/usr/bin/env python3
"""Generate a frequency-weighted pooled dataset across configured deck pairs.

Each ordered pair is generated separately so player-0/player-1 asymmetry is
visible to the learner.  The resulting JSON manifest is also the audit trail
for which deck pairs contributed to a checkpoint.
"""

from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import math
import os
import queue
import random
import signal
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEACHER_DEVICE_TOKEN = "__TEACHER_DEVICE__"


def allocate_counts(
    weights: list[float], total: int, minimum: int,
    tie_break_seed: int | None = None,
) -> list[int]:
    if total < len(weights) * minimum:
        raise ValueError(
            f"total games ({total}) must be at least {len(weights) * minimum} "
            f"for {len(weights)} ordered pairs"
        )
    counts = [minimum] * len(weights)
    remaining = total - sum(counts)
    if not remaining:
        return counts
    scale = remaining / sum(weights)
    raw = [weight * scale for weight in weights]
    floors = [math.floor(value) for value in raw]
    counts = [count + floor for count, floor in zip(counts, floors)]
    tie_order = list(range(len(weights)))
    if tie_break_seed is not None:
        random.Random(tie_break_seed).shuffle(tie_order)
    tie_rank = {index: rank for rank, index in enumerate(tie_order)}
    for index in sorted(
        range(len(weights)),
        key=lambda item: (-(raw[item] - floors[item]), tie_rank[item]),
    )[: remaining - sum(floors)]:
        counts[index] += 1
    return counts


def _record_failed_future(
    records: list[dict], futures: dict, future: object, error: Exception,
) -> int:
    """Keep parallel job errors attached to their manifest index."""
    index = futures[future]
    records[index]["status"] = "failed"
    records[index]["error"] = str(error)
    return index


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--config", type=Path,
        default=ROOT / "config" / "decks_20260920_multi.json",
    )
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "reports" / "multideck_data")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports" / "multideck_training_manifest.json")
    parser.add_argument("--total-games", type=int, default=1024)
    parser.add_argument("--min-games-per-pair", type=int, default=2)
    parser.add_argument("--seed", type=int, default=202609200000)
    parser.add_argument(
        "--seed-stride", type=int, default=10007,
        help="Coprime stride between ordered deck-pair seed ranges."
    )
    parser.add_argument("--teacher-samples", type=int, default=2)
    parser.add_argument("--teacher-iterations", type=int, default=32)
    parser.add_argument(
        "--mulligan-mode", choices=("automatic", "teacher", "model"),
        default="automatic",
    )
    parser.add_argument("--mulligan-checkpoint", type=Path)
    parser.add_argument("--mulligan-device", default="cpu")
    parser.add_argument("--rollout-depth", type=int, default=3)
    parser.add_argument(
        "--teacher-checkpoint", type=Path,
        help="Optional checkpoint used for neural-prior/value ISMCTS self-play.",
    )
    parser.add_argument(
        "--teacher-devices", default="",
        help=(
            "Comma-separated devices assigned round-robin to concurrent matchup "
            "jobs, for example npu:0,npu:1."
        ),
    )
    parser.add_argument(
        "--teacher-value-mode", choices=("prior-only", "trained"),
        default="trained",
    )
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument(
        "--exclude-deck", action="append", default=[],
        help="Deck id to omit from this corpus (repeatable); retained in the manifest.",
    )
    parser.add_argument(
        "--parallel-jobs", type=int, default=1,
        help="Run independent ordered deck-pair jobs concurrently. Each job still uses --workers processes.",
    )
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument(
        "--job-timeout-seconds", type=int,
        help=(
            "Hard wall-clock limit for one independent matchup process. "
            "Timed-out jobs are recorded as failed when --continue-on-error is set, "
            "so one pathological game cannot stall an entire corpus."
        ),
    )
    parser.add_argument("--ruleset-label", default="standard-multideck-runtime-v2")
    parser.add_argument(
        "--card-vocab", choices=("legacy", "expanded-executable", "frozen-file"),
        default="expanded-executable",
    )
    parser.add_argument("--card-vocab-file", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--continue-on-error", action="store_true",
        help="Finish independent matchup jobs and record failures in the manifest."
    )
    parser.add_argument(
        "--resume", action="store_true",
        help="Skip matchup outputs that already exist and resume an interrupted corpus."
    )
    args = parser.parse_args()
    if args.mulligan_mode == "model" and args.mulligan_checkpoint is None:
        parser.error("--mulligan-mode model requires --mulligan-checkpoint")
    if args.card_vocab == "frozen-file" and args.card_vocab_file is None:
        parser.error("--card-vocab frozen-file requires --card-vocab-file")
    if args.seed_stride <= 0:
        parser.error("--seed-stride must be positive")
    if args.job_timeout_seconds is not None and args.job_timeout_seconds <= 0:
        parser.error("--job-timeout-seconds must be positive")
    teacher_devices = [
        item.strip() for item in args.teacher_devices.split(",") if item.strip()
    ]
    if args.teacher_checkpoint is not None:
        if not args.teacher_checkpoint.is_file():
            parser.error(f"teacher checkpoint does not exist: {args.teacher_checkpoint}")
        if not teacher_devices:
            parser.error("--teacher-checkpoint requires --teacher-devices")
        if args.workers != 1:
            parser.error("neural checkpoint self-play requires --workers 1")
    elif teacher_devices:
        parser.error("--teacher-devices requires --teacher-checkpoint")

    config = json.loads(args.config.read_text(encoding="utf-8"))
    excluded_decks = set(args.exclude_deck)
    known_ids = {deck["id"] for deck in config["decks"]}
    unknown_exclusions = excluded_decks - known_ids
    if unknown_exclusions:
        raise ValueError(f"unknown --exclude-deck IDs: {sorted(unknown_exclusions)}")
    decks = [deck for deck in config["decks"] if deck["id"] not in excluded_decks]
    if not decks:
        raise ValueError("deck config contains no decks")
    ids = [deck["id"] for deck in decks]
    if len(set(ids)) != len(ids):
        raise ValueError("deck IDs must be unique")
    weights = [float(deck.get("frequency_weight", 1.0)) for deck in decks]
    jobs = [
        (left, right, weights[left_index] * weights[right_index])
        for left_index, left in enumerate(ids)
        for right_index, right in enumerate(ids)
    ]
    counts = allocate_counts(
        [job[2] for job in jobs], args.total_games, args.min_games_per_pair,
        tie_break_seed=args.seed,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    child_log_dir = args.output_dir / "_logs"
    child_log_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for index, ((deck_a, deck_b, weight), games) in enumerate(zip(jobs, counts)):
        output = args.output_dir / f"{deck_a}__{deck_b}.jsonl.gz"
        command = [
            sys.executable, str(ROOT / "scripts" / "generate_policy_value_data.py"),
            "--games", str(games), "--seed", str(args.seed + index * args.seed_stride),
            "--teacher", "ismcts", "--samples", str(args.teacher_samples),
            "--iterations", str(args.teacher_iterations),
            "--rollout-depth", str(args.rollout_depth),
            "--behavior", "teacher", "--workers", str(args.workers),
            "--max-actions", str(args.max_actions),
            "--card-vocab", args.card_vocab,
            "--ruleset-label", args.ruleset_label,
            "--cards", str(args.cards), "--deck-config", str(args.config),
            "--deck-a", deck_a, "--deck-b", deck_b,
            "--output", str(output),
            "--mulligan-mode", args.mulligan_mode,
        ]
        if args.mulligan_checkpoint is not None:
            command.extend(("--mulligan-checkpoint", str(args.mulligan_checkpoint),
                            "--mulligan-device", args.mulligan_device))
        if args.card_vocab_file is not None:
            command.extend(("--card-vocab-file", str(args.card_vocab_file)))
        if args.teacher_checkpoint is not None:
            command.extend((
                "--teacher-checkpoint", str(args.teacher_checkpoint),
                "--teacher-device", TEACHER_DEVICE_TOKEN,
                "--teacher-value-mode", args.teacher_value_mode,
            ))
        records.append({
            "deck_a": deck_a, "deck_b": deck_b, "games": games,
            "frequency_weight": weight, "output": str(output),
            "log": str(child_log_dir / f"{deck_a}__{deck_b}.log"),
            "command": command, "status": "planned",
        })
    if args.resume:
        for job in records:
            if Path(job["output"]).is_file() and Path(job["output"]).stat().st_size > 0:
                job["status"] = "complete"
    manifest = {
        "schema_version": 1,
        "config": str(args.config),
        "excluded_decks": sorted(excluded_decks),
        "total_games": args.total_games,
        "min_games_per_pair": args.min_games_per_pair,
        "seed": args.seed,
        "seed_stride": args.seed_stride,
        "job_timeout_seconds": args.job_timeout_seconds,
        "resume": args.resume,
        "mulligan": {
            "mode": args.mulligan_mode,
            "checkpoint": str(args.mulligan_checkpoint) if args.mulligan_checkpoint else None,
        },
        "teacher": {
            "samples": args.teacher_samples,
            "iterations_per_sample": args.teacher_iterations,
            "simulations_per_decision": args.teacher_samples * args.teacher_iterations,
            "rollout_depth": args.rollout_depth,
            "checkpoint": (
                str(args.teacher_checkpoint) if args.teacher_checkpoint else None
            ),
            "devices": teacher_devices,
            "value_mode": args.teacher_value_mode,
        },
        "card_vocab": {
            "mode": args.card_vocab,
            "file": str(args.card_vocab_file) if args.card_vocab_file else None,
        },
        "ruleset": args.ruleset_label,
        "model": {
            "architecture": "structured-v5",
            "hidden_size": 1024,
            "action_hidden_size": 512,
            "residual_blocks": 8,
            "card_embedding_size": 256,
            "policy_target": "visits",
            "policy_weight": 1.0,
            "value_weight": 0.15,
            "batch_size": 512,
            "epochs": 20,
            "early_stopping_patience": 4,
            "early_stopping_metric": "joint",
            "inference_default": "policy-only PUCT until value head passes held-out evaluation",
        },
        "jobs": records,
    }
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    if args.dry_run:
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        return 0

    started = time.perf_counter()
    device_pool: queue.Queue[str] = queue.Queue()
    for teacher_device in teacher_devices:
        device_pool.put(teacher_device)

    def run_job(index: int) -> int:
        teacher_device = device_pool.get() if teacher_devices else None
        try:
            command = [
                teacher_device if item == TEACHER_DEVICE_TOKEN else item
                for item in records[index]["command"]
            ]
            if teacher_device is not None:
                records[index]["teacher_device"] = teacher_device
            with Path(records[index]["log"]).open("wb") as child_log:
                if args.job_timeout_seconds is None:
                    subprocess.run(
                        command, cwd=ROOT, check=True,
                        stdout=child_log, stderr=subprocess.STDOUT,
                    )
                    return index
                # Each matchup generator in turn creates worker processes.  A plain
                # subprocess timeout only kills its direct parent and leaks those
                # workers, so launch a separate session and explicitly terminate its
                # whole process group on timeout.  The child's atomic temp-file writer
                # ensures incomplete data is never promoted to the final output path.
                process = subprocess.Popen(
                    command, cwd=ROOT, start_new_session=True,
                    stdout=child_log, stderr=subprocess.STDOUT,
                )
                try:
                    return_code = process.wait(timeout=args.job_timeout_seconds)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGTERM)
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid, signal.SIGKILL)
                        process.wait()
                    raise subprocess.TimeoutExpired(
                        command, args.job_timeout_seconds
                    )
                if return_code:
                    raise subprocess.CalledProcessError(return_code, command)
                return index
        finally:
            if teacher_device is not None:
                device_pool.put(teacher_device)

    parallel_jobs = max(1, min(args.parallel_jobs, len(records)))
    pending_indices = [
        index for index, job in enumerate(records) if job["status"] != "complete"
    ]
    if parallel_jobs == 1:
        for index in pending_indices:
            job = records[index]
            job["status"] = "running"
            args.manifest.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            try:
                run_job(index)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                if not args.continue_on_error:
                    raise
                job["status"] = "failed"
                job["error"] = str(exc)
            else:
                job["status"] = "complete"
            args.manifest.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
    else:
        # Pair jobs are independent and write disjoint output files.  Running
        # a bounded number concurrently keeps the 910B CPU pool busy while
        # preserving one manifest as the audit trail.  With --continue-on-
        # error, failures are explicit manifest entries while unaffected
        # matchups continue, making simulator-coverage repair resumable.
        for index in pending_indices:
            records[index]["status"] = "running"
        args.manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        with ThreadPoolExecutor(max_workers=parallel_jobs) as executor:
            futures = {
                executor.submit(run_job, index): index for index in pending_indices
            }
            for future in as_completed(futures):
                index = futures[future]
                try:
                    records[future.result()]["status"] = "complete"
                except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as exc:
                    if not args.continue_on_error:
                        for remaining in futures:
                            remaining.cancel()
                        raise
                    # Associate the failure with the future's job index
                    # without parsing a child process's stderr.
                    _record_failed_future(records, futures, future, exc)
                args.manifest.write_text(
                    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
                )
    manifest["elapsed_seconds"] = time.perf_counter() - started
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    failures = [job for job in records if job["status"] == "failed"]
    manifest["failed_jobs"] = len(failures)
    args.manifest.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
