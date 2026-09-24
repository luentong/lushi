#!/usr/bin/env python3
"""Aggregate generated multi-deck game headers into auditable win-rate tables.

The training JSONL files contain one header per ordered matchup.  Reading only
that header avoids accidentally treating every decision in a game as an
independent match result.
"""
from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from pathlib import Path


def rate(wins: int, games: int) -> float | None:
    return wins / games if games else None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    config = json.loads(args.deck_config.read_text(encoding="utf-8"))
    names = {item["id"]: item.get("name_zh", item["id"])
             for item in config["decks"]}
    frequency = {item["id"]: item.get("frequency_weight", 1)
                 for item in config["decks"]}
    overall = defaultdict(lambda: {"wins": 0, "games": 0})
    seats = defaultdict(lambda: {"first_wins": 0, "first_games": 0,
                                 "second_wins": 0, "second_games": 0})
    matrix: dict[str, dict[str, dict[str, int | float | None]]] = defaultdict(dict)
    skipped: list[str] = []

    for path in sorted(args.data_dir.glob("*.jsonl.gz")):
        left, right = path.name.removesuffix(".jsonl.gz").split("__", 1)
        with gzip.open(path, "rt", encoding="utf-8") as stream:
            header = json.loads(next(stream))
        if header.get("record_type") != "header":
            skipped.append(path.name)
            continue
        counts = header.get("statistics", {}).get("winner_counts", {})
        p0 = int(counts.get("player_0", 0)); p1 = int(counts.get("player_1", 0))
        draws = int(counts.get("draw", 0)); games = p0 + p1 + draws
        if not games:
            skipped.append(path.name)
            continue
        for deck, wins, seat in ((left, p0, "first"), (right, p1, "second")):
            overall[deck]["wins"] += wins; overall[deck]["games"] += games
            seats[deck][f"{seat}_wins"] += wins
            seats[deck][f"{seat}_games"] += games
        matrix[left][right] = {"games": games, "left_wins": p0,
                               "right_wins": p1, "draws": draws,
                               "left_win_rate": rate(p0, games)}

    decks = []
    for deck in names:
        total = overall[deck]; seat = seats[deck]
        decks.append({
            "id": deck, "name_zh": names[deck], "frequency_weight": frequency[deck],
            "wins": total["wins"], "games": total["games"],
            "win_rate": rate(total["wins"], total["games"]),
            "first_wins": seat["first_wins"], "first_games": seat["first_games"],
            "first_win_rate": rate(seat["first_wins"], seat["first_games"]),
            "second_wins": seat["second_wins"], "second_games": seat["second_games"],
            "second_win_rate": rate(seat["second_wins"], seat["second_games"]),
        })
    decks.sort(key=lambda row: (-float(row["win_rate"] or 0), row["id"]))
    result = {"scope": {"description": "Generated ISMCTS teacher games only; not ladder win rates.",
                        "files": len(matrix) and sum(len(row) for row in matrix.values()),
                        "games_per_ordered_matchup": 10},
              "decks": decks, "matchup_matrix": matrix, "skipped": skipped}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "ranked_decks": decks}, ensure_ascii=False))


if __name__ == "__main__":
    main()
