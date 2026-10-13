#!/usr/bin/env python3
"""Benchmark and checksum the exact entity input collation contract."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.entity_model import collate_views


def tensor_digest(tensor):
    payload = (str(tuple(tensor.shape)) + str(tensor.dtype)).encode()
    return hashlib.sha256(payload + tensor.contiguous().numpy().tobytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--shard", type=Path, required=True)
    parser.add_argument("--batch-size", type=int, default=6)
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.batch_size < 1 or args.repeats < 1:
        parser.error("batch-size and repeats must be positive")
    with gzip.open(args.shard, "rt", encoding="utf-8") as source:
        header = json.loads(next(source))
        card_ids = header["feature_schema"]["card_vocab_ids"]
        views = []
        for line in source:
            row = json.loads(line)
            if row.get("record_type") == "decision" and row.get("observer_view"):
                views.append(row["observer_view"])
                if len(views) == args.batch_size:
                    break
    if len(views) != args.batch_size:
        raise ValueError("shard has fewer observer views than requested batch size")
    batch = collate_views(views, card_ids, "cpu")
    timings = []
    for _ in range(args.repeats):
        start = time.perf_counter()
        collate_views(views, card_ids, "cpu")
        timings.append(time.perf_counter() - start)
    output = {
        "shard": str(args.shard), "batch_size": args.batch_size,
        "entity_lengths": [len(view["entities"]) + len(view["history"]) + 1
                           for view in views],
        "action_lengths": [len(view["actions"]) for view in views],
        "median_seconds": statistics.median(timings),
        "timings_seconds": timings,
        "tensor_digests": {key: tensor_digest(value)
                           for key, value in sorted(batch.items())},
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: output[key] for key in (
        "batch_size", "entity_lengths", "action_lengths", "median_seconds")}),
          flush=True)


if __name__ == "__main__":
    main()
