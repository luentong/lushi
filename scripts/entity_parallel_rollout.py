"""Synchronous on-policy collection: CPU environments, batched device inference.

Environment subprocesses never create a model or initialize an accelerator.
One round freezes all policies; only learner decisions enter PPO. Per-game RNG
and schedule slots are independent of worker completion order.
"""
from __future__ import annotations

from collections import defaultdict, deque
import copy
import json
import math
import multiprocessing as mp
import random
import time
import traceback


def collection_jobs(args, round_index, known_decks, opponent_pool):
    from train_entity_selfplay import rollout_schedule, rollout_opponent_schedule
    base = args.seed + round_index * 100003
    schedule = rollout_schedule(sorted(known_decks), args.games_per_round, base,
                                args.deck_a, args.deck_b)
    versions = rollout_opponent_schedule(
        [name for name, _ in opponent_pool], len(schedule), base + 31,
        [a if seat == 0 else b for a, b, seat in schedule])
    jobs = [dict(slot=i, seed=base + i, deck_a=a, deck_b=b,
                 learner_seat=seat, opponent_version=versions[i], attempt=0)
            for i, (a, b, seat) in enumerate(schedule)]
    fractions = [getattr(args, "heuristic_opponent_fraction", 0.0),
                 getattr(args, "search_opponent_fraction", 0.0)]
    if any(not math.isfinite(f) or f < 0 for f in fractions) or sum(fractions) > 1:
        raise ValueError("external opponent fractions must be nonnegative and sum to at most one")
    groups = defaultdict(list)
    for job in jobs:
        groups[(job["deck_a"] if job["learner_seat"] == 0 else job["deck_b"],
                job["learner_seat"])].append(job)
    rng = random.Random(base + 73)
    for key in sorted(groups):
        group = groups[key]
        rng.shuffle(group)
        offset = 0
        for fraction, version in zip(fractions, ("external:heuristic", "external:ismcts")):
            count = math.floor(len(group) * fraction)
            for job in group[offset:offset + count]:
                job["opponent_version"] = version
            offset += count
    return jobs


def retry_job(job, count):
    return {**job, "seed": job["seed"] + count, "attempt": job["attempt"] + 1}


def _environment_worker(connection, config, known_decks):
    from hsa import DragonMirrorGame
    from hsa.observer_view import observer_view
    from benchmark_mcts import configure_search_beliefs
    game, job, actions, trace = None, None, [], []
    while True:
        try:
            command = connection.recv()
        except EOFError:
            return
        if command["kind"] == "close":
            return
        try:
            if command["kind"] == "reset":
                job, trace = command["job"], []
                ca, cla = known_decks[job["deck_a"]]
                cb, clb = known_decks[job["deck_b"]]
                game = DragonMirrorGame(config["cards"], job["seed"],
                                        deck_counts=(ca, cb), player_classes=(cla, clb),
                                        manual_mulligan=config.get("learn_mulligan", False))
                configure_search_beliefs(game, config["deck_config"])
                external = None
                if job["opponent_version"] == "external:heuristic":
                    from hsa import HeuristicPolicy
                    external = HeuristicPolicy()
                elif job["opponent_version"] == "external:ismcts":
                    from hsa.mcts import InformationSetMCTSPolicy
                    budget = config["search_opponent_iterations"]
                    external = InformationSetMCTSPolicy(samples=4,
                        iterations_per_sample=math.ceil(budget / 4), max_total_iterations=budget,
                        tree_depth=8, rollout_depth=8, seed=job["seed"])
            elif command["kind"] in ("step", "external_step"):
                if command["kind"] == "external_step":
                    if game is None or external is None or game.current == job["learner_seat"]:
                        raise ValueError("external action requested outside opponent turn")
                    selected = external.choose(game)
                    chosen = next((i for i, a in enumerate(actions) if a.key() == selected.key()), -1)
                    if chosen < 0 and game.pending_choice and game.pending_choice.get("kind") == "MULLIGAN":
                        chosen = next((i for i, a in enumerate(actions) if a.kind == "MULLIGAN_CONFIRM"), -1)
                else:
                    chosen = command["chosen"]
                if game is None or not 0 <= chosen < len(actions):
                    raise ValueError("action does not belong to outstanding observation")
                action = actions[chosen]
                trace.append({"actor": game.current, "action": action.key(), "turn": game.turn})
                game.step(action)
            else:
                raise ValueError("unknown environment command")
            if game.finished:
                connection.send({"status": "complete", "winner": game.winner,
                                 "steps": len(trace), "action_trace": trace,
                                 "first_player": game.first_player,
                                 "invalid_actions": game.invalid_actions})
            elif len(trace) >= config["max_actions"]:
                raise ValueError("truncated at action cap; excluded from PPO returns")
            else:
                actions = game.legal_actions()
                if config.get("learn_mulligan", False):
                    from train_entity_selfplay import constrain_mulligan_actions
                    actions = constrain_mulligan_actions(game, actions)
                view = observer_view(game, game.current, actions=actions,
                                     known_deck=known_decks[(job["deck_a"], job["deck_b"])[game.current]][0])
                connection.send({"status": "ready", "view": view, "actor": game.current,
                                 "step": len(trace), "action_keys": [a.key() for a in actions]})
        except Exception as exc:
            connection.send({"status": "failed", "error": f"{type(exc).__name__}: {exc}",
                             "last_step": len(trace) - 1, "actions": trace,
                             "traceback": traceback.format_exc()})


