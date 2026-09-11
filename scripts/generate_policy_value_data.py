#!/usr/bin/env python3
"""Generate framework-neutral policy/value JSONL.GZ from self-play games."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import os
import sys
import tempfile
import time
from collections import Counter, deque
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame, HeuristicPolicy, InformationSetMCTSPolicy, RULESET
from hsa.encoding import encode_decision, feature_schema
from hsa.lineage import ruleset_manifest


def matchup_deck_counts(config_path: Path, deck_a: str, deck_b: str):
    """Decode two configured deckstrings into runtime card-count maps."""
    try:
        from hearthstone.deckstrings import Deck
    except ImportError:
        sys.path.insert(0, str(ROOT / ".deps"))
        from hearthstone.deckstrings import Deck
    config = json.loads(config_path.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in config["decks"]}
    cards = json.loads((ROOT / "cards.zhCN.json").read_text(encoding="utf-8"))
    by_dbf = {int(card["dbfId"]): card["id"] for card in cards if "dbfId" in card}

    def decode(name: str):
        deck = Deck.from_deckstring(by_id[name]["deckstring"])
        return {by_dbf[dbf_id]: count for dbf_id, count in deck.cards}

    return decode(deck_a), decode(deck_b)


class DatasetStatistics:
    """Accumulate dataset metrics without retaining completed games."""

    def __init__(self) -> None:
        self.games = 0
        self.records = 0
        self.winners: Counter[str] = Counter()
        self.legal_actions = 0
        self.nontrivial_records = 0
        self.disagreements = 0
        self.soft_targets = 0
        self.entropy = 0.0
        self.max_probability = 0.0
        self.visited_actions = 0
        self.one_hot = 0
        self.simulations = 0
        self.adaptive_decisions = 0
        self.visited_value_range = 0.0

    def add_game(self, records: list[dict]) -> None:
        self.games += 1
        if records:
            winner = records[0]["winner"]
            self.winners[
                "draw" if winner is None else f"player_{winner}"
            ] += 1
        for record in records:
            self.records += 1
            self.legal_actions += record["legal_action_count"]
            if record["legal_action_count"] <= 1:
                continue
            self.nontrivial_records += 1
            self.disagreements += (
                record.get("executed_action", record["chosen_action"])
                != record["chosen_action"]
            )
            target = record.get("policy_target")
            if target is None:
                continue
            self.soft_targets += 1
            self.entropy += -sum(
                probability * math.log(probability)
                for probability in target
                if probability > 0
            )
            self.max_probability += max(target)
            self.visited_actions += sum(probability > 0 for probability in target)
            self.one_hot += max(target) >= 1.0 - 1e-12
            self.simulations += record.get("teacher_simulations", 0)
            self.adaptive_decisions += (
                record.get("teacher_adaptive_simulations", 0) > 0
            )
            action_values = record.get("teacher_action_values", ())
            if action_values:
                visited_values = [
                    value for value, probability in zip(
                        action_values, target, strict=True
                    ) if probability > 0
                ]
                self.visited_value_range += (
                    max(visited_values) - min(visited_values)
                )

    def result(self) -> dict[str, object]:
        statistics: dict[str, object] = {
            "winner_counts": {
                key: self.winners.get(key, 0)
                for key in ("player_0", "player_1", "draw")
            },
            "mean_decisions_per_game": self.records / max(1, self.games),
            "mean_legal_actions": self.legal_actions / max(1, self.records),
            "forced_action_fraction": (
                1.0 - self.nontrivial_records / max(1, self.records)
            ),
            "teacher_behavior_disagreement_fraction": (
                self.disagreements / max(1, self.nontrivial_records)
            ),
        }
        if self.soft_targets:
            statistics["teacher_policy"] = {
                "mean_entropy": self.entropy / self.soft_targets,
                "mean_max_probability": self.max_probability / self.soft_targets,
                "mean_visited_actions": self.visited_actions / self.soft_targets,
                "one_hot_fraction": self.one_hot / self.soft_targets,
                "mean_simulations": self.simulations / self.nontrivial_records,
                "adaptive_decision_fraction": (
                    self.adaptive_decisions / self.nontrivial_records
                ),
                "mean_visited_value_range": (
                    self.visited_value_range / self.nontrivial_records
                ),
            }
        return statistics


def dataset_statistics(games: list[list[dict]]) -> dict[str, object]:
    accumulator = DatasetStatistics()
    for game in games:
        accumulator.add_game(game)
    return accumulator.result()


def generated_games(args, game_seeds: list[int]):
    """Yield completed games with bounded parallel-result memory."""
    if args.workers <= 1:
        for game_seed in game_seeds:
            yield play_game(args.cards, game_seed, args.teacher, args)
        return
    with ProcessPoolExecutor(max_workers=args.workers) as executor:
        seeds = iter(game_seeds)
        pending = deque()
        for _ in range(min(len(game_seeds), args.workers * 2)):
            game_seed = next(seeds)
            pending.append(executor.submit(
                play_game, args.cards, game_seed, args.teacher, args
            ))
        while pending:
            yield pending.popleft().result()
            try:
                game_seed = next(seeds)
            except StopIteration:
                continue
            pending.append(executor.submit(
                play_game, args.cards, game_seed, args.teacher, args
            ))


def play_game(cards: Path, seed: int, teacher: str, args) -> list[dict]:
    deck_counts = None
    if args.deck_a and args.deck_b:
        deck_counts = matchup_deck_counts(args.deck_config, args.deck_a, args.deck_b)
    game = DragonMirrorGame(cards, seed, deck_counts=deck_counts)
    if teacher == "heuristic":
        policies = [HeuristicPolicy(), HeuristicPolicy()]
    else:
        policies = [
            InformationSetMCTSPolicy(
                samples=args.samples,
                iterations_per_sample=args.iterations,
                rollout_depth=args.rollout_depth,
                seed=args.search_seed + seed * 2 + seat,
                min_simulations_per_root_action=(
                    args.min_simulations_per_root_action
                ),
                max_total_iterations=args.max_total_iterations,
            )
            for seat in (0, 1)
        ]
    if args.behavior == "teacher":
        behavior_policies = policies
    elif args.behavior == "heuristic":
        behavior_policies = [HeuristicPolicy(), HeuristicPolicy()]
    else:
        behavior_policies = [
            InformationSetMCTSPolicy(
                samples=args.behavior_samples,
                iterations_per_sample=args.behavior_iterations,
                rollout_depth=args.behavior_rollout_depth,
                seed=args.behavior_search_seed + seed * 2 + seat,
                min_simulations_per_root_action=(
                    args.behavior_min_simulations_per_root_action
                ),
                max_total_iterations=args.behavior_max_total_iterations,
            )
            for seat in (0, 1)
        ]
    records: list[dict] = []
    ply = 0
    while not game.finished and ply < args.max_actions:
        actor = game.current
        decision = encode_decision(game)
        teacher_action = policies[actor].choose(game)
        chosen = decision.action_keys.index(teacher_action.key())
        policy_target = (
            policies[actor].last_search.get("root_policy")
            if teacher == "ismcts" else None
        )
        teacher_simulations = (
            int(policies[actor].last_search.get("iterations", 0))
            if teacher == "ismcts" else 0
        )
        teacher_adaptive_simulations = (
            int(policies[actor].last_search.get("adaptive_iterations", 0))
            if teacher == "ismcts" else 0
        )
        root_action_stats = (
            policies[actor].last_search.get("root_action_stats", ())
            if teacher == "ismcts" else ()
        )
        teacher_action_values = (
            [float(item["mean_value"]) for item in root_action_stats]
            if root_action_stats else [0.0] * len(decision.actions)
        )
        teacher_action_visits = (
            [int(item["visits"]) for item in root_action_stats]
            if root_action_stats else [0] * len(decision.actions)
        )
        behavior_action = (
            teacher_action
            if behavior_policies is policies
            else behavior_policies[actor].choose(game)
        )
        executed = decision.action_keys.index(behavior_action.key())
        records.append({
            "record_type": "decision",
            "game_seed": seed,
            "ply": ply,
            "actor": actor,
            "state": decision.state,
            "actions": decision.actions,
            "chosen_action": chosen,
            "executed_action": executed,
            "policy_target": policy_target,
            "teacher_simulations": teacher_simulations,
            "teacher_adaptive_simulations": teacher_adaptive_simulations,
            "teacher_action_values": teacher_action_values,
            "teacher_action_visits": teacher_action_visits,
            "legal_action_count": len(decision.actions),
        })
        game.step(behavior_action)
        ply += 1
    if not game.finished:
        raise RuntimeError(f"game {seed} exceeded {args.max_actions} actions")
    for record in records:
        record["value_target"] = (
            0.0 if game.winner is None
            else 1.0 if game.winner == record["actor"] else -1.0
        )
        record["winner"] = game.winner
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--seed", type=int, default=202609092000)
    parser.add_argument("--teacher", choices=("heuristic", "ismcts"), default="heuristic")
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--rollout-depth", type=int, default=3)
    parser.add_argument("--min-simulations-per-root-action", type=int, default=0)
    parser.add_argument("--max-total-iterations", type=int)
    parser.add_argument("--search-seed", type=int, default=20260909)
    parser.add_argument(
        "--behavior", choices=("teacher", "heuristic", "ismcts"),
        default="teacher",
        help="Policy that advances the game; teacher still supplies labels.",
    )
    parser.add_argument("--behavior-samples", type=int, default=2)
    parser.add_argument("--behavior-iterations", type=int, default=8)
    parser.add_argument("--behavior-rollout-depth", type=int, default=3)
    parser.add_argument(
        "--behavior-min-simulations-per-root-action", type=int, default=0
    )
    parser.add_argument("--behavior-max-total-iterations", type=int)
    parser.add_argument("--behavior-search-seed", type=int, default=20260911)
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--deck-config", type=Path, default=ROOT / "config" / "decks.json")
    parser.add_argument("--deck-a")
    parser.add_argument("--deck-b")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "policy-value-smoke.jsonl.gz",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    game_seeds = [args.seed + offset for offset in range(args.games)]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=args.output.name + ".", suffix=".records.jsonl.gz",
        dir=args.output.parent,
    )
    os.close(descriptor)
    temporary_records = Path(temporary_name)
    statistics = DatasetStatistics()
    try:
        with gzip.open(temporary_records, "wt", encoding="utf-8") as handle:
            for game_records in generated_games(args, game_seeds):
                statistics.add_game(game_records)
                for record in game_records:
                    handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        generation_seconds = time.perf_counter() - started
        header = {
            "record_type": "header",
            "dataset_schema_version": 3,
            "ruleset": RULESET,
            "ruleset_fingerprint": ruleset_manifest(ROOT)["fingerprint_sha256"],
            "teacher": args.teacher,
            "teacher_budget": (
                {
                    "samples": args.samples,
                    "iterations_per_sample": args.iterations,
                    "simulations_per_decision": args.samples * args.iterations,
                    "rollout_depth": args.rollout_depth,
                    "min_simulations_per_root_action": (
                        args.min_simulations_per_root_action
                    ),
                    "max_total_iterations": args.max_total_iterations,
                }
                if args.teacher == "ismcts" else None
            ),
            "behavior": args.behavior,
            "behavior_budget": (
                {
                    "samples": args.behavior_samples,
                    "iterations_per_sample": args.behavior_iterations,
                    "simulations_per_decision": (
                        args.behavior_samples * args.behavior_iterations
                    ),
                    "rollout_depth": args.behavior_rollout_depth,
                    "min_simulations_per_root_action": (
                        args.behavior_min_simulations_per_root_action
                    ),
                    "max_total_iterations": args.behavior_max_total_iterations,
                }
                if args.behavior == "ismcts" else None
            ),
            "feature_schema": feature_schema(),
            "games": args.games,
            "workers": args.workers,
            "records": statistics.records,
            "statistics": statistics.result(),
            "generation_seconds": generation_seconds,
        }
        with gzip.open(args.output, "wt", encoding="utf-8") as output_handle:
            output_handle.write(json.dumps(header, separators=(",", ":")) + "\n")
            with gzip.open(temporary_records, "rt", encoding="utf-8") as input_handle:
                for line in input_handle:
                    output_handle.write(line)
    finally:
        temporary_records.unlink(missing_ok=True)
    print(json.dumps({**header, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
