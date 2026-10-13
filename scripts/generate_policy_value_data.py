#!/usr/bin/env python3
"""Generate framework-neutral policy/value JSONL.GZ from self-play games."""

from __future__ import annotations

import argparse
import gzip
import hashlib
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
from hsa.deck_metadata import apply_deck_metadata_overrides
from hsa.encoding import (
    configure_card_vocab, encode_decision, encode_state,
    feature_schema,
)
from hsa.lineage import ruleset_manifest


_NEURAL_TEACHERS = {}


def validate_teacher_alignment(action_keys, search):
    """Reject missing, reordered or collapsed root labels before writing a row."""
    keys = tuple(tuple(key) for key in action_keys)
    if len(keys) != len(set(keys)):
        raise ValueError("duplicate concrete action keys in encoded decision")
    root_keys = search.get("root_action_keys")
    if root_keys is None or tuple(tuple(key) for key in root_keys) != keys:
        raise ValueError("teacher root action keys differ from encoded decision")
    policy = search.get("root_policy")
    if policy is None or len(policy) != len(keys):
        raise ValueError("teacher policy target/action length mismatch")
    stats = search.get("root_action_stats")
    if stats is not None and len(stats) != len(keys):
        raise ValueError("teacher action statistics/action length mismatch")


def neural_teacher_kwargs(args):
    """Load once per worker; fail on schema drift instead of silently relabeling."""
    checkpoint = getattr(args, "teacher_checkpoint", None)
    if checkpoint is None:
        return {}
    device = getattr(args, "teacher_device", "cpu")
    mode = getattr(args, "teacher_value_mode", "prior-only")
    path = Path(checkpoint).resolve()
    key = (str(path), path.stat().st_mtime_ns, device)
    before = feature_schema()
    if key not in _NEURAL_TEACHERS:
        if str(device).startswith("npu"):
            import torch_npu  # noqa: F401 -- registers the explicit NPU device
        from hsa.torch_model import TorchPolicyValueModel
        _NEURAL_TEACHERS[key] = TorchPolicyValueModel.from_checkpoint(str(path), device)
    model = _NEURAL_TEACHERS[key]
    if before != feature_schema() or model.model.state_size != before["state_size"]:
        raise ValueError("teacher checkpoint and requested dataset schema differ; migrate explicitly")
    if mode == "trained" and not model.value_trained:
        raise ValueError("requested model value but checkpoint value head is untrained")
    return {"policy_value_model": model, "use_model_value": mode == "trained",
            "force_uniform_expansion": False}


def neural_teacher_metadata(args):
    checkpoint = getattr(args, "teacher_checkpoint", None)
    if checkpoint is None:
        return None
    path = Path(checkpoint).resolve()
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return {"checkpoint": str(path), "sha256": digest.hexdigest(),
            "device": args.teacher_device, "value_mode": args.teacher_value_mode}


def action_value_policy_target(
    action_values: list[float] | tuple[float, ...],
    action_visits: list[int] | tuple[int, ...],
    temperature: float,
) -> list[float]:
    """Build an experimental policy target from visited root-action Q values.

    Unvisited actions are deliberately masked rather than assigned an arbitrary
    Q value.  This is an opt-in alternative to MCTS visit-count targets, not a
    claim that noisy finite-budget Q estimates are optimal labels.
    """
    if not math.isfinite(temperature) or temperature <= 0:
        raise ValueError("policy action-value temperature must be finite and positive")
    if not action_values or len(action_values) != len(action_visits):
        raise ValueError("action values and visits must be non-empty and aligned")
    values = [float(value) for value in action_values]
    visits = [int(count) for count in action_visits]
    if any(not math.isfinite(value) for value in values):
        raise ValueError("action values must be finite")
    if any(count < 0 for count in visits):
        raise ValueError("action visits must be non-negative")
    visited = [index for index, count in enumerate(visits) if count > 0]
    if not visited:
        return [0.0] * len(values)
    maximum = max(values[index] for index in visited)
    weights = [
        math.exp(max(-80.0, (values[index] - maximum) / temperature))
        if index in visited else 0.0
        for index in range(len(values))
    ]
    total = sum(weights)
    return [weight / total for weight in weights]


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
    by_dbf = {int(card["dbfId"]): card for card in cards if "dbfId" in card}
    apply_deck_metadata_overrides(by_dbf)

    def decode(name: str):
        deck = Deck.from_deckstring(by_id[name]["deckstring"])
        if len(deck.heroes) != 1:
            raise ValueError(f"deck {name} must have exactly one hero")
        hero = by_dbf[deck.heroes[0]]
        card_class = str(hero.get("cardClass", ""))
        if not card_class:
            raise ValueError(f"deck {name} hero lacks cardClass")
        return (
            {by_dbf[dbf_id]["id"]: count for dbf_id, count in deck.cards},
            card_class,
        )

    return decode(deck_a), decode(deck_b)


