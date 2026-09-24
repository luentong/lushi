#!/usr/bin/env python3
"""Freeze a card-identity vocabulary for a reproducible model schema."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import BASIC_AUXILIARY_IDS, EXECUTABLE_CARD_IDS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--include-runtime-auxiliaries", action="store_true")
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    card_ids = tuple(sorted(
        set(EXECUTABLE_CARD_IDS)
        | (set(BASIC_AUXILIARY_IDS) if args.include_runtime_auxiliaries else set())
    ))
    digest = hashlib.sha256(
        json.dumps(card_ids, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    payload = {
        "schema_version": 1,
        "label": args.label,
        "card_ids": card_ids,
        "card_vocab_size": len(card_ids),
        "card_vocab_sha256": digest,
        "includes_runtime_auxiliaries": args.include_runtime_auxiliaries,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), **payload}, ensure_ascii=False))


if __name__ == "__main__":
    main()
