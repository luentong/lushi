#!/usr/bin/env python3
"""Observer-v1 bootstrap and small synchronous on-policy PPO reference runner.

This is a correctness-first vertical slice, not a high-throughput league system.
Legacy teacher files need explicit observer_view exports; no fabricated upgrade.
"""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def terminal_return(winner, actor, *, terminated):
    if not terminated:
        raise ValueError("a truncated game has no Monte Carlo terminal label")
    if actor not in (0, 1):
        raise ValueError("actor must be 0 or 1")
    if winner not in (None, 0, 1):
        raise ValueError("invalid winner")
    return 0.0 if winner is None else 1.0 if actor == winner else -1.0


def file_digest(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def report_argument(value):
    """Normalize argparse paths, including repeated checkpoint arguments."""
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, (list, tuple)):
        return [report_argument(item) for item in value]
    return value


def run_provenance(args):
    """Persist exactly which inputs and source snapshot produced each model."""
    paths = list((ROOT / "src/hsa").rglob("*.py")) + [Path(__file__), args.cards, args.deck_config,
            ROOT / "scripts/entity_parallel_rollout.py", ROOT / "scripts/benchmark_mcts.py",
            ROOT / "scripts/ppo_kl_probe.py"]
    files = {str(path): file_digest(path) for path in paths}
    return {"source_sha256": files,
            "data_sha256": {str(path): file_digest(path) for path in args.data or ()},
            "init_checkpoint_sha256": file_digest(args.init_checkpoint) if args.init_checkpoint else None,
            "anchor_checkpoint_sha256": file_digest(args.anchor_checkpoint) if args.anchor_checkpoint else None,
            "history_checkpoint_sha256": {str(path): file_digest(path)
                                          for path in args.history_checkpoint or ()}}


def load_observer_records(paths, limit, seed):
    """Reservoir sample games' rows under a memory cap, retaining game seed split."""
    rng = random.Random(seed)
    rows, seen = [], 0
    for path in paths:
        opener = gzip.open if str(path).endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line in handle:
                row = json.loads(line)
                if row.get("record_type") != "decision" or row.get("conditional"):
                    continue
                if "observer_view" not in row:
                    raise ValueError(f"{path}: missing observer_view; regenerate from real state")
                if not row.get("value_target_valid", True) or row.get("value_target") is None:
                    continue
                seen += 1
                compact = {"view": row["observer_view"], "target": row["policy_target"],
                           "value": row["value_target"], "seed": row["game_seed"]}
                if not isinstance(compact["value"], (int, float)) or not -1 <= compact["value"] <= 1:
                    raise ValueError("invalid terminal value target")
                if len(rows) < limit:
                    rows.append(compact)
                else:
                    index = rng.randrange(seen)
                    if index < limit:
                        rows[index] = compact
    if not rows:
        raise ValueError("no observer records")
    return rows, seen


def select_device(name):
    import torch
    if name.startswith("npu"):
        import torch_npu  # noqa: F401
        torch.npu.set_device(name if ":" in name else "npu:0")
    device = torch.device(name)
    # Explicit requests never silently fall back to CPU.
    torch.zeros(1, device=device)
    return device


def weight_games(rows):
    """One game's many correlated decisions must not dominate shorter games."""
    counts = Counter(row["seed"] for row in rows)
    if not counts:
        raise ValueError("cannot weight an empty dataset")
    for row in rows:
        row["weight"] = len(rows) / (len(counts) * counts[row["seed"]])


def aggregate_metrics(batches):
    """Weight the partial final batch correctly; old reports omitted row counts."""
    if not batches or any(batch.get("rows", 0) <= 0 for batch in batches):
        raise ValueError("metrics require positive batch row counts")
    total = sum(batch["rows"] for batch in batches)
    return {key: sum(batch[key] * batch["rows"] for batch in batches) / total
            for key in batches[0] if key != "rows"}


def selection_score(metrics, value_weight):
    return metrics["policy_ce"] + 4 * value_weight * metrics["value_brier"]