class EnvironmentPool:
    def __init__(self, workers, config, known_decks):
        self.connections, self.processes = [], []
        context = mp.get_context("spawn")
        try:
            for _ in range(workers):
                parent, child = context.Pipe()
                process = context.Process(target=_environment_worker,
                                          args=(child, config, known_decks), daemon=True)
                process.start()
                child.close()
                self.connections.append(parent)
                self.processes.append(process)
        except BaseException:
            self.close()
            raise

    def close(self):
        for pipe in self.connections:
            try:
                pipe.send({"kind": "close"})
            except (OSError, EOFError):
                pass
        for process in self.processes:
            process.join(timeout=2)
            if process.is_alive():
                process.terminate()
                process.join(timeout=2)
        for pipe in self.connections:
            pipe.close()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def collect_parallel_round(model, opponent_pool, args, device, round_index, known_decks):
    import torch
    from hsa.entity_model import collate_views
    from train_entity_selfplay import assign_ppo_advantages, terminal_return

    started = time.monotonic()
    # Frozen policies make scheduling order immaterial. Group opponents so a
    # large history pool does not fragment inference into singleton batches.
    pending = deque(sorted(collection_jobs(args, round_index, known_decks, opponent_pool),
                           key=lambda job: (job["opponent_version"], job["slot"])))
    worker_count = min(args.rollout_workers, args.games_per_round)
    config = {"cards": args.cards, "deck_config": args.deck_config, "max_actions": args.max_actions,
              "search_opponent_iterations": getattr(args, "search_opponent_iterations", 16),
              "learn_mulligan": getattr(args, "learn_mulligan", False)}
    policies = {"learner": model}
    for version, state in opponent_pool:
        frozen = copy.deepcopy(model)
        frozen.load_state_dict(state, strict=True)
        policies[version] = frozen.eval()
    completed, failures, active = {}, [], {}
    forward_count = forward_rows = 0
    inference_seconds = environment_wait_seconds = 0.0
    max_batch = 0
    last_progress = started
    with EnvironmentPool(worker_count, config, known_decks) as pool:
        while pending or active:
            for worker in range(worker_count):
                if worker not in active and pending:
                    job = pending.popleft()
                    active[worker] = {"job": job, "episode": [],
                                      "rng": random.Random(job["seed"] ^ 0x51A7E)}
                    pool.connections[worker].send({"kind": "reset", "job": job})
            ready = defaultdict(list)
            for worker in sorted(list(active)):
                before = time.monotonic()
                pipe = pool.connections[worker]
                if not pipe.poll(args.worker_timeout):
                    raise TimeoutError(f"environment worker {worker} did not respond; round is not trained")
                message = pipe.recv()
                environment_wait_seconds += time.monotonic() - before
                state = active[worker]
                job = state["job"]
                if message["status"] == "ready":
                    version = "learner" if message["actor"] == job["learner_seat"] else job["opponent_version"]
                    if version.startswith("external:"):
                        pipe.send({"kind": "external_step"})
                        continue
                    ready[version].append((worker, message))
                    continue
                del active[worker]
                if message["status"] == "failed":
                    failures.append({**job, **message})
                    if job["attempt"] < 2:
                        pending.append(retry_job(job, args.games_per_round))
                else:
                    if message["invalid_actions"]:
                        raise ValueError("completed game contained an invalid action")
                    assign_ppo_advantages(state["episode"], terminal_return(
                        message["winner"], job["learner_seat"], terminated=True),
                        mode=args.advantage_mode, gae_lambda=args.gae_lambda)
                    completed[job["slot"]] = (state["episode"], {**job, **message})
            for version, requests in ready.items():
                policy = policies[version]
                for start in range(0, len(requests), args.inference_batch_size):
                    batch_requests = requests[start:start + args.inference_batch_size]
                    before = time.monotonic()
                    with torch.no_grad():
                        logits, values = policy(collate_views(
                            [msg["view"] for _, msg in batch_requests], policy.card_ids, device))
                        probabilities = logits.softmax(-1).cpu().tolist()
                        values = values.cpu().tolist()
                    inference_seconds += time.monotonic() - before
                    forward_count += 1
                    forward_rows += len(batch_requests)
                    max_batch = max(max_batch, len(batch_requests))
                    for i, (worker, message) in enumerate(batch_requests):
                        state = active[worker]
                        job = state["job"]
                        probs = probabilities[i][:len(message["action_keys"])]
                        if not all(math.isfinite(p) and p >= 0 for p in probs) or sum(probs) <= 0:
                            raise ValueError("invalid behavior policy probabilities")
                        chosen = state["rng"].choices(range(len(probs)), weights=probs)[0]
                        if version == "learner":
                            state["episode"].append({"view": message["view"], "chosen": chosen,
                                "trace_step": message["step"], "action_key": message["action_keys"][chosen],
                                "logp": math.log(max(probs[chosen], 1e-30)), "old_value": values[i],
                                "actor": message["actor"], "game_seed": job["seed"],
                                "policy_version": round_index, "opponent_version": job["opponent_version"],
                                "deck_a": job["deck_a"], "deck_b": job["deck_b"]})
                        pool.connections[worker].send({"kind": "step", "chosen": chosen})
            now = time.monotonic()
            if now - last_progress >= 10 or not pending and not active:
                print(json.dumps({"stage": "parallel_collect", "round": round_index,
                    "games": len(completed), "planned": args.games_per_round, "failed": len(failures),
                    "active": len(active), "elapsed_seconds": now - started,
                    "mean_inference_batch": forward_rows / max(1, forward_count)}, ensure_ascii=False), flush=True)
                last_progress = now
    rows, games = [], []
    for slot in sorted(completed):
        episode, game = completed[slot]
        rows.extend(episode)
        games.append(game)
    args.last_collection_metrics = {
        "workers": worker_count, "seconds": time.monotonic() - started,
        "inference_rows": forward_rows, "inference_calls": forward_count,
        "mean_inference_batch": forward_rows / max(1, forward_count), "max_inference_batch": max_batch,
        "inference_seconds_including_collation": inference_seconds,
        "environment_wait_seconds": environment_wait_seconds,
        "sampler": "per_game_rng_v1", "completed_schedule_slots": len(completed)}
    return rows, games, failures
