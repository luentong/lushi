#!/usr/bin/env python3
"""Build reproducible, archetype-balanced self-play schedules.

Deck variants are sampled inside each archetype-pair rather than treating all
91 concrete lists as independent equally-weighted identities.  This prevents
large archetype families from dominating the teacher corpus and makes an
archetype-level held-out evaluation meaningful.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


def _groups(config: dict, allowed: set[str]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = defaultdict(list)
    for deck in config["decks"]:
        archetype = deck.get("archetype", deck.get("name_zh", deck["id"]))
        if archetype in allowed:
            result[archetype].append(deck["id"])
    return dict(result)


def _build_jobs(groups: dict[str, list[str]], games_per_pair: int, seed: int) -> list[dict]:
    rng = random.Random(seed)
    jobs: list[dict] = []
    for left in sorted(groups):
        for right in sorted(groups):
            for replica in range(games_per_pair):
                jobs.append({
                    "archetype_a": left,
                    "archetype_b": right,
                    "deck_a": rng.choice(groups[left]),
                    "deck_b": rng.choice(groups[right]),
                    "replica": replica,
                    "seed": seed + len(jobs) * 10007,
                })
    return jobs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--splits", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--train-games-per-pair", type=int, default=4)
    parser.add_argument("--validation-games-per-pair", type=int, default=4)
    parser.add_argument("--unseen-games-per-pair", type=int, default=4)
    parser.add_argument("--seed", type=int, default=202609240001)
    args = parser.parse_args()
    config = json.loads(args.deck_config.read_text(encoding="utf-8"))
    splits = json.loads(args.splits.read_text(encoding="utf-8"))
    names = {split: {item["name"] for item in splits[split]} for split in ("train", "validation", "unseen")}
    groups = {split: _groups(config, names[split]) for split in names}
    missing = {split: sorted(names[split] - set(groups[split])) for split in names}
    if any(missing.values()):
        raise ValueError(f"split archetypes absent from deck config: {missing}")

    train = _build_jobs(groups["train"], args.train_games_per_pair, args.seed)
    validation = _build_jobs(groups["validation"], args.validation_games_per_pair, args.seed + 1_000_000)
    # Generalization evaluation: each unseen archetype faces each training
    # archetype in both seat directions, with independently sampled variants.
    mixed_groups = {**groups["train"], **groups["unseen"]}
    unseen = []
    rng = random.Random(args.seed + 2_000_000)
    for unseen_name in sorted(groups["unseen"]):
        for train_name in sorted(groups["train"]):
            for left, right in ((unseen_name, train_name), (train_name, unseen_name)):
                for replica in range(args.unseen_games_per_pair):
                    unseen.append({"archetype_a": left, "archetype_b": right,
                                   "deck_a": rng.choice(mixed_groups[left]),
                                   "deck_b": rng.choice(mixed_groups[right]),
                                   "replica": replica,
                                   "seed": args.seed + 2_000_000 + len(unseen) * 10007})
    plan = {
        "schema_version": 1,
        "purpose": "archetype-balanced generalized policy/value training",
        "deck_config": str(args.deck_config), "splits": str(args.splits),
        "seed": args.seed,
        "groups": groups,
        "jobs": {"train": train, "validation": validation, "unseen": unseen},
        "summary": {
            "train_archetypes": len(groups["train"]), "validation_archetypes": len(groups["validation"]),
            "unseen_archetypes": len(groups["unseen"]), "train_games": len(train),
            "validation_games": len(validation), "unseen_games": len(unseen),
            "train_variant_appearances": dict(Counter(j["deck_a"] for j in train) + Counter(j["deck_b"] for j in train)),
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(plan["summary"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