def bootstrap_gate(selected, initial, constant_baseline):
    """Conservative engineering gate, NOT a strength/promotional criterion."""
    threshold = min(0.25, constant_baseline)
    reasons = []
    if not all(math.isfinite(v) for v in selected.values()):
        reasons.append("non-finite validation metrics")
    if selected["value_brier"] > threshold + 1e-8:
        reasons.append("value calibration is worse than a constant baseline")
    if selected["policy_ce"] > initial["policy_ce"] + 1e-8:
        reasons.append("policy holdout CE degraded from initialization")
    return {"passed": not reasons, "reasons": reasons, "brier_threshold": threshold,
            "strength_validated": False}


def reset_value_prediction(model):
    """Keep policy/trunk intact; start an unreliable critic at neutral value zero."""
    import torch
    with torch.no_grad():
        model.value[-2].weight.zero_()
        model.value[-2].bias.zero_()


def rollout_schedule(deck_ids, count, seed, deck_a=None, deck_b=None):
    """Balance seats and deck exposure even for a short prefix of a cycle."""
    first = [deck_a] if deck_a else sorted(deck_ids)
    second = [deck_b] if deck_b else sorted(deck_ids)
    if not first or not second or count < 1 or any(d not in deck_ids for d in first + second):
        raise ValueError("invalid rollout deck schedule")
    rng = random.Random(seed)
    jobs = []
    while len(jobs) < count:
        if len(first) == len(second) and set(first) == set(second):
            # One offset visits each deck exactly once in each position, and
            # puts the learner in both seats. Across all offsets every ordered
            # pairing is still covered once per seat.
            order = list(first)
            rng.shuffle(order)
            offsets = list(range(len(order)))
            rng.shuffle(offsets)
            cycle = [(order[i], order[(i + offset) % len(order)], seat)
                     for offset in offsets for i in range(len(order)) for seat in (0, 1)]
        else:
            cycle = [(a, b, seat) for a in first for b in second for seat in (0, 1)]
            rng.shuffle(cycle)
        jobs.extend(cycle)
    return jobs[:count]


def constrain_mulligan_actions(game, actions):
    """Keep sampled/evaluated mulligans finite while preserving engine legality.

    A card can legally be toggled back, but allowing an untrained stochastic
    policy to revisit the same card creates long off-policy loops.  For
    behavior collection we expose each offered card's replace transition once;
    confirmation remains available at every state.  The engine itself still
    accepts the full reversible action set.
    """
    pending = getattr(game, "pending_choice", None)
    if not pending or pending.get("kind") != "MULLIGAN":
        return actions
    selected = set(pending.get("selected", ()))
    filtered = [a for a in actions
                if a.kind != "MULLIGAN_TOGGLE" or a.source not in selected]
    return filtered or actions


def rollout_opponent_schedule(opponent_ids, count, seed, learner_decks=None):
    """Rotate frozen opponents, optionally balancing each learner deck separately."""
    if not opponent_ids or len(set(opponent_ids)) != len(opponent_ids) or count < 1:
        raise ValueError("invalid opponent pool schedule")
    rng = random.Random(seed)
    if learner_decks is not None:
        if len(learner_decks) != count:
            raise ValueError("learner_decks must match the game schedule")
        buckets = {}
        result = []
        for deck in learner_decks:
            if deck not in buckets or not buckets[deck]:
                buckets[deck] = list(opponent_ids)
                rng.shuffle(buckets[deck])
            result.append(buckets[deck].pop())
        return result
    cycle = list(opponent_ids)
    jobs = []
    while len(jobs) < count:
        rng.shuffle(cycle)
        jobs.extend(cycle)
    return jobs[:count]


def weight_ppo_games(rows):
    """Each completed game contributes the same policy/value mass.

    A long-game deck must not receive more gradient solely because it had more
    decision points. The caller shuffles after weighting, so weights are
    dataset-global rather than renormalized within each minibatch.
    """
    counts = Counter(row["game_seed"] for row in rows)
    if not counts:
        raise ValueError("cannot weight empty PPO rollouts")
    scale = len(rows) / len(counts)
    for row in rows:
        row["weight"] = scale / counts[row["game_seed"]]


