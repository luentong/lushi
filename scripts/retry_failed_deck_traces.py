"""Retry trace jobs that produced no JSON after serialization/choice fixes."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--device", default="npu")
    p.add_argument("--max-actions", type=int, default=80)
    args = p.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    failed = [x for x in manifest["traces"] if "json" not in x]
    args.output.mkdir(parents=True, exist_ok=True)
    trace_script = Path(__file__).with_name("trace_search_match.py")
    out = {"schema_version": 1, "source_manifest": str(args.manifest),
           "checkpoint": str(args.checkpoint), "deck_config": str(args.deck_config),
           "jobs": []}
    for x in failed:
        prefix = args.output / f"retry-{int(x['job_id']):04d}"
        cmd = [sys.executable, str(trace_script),
               "--seed", str(2026101800 + int(x["job_id"])),
               "--candidate-seat", "0", "--checkpoint", str(args.checkpoint),
               "--deck-config", str(args.deck_config), "--deck-a", x["deck_a"],
               "--deck-b", x["deck_b"], "--device", args.device,
               "--samples", "1", "--iterations", "4", "--tree-depth", "4",
               "--rollout-depth", "1", "--max-actions", str(args.max_actions),
               "--output-prefix", str(prefix)]
        r = subprocess.run(cmd, text=True, capture_output=True)
        item = {"job_id": x["job_id"], "deck_a": x["deck_a"],
                "deck_b": x["deck_b"], "returncode": r.returncode,
                "stdout_tail": r.stdout[-1000:], "stderr_tail": r.stderr[-1000:]}
        if prefix.with_suffix(".json").exists():
            item["json"] = str(prefix.with_suffix(".json"))
            item["markdown"] = str(prefix.with_suffix(".md"))
        out["jobs"].append(item)
        (args.output / "retry-manifest.json").write_text(
            json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(item, ensure_ascii=False), flush=True)
    out["complete"] = True
    (args.output / "retry-manifest.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0 if all("json" in x for x in out["jobs"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
