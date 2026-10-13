"""Combine nonoverlapping paired-root audits without losing paired outcomes."""
from __future__ import annotations

import argparse
import json
from math import comb
from pathlib import Path


def _sign_test_two_sided(better: int, worse: int) -> float | None:
    n = better + worse
    if not n:
        return None
    tail = sum(comb(n, k) for k in range(min(better, worse) + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def aggregate(paths: list[Path]) -> dict:
    if not paths:
        raise ValueError("at least one audit is required")
    audits = [json.loads(path.read_text(encoding="utf-8")) for path in paths]
    first = audits[0]
    context = ("schema", "trace", "step", "actor", "recorded_action",
               "continuation_policy", "checkpoint", "max_actions")
    identity = [(row["action_key"], row["description"])
                for row in first["results"]]
    outcomes = {tuple(row["action_key"]): {} for row in first["results"]}
    for audit in audits:
        if any(audit[field] != first[field] for field in context):
            raise ValueError("audit root, continuation, or checkpoint mismatch")
        if [(row["action_key"], row["description"])
                for row in audit["results"]] != identity:
            raise ValueError("root action identity or ordering mismatch")
        for row in audit["results"]:
            target = outcomes[tuple(row["action_key"])]
            for item in row["outcomes"]:
                global_seed = audit["seed"] + item["replicate"]
                if global_seed in target:
                    raise ValueError(f"duplicate continuation seed {global_seed}")
                target[global_seed] = item["status"]
    selected = next(row for row in first["results"]
                    if row["description"] == first["recorded_action"])
    baseline = outcomes[tuple(selected["action_key"])]
    score = {"wins": 1.0, "draws": 0.5, "losses": 0.0}
    rows = []
    for action_key, description in identity:
        statuses = outcomes[tuple(action_key)]
        counts = {name: sum(status == name for status in statuses.values())
                  for name in ("wins", "losses", "draws", "truncated", "invalid")}
        better = worse = tied = 0
        if description != first["recorded_action"]:
            for seed, status in statuses.items():
                if status not in score or baseline[seed] not in score:
                    continue
                delta = score[status] - score[baseline[seed]]
                better += delta > 0
                worse += delta < 0
                tied += delta == 0
        rows.append({"action_key": action_key, "description": description,
                     **counts, "alternative_better": better,
                     "recorded_better": worse, "tied": tied,
                     "paired_sign_p_two_sided": _sign_test_two_sided(better, worse)})
    return {"schema": "paired-root-audit-aggregate-v1",
            "source_files": [str(path) for path in paths],
            "root": {field: first[field] for field in context},
            "seed_count": len(baseline), "results": rows,
            "warning": "Sign tests are exploratory across multiple alternatives; neither the continuation policy nor this root is an optimal-play oracle."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audits", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    result = aggregate(args.audits)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"seed_count": result["seed_count"],
                      "results": result["results"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
