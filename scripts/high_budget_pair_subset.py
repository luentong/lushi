"""Rerun representative hard-negative deck pairs with a stronger search budget."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--pairs", type=int, default=20)
    p.add_argument("--device", default="npu")
    p.add_argument("--samples", type=int, default=4)
    p.add_argument("--iterations", type=int, default=16)
    p.add_argument("--tree-depth", type=int, default=8)
    p.add_argument("--rollout-depth", type=int, default=2)
    p.add_argument("--max-actions", type=int, default=120)
    args = p.parse_args()
    data = json.loads(args.candidates.read_text(encoding="utf-8"))
    pair_stats = defaultdict(lambda: {"count": 0, "max_regret": 0.0})
    for c in data.get("candidates", []):
        key = (c["deck_a"], c["deck_b"])
        pair_stats[key]["count"] += 1
        pair_stats[key]["max_regret"] = max(pair_stats[key]["max_regret"], float(c.get("regret_gap", 0.0)))
    pairs = sorted(pair_stats, key=lambda k: (-pair_stats[k]["max_regret"], -pair_stats[k]["count"]))[:args.pairs]
    args.output.mkdir(parents=True, exist_ok=True)
    trace_script = Path(__file__).with_name("trace_search_match.py")
    results = []
    for job, (deck_a, deck_b) in enumerate(pairs):
        prefix = args.output / f"pair-{job:03d}"
        cmd = [sys.executable, str(trace_script), "--seed", str(2026100900 + job),
               "--candidate-seat", "0", "--both-model", "--use-model-value",
               "--checkpoint", str(args.checkpoint), "--deck-config", str(args.deck_config),
               "--deck-a", deck_a, "--deck-b", deck_b, "--device", args.device,
               "--samples", str(args.samples), "--iterations", str(args.iterations),
               "--tree-depth", str(args.tree_depth), "--rollout-depth", str(args.rollout_depth),
               "--max-actions", str(args.max_actions), "--output-prefix", str(prefix)]
        r = subprocess.run(cmd, text=True, capture_output=True)
        item = {"job": job, "deck_a": deck_a, "deck_b": deck_b,
                "source_candidates": pair_stats[(deck_a, deck_b)],
                "returncode": r.returncode, "json": str(prefix.with_suffix('.json')) if prefix.with_suffix('.json').exists() else None,
                "stdout_tail": r.stdout[-1200:], "stderr_tail": r.stderr[-1200:]}
        results.append(item)
        config = {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()}
        (args.output / "manifest.json").write_text(json.dumps({"schema_version": 1, "config": config, "results": results}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(item, ensure_ascii=False), flush=True)
    return 0 if all(x["json"] for x in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
