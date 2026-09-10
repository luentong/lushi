#!/usr/bin/env python3
"""Generate framework-neutral policy/value JSONL.GZ from self-play games."""

from __future__ import annotations

import argparse
import gzip
import json
import math
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame, HeuristicPolicy, InformationSetMCTSPolicy
from hsa.encoding import encode_decision, feature_schema


def dataset_statistics(games: list[list[dict]]) -> dict[str, object]:
    records = [record for game in games for record in game]
    winner_by_seed = {
        game[0]["game_seed"]: game[0]["winner"] for game in games if game
    }
    winners = Counter(
        "draw" if winner is None else f"player_{winner}"
        for winner in winner_by_seed.values()
    )
    nontrivial_records = [
        record for record in records if record["legal_action_count"] > 1
    ]
    targets = [record.get("policy_target") for record in nontrivial_records]
    soft_targets = [target for target in targets if target is not None]
    statistics: dict[str, object] = {
        "winner_counts": {
            key: winners.get(key, 0) for key in ("player_0", "player_1", "draw")
        },
        "mean_decisions_per_game": len(records) / max(1, len(games)),
        "mean_legal_actions": sum(
            record["legal_action_count"] for record in records
        ) / max(1, len(records)),
        "forced_action_fraction": (
            1.0 - len(nontrivial_records) / max(1, len(records))
        ),
        "teacher_behavior_disagreement_fraction": sum(
            record.get("executed_action", record["chosen_action"])
            != record["chosen_action"]
            for record in nontrivial_records
        ) / max(1, len(nontrivial_records)),
    }
    if soft_targets:
        entropies = [
            -sum(probability * math.log(probability) for probability in target
                 if probability > 0)
            for target in soft_targets
        ]
        statistics["teacher_policy"] = {
            "mean_entropy": sum(entropies) / len(entropies),
            "mean_max_probability": sum(map(max, soft_targets)) / len(soft_targets),
            "mean_visited_actions": sum(
                sum(probability > 0 for probability in target)
                for target in soft_targets
            ) / len(soft_targets),
            "one_hot_fraction": sum(
                max(target) >= 1.0 - 1e-12 for target in soft_targets
            ) / len(soft_targets),
            "mean_simulations": sum(
                record.get("teacher_simulations", 0)
                for record in nontrivial_records
            ) / len(nontrivial_records),
            "adaptive_decision_fraction": sum(
                record.get("teacher_adaptive_simulations", 0) > 0
                for record in nontrivial_records
            ) / len(nontrivial_records),
            "mean_visited_value_range": sum(
                (
                    max(
                        value for value, probability in zip(
                            record.get("teacher_action_values", ()),
                            record["policy_target"], strict=True,
                        ) if probability > 0
                    )
                    - min(
                        value for value, probability in zip(
                            record.get("teacher_action_values", ()),
                            record["policy_target"], strict=True,
                        ) if probability > 0
                    )
                )
                if record.get("teacher_action_values") else 0.0
                for record in nontrivial_records
            ) / len(nontrivial_records),
        }
    return statistics


def play_game(cards: Path, seed: int, teacher: str, args) -> list[dict]:
    game = DragonMirrorGame(cards, seed)
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
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "policy-value-smoke.jsonl.gz",
    )
    args = parser.parse_args()
    started = time.perf_counter()
    game_seeds = [args.seed + offset for offset in range(args.games)]
    if args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            games = list(executor.map(
                play_game,
                [args.cards] * args.games,
                game_seeds,
                [args.teacher] * args.games,
                [args] * args.games,
            ))
    else:
        games = [
            play_game(args.cards, game_seed, args.teacher, args)
            for game_seed in game_seeds
        ]
    header = {
        "record_type": "header",
        "dataset_schema_version": 3,
        "ruleset": "dragon-warrior-closed-v2",
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
        "records": sum(map(len, games)),
        "statistics": dataset_statistics(games),
        "generation_seconds": time.perf_counter() - started,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(args.output, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(header, separators=(",", ":")) + "\n")
        for game_records in games:
            for record in game_records:
                handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    print(json.dumps({**header, "output": str(args.output)}, indent=2))


if __name__ == "__main__":
    main()