class DatasetStatistics:
    """Accumulate dataset metrics without retaining completed games."""

    def __init__(self) -> None:
        self.games = 0
        self.records = 0
        self.gameplay_records = 0
        self.teacher_nontrivial_records = 0
        self.conditional_records = 0
        self.conditional_trigger_depths: Counter[int] = Counter()
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
        self.conditional_target_quality_count = 0
        self.conditional_target_agreement = 0.0
        self.conditional_target_value_std = 0.0

    def add_game(self, records: list[dict]) -> None:
        self.games += 1
        if records:
            winner = records[0]["winner"]
            self.winners[
                "draw" if winner is None else f"player_{winner}"
            ] += 1
        for record in records:
            self.records += 1
            is_conditional = bool(record.get("conditional", False))
            self.conditional_records += int(is_conditional)
            if is_conditional:
                self.conditional_trigger_depths[
                    int(record.get("conditional_trigger_depth", 1))
                ] += 1
            self.gameplay_records += int(not is_conditional)
            if is_conditional:
                agreement = record.get("conditional_target_top_action_agreement")
                value_std = record.get("conditional_target_mean_value_std")
                if agreement is not None and value_std is not None:
                    self.conditional_target_quality_count += 1
                    self.conditional_target_agreement += float(agreement)
                    self.conditional_target_value_std += float(value_std)
            self.legal_actions += record["legal_action_count"]
            if record["legal_action_count"] <= 1:
                continue
            self.nontrivial_records += 1
            if not is_conditional:
                self.teacher_nontrivial_records += 1
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
            if not is_conditional:
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
            "mean_decisions_per_game": self.gameplay_records / max(1, self.games),
            "training_decision_records": self.records,
            "conditional_decision_records": self.conditional_records,
            "conditional_trigger_depth_counts": {
                str(depth): count
                for depth, count in sorted(self.conditional_trigger_depths.items())
            },
            "mean_legal_actions": self.legal_actions / max(1, self.records),
            "forced_action_fraction": (
                1.0 - self.nontrivial_records / max(1, self.records)
            ),
            "teacher_behavior_disagreement_fraction": (
                self.disagreements / max(1, self.teacher_nontrivial_records)
            ),
            "conditional_target_quality": {
                "records_with_repeat_metrics": self.conditional_target_quality_count,
                "mean_top_action_agreement": (
                    self.conditional_target_agreement
                    / max(1, self.conditional_target_quality_count)
                ),
                "mean_action_value_std": (
                    self.conditional_target_value_std
                    / max(1, self.conditional_target_quality_count)
                ),
            },
        }
        if self.soft_targets:
            statistics["teacher_policy"] = {
                "mean_entropy": self.entropy / self.soft_targets,
                "mean_max_probability": self.max_probability / self.soft_targets,
                "mean_visited_actions": self.visited_actions / self.soft_targets,
                "one_hot_fraction": self.one_hot / self.soft_targets,
                "mean_simulations": self.simulations / max(1, self.teacher_nontrivial_records),
                "adaptive_decision_fraction": (
                    self.adaptive_decisions / max(1, self.teacher_nontrivial_records)
                ),
                "mean_visited_value_range": (
                    self.visited_value_range / max(1, self.nontrivial_records)
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


def independent_conditional_targets(policy, actor: int, args, seed: int, ply: int,
                                    known_deck=None):
    """Re-search observed chance branches in fresh, independently seeded trees.

    Branch states contain one sampled hidden world, but each new ISMCTS call
    rebuilds PublicBelief from that observation and resamples hidden zones.
    Only averaged root policy/value targets are returned; runtime game objects
    are never serialized into training records.
    """
    branches = policy.conditional_training_states[:args.conditional_training_max_branches]
    if getattr(args, "export_observer_view", False):
        from hsa.observer_view import observer_view
    examples = []
    for branch_index, branch in enumerate(branches):
        branch_game = branch["game"]
        if (branch_game.finished or branch_game.current != actor
                or branch_game.pending_choice is not None):
            continue
        decision = encode_decision(branch_game)
        branch_actions = branch_game.legal_actions()
        if tuple(action.key() for action in branch_actions) != decision.action_keys:
            raise ValueError("conditional search action order differs from encoded actions")
        action_count = len(decision.actions)
        if action_count < 2:
            continue
        policy_rows = []
        value_rows = []
        visit_rows = []
        for repeat in range(args.conditional_training_repeats):
            fresh_search = InformationSetMCTSPolicy(
                samples=1,
                iterations_per_sample=args.conditional_training_iterations,
                rollout_depth=args.rollout_depth,
                seed=(args.search_seed + seed * 1000003 + ply * 1009
                      + branch_index * 97 + repeat),
                **neural_teacher_kwargs(args),
            )
            fresh_search.choose(branch_game.clone(record_events=False))
            validate_teacher_alignment(decision.action_keys, fresh_search.last_search)
            target = fresh_search.last_search.get("root_policy")
            stats = fresh_search.last_search.get("root_action_stats", ())
            # Encoding and search both preserve legal-action order. Skip a
            # branch if future canonicalization changes that contract.
            if target is None or len(target) != action_count or len(stats) != action_count:
                policy_rows = []
                break
            policy_rows.append([float(value) for value in target])
            value_rows.append([float(item["mean_value"]) for item in stats])
            visit_rows.append([int(item["visits"]) for item in stats])
        if not policy_rows:
            continue
        mean_policy = [
            sum(row[i] for row in policy_rows) / len(policy_rows)
            for i in range(action_count)
        ]
        total = sum(mean_policy)
        if total <= 0:
            continue
        mean_policy = [value / total for value in mean_policy]
        mean_values = [
            sum(row[i] for row in value_rows) / len(value_rows)
            for i in range(action_count)
        ]
        mean_visits = [
            sum(row[i] for row in visit_rows)
            for i in range(action_count)
        ]
        target_source = "independent_public_belief_search"
        if getattr(args, "policy_target_source", "visits") == "action-values":
            q_target = action_value_policy_target(
                mean_values, mean_visits,
                getattr(args, "policy_action_value_temperature", 0.15),
            )
            if sum(q_target) > 0:
                mean_policy = q_target
                target_source = "independent_public_belief_action_values"
        top_actions = [max(range(action_count), key=row.__getitem__)
                       for row in policy_rows]
        conditional_agreement = max(
            top_actions.count(action) for action in set(top_actions)
        ) / len(top_actions)
        if len(value_rows) > 1:
            value_variance = sum(
                sum((row[i] - mean_values[i]) ** 2 for row in value_rows)
                / (len(value_rows) - 1)
                for i in range(action_count)
            ) / action_count
            value_std = math.sqrt(value_variance)
        else:
            value_std = 0.0
        target_entropy = -sum(
            probability * math.log(probability)
            for probability in mean_policy if probability > 0
        )
        examples.append({
            "state": list(decision.state),
            "actions": [list(action) for action in decision.actions],
            "chosen_action": max(range(action_count), key=mean_policy.__getitem__),
            "policy_target": mean_policy,
            "teacher_action_values": mean_values,
            "conditional_root_action": branch["root_action"],
            "conditional_trigger_depth": branch.get("trigger_depth", 1),
            "conditional_observation_visits": branch["observation_visits"],
            "conditional_policy_visits": branch["policy_visits"],
            "conditional_target_repeats": len(policy_rows),
            "conditional_target_iterations": args.conditional_training_iterations,
            "conditional_target_source": target_source,
            "policy_target_source": target_source,
            "conditional_target_top_action_agreement": conditional_agreement,
            "conditional_target_mean_value_std": value_std,
            "conditional_target_entropy": target_entropy,
            "action_keys": decision.action_keys,
            **({"observer_view": observer_view(
                branch_game, actor, actions=branch_actions, known_deck=known_deck,
            )} if getattr(args, "export_observer_view", False) else {}),
        })
    return examples


def play_game(cards: Path, seed: int, teacher: str, args) -> list[dict]:
    from hsa.dragon_mirror import DRAGON_DECK_COUNTS
    neural_kwargs = neural_teacher_kwargs(args)
    deck_counts = None
    player_classes = ("WARRIOR", "WARRIOR")
    if args.deck_a and args.deck_b:
        decoded = matchup_deck_counts(args.deck_config, args.deck_a, args.deck_b)
        (counts_a, class_a), (counts_b, class_b) = decoded
        deck_counts = (counts_a, counts_b)
        player_classes = (class_a, class_b)
    game = DragonMirrorGame(
        cards, seed, deck_counts=deck_counts, player_classes=player_classes
    )
    if deck_counts is not None:
        from benchmark_mcts import configure_search_beliefs
        configure_search_beliefs(game, args.deck_config)
    if teacher == "heuristic":
        policies = [HeuristicPolicy(), HeuristicPolicy()]
    else:
        policies = [
            InformationSetMCTSPolicy(
                **neural_kwargs,
                samples=args.samples,
                iterations_per_sample=args.iterations,
                rollout_depth=args.rollout_depth,
                seed=args.search_seed + seed * 2 + seat,
                min_simulations_per_root_action=(
                    args.min_simulations_per_root_action
                ),
                max_total_iterations=args.max_total_iterations,
                min_visits_per_observed_action=(
                    args.conditional_training_min_action_visits
                    if args.collect_conditional_training else 0
                ),
                collect_conditional_training_examples=(
                    args.collect_conditional_training
                ),
                conditional_training_min_visits=(
                    args.conditional_training_min_visits
                ),
                conditional_training_max_branches=(
                    args.conditional_training_max_branches
                ),
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
        if teacher == "ismcts":
            validate_teacher_alignment(decision.action_keys, policies[actor].last_search)
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
        target_source = "visits"
        if teacher == "ismcts" and args.policy_target_source == "action-values":
            q_target = action_value_policy_target(
                teacher_action_values,
                teacher_action_visits,
                args.policy_action_value_temperature,
            )
            if sum(q_target) > 0:
                policy_target = q_target
                target_source = "action-values"
            elif policy_target is None:
                policy_target = [
                    1.0 if index == chosen else 0.0
                    for index in range(len(decision.actions))
                ]
                target_source = "chosen-action-fallback"
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
            # The scalar value head is trained for both information views of
            # this exact public state. Search can then keep one fixed root
            # player's perspective across alternating turns instead of
            # assuming independently observed values are antisymmetric.
            "opponent_value_state": list(encode_state(game, 1 - actor)),
            "actions": decision.actions,
            "action_keys": decision.action_keys,
            "chosen_action": chosen,
            "executed_action": executed,
            "policy_target": policy_target,
            "policy_target_source": target_source,
            "teacher_simulations": teacher_simulations,
            "teacher_adaptive_simulations": teacher_adaptive_simulations,
            "teacher_action_values": teacher_action_values,
            "teacher_action_visits": teacher_action_visits,
            "teacher_search_version": (
                policies[actor].last_search.get("search_rules_version", "unspecified")
                if teacher == "ismcts" else "heuristic"
            ),
            "teacher_selection_source": (policies[actor].last_search.get("selection_source", "search")
                                         if teacher == "ismcts" else "heuristic"),
            "legal_action_count": len(decision.actions),
        })
        if getattr(args, "export_observer_view", False):
            from hsa.observer_view import observer_view
            observer_actions = game.legal_actions()
            if tuple(action.key() for action in observer_actions) != decision.action_keys:
                raise ValueError("teacher search changed root action ordering/state before observer export")
            records[-1]["observer_view"] = observer_view(
                game, actor, actions=observer_actions,
                known_deck=deck_counts[actor] if deck_counts else DRAGON_DECK_COUNTS,
            )
        if teacher == "ismcts" and args.collect_conditional_training:
            if args.conditional_training_target_source == "independent-search":
                conditional_examples = independent_conditional_targets(
                    policies[actor], actor, args, seed, ply,
                    known_deck=(deck_counts[actor] if deck_counts else DRAGON_DECK_COUNTS),
                )
            else:
                conditional_examples = policies[actor].last_search.get(
                    "conditional_training_examples", ()
                )
            for conditional in conditional_examples:
                conditional_record = {
                    "record_type": "decision",
                    "game_seed": seed,
                    "ply": ply,
                    "actor": actor,
                    "state": conditional["state"],
                    "actions": conditional["actions"],
                    "chosen_action": conditional["chosen_action"],
                    "executed_action": conditional["chosen_action"],
                    "policy_target": conditional["policy_target"],
                    "teacher_action_values": conditional[
                        "teacher_action_values"
                    ],
                    "teacher_simulations": teacher_simulations,
                    "teacher_search_version": (
                        policies[actor].last_search.get(
                            "search_rules_version", "unspecified"
                        )
                    ),
                    "teacher_selection_source": "conditional_observation_search",
                    "conditional": True,
                    "conditional_root_action": conditional[
                        "conditional_root_action"
                    ],
                    "conditional_trigger_depth": conditional.get(
                        "conditional_trigger_depth", 1
                    ),
                    "conditional_observation_visits": conditional[
                        "conditional_observation_visits"
                    ],
                    "conditional_policy_visits": conditional[
                        "conditional_policy_visits"
                    ],
                    "conditional_target_repeats": conditional.get(
                        "conditional_target_repeats"
                    ),
                    "conditional_target_iterations": conditional.get(
                        "conditional_target_iterations"
                    ),
                    "conditional_target_source": conditional.get(
                        "conditional_target_source",
                        "same_search_observation_visits",
                    ),
                    "conditional_target_top_action_agreement": conditional.get(
                        "conditional_target_top_action_agreement"
                    ),
                    "conditional_target_mean_value_std": conditional.get(
                        "conditional_target_mean_value_std"
                    ),
                    "conditional_target_entropy": conditional.get(
                        "conditional_target_entropy"
                    ),
                    "legal_action_count": len(conditional["actions"]),
                    "value_target": None,
                    "value_target_valid": False,
                }
                for field in ("observer_view", "action_keys"):
                    if field in conditional:
                        conditional_record[field] = conditional[field]
                records.append(conditional_record)
        game.step(behavior_action)
        ply += 1
    if not game.finished:
        raise RuntimeError(f"game {seed} exceeded {args.max_actions} actions")
    for record in records:
        if record.get("value_target_valid", True):
            record["value_target"] = (
                0.0 if game.winner is None
                else 1.0 if game.winner == record["actor"] else -1.0
            )
            record["opponent_value_target"] = -record["value_target"]
        record["winner"] = game.winner
    return records


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--games", type=int, default=10)
    parser.add_argument("--seed", type=int, default=202609092000)
    parser.add_argument("--teacher", choices=("heuristic", "ismcts"), default="heuristic")
    parser.add_argument("--teacher-checkpoint", type=Path)
    parser.add_argument("--teacher-device", default="cpu")
    parser.add_argument("--teacher-value-mode", choices=("prior-only", "trained"), default="prior-only")
    parser.add_argument("--export-observer-view", action="store_true")
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--rollout-depth", type=int, default=3)
    parser.add_argument(
        "--policy-target-source", choices=("visits", "action-values"),
        default="visits",
        help="Optional experimental root policy target; action-values softmaxes visited-action Q estimates.",
    )
    parser.add_argument("--policy-action-value-temperature", type=float, default=0.15)
    parser.add_argument("--min-simulations-per-root-action", type=int, default=0)
    parser.add_argument("--max-total-iterations", type=int)
    parser.add_argument(
        "--collect-conditional-training", action="store_true",
        help=("Emit policy-only examples for distinct public observations after "
              "stochastic root actions; requires teacher=ismcts and tree depth >= 3."),
    )
    parser.add_argument("--conditional-training-min-visits", type=int, default=8)
    parser.add_argument("--conditional-training-min-action-visits", type=int, default=1)
    parser.add_argument(
        "--conditional-training-target-source",
        choices=("independent-search", "same-search"),
        default="independent-search",
        help="Use fresh belief-resampled search trees for branch labels by default.",
    )
    parser.add_argument("--conditional-training-repeats", type=int, default=3)
    parser.add_argument("--conditional-training-iterations", type=int, default=24)
    parser.add_argument("--conditional-training-max-branches", type=int, default=2)
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
    parser.add_argument(
        "--ruleset-label", default=RULESET,
        help="Lineage label stored in the dataset header; use a new label for pooled multi-deck data.",
    )
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--card-vocab", choices=("legacy", "expanded-executable", "frozen-file"),
        default="legacy",
        help="Identity vocabulary; expanded mode is required for multi-deck training.",
    )
    parser.add_argument(
        "--card-vocab-file", type=Path,
        help="Frozen ordered card-vocabulary manifest for a new model generation.",
    )
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--deck-config", type=Path, default=ROOT / "config" / "decks.json")
    parser.add_argument("--deck-a")
    parser.add_argument("--deck-b")
    parser.add_argument(
        "--output", type=Path,
        default=ROOT / "reports" / "policy-value-smoke.jsonl.gz",
    )
    args = parser.parse_args()
    if args.teacher_checkpoint is not None and args.teacher != "ismcts":
        parser.error("neural teacher requires --teacher ismcts")
    if args.teacher_checkpoint is not None and args.workers != 1:
        parser.error("neural teacher currently requires --workers 1; explicit device scheduling needed")
    if args.card_vocab == "frozen-file" and args.card_vocab_file is None:
        parser.error("--card-vocab frozen-file requires --card-vocab-file")
    if (not math.isfinite(args.policy_action_value_temperature)
            or args.policy_action_value_temperature <= 0):
        parser.error("--policy-action-value-temperature must be finite and positive")
    if args.collect_conditional_training and args.teacher != "ismcts":
        parser.error("--collect-conditional-training requires --teacher ismcts")
    if args.conditional_training_min_visits < 1:
        parser.error("--conditional-training-min-visits must be positive")
    if args.conditional_training_min_action_visits < 0:
        parser.error("--conditional-training-min-action-visits must be non-negative")
    if args.conditional_training_repeats < 1:
        parser.error("--conditional-training-repeats must be positive")
    if args.conditional_training_iterations < 1:
        parser.error("--conditional-training-iterations must be positive")
    if args.conditional_training_max_branches < 1:
        parser.error("--conditional-training-max-branches must be positive")
    configure_card_vocab(args.card_vocab, vocabulary_file=args.card_vocab_file)
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
            "ruleset": args.ruleset_label,
            "ruleset_fingerprint": ruleset_manifest(ROOT)["fingerprint_sha256"],
            "teacher": args.teacher,
            "neural_teacher": neural_teacher_metadata(args),
            "observer_schema": "hsa-observer-entities-v1" if args.export_observer_view else None,
            "policy_target": {
                "source": args.policy_target_source,
                "action_value_temperature": (
                    args.policy_action_value_temperature
                    if args.policy_target_source == "action-values" else None
                ),
            },
            "value_perspective": {
                "primary": "acting_player_observation",
                "auxiliary": "opponent_observation_of_same_decision_state",
                "target": "zero_sum_terminal_outcome",
            },
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
            "conditional_training": {
                "enabled": args.collect_conditional_training,
                "min_policy_visits": args.conditional_training_min_visits,
                "min_action_visits": (
                    args.conditional_training_min_action_visits
                    if args.collect_conditional_training else 0
                ),
                "target_source": args.conditional_training_target_source,
                "independent_repeats": args.conditional_training_repeats,
                "independent_iterations": args.conditional_training_iterations,
                "max_branches_per_decision": args.conditional_training_max_branches,
                "target_source_mode": args.conditional_training_target_source,
                "value_target": "masked",
            },
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
