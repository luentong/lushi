#!/usr/bin/env python3
"""Create archetype-level train/validation/unseen splits."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("manifest", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--unseen", type=int, default=4)
    p.add_argument("--validation", type=int, default=4)
    args = p.parse_args()
    data = json.loads(args.manifest.read_text(encoding="utf-8"))
    groups = data["archetypes"]
    # Stable order makes repeated training runs reproducible.
    unseen = groups[-args.unseen:] if args.unseen else []
    remaining = groups[:-args.unseen] if args.unseen else groups
    validation = remaining[-args.validation:] if args.validation else []
    train = remaining[:-args.validation] if args.validation else remaining
    result = {"source": str(args.manifest), "train": train,
              "validation": validation, "unseen": unseen,
              "summary": {"train_archetypes": len(train),
                          "validation_archetypes": len(validation),
                          "unseen_archetypes": len(unseen)}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
