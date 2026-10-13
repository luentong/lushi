#!/usr/bin/env python3
"""Generate independently re-searched, observer-aligned conditional decisions.

This is a data-quality pilot. It never starts training or promotes a checkpoint.
"""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from audit_entity_dataset import audit
from run_entity_pilot import jobs_for


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--teacher-checkpoint", type=Path, required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--devices", nargs="+", required=True)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--seed", type=int, default=202610030100)
    parser.add_argument("--min-visits", type=int, default=4)
    parser.add_argument("--max-branches", type=int, default=2)
    parser.add_argument("--conditional-repeats", type=int, default=2)
    parser.add_argument("--conditional-iterations", type=int, default=32)
    args = parser.parse_args()
    if (args.repetitions < 1 or args.min_visits < 1 or args.max_branches < 1
            or args.conditional_repeats < 2
            or args.conditional_iterations < 1 or len(set(args.devices)) != len(args.devices)):
        parser.error("invalid or duplicate device/conditional-search configuration")
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    decks = [item["id"] for item in json.loads(args.deck_config.read_text())["decks"]]
    schedule = jobs_for(decks, args.repetitions, args.seed)
    if len(decks) != 2:
        parser.error("pilot expects two deck archetypes and all ordered matchups")
    manifest = args.output_dir / "manifest.json"
    report = {"status": "generating", "started_at": time.time(), "jobs": [],
              "schedule": schedule, "source_sha256": {
                  str(p.relative_to(ROOT)): sha256(p) for p in
                  (ROOT / "src/hsa/dragon_mirror.py", ROOT / "src/hsa/mcts.py",
                   ROOT / "scripts/generate_policy_value_data.py", Path(__file__))},
              "teacher_sha256": sha256(args.teacher_checkpoint),
              "deck_config_sha256": sha256(args.deck_config),
              "settings": {k: str(v) if isinstance(v, Path) else v
                           for k, v in vars(args).items()}}
    lock = Lock()

    def progress():
        temporary = manifest.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False))
        temporary.replace(manifest)

    def worker(device, assigned):
        for index, a, b, seed in assigned:
            data = args.output_dir / f"game-{index:04d}.jsonl.gz"
            log = args.output_dir / f"game-{index:04d}.log"
            command = [sys.executable, "-u", str(ROOT / "scripts/generate_policy_value_data.py"),
                       "--games", "1", "--seed", str(seed), "--teacher", "ismcts",
                       "--samples", "2", "--iterations", "32", "--rollout-depth", "3",
                       "--teacher-checkpoint", str(args.teacher_checkpoint.resolve()),
                       "--teacher-device", device, "--teacher-value-mode", "prior-only",
                       "--export-observer-view", "--card-vocab", "expanded-executable",
                       "--workers", "1", "--max-actions", "400",
                       "--deck-config", str(args.deck_config.resolve()),
                       "--deck-a", a, "--deck-b", b,
                       "--collect-conditional-training", "--conditional-training-min-visits",
                       str(args.min_visits), "--conditional-training-min-action-visits", "1",
                       "--conditional-training-repeats", str(args.conditional_repeats),
                       "--conditional-training-iterations", str(args.conditional_iterations),
                       "--conditional-training-max-branches", str(args.max_branches),
                       "--output", str(data), "--ruleset-label", "entity-v1-independent-conditional-pilot"]
            with log.open("xb") as handle:
                try:
                    code = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                          stdout=handle, stderr=subprocess.STDOUT,
                                          timeout=900).returncode
                except subprocess.TimeoutExpired:
                    code = 124
            result = {"index": index, "deck_a": a, "deck_b": b, "seed": seed,
                      "device": device, "exit_code": code, "data": str(data), "log": str(log)}
            if code == 0:
                result["data_sha256"] = sha256(data)
            with lock:
                report["jobs"].append(result)
                progress()
            print(json.dumps({"stage": "game", **result}), flush=True)

    progress()
    with ThreadPoolExecutor(max_workers=len(args.devices)) as executor:
        futures = [executor.submit(worker, device, schedule[i::len(args.devices)])
                   for i, device in enumerate(args.devices)]
        for future in as_completed(futures):
            future.result()
    if len(report["jobs"]) != len(schedule) or any(j["exit_code"] for j in report["jobs"]):
        report.update(status="incomplete", error="one or more games failed; keep good shards")
        progress()
        return 1
    result = audit([Path(j["data"]) for j in sorted(report["jobs"], key=lambda j: j["index"])])
    (args.output_dir / "dataset-audit.json").write_text(json.dumps(result, indent=2))
    report.update(status="complete" if result["status"] == "passed" else "dataset_rejected",
                  conditional_valid_rows=result["conditional_valid_rows"],
                  elapsed_seconds=time.time() - report["started_at"])
    progress()
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