def assign_ppo_advantages(episode, outcome, *, mode="terminal", gae_lambda=0.95):
    """Label one learner trajectory without treating every move as equally good.

    Consecutive rows are the learner's decisions, with opponent and chance
    transitions folded into the next observation. The critic always receives
    the observed terminal outcome; GAE changes only the actor's credit signal.
    """
    if mode not in ("terminal", "gae"):
        raise ValueError("unknown PPO advantage mode")
    if not math.isfinite(gae_lambda) or not 0 <= gae_lambda <= 1:
        raise ValueError("GAE lambda must be between zero and one")
    if not math.isfinite(outcome) or not -1 <= outcome <= 1:
        raise ValueError("invalid terminal outcome")
    if not episode:
        return
    if len({row["actor"] for row in episode}) != 1:
        raise ValueError("one learner trajectory cannot mix actors")
    next_value = outcome
    next_advantage = 0.0
    for row in reversed(episode):
        value = row["old_value"]
        if not math.isfinite(value) or not -1 <= value <= 1:
            raise ValueError("invalid old value estimate")
        row["return"] = outcome
        row["terminated"] = True
        row["truncated"] = False
        if mode == "terminal":
            row["advantage"] = outcome - value
        else:
            delta = next_value - value
            next_advantage = delta + gae_lambda * next_advantage
            row["advantage"] = next_advantage
        next_value = value


def retain_opponent_pool(pool, size):
    """Always retain the approved initialization as an anchor opponent."""
    if size < 1 or not pool or pool[0][0] != "bootstrap":
        raise ValueError("invalid anchored opponent pool")
    return pool[:1] if size == 1 else pool[:1] + pool[max(1, len(pool) - (size - 1)):]


def supervised_loss(model, rows, device, value_weight=0.5):
    import torch
    from hsa.entity_model import collate_views
    batch = collate_views([row["view"] for row in rows], model.card_ids, device)
    logits, values = model(batch)
    targets = torch.zeros_like(logits)
    for i, row in enumerate(rows):
        target = torch.tensor(row["target"], device=device)
        if (len(target) != len(row["view"]["actions"]) or not torch.isfinite(target).all()
                or (target < 0).any() or target.sum() <= 0):
            raise ValueError("invalid policy target")
        targets[i, :len(target)] = target / target.sum()
    returns = torch.tensor([row["value"] for row in rows], dtype=torch.float32, device=device)
    policy_rows = -(targets * logits.log_softmax(-1)).sum(-1)
    value_rows = (values - returns).square()
    weights = torch.tensor([r.get("weight", 1.0) for r in rows], dtype=torch.float32, device=device)
    # Dataset-global mean weight is one. Do not renormalize within each batch:
    # that would cancel weighting for batches drawn from a single game.
    loss = ((policy_rows + value_weight * value_rows) * weights).mean()
    return loss, {"rows": len(rows), "policy_ce": float(policy_rows.mean().detach()),
                  "value_brier": float((value_rows.mean() / 4).detach()),
                  "game_weighted_policy_ce": float((policy_rows * weights).mean().detach()),
                  "game_weighted_value_brier": float((value_rows * weights).mean().detach() / 4)}


def ppo_loss(model, rows, device, clip=0.2):
    import torch
    from hsa.entity_model import collate_views
    batch = collate_views([row["view"] for row in rows], model.card_ids, device)
    logits, values = model(batch)
    distribution = torch.distributions.Categorical(logits=logits)
    choices = torch.tensor([r["chosen"] for r in rows], device=device)
    old_logp = torch.tensor([r["logp"] for r in rows], device=device)
    advantages = torch.tensor([r["advantage"] for r in rows], device=device)
    returns = torch.tensor([r["return"] for r in rows], device=device)
    weights = torch.tensor([r.get("weight", 1.0) for r in rows], device=device)
    if not torch.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError("invalid PPO game weights")
    log_ratio = distribution.log_prob(choices) - old_logp
    ratio = log_ratio.exp()
    policy = -(torch.minimum(ratio * advantages,
                             ratio.clamp(1 - clip, 1 + clip) * advantages) * weights).mean()
    value = ((values - returns).square() * weights).mean()
    entropy = (distribution.entropy() * weights).mean()
    loss = policy + 0.5 * value - 0.01 * entropy
    return loss, {"policy_loss": float(policy.detach()), "value_loss": float(value.detach()),
                  "entropy": float(entropy.detach()), "approx_kl": float(((ratio - 1) - log_ratio).mean().detach())}


