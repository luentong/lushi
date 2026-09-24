#!/usr/bin/env python3
"""Run a reproducible, seat-balanced policy/value tournament.

This keeps one model cache per worker/NPU instead of launching a Python process
for every deck pair.  It is intentionally a low-search-budget screening stage;
the output contains every game so finalists can later be re-tested at a higher
budget without mixing the two measurements.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import signal
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor
from itertools import combinations_with_replacement
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


class GameTimeout(RuntimeError):
    """Raised inside a worker when one simulated game exceeds its budget."""


def play_with_timeout(play, cards: Path, seed: int, mcts_seat: int,
                      args: argparse.Namespace, seconds: int) -> dict:
    def expired(_signum, _frame):
        raise GameTimeout(f"game exceeded {seconds}s wall-clock limit")
    previous = signal.signal(signal.SIGALRM, expired)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        return play(cards, seed, mcts_seat, args)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def make_args(base: argparse.Namespace, deck_a: str, deck_b: str, swapped: bool,
              device: str) -> argparse.Namespace:
    """Provide the small, explicit benchmark_mcts.play contract."""
    return argparse.Namespace(
        deck_config=base.deck_config, deck_a=deck_a, deck_b=deck_b,
        swap_decks=swapped, cards=base.cards, device=device,
        baseline_device=device, npu_devices=base.npu_devices, baseline="puct",
        baseline_checkpoint=base.checkpoint, baseline_policy_only=False,
        baseline_samples=base.samples, baseline_iterations=base.iterations,
        baseline_tree_depth=base.tree_depth, baseline_rollout_depth=0,
        baseline_min_simulations_per_root_action=0,
        baseline_max_total_iterations=base.max_total_iterations,
        baseline_neural_prior_depth=base.neural_prior_depth,
        baseline_prior_first_expansion=False, mode="puct",
        checkpoint=base.checkpoint, policy_only=False, samples=base.samples,
        iterations=base.iterations, tree_depth=base.tree_depth,
        rollout_depth=0, min_simulations_per_root_action=0,
        max_total_iterations=base.max_total_iterations,
        neural_prior_depth=base.neural_prior_depth,
        prior_first_expansion=False, search_seed=base.search_seed,
        max_actions=base.max_actions,
    )


def run_chunk(worker: int, tasks: list[dict], base_dict: dict,
              task_dir_text: str) -> list[dict]:
    # Import inside the spawned worker: each gets a separate Torch/NPU context.
    from benchmark_mcts import play
    base = argparse.Namespace(**base_dict)
    device = f"npu:{worker}"
    task_dir = Path(task_dir_text)
    completed: list[dict] = []
    for task in tasks:
        task_path = task_dir / f"task-{task['index']:03d}.json"
        if task_path.exists():
            completed.extend(json.loads(task_path.read_text(encoding="utf-8"))["games"])
            continue
        args = make_args(base, task["deck_a"], task["deck_b"], task["swapped"], device)
        games = []
        for offset in range(base.pairs):
            seed = task["seed"] + offset
            # Both seats use the identical checkpoint and identical search
            # parameters.  Swapping the labels of candidate/baseline would
            # reproduce the same game, not create another sample.
            mcts_seat = 0
            try:
                game = play_with_timeout(
                    play, base.cards, seed, mcts_seat, args,
                    base.max_game_seconds,
                )
            except GameTimeout as exc:
                game = {"seed": seed, "mcts_seat": mcts_seat, "winner": None,
                        "finished": False, "timed_out": True,
                        "invalid_actions": 0, "error": str(exc)}
            except Exception as exc:
                # A single unfinished card rule must not discard the completed
                # tournament matrix or hide the card/action that caused it.
                # Persist the full worker traceback so the parent can resume
                # and we can repair the underlying rule deterministically.
                game = {"seed": seed, "mcts_seat": mcts_seat, "winner": None,
                        "finished": False, "timed_out": False,
                        "invalid_actions": 0,
                        "error": f"{type(exc).__name__}: {exc}",
                        "traceback": traceback.format_exc()}
            game["deck_a"] = task["deck_a"]
            game["deck_b"] = task["deck_b"]
            game["swapped"] = task["swapped"]
            games.append(game)
        payload = {"task": task, "worker": worker, "games": games}
        temporary = task_path.with_suffix(f".worker{worker}.tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        os.replace(temporary, task_path)
        completed.extend(games)
        print(json.dumps({"worker": worker, "done": task["index"],
                          "total": task["total"], "games": len(games)}), flush=True)
    return completed


def summarize(games: list[dict], names: dict[str, str]) -> list[dict]:
    rows = {deck: {"wins": 0, "games": 0, "first_wins": 0, "first_games": 0,
                   "second_wins": 0, "second_games": 0} for deck in names}
    excluded = 0
    for game in games:
        # DragonMirrorGame player 0 is the first player. swap_decks reverses
        # the configured deck placement, never the meaning of winner 0/1.
        first, second = game["deck_a"], game["deck_b"]
        if game["swapped"]:
            first, second = second, first
        winner = game["winner"]
        if winner not in (0, 1) or not game.get("finished", False):
            excluded += 1
            continue
        for deck, player, seat in ((first, 0, "first"), (second, 1, "second")):
            rows[deck]["games"] += 1; rows[deck][f"{seat}_games"] += 1
            if winner == player:
                rows[deck]["wins"] += 1; rows[deck][f"{seat}_wins"] += 1
    result = []
    for deck, row in rows.items():
        games_count = row["games"]
        result.append({"id": deck, "name_zh": names[deck], **row,
                       "win_rate": row["wins"] / games_count if games_count else None,
                       "first_win_rate": row["first_wins"] / row["first_games"] if row["first_games"] else None,
                       "second_win_rate": row["second_wins"] / row["second_games"] if row["second_games"] else None})
    return sorted(result, key=lambda x: (-float(x["win_rate"] or 0), x["id"])), excluded


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--pairs", type=int, default=10, help="Independent seeds per seating.")
    p.add_argument("--workers", type=int, default=4)
    p.add_argument("--npu-devices", default="0,1,2,3",
                   help="Comma-separated NPU indices used by tournament workers.")
    p.add_argument("--samples", type=int, default=1)
    p.add_argument("--iterations", type=int, default=4)
    p.add_argument("--tree-depth", type=int, default=4)
    p.add_argument("--max-total-iterations", type=int, default=4)
    p.add_argument("--neural-prior-depth", type=int, default=1)
    p.add_argument("--max-actions", type=int, default=250)
    p.add_argument("--max-game-seconds", type=int, default=30)
    p.add_argument("--search-seed", type=int, default=2026092201)
    args = p.parse_args()
    config = json.loads(args.deck_config.read_text(encoding="utf-8"))
    decks = [row["id"] for row in config["decks"]]
    names = {row["id"]: row.get("name_zh", row["id"]) for row in config["decks"]}
    tasks = []
    for left, right in combinations_with_replacement(decks, 2):
        tasks.append({"deck_a": left, "deck_b": right, "swapped": False})
        if left != right:
            tasks.append({"deck_a": left, "deck_b": right, "swapped": True})
    for index, task in enumerate(tasks):
        task.update({"index": index + 1, "total": len(tasks),
                     "seed": args.search_seed + index * 1000})
    task_dir = args.output.with_name(f"{args.output.stem}_tasks")
    task_dir.mkdir(parents=True, exist_ok=True)
    chunks = [tasks[index::args.workers] for index in range(args.workers)]
    started = time.perf_counter(); games = []
    # spawn avoids inheriting an initialized torch/NPU context from the parent.
    context = mp.get_context("spawn")
    with ProcessPoolExecutor(max_workers=args.workers, mp_context=context) as pool:
        futures = [pool.submit(run_chunk, worker, chunk, vars(args), str(task_dir))
                   for worker, chunk in enumerate(chunks) if chunk]
        for future in futures:
            games.extend(future.result())
    ranking, excluded = summarize(games, names)
    result = {"schema_version": 1, "kind": "v4e2_low_budget_screening",
              "checkpoint": str(args.checkpoint), "pairs_per_seating": args.pairs,
              "search": {"samples": args.samples, "iterations": args.iterations,
                         "tree_depth": args.tree_depth,
                         "max_total_iterations": args.max_total_iterations,
                         "neural_prior_depth": args.neural_prior_depth},
              "games": games, "excluded_games": excluded, "deck_summary": ranking,
              "elapsed_seconds": time.perf_counter() - started}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(args.output), "games": len(games),
                      "ranking": result["deck_summary"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
