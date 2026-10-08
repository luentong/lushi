"""Generate a uniform search trace for many configured deck matchups."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def _deck_names(path: Path) -> list[str]:
    # Reuse the canonical decoder so deck codes, counts and aliases match the
    # tournament/evaluation path exactly.
    sys.path.insert(0, str(path.parents[1] / "scripts"))
    from benchmark_mcts import _decoded_decks
    return list(_decoded_decks(path))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-decks", type=int, default=0,
                   help="0 means all configured decks")
    p.add_argument("--pairs-per-deck", type=int, default=1)
    p.add_argument("--iterations", type=int, default=8)
    p.add_argument("--samples", type=int, default=2)
    p.add_argument("--tree-depth", type=int, default=6)
    p.add_argument("--rollout-depth", type=int, default=1)
    p.add_argument("--max-actions", type=int, default=100)
    p.add_argument("--device", default="npu")
    p.add_argument("--seed", type=int, default=2026100801)
    args = p.parse_args()
    names = _deck_names(args.deck_config)
    if args.max_decks > 0:
        names = names[:args.max_decks]
    if len(names) < 2:
        raise SystemExit("need at least two decoded decks")
    args.output.mkdir(parents=True, exist_ok=True)
    trace_script = Path(__file__).with_name("trace_search_match.py")
    manifest = {
        "schema_version": 1,
        "deck_config": str(args.deck_config),
        "checkpoint": str(args.checkpoint),
        "deck_count": len(names),
        "pairs_per_deck": args.pairs_per_deck,
        "iterations": args.iterations,
        "samples": args.samples,
        "traces": [],
    }
    job_id = 0
    for i, deck_a in enumerate(names):
        for offset in range(args.pairs_per_deck):
            # Adjacent rotation gives every deck a different opponent without
            # exploding the first diagnostic run to the full Cartesian product.
            deck_b = names[(i + offset + 1) % len(names)]
            prefix = args.output / f"match-{job_id:04d}"
            command = [
                sys.executable, str(trace_script),
                "--seed", str(args.seed + job_id),
                "--candidate-seat", "0",
                "--checkpoint", str(args.checkpoint),
                "--deck-config", str(args.deck_config),
                "--deck-a", deck_a, "--deck-b", deck_b,
                "--device", args.device,
                "--samples", str(args.samples),
                "--iterations", str(args.iterations),
                "--tree-depth", str(args.tree_depth),
                "--rollout-depth", str(args.rollout_depth),
                "--max-actions", str(args.max_actions),
                "--output-prefix", str(prefix),
            ]
            result = subprocess.run(command, text=True, capture_output=True)
            item = {"job_id": job_id, "deck_a": deck_a, "deck_b": deck_b,
                    "returncode": result.returncode,
                    "stdout_tail": result.stdout[-1000:],
                    "stderr_tail": result.stderr[-1000:]}
            # trace_search_match returns non-zero for a capped/partial game,
            # but still writes a useful JSON/Markdown trace.  Keep those
            # artifacts for hard-negative scanning; only mark the job failed
            # when no trace was produced at all.
            trace_json = prefix.with_suffix(".json")
            trace_md = prefix.with_suffix(".md")
            if trace_json.exists():
                item["json"] = str(prefix.with_suffix(".json"))
                item["markdown"] = str(prefix.with_suffix(".md"))
                item["partial_trace"] = result.returncode != 0
            manifest["traces"].append(item)
            manifest["completed_jobs"] = job_id + 1
            (args.output / "manifest.json").write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            print(json.dumps({"job_id": job_id, "deck_a": deck_a,
                              "deck_b": deck_b,
                              "returncode": result.returncode}, ensure_ascii=False),
                  flush=True)
            job_id += 1
    manifest["complete"] = True
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