def collect_round(model, opponent, opponent_pool, args, device, round_index, known_decks):
    if getattr(args, "rollout_workers", 0):
        from entity_parallel_rollout import collect_parallel_round
        return collect_parallel_round(model, opponent_pool, args, device, round_index, known_decks)
    import torch
    from hsa import DragonMirrorGame
    from hsa.entity_model import collate_views
    from hsa.observer_view import observer_view
    from benchmark_mcts import configure_search_beliefs
    rows, games, failures = [], [], []
    selection_rng = random.Random(args.seed + round_index * 100003)
    schedule = rollout_schedule(sorted(known_decks), args.games_per_round,
                                args.seed + round_index * 100003, args.deck_a, args.deck_b)
    opponent_versions = rollout_opponent_schedule(
        [version for version, _ in opponent_pool], args.games_per_round,
        args.seed + round_index * 100003 + 31,
        [a if seat == 0 else b for a, b, seat in schedule])
    opponent_states = dict(opponent_pool)
    for attempt in range(args.games_per_round * 3):
        if len(games) >= args.games_per_round:
            break
        seed = args.seed + round_index * 100003 + attempt
        # Retry a failed schedule slot with a new seed; don't silently lose seats.
        a, b, learner_seat = schedule[len(games)]
        opponent_version = opponent_versions[len(games)]
        opponent.load_state_dict(opponent_states[opponent_version])
        opponent.eval()
        (counts_a, cls_a), (counts_b, cls_b) = known_decks[a], known_decks[b]
        game = DragonMirrorGame(args.cards, seed, deck_counts=(counts_a, counts_b),
                                player_classes=(cls_a, cls_b),
                                manual_mulligan=args.learn_mulligan)
        configure_search_beliefs(game, args.deck_config)
        episode = []
        step = -1
        action_trace = []
        try:
            for step in range(args.max_actions):
                if game.finished:
                    break
                actor = game.current
                actions = game.legal_actions()
                if args.learn_mulligan:
                    actions = constrain_mulligan_actions(game, actions)
                view = observer_view(game, actor, actions=actions,
                                     known_deck=(counts_a, counts_b)[actor])
                acting = model if actor == learner_seat else opponent
                with torch.no_grad():
                    logits, values = acting(collate_views([view], acting.card_ids, device))
                    probabilities = logits.softmax(-1)[0].cpu().tolist()
                chosen = selection_rng.choices(range(len(actions)), weights=probabilities)[0]
                action_trace.append({"actor": actor, "action": actions[chosen].key(), "turn": game.turn})
                if actor == learner_seat:
                    episode.append({"view": view, "chosen": chosen,
                                    "trace_step": len(action_trace) - 1,
                                    "action_key": actions[chosen].key(),
                                    "logp": math.log(max(probabilities[chosen], 1e-30)),
                                    "old_value": float(values[0]), "actor": actor,
                                    "game_seed": seed, "policy_version": round_index,
                                    "opponent_version": opponent_version,
                                    "deck_a": a, "deck_b": b})
                game.step(actions[chosen])
            if not game.finished:
                raise ValueError("truncated at action cap; excluded from PPO returns")
            if episode:
                assign_ppo_advantages(
                    episode, terminal_return(game.winner, learner_seat, terminated=True),
                    mode=args.advantage_mode, gae_lambda=args.gae_lambda)
            rows.extend(episode)
            games.append({"seed": seed, "winner": game.winner, "learner_seat": learner_seat,
                          "deck_a": a, "deck_b": b, "opponent_version": opponent_version,
                          "steps": len(action_trace), "action_trace": action_trace})
        except Exception as exc:
            failures.append({"seed": seed, "deck_a": a, "deck_b": b,
                             "opponent_version": opponent_version,
                             "error": f"{type(exc).__name__}: {exc}",
                             "last_step": step, "actions": action_trace,
                             "traceback": traceback.format_exc()})
        print(json.dumps({"stage": "collect", "round": round_index,
                          "games": len(games), "failed": len(failures)}, ensure_ascii=False), flush=True)
    # Caller persists the failures even when no valid game completes.
    return rows, games, failures


