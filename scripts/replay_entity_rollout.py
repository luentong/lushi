#!/usr/bin/env python3
"""Reconstruct an on-policy game exactly, or stop at a counterfactual root.

Only reports written after action_trace capture was added can be replayed.
The returned game is suitable for a separate public-belief root audit; this
script does not treat its hidden state as player-visible information.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_report_inputs(report, cards, deck_config):
    """Refuse replay when the deck, card catalog or engine source has drifted."""
    config = report.get("config", {})
    recorded = report.get("provenance", {}).get("source_sha256", {})
    for name, current in (("cards", cards), ("deck_config", deck_config)):
        expected = recorded.get(config.get(name))
        if expected is None or file_digest(current) != expected:
            raise ValueError(f"{name} differs from the saved rollout provenance")
    engine_hashes = {}
    for source, digest in recorded.items():
        normalized = source.replace("\\", "/")
        if "/src/hsa/" in normalized:
            engine_hashes[normalized.split("/src/hsa/", 1)[1]] = digest
    current_sources = {str(path.relative_to(ROOT / "src/hsa")).replace("\\", "/"): path
                       for path in (ROOT / "src/hsa").rglob("*.py")}
    if set(engine_hashes) != set(current_sources) or any(
        file_digest(current_sources[name]) != digest for name, digest in engine_hashes.items()
    ):
        raise ValueError("engine source differs from the saved rollout provenance")


def replay_game_prefix(record, cards, deck_config, *, until=None):
    from hsa import DragonMirrorGame
    from benchmark_mcts import _decoded_decks, configure_search_beliefs

    decks = _decoded_decks(deck_config)
    a, b = record["deck_a"], record["deck_b"]
    (counts_a, cls_a), (counts_b, cls_b) = decks[a], decks[b]
    game = DragonMirrorGame(cards, record["seed"],
                            deck_counts=(counts_a, counts_b),
                            player_classes=(cls_a, cls_b))
    configure_search_beliefs(game, deck_config)
    trace = record.get("action_trace")
    if trace is None:
        raise ValueError("report lacks complete action_trace; cannot reconstruct root")
    limit = len(trace) if until is None else until
    if not 0 <= limit <= len(trace):
        raise ValueError("root step out of range")
    for index, row in enumerate(trace[:limit]):
        if game.finished or game.current != row["actor"] or game.turn != row["turn"]:
            raise ValueError(f"state drift before action {index}")
        legal = game.legal_actions()
        matches = [action for action in legal if list(action.key()) == row["action"]]
        if len(matches) != 1:
            raise ValueError(f"recorded action {index} has {len(matches)} legal matches")
        game.step(matches[0])
    if until is None and (not game.finished or game.winner != record["winner"]
                          or len(trace) != record["steps"]):
        raise ValueError("terminal replay does not match the recorded game")
    return game


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--game-index", type=int, default=0)
    parser.add_argument("--step", type=int)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--deck-config", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    verify_report_inputs(report, args.cards, args.deck_config)
    rounds = [row for row in report["history"] if row["round"] == args.round]
    if len(rounds) != 1 or not 0 <= args.game_index < len(rounds[0]["games"]):
        raise ValueError("round or game index unavailable")
    record = rounds[0]["games"][args.game_index]
    game = replay_game_prefix(record, args.cards, args.deck_config, until=args.step)
    result = {"seed": record["seed"], "deck_a": record["deck_a"],
              "deck_b": record["deck_b"], "replayed_actions": len(record["action_trace"])
              if args.step is None else args.step,
              "finished": game.finished, "winner": game.winner,
              "turn": game.turn, "actor": game.current}
    if not game.finished:
        result["legal_actions"] = [list(action.key()) for action in game.legal_actions()]
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
