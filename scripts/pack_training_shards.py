#!/usr/bin/env python3
"""Pack compact JSONL.GZ decisions into bounded torch batch shards.

The resulting files contain only Python lists of decision dictionaries and are
intended for incremental/replay training. Packing is a one-time parse step;
subsequent training can load one .pt shard at a time.
"""
from __future__ import annotations

import argparse
import gzip
import json
from multiprocessing import Pool
from pathlib import Path
import torch


def pack(src: Path, out_dir: Path, batch_size: int) -> int:
    out_dir.mkdir(parents=True, exist_ok=True)
    count = 0
    batch = []
    part = 0
    with gzip.open(src, "rt", encoding="utf-8") as handle:
        header = json.loads(next(handle))
        for line in handle:
            record = json.loads(line)
            if record.get("record_type") != "decision":
                continue
            batch.append(record)
            count += 1
            if len(batch) >= batch_size:
                torch.save({"header": header, "records": batch},
                           out_dir / f"{src.stem}.part{part:05d}.pt")
                batch = []
                part += 1
        if batch:
            torch.save({"header": header, "records": batch},
                       out_dir / f"{src.stem}.part{part:05d}.pt")
    return count


def _pack_one(args: tuple[Path, Path, int]) -> tuple[str, int]:
    """Pickle-friendly worker wrapper for independent compressed game files."""
    src, out_dir, batch_size = args
    return src.name, pack(src, out_dir, batch_size)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--batch-size", type=int, default=512)
    parser.add_argument("--workers", type=int, default=1,
                        help="Independent JSONL files to pack concurrently.")
    args = parser.parse_args()
    total = 0
    jobs = [(source, args.output, args.batch_size)
            for source in sorted(args.source.glob("*.jsonl.gz"))]
    if args.workers > 1:
        with Pool(processes=args.workers) as pool:
            results = pool.imap_unordered(_pack_one, jobs)
            for name, n in results:
                total += n
                print(f"{name}: {n}", flush=True)
    else:
        for job in jobs:
            name, n = _pack_one(job)
            total += n
            print(f"{name}: {n}", flush=True)
    print(f"total: {total}")


if __name__ == "__main__":
    main()
