#!/usr/bin/env python3
"""Check two PPO runs used identical games/actions before credit-target A/B."""
from __future__ import annotations

import argparse
import gzip
import json
from itertools import zip_longest


LABEL_FIELDS = {"advantage", "return", "terminated", "truncated", "weight"}


def compare(left, right):
    count = 0
    with gzip.open(left, "rt", encoding="utf-8") as a, gzip.open(right, "rt", encoding="utf-8") as b:
        for count, (line_a, line_b) in enumerate(zip_longest(a, b), 1):
            if line_a is None or line_b is None:
                raise ValueError(f"rollout lengths differ at row {count}")
            row_a, row_b = json.loads(line_a), json.loads(line_b)
            for field in LABEL_FIELDS:
                row_a.pop(field, None)
                row_b.pop(field, None)
            if row_a != row_b:
                differing = sorted(key for key in row_a.keys() | row_b.keys()
                                   if row_a.get(key) != row_b.get(key))
                raise ValueError(f"non-target rollout drift at row {count}: {differing}")
    return {"identical_observations_actions_values": True, "rows": count,
            "ignored_label_fields": sorted(LABEL_FIELDS)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("left")
    parser.add_argument("right")
    args = parser.parse_args()
    print(json.dumps(compare(args.left, args.right), indent=2))


if __name__ == "__main__":
    main()
