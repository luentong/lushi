#!/usr/bin/env python3
"""Rewrite decision shards with only fields consumed by policy/value training."""
import gzip, json, sys
from pathlib import Path

KEEP = {
    "record_type", "state", "actions", "chosen_action", "value_target",
    "policy_target", "teacher_action_values", "actor", "game_seed", "winner",
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
