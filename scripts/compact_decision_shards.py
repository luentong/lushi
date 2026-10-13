#!/usr/bin/env python3
"""Rewrite decision shards with only fields consumed by policy/value training."""
import gzip, json, sys
from pathlib import Path

KEEP = {
    "record_type", "state", "actions", "chosen_action", "value_target",
    "opponent_value_state", "opponent_value_target",
    "policy_target", "policy_target_source", "teacher_action_values",
    "teacher_action_visits", "actor", "game_seed", "winner",
    "teacher_search_version", "teacher_selection_source", "conditional",
    "conditional_root_action", "conditional_observation_visits",
    "conditional_trigger_depth",
    "conditional_policy_visits", "conditional_target_repeats",
    "conditional_target_iterations", "conditional_target_source",
    "conditional_target_top_action_agreement",
    "conditional_target_mean_value_std", "conditional_target_entropy",
    "value_target_valid",
}

def compact(src: Path, dst: Path) -> int:
    count = 0
    dst.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(src, "rt", encoding="utf-8") as fi, gzip.open(dst, "wt", encoding="utf-8") as fo:
        header = json.loads(next(fi))
        fo.write(json.dumps(header, separators=(",", ":")) + "\n")
        for line in fi:
            rec = json.loads(line)
            if rec.get("record_type") != "decision":
                continue
            fo.write(json.dumps({k: rec[k] for k in KEEP if k in rec}, separators=(",", ":")) + "\n")
            count += 1
    return count

if __name__ == "__main__":
    src_dir, dst_dir = map(Path, sys.argv[1:3])
    total = 0
    for src in sorted(src_dir.glob("*.jsonl.gz")):
        dst = dst_dir / src.name
        n = compact(src, dst)
        total += n
        print(src.name, n, flush=True)
    print("total", total)
