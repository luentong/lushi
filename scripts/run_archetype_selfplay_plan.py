#!/usr/bin/env python3
"""Execute a reproducible archetype-balanced self-play plan, resumably."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--split", choices=("train", "validation", "unseen"), required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--iterations", type=int, default=16)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--rollout-depth", type=int, default=3)
    parser.add_argument("--parallel-jobs", type=int, default=24)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text(encoding="utf-8"))
    tasks = plan["jobs"][args.split]
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for index, task in enumerate(tasks):
        output = args.output_dir / f"{args.split}-{index:04d}-{task['deck_a']}__{task['deck_b']}.jsonl.gz"
        records.append({**task, "index": index, "output": str(output),
                        "status": "complete" if args.resume and output.is_file() and output.stat().st_size else "planned"})
    manifest = {"schema_version": 1, "plan": str(args.plan), "split": args.split,
                "teacher": {"samples": args.samples, "iterations": args.iterations,
                            "simulations_per_decision": args.samples * args.iterations,
                            "rollout_depth": args.rollout_depth},
                "parallel_jobs": args.parallel_jobs, "timeout_seconds": args.timeout_seconds,
                "records": records, "started_at": time.time()}

    def save() -> None:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    def run(index: int) -> int:
        row = records[index]
        command = [sys.executable, str(ROOT / "scripts" / "generate_policy_value_data.py"),
                   "--games", "1", "--seed", str(row["seed"]), "--teacher", "ismcts",
                   "--samples", str(args.samples), "--iterations", str(args.iterations),
                   "--rollout-depth", str(args.rollout_depth), "--behavior", "teacher", "--workers", "1",
                   "--max-actions", "1000", "--card-vocab", "expanded-executable",
                   "--ruleset-label", "standard91-generalized-v1", "--cards", str(args.cards),
                   "--deck-config", str(args.deck_config), "--deck-a", row["deck_a"], "--deck-b", row["deck_b"],
                   "--output", row["output"]]
        process = subprocess.Popen(command, cwd=ROOT, start_new_session=True,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        try:
            _, stderr = process.communicate(timeout=args.timeout_seconds)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                _, stderr = process.communicate(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                _, stderr = process.communicate()
            raise TimeoutError(f"timeout after {args.timeout_seconds}s: {stderr[-1000:]}")
        if process.returncode:
            raise RuntimeError(stderr[-2000:])
        return index

    save()
    pending = [row["index"] for row in records if row["status"] != "complete"]
    with ThreadPoolExecutor(max_workers=min(args.parallel_jobs, len(pending) or 1)) as pool:
        futures = {pool.submit(run, index): index for index in pending}
        for future in as_completed(futures):
            index = futures[future]
            try:
                future.result()
            except Exception as exc:  # keep independent work progressing
                records[index]["status"] = "failed"
                records[index]["error"] = str(exc)
            else:
                records[index]["status"] = "complete"
            save()
    manifest["finished_at"] = time.time()
    manifest["summary"] = {state: sum(row["status"] == state for row in records)
                           for state in ("complete", "failed", "planned")}
    save()
    print(json.dumps(manifest["summary"], ensure_ascii=False))
    return 0 if not manifest["summary"]["failed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