def save(model, optimizer, path, report):
    import torch
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"entity_model": model.metadata(),
               "model_state_dict": {k: v.detach().cpu() for k, v in model.state_dict().items()},
               "optimizer_state_dict": optimizer.state_dict(), "report": report}
    temporary = path.with_suffix(path.suffix + ".tmp")
    torch.save(payload, temporary)
    temporary.replace(path)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=("bootstrap", "ppo"), required=True)
    p.add_argument("--data", type=Path, nargs="*")
    p.add_argument("--init-checkpoint", type=Path)
    p.add_argument("--anchor-checkpoint", type=Path,
                   help="Approved bootstrap opponent when resuming from a later checkpoint")
    p.add_argument("--history-checkpoint", type=Path, nargs="*",
                   help="Round 1..N frozen opponents preceding --round-offset")
    p.add_argument("--round-offset", type=int, default=0,
                   help="Resume at this zero-based round; preserves the original rollout seeds")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--d-model", type=int, default=256)
    p.add_argument("--layers", type=int, default=6)
    p.add_argument("--heads", type=int, default=8)
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--epochs", type=int, default=2)
    p.add_argument("--learning-rate", type=float, default=1e-4)
    p.add_argument("--value-weight", type=float, default=0.5)
    p.add_argument("--reset-value-head", action="store_true",
                   help="Zero only critic output projection; policy and trunk are preserved")
    p.add_argument("--bootstrap-weighting", choices=("game", "row"), default="game")
    p.add_argument("--early-stopping-patience", type=int, default=2)
    p.add_argument("--max-records", type=int, default=20000)
    p.add_argument("--seed", type=int, default=20260929)
    p.add_argument("--holdout-mod", type=int, default=5)
    p.add_argument("--holdout-rem", type=int, default=0)
    p.add_argument("--rounds", type=int, default=2)
    p.add_argument("--games-per-round", type=int, default=4)
    p.add_argument("--max-actions", type=int, default=300)
    p.add_argument("--rollout-workers", type=int, default=0,
                   help="CPU environment processes sharing batched inference; zero keeps serial collection")
    p.add_argument("--inference-batch-size", type=int, default=32)
    p.add_argument("--worker-timeout", type=float, default=120)
    p.add_argument("--opponent-pool-size", type=int, default=4)
    p.add_argument("--heuristic-opponent-fraction", type=float, default=0.0)
    p.add_argument("--search-opponent-fraction", type=float, default=0.0)
    p.add_argument("--search-opponent-iterations", type=int, default=16)
    p.add_argument("--target-kl", type=float, default=0.03,
                   help="Stop PPO updates when observed old/new policy KL exceeds this limit")
    p.add_argument("--kl-guard", choices=("minibatch", "probe"), default="minibatch",
                   help="Experimental probe confirms minibatch spikes using fixed game-balanced full distributions")
    p.add_argument("--kl-probe-size", type=int, default=256)
    p.add_argument("--kl-check-interval", type=int, default=100)
    p.add_argument("--advantage-mode", choices=("terminal", "gae"), default="terminal",
                   help="GAE changes actor credit only; critic retains terminal labels")
    p.add_argument("--gae-lambda", type=float, default=0.95)
    p.add_argument("--learn-mulligan", action="store_true",
                   help="Expose mulligan choices to PPO; default uses engine baseline mulligan")
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--deck-config", type=Path, default=ROOT / "config/decision_quality_pair_decks_20260928.json")
    p.add_argument("--deck-a")
    p.add_argument("--deck-b")
    args = p.parse_args()
    external_fractions = (args.heuristic_opponent_fraction, args.search_opponent_fraction)
    if (any(not math.isfinite(f) or f < 0 for f in external_fractions)
            or sum(external_fractions) > 1 or args.search_opponent_iterations < 1):
        p.error("invalid external opponent mixture")
    if sum(external_fractions) and (args.rollout_workers < 1 or args.mode != "ppo"):
        p.error("external opponent mixture requires parallel PPO collection")
    if args.kl_probe_size < 1 or args.kl_check_interval < 1:
        p.error("KL probe settings must be positive")
    if (args.rollout_workers < 0 or args.inference_batch_size < 1 or
            not math.isfinite(args.worker_timeout) or args.worker_timeout <= 0):
        p.error("invalid parallel collection settings")
    if args.games_per_round * 3 >= 100003:
        p.error("games-per-round overlaps the next round's reserved retry seed range")
    if any(v < 1 for v in (args.batch_size, args.epochs, args.max_records,
                           args.rounds, args.games_per_round, args.max_actions, args.opponent_pool_size)):
        p.error("counts must be positive")
    if args.holdout_mod < 2 or not 0 <= args.holdout_rem < args.holdout_mod:
        p.error("invalid holdout split")
    if not math.isfinite(args.value_weight) or args.value_weight < 0 or args.early_stopping_patience < 1:
        p.error("invalid value weight or early stopping patience")
    if not math.isfinite(args.target_kl) or args.target_kl <= 0:
        p.error("target KL must be finite and positive")
    if not math.isfinite(args.gae_lambda) or not 0 <= args.gae_lambda <= 1:
        p.error("GAE lambda must be between zero and one")
    if args.mode == "bootstrap" and not args.data:
        p.error("bootstrap needs observer-exported --data")
    if args.mode == "ppo" and args.init_checkpoint is None:
        p.error("PPO requires an entity bootstrap checkpoint; no accidental random-init training")
    if args.round_offset < 0:
        p.error("round offset must be non-negative")
    if args.mode == "ppo" and args.round_offset:
        if not args.anchor_checkpoint or len(args.history_checkpoint or ()) != args.round_offset:
            p.error("resuming PPO requires anchor and one history checkpoint per completed round")
    elif args.anchor_checkpoint or args.history_checkpoint:
        p.error("anchor/history checkpoints require a positive PPO round offset")
    if args.output.exists() or args.output.with_suffix(".report.json").exists():
        p.error("output/checkpoint report already exists; choose a new run path")
    import torch
    from hsa.entity_model import EntityPolicyValueNet
    from hsa import DragonMirrorGame
    torch.set_num_threads(2)
    torch.manual_seed(args.seed)
    device = select_device(args.device)
    if args.init_checkpoint:
        payload = torch.load(args.init_checkpoint, map_location="cpu", weights_only=False)
        model = EntityPolicyValueNet.from_payload(payload)
    else:
        catalog = DragonMirrorGame(args.cards, args.seed).card_defs
        model = EntityPolicyValueNet(sorted(catalog), args.d_model, args.layers, args.heads)
    if args.reset_value_head:
        reset_value_prediction(model)
    model.to(device).eval()
    optimizer = torch.optim.AdamW(model.parameters(), lr=args.learning_rate)
    if args.mode == "ppo" and args.round_offset:
        optimizer.load_state_dict(payload["optimizer_state_dict"])
        for group in optimizer.param_groups:
            group["lr"] = args.learning_rate
    report = {"mode": args.mode, "init_checkpoint": str(args.init_checkpoint),
              "device": str(device), "parameters": sum(p.numel() for p in model.parameters()),
              "status": "running", "history": [], "failures": [], "strength_validated": False,
              "optimizer_reinitialized": not bool(args.mode == "ppo" and args.round_offset),
              "seed": args.seed, "started_at": time.time(),
              "config": {k: report_argument(v) for k, v in vars(args).items() if k != "data"},
              "provenance": run_provenance(args)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    report_path = args.output.with_suffix(".report.json")

    def progress():
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    previous_exception_hook = sys.excepthook

    def failed(exc_type, exc, tb):
        report.update(status="failed", error=f"{exc_type.__name__}: {exc}",
                      elapsed_seconds=time.time() - report["started_at"])
        progress()
        previous_exception_hook(exc_type, exc, tb)

    sys.excepthook = failed

    progress()
    if args.mode == "bootstrap":
        rows, seen = load_observer_records(args.data, args.max_records, args.seed)
        train = [r for r in rows if r["seed"] % args.holdout_mod != args.holdout_rem]
        valid = [r for r in rows if r["seed"] % args.holdout_mod == args.holdout_rem]
        if not train or not valid:
            raise ValueError("bootstrap requires both training and game-level holdout rows")
        if args.bootstrap_weighting == "game":
            weight_games(train)
        # Holdout loss is never training-weighted; report its own game macro too.
        weight_games(valid)
        probability = sum((r["value"] + 1) / 2 for r in train) / len(train)
        baseline = sum((probability - (r["value"] + 1) / 2) ** 2 for r in valid) / len(valid)
        report.update(records_seen=seen, train_rows=len(train), validation_rows=len(valid),
                      train_games=len({r["seed"] for r in train}),
                      validation_games=len({r["seed"] for r in valid}),
                      constant_value_baseline=baseline, selection_metric="policy_ce + 4 * value_weight * brier")

        def validate():
            metrics = []
            with torch.no_grad():
                for start in range(0, len(valid), args.batch_size):
                    _, item = supervised_loss(model, valid[start:start + args.batch_size], device, args.value_weight)
                    metrics.append(item)
            return metrics, aggregate_metrics(metrics)

        _, initial = validate()
        best_path = args.output.with_suffix(".best.pt")
        best_score = selection_score(initial, args.value_weight)
        report.update(initial_validation=initial,
                      selection={"epoch": 0, "path": str(best_path), "metrics": initial, "score": best_score})
        report["value_head_initialization"] = "neutral_zero" if args.reset_value_head else "checkpoint_or_random"
        save(model, optimizer, best_path, report)
        stale_epochs = 0
        progress()
        for epoch in range(1, args.epochs + 1):
            random.Random(args.seed + epoch).shuffle(train)
            stats = []
            for start in range(0, len(train), args.batch_size):
                optimizer.zero_grad(set_to_none=True)
                loss, metrics = supervised_loss(model, train[start:start + args.batch_size], device, args.value_weight)
                if not torch.isfinite(loss):
                    raise ValueError("non-finite bootstrap loss")
                loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step(); stats.append(metrics)
            validation, summary = validate()
            row = {"epoch": epoch, "train": stats, "validation": validation,
                   "train_summary": aggregate_metrics(stats), "validation_summary": summary}
            report["history"].append(row)
            score = selection_score(summary, args.value_weight)
            if score < best_score - 1e-8:
                best_score, stale_epochs = score, 0
                report["selection"] = {"epoch": epoch, "path": str(best_path), "metrics": summary, "score": score}
                save(model, optimizer, best_path, report)
            else:
                stale_epochs += 1
            report["bootstrap_gate"] = bootstrap_gate(report["selection"]["metrics"], initial, baseline)
            report["selected_value_status"] = ("neutral_untrained" if args.reset_value_head and
                                                report["selection"]["epoch"] == 0 else "fitted_not_strength_validated")
            save(model, optimizer, args.output.with_suffix(f".epoch{epoch}.pt"), report)
            progress()
            print(json.dumps({"stage": "bootstrap", "epoch": epoch, "batches": len(stats),
                              "validation_batches": len(validation), "validation": summary,
                              "best_epoch": report["selection"]["epoch"]}), flush=True)
            if stale_epochs >= args.early_stopping_patience:
                report["early_stopped"] = True
                break
    else:
        from benchmark_mcts import _decoded_decks
        known_decks = _decoded_decks(args.deck_config)
        opponent = copy.deepcopy(model).eval()
        def frozen_checkpoint(path):
            state = torch.load(path, map_location="cpu", weights_only=False)["model_state_dict"]
            opponent.load_state_dict(state, strict=True)
            return {k: v.detach().cpu().clone() for k, v in state.items()}

        if args.round_offset:
            pool = [("bootstrap", frozen_checkpoint(args.anchor_checkpoint))]
            pool.extend((f"round{i}", frozen_checkpoint(path))
                        for i, path in enumerate(args.history_checkpoint, 1)
                        if i > args.round_offset - (args.opponent_pool_size - 1))
            pool = retain_opponent_pool(pool, args.opponent_pool_size)
        else:
            pool = [("bootstrap", {k: v.detach().cpu().clone() for k, v in model.state_dict().items()})]
        for round_index in range(args.round_offset, args.round_offset + args.rounds):
            rows, games, failures = collect_round(
                model, opponent, pool, args, device, round_index, known_decks)
            report["failures"].extend(failures)
            report["latest_collection"] = getattr(args, "last_collection_metrics", None)
            progress()
            if not rows:
                raise ValueError("no terminal on-policy trajectories; see persisted failure library")
            weight_ppo_games(rows)
            rollout = args.output.with_suffix(f".round{round_index + 1}.jsonl.gz")
            print(json.dumps({"stage": "save_rollout", "round": round_index + 1,
                              "games": len(games), "rows": len(rows)}), flush=True)
            with gzip.open(rollout, "wt", encoding="utf-8") as handle:
                for row in rows:
                    handle.write(json.dumps(row, separators=(",", ":")) + "\n")
            if len(games) != args.games_per_round:
                raise ValueError("incomplete balanced round; valid trajectories saved, PPO update withheld")
            stats = []
            kl_stopped = False
            kl_checks = []
            probe = None
            if args.kl_guard == "probe":
                from ppo_kl_probe import build_probe, measure_probe
                probe = build_probe(model, rows, args.kl_probe_size,
                                    args.seed + round_index * 101, device, args.batch_size)
            for epoch in range(args.epochs):
                random.Random(args.seed + round_index * 101 + epoch).shuffle(rows)
                for start in range(0, len(rows), args.batch_size):
                    optimizer.zero_grad(set_to_none=True)
                    loss, metrics = ppo_loss(model, rows[start:start + args.batch_size], device)
                    if not torch.isfinite(loss):
                        raise ValueError("non-finite PPO loss")
                    stop_for_kl = metrics["approx_kl"] > args.target_kl
                    if probe is not None:
                        if stop_for_kl or len(stats) % args.kl_check_interval == 0:
                            measured = measure_probe(model, probe, device)
                            kl_checks.append({"before_update": len(stats), **measured})
                            metrics["probe_kl"] = measured["mean"]
                            stop_for_kl = measured["mean"] > args.target_kl
                        else:
                            stop_for_kl = False
                    if stop_for_kl:
                        kl_stopped = True
                        stats.append({**metrics, "update_applied": False})
                        break
                    loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                    optimizer.step(); stats.append({**metrics, "update_applied": True})
                    if len(stats) % 100 == 0:
                        print(json.dumps({"stage": "ppo_minibatch", "round": round_index + 1,
                                          "epoch": epoch + 1, "updates": len(stats),
                                          **metrics}), flush=True)
                if kl_stopped:
                    break
            report["history"].append({"round": round_index + 1, "games": games,
                                       "rows": len(rows), "updates": stats,
                                       "collection": getattr(args, "last_collection_metrics", None),
                                       "kl_early_stopped": kl_stopped,
                                       "kl_guard": args.kl_guard, "kl_probe_checks": kl_checks,
                                       "opponent_versions": dict(Counter(
                                           game["opponent_version"] for game in games))})
            pool.append((f"round{round_index + 1}",
                         {k: v.detach().cpu().clone() for k, v in model.state_dict().items()}))
            pool = retain_opponent_pool(pool, args.opponent_pool_size)
            save(model, optimizer, args.output.with_suffix(f".round{round_index + 1}.pt"), report)
            progress()
            print(json.dumps({"stage": "ppo_update", "round": round_index + 1,
                              "games": len(games), "rows": len(rows)}), flush=True)
    report["status"] = "complete"
    report["elapsed_seconds"] = time.time() - report["started_at"]
    save(model, optimizer, args.output, report)
    progress()
    sys.excepthook = previous_exception_hook
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
