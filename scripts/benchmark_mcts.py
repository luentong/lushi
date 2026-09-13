#!/usr/bin/env python3
"""Seat-swapped engineering benchmark for MCTS v0 versus heuristic v1."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import (
    DeterminizedMCTSPolicy,
    DragonMirrorGame,
    HeuristicPolicy,
    InformationSetMCTSPolicy,
    MCTSPolicy,
    RULESET,
)


def matchup_deck_counts(config_path: Path, deck_a: str, deck_b: str):
    try:
        from hearthstone.deckstrings import Deck
    except ImportError:
        sys.path.insert(0, str(ROOT / ".deps"))
        from hearthstone.deckstrings import Deck
    config = json.loads(config_path.read_text(encoding="utf-8"))
    by_id = {item["id"]: item for item in config["decks"]}
    cards = json.loads((ROOT / "cards.zhCN.json").read_text(encoding="utf-8"))
    by_dbf = {int(card["dbfId"]): card["id"] for card in cards if "dbfId" in card}
    def decode(name):
        deck = Deck.from_deckstring(by_id[name]["deckstring"])
        return {by_dbf[dbf_id]: count for dbf_id, count in deck.cards}
    return decode(deck_a), decode(deck_b)
from hsa.evaluation import wilson_interval


_MODEL_CACHE = {}


def load_model(checkpoint: Path, device: str):
    key = (str(checkpoint.resolve()), device)
    if key not in _MODEL_CACHE:
        from hsa.torch_model import TorchPolicyValueModel
        _MODEL_CACHE[key] = TorchPolicyValueModel.from_checkpoint(
            str(checkpoint), device
        )
    return _MODEL_CACHE[key]


def worker_device(requested: str, npu_devices: str, seed: int) -> str:
    """Assign an NPU deterministically without making all workers use npu:0.

    A search game is sequential, so each worker owns one model instance and
    repeatedly issues small policy/value calls.  Mapping game seeds across a
    user-provided device set gives concurrent worker processes separate NPU
    contexts while retaining CPU behaviour unchanged.
    """
    if not requested.startswith("npu") or requested != "npu":
        return requested
    devices = [item.strip() for item in npu_devices.split(",") if item.strip()]
    if not devices:
        raise ValueError("--npu-devices must contain at least one device index")
    # Include the worker PID so long-running workers remain pinned to one NPU
    # even when ProcessPoolExecutor schedules several game seeds on it.
    return f"npu:{devices[os.getpid() % len(devices)]}"


def play(cards: Path, seed: int, mcts_seat: int, args: argparse.Namespace) -> dict:
    deck_counts = (
        matchup_deck_counts(args.deck_config, args.deck_a, args.deck_b)
        if args.deck_a and args.deck_b else None
    )
    if deck_counts is not None and getattr(args, "swap_decks", False):
        deck_counts = (deck_counts[1], deck_counts[0])
    game = DragonMirrorGame(cards, seed, deck_counts=deck_counts)
    candidate_device = worker_device(args.device, args.npu_devices, seed)
    baseline_device = worker_device(
        args.baseline_device, args.npu_devices, seed
    )
    policies = [HeuristicPolicy(), HeuristicPolicy()]
    if args.baseline in {"ismcts", "puct"}:
        baseline_seat = 1 - mcts_seat
        baseline_model = None
        if args.baseline == "puct":
            if args.baseline_checkpoint is None:
                raise ValueError(
                    "--baseline-checkpoint is required for puct baseline"
                )
            baseline_model = load_model(
                args.baseline_checkpoint, baseline_device
            )
            if not baseline_model.value_trained and not args.baseline_policy_only:
                raise ValueError(
                    "baseline checkpoint value head was not trained; pass "
                    "--baseline-policy-only"
                )
        policies[baseline_seat] = InformationSetMCTSPolicy(
            samples=args.baseline_samples or args.samples,
            iterations_per_sample=(
                args.baseline_iterations or args.iterations
            ),
            tree_depth=args.baseline_tree_depth or args.tree_depth,
            rollout_depth=(
                args.baseline_rollout_depth
                if args.baseline_rollout_depth is not None
                else args.rollout_depth
                if args.baseline != "puct" or args.baseline_policy_only else 0
            ),
            seed=args.search_seed + seed * 2 + baseline_seat,
            policy_value_model=baseline_model,
            use_model_value=(
                args.baseline == "puct" and not args.baseline_policy_only
            ),
            force_uniform_expansion=not args.baseline_prior_first_expansion,
            min_simulations_per_root_action=(
                args.baseline_min_simulations_per_root_action
            ),
            max_total_iterations=args.baseline_max_total_iterations,
            neural_prior_depth=args.baseline_neural_prior_depth,
        )
    if args.mode == "puct":
        if args.checkpoint is None:
            raise ValueError("--checkpoint is required for puct mode")
        model = load_model(args.checkpoint, candidate_device)
        if not args.policy_only and not model.value_trained:
            raise ValueError(
                "checkpoint value head was not trained; pass --policy-only"
            )
        search = InformationSetMCTSPolicy(
            samples=args.samples,
            iterations_per_sample=args.iterations,
            tree_depth=args.tree_depth,
            rollout_depth=args.rollout_depth if args.policy_only else 0,
            seed=args.search_seed + seed * 2 + mcts_seat,
            policy_value_model=model,
            use_model_value=not args.policy_only,
            force_uniform_expansion=not args.prior_first_expansion,
            min_simulations_per_root_action=args.min_simulations_per_root_action,
            max_total_iterations=args.max_total_iterations,
            neural_prior_depth=args.neural_prior_depth,
        )
    else:
        search = (
            InformationSetMCTSPolicy(
                samples=args.samples,
                iterations_per_sample=args.iterations,
                tree_depth=args.tree_depth,
                rollout_depth=args.rollout_depth,
                seed=args.search_seed + seed * 2 + mcts_seat,
            )
            if args.mode == "ismcts"
            else DeterminizedMCTSPolicy(
                samples=args.samples,
                iterations_per_sample=args.iterations,
                rollout_depth=args.rollout_depth,
                seed=args.search_seed + seed * 2 + mcts_seat,
            )
            if args.mode == "determinized"
            else MCTSPolicy(args.iterations, args.rollout_depth)
        )
    policies[mcts_seat] = search
    actions = searches = nodes = simulations = adaptive_searches = 0
    started = time.perf_counter()
    while not game.finished and actions < args.max_actions:
        actor = game.current
        game.step(policies[actor].choose(game))
        if actor == mcts_seat:
            searches += 1
            nodes += int(search.last_search.get("nodes", 0))
            simulations += int(search.last_search.get("iterations", 0))
            adaptive_searches += int(
                search.last_search.get("adaptive_iterations", 0) > 0
            )
        actions += 1
    return {
        "seed": seed,
        "mcts_seat": mcts_seat,
        "winner": game.winner,
        "mcts_win": game.winner == mcts_seat,
        "finished": game.finished,
        "invalid_actions": game.invalid_actions,
        "turns": game.turn,
        "actions": actions,
        "searches": searches,
        "nodes": nodes,
        "simulations": simulations,
        "adaptive_searches": adaptive_searches,
        "elapsed_seconds": time.perf_counter() - started,
        "candidate_device": candidate_device,
        "baseline_device": baseline_device,
    }


def _new_live_match(
    cards: Path, seed: int, mcts_seat: int, args: argparse.Namespace,
) -> dict:
    """Build one match without advancing it.

    ``play_batched_root_priors`` interleaves many such matches. This lets a
    single NPU evaluate their visible root states together, while each match's
    CPU-side ISMCTS remains deterministic and independent.
    """
    deck_counts = (
        matchup_deck_counts(args.deck_config, args.deck_a, args.deck_b)
        if args.deck_a and args.deck_b else None
    )
    if deck_counts is not None and args.swap_decks:
        deck_counts = (deck_counts[1], deck_counts[0])
    game = DragonMirrorGame(cards, seed, deck_counts=deck_counts)
    candidate_device = worker_device(args.device, args.npu_devices, seed)
    baseline_device = worker_device(args.baseline_device, args.npu_devices, seed)
    policies = [HeuristicPolicy(), HeuristicPolicy()]
    if args.baseline in {"ismcts", "puct"}:
        baseline_seat = 1 - mcts_seat
        baseline_model = (
            load_model(args.baseline_checkpoint, baseline_device)
            if args.baseline == "puct" else None
        )
        policies[baseline_seat] = InformationSetMCTSPolicy(
            samples=args.baseline_samples or args.samples,
            iterations_per_sample=args.baseline_iterations or args.iterations,
            tree_depth=args.baseline_tree_depth or args.tree_depth,
            rollout_depth=(
                args.baseline_rollout_depth
                if args.baseline_rollout_depth is not None
                else args.rollout_depth
            ),
            seed=args.search_seed + seed * 2 + baseline_seat,
            policy_value_model=baseline_model,
            use_model_value=False,
            force_uniform_expansion=not args.baseline_prior_first_expansion,
            min_simulations_per_root_action=(
                args.baseline_min_simulations_per_root_action
            ),
            max_total_iterations=args.baseline_max_total_iterations,
            neural_prior_depth=args.baseline_neural_prior_depth,
        )
    model = load_model(args.checkpoint, candidate_device)
    policies[mcts_seat] = InformationSetMCTSPolicy(
        samples=args.samples,
        iterations_per_sample=args.iterations,
        tree_depth=args.tree_depth,
        rollout_depth=args.rollout_depth,
        seed=args.search_seed + seed * 2 + mcts_seat,
        policy_value_model=model,
        use_model_value=False,
        force_uniform_expansion=not args.prior_first_expansion,
        min_simulations_per_root_action=args.min_simulations_per_root_action,
        max_total_iterations=args.max_total_iterations,
        neural_prior_depth=args.neural_prior_depth,
    )
    return {
        "seed": seed,
        "mcts_seat": mcts_seat,
        "game": game,
        "policies": policies,
        "candidate_device": candidate_device,
        "baseline_device": baseline_device,
        "actions": 0,
        "searches": 0,
        "nodes": 0,
        "simulations": 0,
        "adaptive_searches": 0,
        "started": time.perf_counter(),
    }


def _live_match_result(match: dict) -> dict:
    game = match["game"]
    return {
        "seed": match["seed"],
        "mcts_seat": match["mcts_seat"],
        "winner": game.winner,
        "mcts_win": game.winner == match["mcts_seat"],
        "finished": game.finished,
        "invalid_actions": game.invalid_actions,
        "turns": game.turn,
        "actions": match["actions"],
        "searches": match["searches"],
        "nodes": match["nodes"],
        "simulations": match["simulations"],
        "adaptive_searches": match["adaptive_searches"],
        "elapsed_seconds": time.perf_counter() - match["started"],
        "candidate_device": match["candidate_device"],
        "baseline_device": match["baseline_device"],
    }


def play_batched_root_priors(
    jobs: list[tuple], args: argparse.Namespace,
) -> tuple[list[dict], dict[str, int]]:
    """Run policy-only root-prior PUCT matches with batched NPU inference.

    This intentionally supports only ``neural_prior_depth=1`` and heuristic
    leaf rollout. Otherwise an ISMCTS decision would require neural calls at
    different, data-dependent tree leaves and batching would silently change
    the algorithm rather than merely its execution schedule.
    """
    matches = [_new_live_match(*job) for job in jobs]
    completed: list[dict] = []
    batch_calls = batch_requests = max_batch_size = 0
    while matches:
        requests_by_model: dict[int, tuple[object, list[tuple[dict, object]]]] = {}
        for match in matches:
            game = match["game"]
            if game.finished or match["actions"] >= args.max_actions:
                continue
            policy = match["policies"][game.current]
            if (
                isinstance(policy, InformationSetMCTSPolicy)
                and policy.policy_value_model is not None
                and policy.neural_prior_depth == 1
                and not policy.use_model_value
                and len(game.legal_actions()) > 1
            ):
                key = id(policy.policy_value_model)
                if key not in requests_by_model:
                    requests_by_model[key] = (policy.policy_value_model, [])
                requests_by_model[key][1].append((match, policy))

        prepared: dict[tuple[int, int], object] = {}
        for model, entries in requests_by_model.values():
            batch = [(item["game"], item["game"].legal_actions()) for item, _ in entries]
            outputs = model.predict_batch(batch)
            batch_calls += 1
            batch_requests += len(batch)
            max_batch_size = max(max_batch_size, len(batch))
            for (match, policy), output in zip(entries, outputs, strict=True):
                prepared[(id(match), id(policy))] = output

        next_matches: list[dict] = []
        for match in matches:
            game = match["game"]
            if not game.finished and match["actions"] < args.max_actions:
                actor = game.current
                policy = match["policies"][actor]
                prediction = prepared.get((id(match), id(policy)))
                if prediction is not None:
                    action = policy.choose(game, root_prediction=prediction)
                else:
                    action = policy.choose(game)
                game.step(action)
                if actor == match["mcts_seat"]:
                    search = policy
                    match["searches"] += 1
                    match["nodes"] += int(search.last_search.get("nodes", 0))
                    match["simulations"] += int(search.last_search.get("iterations", 0))
                    match["adaptive_searches"] += int(
                        search.last_search.get("adaptive_iterations", 0) > 0
                    )
                match["actions"] += 1
            if game.finished or match["actions"] >= args.max_actions:
                completed.append(_live_match_result(match))
            else:
                next_matches.append(match)
        matches = next_matches
    return completed, {
        "root_prior_batch_calls": batch_calls,
        "root_prior_batch_requests": batch_requests,
        "root_prior_batch_max_size": max_batch_size,
    }


def _batched_worker(
    jobs: list[tuple], args: argparse.Namespace, worker_index: int,
) -> tuple[list[dict], dict[str, int]]:
    """Run one batch actor pinned to one requested NPU, when applicable."""
    local_args = argparse.Namespace(**vars(args))
    devices = [item.strip() for item in args.npu_devices.split(",") if item.strip()]
    if args.device == "npu":
        local_args.device = f"npu:{devices[worker_index % len(devices)]}"
    if args.baseline_device == "npu":
        local_args.baseline_device = f"npu:{devices[worker_index % len(devices)]}"
    return play_batched_root_priors(jobs, local_args)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=int, default=5)
    parser.add_argument("--seed", type=int, default=202609090501)
    parser.add_argument("--iterations", type=int, default=12)
    parser.add_argument("--rollout-depth", type=int, default=8)
    parser.add_argument(
        "--mode", choices=("full", "determinized", "ismcts", "puct"), default="full"
    )
    parser.add_argument("--samples", type=int, default=4)
    parser.add_argument("--tree-depth", type=int, default=8)
    parser.add_argument("--min-simulations-per-root-action", type=int, default=0)
    parser.add_argument("--max-total-iterations", type=int)
    parser.add_argument(
        "--neural-prior-depth",
        type=int,
        help="limit neural policy priors to this many tree levels; 1 is root only",
    )
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument(
        "--policy-only", action="store_true",
        help="use checkpoint priors but retain heuristic rollout leaf values",
    )
    parser.add_argument(
        "--prior-first-expansion", action="store_true",
        help="experimental PUCT expansion that may revisit before all actions",
    )
    parser.add_argument("--device", default="cpu")
    parser.add_argument(
        "--npu-devices", default="0,1,2,3",
        help="comma-separated NPU indices used when --device=npu",
    )
    parser.add_argument("--baseline-checkpoint", type=Path)
    parser.add_argument("--baseline-device", default="cpu")
    parser.add_argument("--baseline-samples", type=int)
    parser.add_argument("--baseline-iterations", type=int)
    parser.add_argument("--baseline-tree-depth", type=int)
    parser.add_argument("--baseline-rollout-depth", type=int)
    parser.add_argument(
        "--baseline-min-simulations-per-root-action", type=int, default=0
    )
    parser.add_argument("--baseline-max-total-iterations", type=int)
    parser.add_argument(
        "--baseline-neural-prior-depth",
        type=int,
        help="limit baseline neural priors to this many tree levels; 1 is root only",
    )
    parser.add_argument(
        "--baseline-policy-only", action="store_true",
        help="use baseline checkpoint priors with heuristic rollout values",
    )
    parser.add_argument(
        "--baseline-prior-first-expansion", action="store_true",
        help="use experimental prior-first expansion for a PUCT baseline",
    )
    parser.add_argument("--search-seed", type=int, default=20260909)
    parser.add_argument("--max-actions", type=int, default=1000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--batch-root-priors",
        action="store_true",
        help=(
            "interleave matches and batch policy-only root-prior PUCT "
            "inference; requires prior depth 1"
        ),
    )
    parser.add_argument(
        "--baseline", choices=("heuristic", "ismcts", "puct"), default="heuristic"
    )
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--deck-config", type=Path, default=ROOT / "config" / "decks.json")
    parser.add_argument("--deck-a")
    parser.add_argument("--deck-b")
    parser.add_argument("--swap-decks", action="store_true",
                        help="place deck B in player 0 and deck A in player 1")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "mcts-smoke.json")
    args = parser.parse_args()
    jobs = [
        (args.cards, args.seed + offset, seat, args)
        for offset in range(args.pairs) for seat in (0, 1)
    ]
    benchmark_started = time.perf_counter()
    games = []
    batch_stats: dict[str, int] = {}
    if args.batch_root_priors:
        if (
            args.mode != "puct"
            or not args.policy_only
            or args.neural_prior_depth != 1
            or args.checkpoint is None
        ):
            raise ValueError(
                "--batch-root-priors requires policy-only PUCT, a checkpoint, "
                "and --neural-prior-depth 1"
            )
        if args.baseline == "puct" and (
            not args.baseline_policy_only
            or args.baseline_neural_prior_depth != 1
            or args.baseline_checkpoint is None
        ):
            raise ValueError(
                "batched PUCT baseline requires --baseline-policy-only, "
                "--baseline-neural-prior-depth 1, and a checkpoint"
            )
        if args.device == "npu":
            npu_count = len(
                [item for item in args.npu_devices.split(",") if item.strip()]
            )
            if args.workers > npu_count:
                raise ValueError(
                    "--batch-root-priors workers cannot exceed --npu-devices "
                    "when candidate --device=npu"
                )
        if args.workers == 1:
            games, batch_stats = play_batched_root_priors(jobs, args)
            for count in range(1, len(games) + 1):
                print(f"progress {count}/{len(jobs)} games", flush=True)
        else:
            shards = [jobs[index::args.workers] for index in range(args.workers)]
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = [
                    executor.submit(_batched_worker, shard, args, index)
                    for index, shard in enumerate(shards) if shard
                ]
                for future in as_completed(futures):
                    shard_games, shard_stats = future.result()
                    games.extend(shard_games)
                    for key, value in shard_stats.items():
                        if key == "root_prior_batch_max_size":
                            batch_stats[key] = max(batch_stats.get(key, 0), value)
                        else:
                            batch_stats[key] = batch_stats.get(key, 0) + value
                    print(f"progress {len(games)}/{len(jobs)} games", flush=True)
    elif args.workers > 1:
        with ProcessPoolExecutor(max_workers=args.workers) as executor:
            futures = [executor.submit(play, *job) for job in jobs]
            for future in as_completed(futures):
                games.append(future.result())
                print(
                    f"progress {len(games)}/{len(jobs)} games",
                    flush=True,
                )
    else:
        for job in jobs:
            games.append(play(*job))
            print(f"progress {len(games)}/{len(jobs)} games", flush=True)
    games.sort(key=lambda row: (row["seed"], row["mcts_seat"]))
    wins = sum(row["mcts_win"] for row in games)
    summary = {
        "schema_version": 1,
        "ruleset": RULESET,
        "candidate": (
            "policy-prior-puct-v1" if args.mode == "puct" and args.policy_only
            else "policy-value-puct-v1" if args.mode == "puct"
            else "shared-tree-ismcts-v1" if args.mode == "ismcts"
            else "root-determinized-mcts-v3" if args.mode == "determinized"
            else "mcts-full-state-v0"
        ),
        "information_mode": (
            "public_dragon_mirror_v3"
            if args.mode in {"determinized", "ismcts", "puct"} else "debug_full_state"
        ),
        "baseline": (
            "policy-prior-puct-v1"
            if args.baseline == "puct"
            else "shared-tree-ismcts-v1"
            if args.baseline == "ismcts"
            else "heuristic-tempo-v1"
        ),
        "baseline_checkpoint": (
            str(args.baseline_checkpoint)
            if args.baseline_checkpoint is not None else None
        ),
        "baseline_device": (
            args.baseline_device if args.baseline == "puct" else None
        ),
        "baseline_policy_only": (
            args.baseline_policy_only if args.baseline == "puct" else None
        ),
        "baseline_samples": (
            (args.baseline_samples or args.samples)
            if args.baseline in {"ismcts", "puct"} else None
        ),
        "baseline_iterations": (
            (args.baseline_iterations or args.iterations)
            if args.baseline in {"ismcts", "puct"} else None
        ),
        "baseline_tree_depth": (
            (args.baseline_tree_depth or args.tree_depth)
            if args.baseline in {"ismcts", "puct"} else None
        ),
        "baseline_rollout_depth": (
            args.baseline_rollout_depth
            if args.baseline_rollout_depth is not None
            else args.rollout_depth
            if args.baseline in {"ismcts", "puct"} else None
        ),
        "baseline_min_simulations_per_root_action": (
            args.baseline_min_simulations_per_root_action
            if args.baseline in {"ismcts", "puct"} else None
        ),
        "baseline_max_total_iterations": (
            args.baseline_max_total_iterations
            if args.baseline in {"ismcts", "puct"} else None
        ),
        "baseline_neural_prior_depth": (
            args.baseline_neural_prior_depth
            if args.baseline == "puct" else None
        ),
        "iterations": args.iterations,
        "min_simulations_per_root_action": (
            args.min_simulations_per_root_action
            if args.mode in {"ismcts", "puct"} else 0
        ),
        "max_total_iterations": (
            args.max_total_iterations
            if args.mode in {"ismcts", "puct"} else None
        ),
        "neural_prior_depth": (
            args.neural_prior_depth if args.mode == "puct" else None
        ),
        "tree_depth": args.tree_depth if args.mode in {"ismcts", "puct"} else None,
        "rollout_depth": (
            args.rollout_depth
            if args.mode != "puct" or args.policy_only else 0
        ),
        "leaf_value_source": (
            "heuristic_rollout" if args.mode == "puct" and args.policy_only
            else "model" if args.mode == "puct" else "heuristic_rollout"
        ),
        "candidate_expansion_mode": (
            "puct_prior"
            if args.mode == "puct" and args.prior_first_expansion
            else "force_unvisited" if args.mode == "puct" else "uct"
        ),
        "baseline_expansion_mode": (
            "puct_prior"
            if args.baseline == "puct" and args.baseline_prior_first_expansion
            else "force_unvisited" if args.baseline == "puct" else "uct"
        ),
        "samples": args.samples if args.mode in {"determinized", "ismcts", "puct"} else 1,
        "checkpoint": str(args.checkpoint) if args.mode == "puct" else None,
        "device": args.device if args.mode == "puct" else None,
        "workers": args.workers,
        "batch_root_priors": args.batch_root_priors,
        **batch_stats,
        "pairs": args.pairs,
        "games": len(games),
        "finished": sum(row["finished"] for row in games),
        "invalid_actions": sum(row["invalid_actions"] for row in games),
        "mcts_wins": wins,
        "mcts_win_rate": wins / len(games),
        "mcts_win_rate_wilson95": wilson_interval(wins, len(games)),
        "elapsed_seconds": sum(row["elapsed_seconds"] for row in games),
        "wall_clock_seconds": time.perf_counter() - benchmark_started,
        "searches": sum(row["searches"] for row in games),
        "nodes": sum(row["nodes"] for row in games),
        "simulations": sum(row["simulations"] for row in games),
        "adaptive_searches": sum(row["adaptive_searches"] for row in games),
    }
    summary["mean_simulations_per_search"] = (
        summary["simulations"] / summary["searches"]
        if summary["searches"] else 0.0
    )
    document = {"summary": summary, "games": games}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes((json.dumps(document, indent=2) + "\n").encode())
    print(json.dumps(summary, indent=2))
    return 0 if summary["finished"] == summary["games"] and not summary["invalid_actions"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
