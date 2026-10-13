#!/usr/bin/env python3
"""Validate Windows live-companion deck configuration files."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--known", type=Path, required=True)
    parser.add_argument("--candidates", type=Path, required=True)
    args = parser.parse_args()
    known = json.loads(args.known.read_text(encoding="utf-8"))
    candidates = json.loads(args.candidates.read_text(encoding="utf-8"))
    if not isinstance(known, dict) or not isinstance(candidates, dict):
        raise SystemExit("configuration root must be an object")
    known_decks = [deck for deck in known.values() if isinstance(deck, dict)]
    candidate_decks = [deck for decks in candidates.values() if isinstance(decks, list)
                      for deck in decks if isinstance(deck, dict)]
    if len(known_decks) != 1:
        raise SystemExit(f"expected exactly one known deck, got {len(known_decks)}")
    known_size = sum(int(count) for count in known_decks[0].values())
    if known_size != 30:
        raise SystemExit(f"known deck must contain 30 cards, got {known_size}")
    if not candidate_decks:
        raise SystemExit("candidate deck list is empty")
    sizes = [sum(int(count) for count in deck.values()) for deck in candidate_decks]
    # Some exported meta entries are partial 20-card lists.  Keep them in the
    # raw belief file for provenance; the live recommender drops them whenever
    # at least one complete candidate exists.
    invalid = [size for size in sizes if size not in (20, 30, 40)]
    if invalid:
        raise SystemExit(f"candidate deck sizes invalid: {invalid[:5]}")
    print(json.dumps({"known_decks": 1, "known_size": known_size,
                      "candidate_decks": len(candidate_decks),
                      "candidate_sizes": sorted(set(sizes)),
                      "short_format_candidates": sum(size == 20 for size in sizes)},
                     ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
