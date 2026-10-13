#!/usr/bin/env python3
"""Audited, generation-only high-budget ISMCTS teacher pilot."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from threading import Lock
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from audit_entity_dataset import audit
from run_entity_pilot import jobs_for


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_teacher_checkpoint(path):
    """Reject an entity-model checkpoint before creating empty game shards."""
    from hsa.torch_model import TorchPolicyValueModel
    try:
        model = TorchPolicyValueModel.from_checkpoint(str(path), "cpu")
    except (KeyError, RuntimeError, ValueError) as error:
        raise ValueError(
            "teacher checkpoint is incompatible with the structured-model "
            "loader used by generate_policy_value_data.py"
        ) from error
    del model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--teacher-checkpoint", type=Path, required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--devices", nargs="+", required=True)
    parser.add_argument("--repetitions", type=int, default=2)
    parser.add_argument("--seed", type=int, default=202610080000)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--iterations", type=int, default=64)
    parser.add_argument("--rollout-depth", type=int, default=4)
    parser.add_argument("--timeout-seconds", type=int, default=900)
    args = parser.parse_args()
    if (min(args.repetitions, args.samples, args.iterations,
            args.timeout_seconds) < 1 or args.rollout_depth < 0
            or len(set(args.devices)) != len(args.devices)):
        parser.error("invalid high-budget teacher configuration")
    try:
        validate_teacher_checkpoint(args.teacher_checkpoint)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    args.output_dir = args.output_dir.resolve()
    args.output_dir.mkdir(parents=True, exist_ok=False)
    decks = [item["id"] for item in json.loads(args.deck_config.read_text())["decks"]]
    schedule = jobs_for(decks, args.repetitions, args.seed)
    manifest = args.output_dir / "manifest.json"
    report = {"status": "generating", "started_at": time.time(), "jobs": [],
              "schedule": schedule, "strength_validated": False,
              "teacher_sha256": sha256(args.teacher_checkpoint),
              "deck_config_sha256": sha256(args.deck_config),
              "cards_sha256": sha256(ROOT / "cards.251332.enUS.json"),
              "source_sha256": {str(p.relative_to(ROOT)): sha256(p) for p in (
                  *sorted((ROOT / "src/hsa").rglob("*.py")),
                  ROOT / "scripts/generate_policy_value_data.py",
                  ROOT / "scripts/benchmark_mcts.py",
                  ROOT / "scripts/audit_entity_dataset.py",
                  ROOT / "scripts/run_entity_pilot.py", Path(__file__))},
              "settings": {key: str(value) if isinstance(value, Path) else value
                           for key, value in vars(args).items()}}
    lock = Lock()

    def progress():
        temporary = manifest.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        temporary.replace(manifest)

    def worker(device, assigned):
        for index, deck_a, deck_b, seed in assigned:
            data = args.output_dir / f"game-{index:04d}.jsonl.gz"
            log = args.output_dir / f"game-{index:04d}.log"
            command = [sys.executable, "-u", str(ROOT / "scripts/generate_policy_value_data.py"),
                       "--games", "1", "--seed", str(seed), "--teacher", "ismcts",
                       "--samples", str(args.samples), "--iterations", str(args.iterations),
                       "--rollout-depth", str(args.rollout_depth),
                       "--teacher-checkpoint", str(args.teacher_checkpoint.resolve()),
                       "--teacher-device", device, "--teacher-value-mode", "prior-only",
                       "--export-observer-view", "--card-vocab", "expanded-executable",
                       "--workers", "1", "--max-actions", "400",
                       "--deck-config", str(args.deck_config.resolve()),
                       "--deck-a", deck_a, "--deck-b", deck_b,
                       "--output", str(data), "--ruleset-label", "entity-v1-highbudget-teacher"]
            with log.open("xb") as handle:
                try:
                    code = subprocess.run(command, cwd=ROOT, stdin=subprocess.DEVNULL,
                                          stdout=handle, stderr=subprocess.STDOUT,
                                          timeout=args.timeout_seconds).returncode
                except subprocess.TimeoutExpired:
                    code = 124
                    handle.write(b"\nENGINEERING TIMEOUT: excluded, not a draw.\n")
            result = {"index": index, "deck_a": deck_a, "deck_b": deck_b,
                      "seed": seed, "device": device, "exit_code": code,
                      "data": str(data), "log": str(log)}
            if code == 0:
                result["data_sha256"] = sha256(data)
            with lock:
                report["jobs"].append(result)
                progress()
            print(json.dumps({"stage": "game", **result}), flush=True)

    progress()
    with ThreadPoolExecutor(max_workers=len(args.devices)) as executor:
        futures = [executor.submit(worker, device, schedule[index::len(args.devices)])
                   for index, device in enumerate(args.devices)]
        for future in as_completed(futures):
            future.result()
    if len(report["jobs"]) != len(schedule) or any(j["exit_code"] for j in report["jobs"]):
        report.update(status="incomplete", error="one or more games failed")
        progress()
        return 1
    result = audit([Path(j["data"]) for j in sorted(report["jobs"], key=lambda j: j["index"])])
    (args.output_dir / "dataset-audit.json").write_text(json.dumps(result, indent=2))
    report.update(status="complete" if result["status"] == "passed" else "dataset_rejected",
                  ordinary_decisions=result["valid_decisions"],
                  elapsed_seconds=time.time() - report["started_at"])
    progress()
    return 0 if report["status"] == "complete" else 2


if __name__ == "__main__":
    raise SystemExit(main())
