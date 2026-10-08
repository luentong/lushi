"""Select a de-duplicated, stratified hard-negative set from scan output."""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path


def action_type(c: dict) -> str:
    text = str(c.get("selected") or c.get("description") or "")
    parts = text.split()
    return parts[1] if len(parts) > 1 and parts[0].startswith("P") else "UNKNOWN"


def score(c: dict) -> float:
    return float(c.get("regret_gap", 0.0)) + 0.02 * (1.0 - float(c.get("selected_visit_share", c.get("selected_visit_share", 1.0)) or 0.0))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--input", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--limit", type=int, default=1000)
    p.add_argument("--per-stratum", type=int, default=6)
    args = p.parse_args()
    data = json.loads(args.input.read_text(encoding="utf-8"))
    unique = {}
    for c in data.get("candidates", []):
        key = (c.get("deck_a"), c.get("deck_b"), c.get("seed"), c.get("step"), c.get("selected"))
        old = unique.get(key)
        if old is None or score(c) > score(old):
            unique[key] = c
    candidates = list(unique.values())
    for c in candidates:
        c["action_type"] = action_type(c)
        c["selection_score"] = score(c)
        c["stratum"] = "|".join([
            str(c.get("deck_a", "")), str(c.get("deck_b", "")),
            c["action_type"], "+".join(sorted(c.get("reasons", [])))])
    candidates.sort(key=score, reverse=True)
    by_stratum = defaultdict(list)
    selected = []
    for c in candidates:
        if len(selected) >= args.limit:
            break
        bucket = by_stratum[c["stratum"]]
        if len(bucket) < args.per_stratum:
            bucket.append(c)
            selected.append(c)
    selected_ids = {id(x) for x in selected}
    for c in candidates:
        if len(selected) >= args.limit:
            break
        if id(c) not in selected_ids:
            selected.append(c)
            selected_ids.add(id(c))
    out = {
        "schema_version": 2,
        "source": str(args.input),
        "unique_candidate_count": len(candidates),
        "selected_count": len(selected),
        "dedupe_key": ["deck_a", "deck_b", "seed", "step", "selected"],
        "selection": {"limit": args.limit, "per_stratum": args.per_stratum,
                       "sort": "regret_gap + 0.02*(1-selected_visit_share)"},
        "reason_counts": Counter(r for c in selected for r in c.get("reasons", [])),
        "action_counts": Counter(c["action_type"] for c in selected),
        "candidates": selected,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"unique": len(candidates), "selected": len(selected),
                      "reasons": out["reason_counts"], "actions": out["action_counts"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
