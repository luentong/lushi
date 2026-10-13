#!/usr/bin/env python3
"""Reindex every columnar tensor shard in a directory to one target schema."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import torch

from reindex_columnar_vocab import reindex_shard


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", type=Path, required=True)
    parser.add_argument("--target-shard", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    target = torch.load(args.target_shard, map_location="cpu", weights_only=False)
    schema = target["header"]["feature_schema"]
    sources = sorted(args.input_dir.rglob("*.pt"))
    if not sources:
        parser.error("input directory contains no .pt shards")
    rows = []
    for index, source in enumerate(sources, 1):
        payload = torch.load(source, map_location="cpu", weights_only=False)
        output = reindex_shard(payload, schema)
        relative = source.relative_to(args.input_dir)
        destination = args.output_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        torch.save(output, destination)
        rows.append({"source": str(relative), "records": int(output["count"])})
        if index % 8 == 0 or index == len(sources):
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps({
                "complete": index == len(sources), "processed": index,
                "total": len(sources), "records": sum(r["records"] for r in rows),
                "rows": rows,
            }, indent=2), encoding="utf-8")
            print(f"processed={index}/{len(sources)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
