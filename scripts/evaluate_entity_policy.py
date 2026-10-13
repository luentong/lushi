#!/usr/bin/env python3
"""Independent seat-paired pure-policy evaluation for entity checkpoints.

No training, search or automatic promotion. Failed/truncated games are not draws.
Trace snapshots may show both hands for offline audit; models never receive them.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import statistics
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]


def make_schedule(decks, pairs, seed):
    jobs = []
    for a in decks:
        for b in decks:
            for _ in range(pairs):
                pair_id = len(jobs) // 2
                for seat in (0, 1):
                    jobs.append({"pair_id": pair_id, "seed": seed + pair_id,
                                 "candidate_deck": a, "opponent_deck": b,
                                 "candidate_seat": seat})
    return jobs


def outcome_score(game):
    if game["status"] != "complete":
        return None
    if game["winner"] is None:
        return 0.5
    if game["winner"] not in (0, 1) or game["candidate_seat"] not in (0, 1):
        raise ValueError("invalid winner/seat")
    return float(game["winner"] == game["candidate_seat"])


def summary(games):
    scores = [outcome_score(g) for g in games]
    complete = [s for s in scores if s is not None]
    pairs = defaultdict(list)
    for game in games:
        pairs[game["pair_id"]].append(game)
    pair_scores = []
    for pair in pairs.values():
        if len(pair) > 2 or len({g["candidate_seat"] for g in pair}) != len(pair):
            raise ValueError("duplicate seat in paired evaluation")
        if len(pair) == 2 and all(outcome_score(g) is not None for g in pair):
            pair_scores.append(sum(outcome_score(g) for g in pair) / 2)
    interval = None
    if pair_scores:
        mean = statistics.mean(pair_scores)
        # Independent seed-pair scores are bounded [0,1]. This conservative
        # Hoeffding bound does not pretend the two games in a pair are independent.
        radius = math.sqrt(math.log(2 / 0.05) / (2 * len(pair_scores)))
        interval = [max(0.0, mean - radius), min(1.0, mean + radius)]
    return {"attempted_games": len(games), "completed_games": len(complete),
            "failed_or_truncated": len(games) - len(complete),
            "wins": complete.count(1.0), "draws": complete.count(0.5),
            "losses": complete.count(0.0),
            "win_rate": complete.count(1.0) / len(complete) if complete else None,
            "score_rate": statistics.mean(complete) if complete else None,
            "complete_pairs": len(pair_scores), "incomplete_pairs": len(pairs) - len(pair_scores),
            "pair_score_mean": statistics.mean(pair_scores) if pair_scores else None,
            "pair_hoeffding_95_interval": interval}


def grouped_summary(games):
    groups = defaultdict(list)
    for game in games:
        groups[(game["candidate_deck"], game["opponent_deck"])].append(game)
    return [{"candidate_deck": a, "opponent_deck": b, **summary(rows)}
            for (a, b), rows in sorted(groups.items())]


def candidate_deck_summary(games):
    """Expose subgroup regressions that an aggregate win rate can conceal."""
    groups = defaultdict(list)
    for game in games:
        groups[game["candidate_deck"]].append(game)
    return {deck: summary(rows) for deck, rows in sorted(groups.items())}


def value_calibration_summary(games):
    """Game-macro held-out critic calibration for candidate-induced positions."""
    eligible = [game for game in games if game["status"] == "complete"
                and game.get("candidate_value_predictions")]
    if not eligible:
        return {"games": 0, "game_macro_brier": None, "first_decision_brier": None,
                "predicted_score": None, "observed_score": None}
    scores = [outcome_score(game) for game in eligible]
    predictions = [[(value + 1) / 2 for value in game["candidate_value_predictions"]]
                   for game in eligible]
    if any(not math.isfinite(p) or not 0 <= p <= 1
           for game_predictions in predictions for p in game_predictions):
        raise ValueError("invalid candidate value prediction")
    return {"games": len(eligible),
            "game_macro_brier": statistics.mean(
                statistics.mean((p - score) ** 2 for p in game_predictions)
                for game_predictions, score in zip(predictions, scores)),
            "first_decision_brier": statistics.mean(
                (game_predictions[0] - score) ** 2
                for game_predictions, score in zip(predictions, scores)),
            "predicted_score": statistics.mean(statistics.mean(game_predictions)
                                               for game_predictions in predictions),
            "observed_score": statistics.mean(scores)}


class EntityValueAdapter:
    """Search-only actor-perspective value from an entity checkpoint.

    Offline matchup simulations let each actor know its own fixture deck.
    This does not certify that a sampled opponent hypothesis matches that
    fixture deck, so the adapter must not become a live-advice default.
    """
    name = "entity-value-search-diagnostic"

    def __init__(self, model, device):
        self.model, self.device = model, device

    def predict(self, state, legal):
        import torch
        from hsa.entity_model import collate_views
        from hsa.observer_view import observer_view
        from hsa.policy_value import PolicyValueOutput
        leaf_view = observer_view(state, actions=legal,
                                  known_deck=state.deck_counts[state.current])
        with torch.no_grad():
            logits, values = self.model(collate_views(
                [leaf_view], self.model.card_ids, self.device))
            count = len(legal)
            if not torch.isfinite(logits[0, :count]).all() or not torch.isfinite(values[0]):
                raise ValueError("non-finite search leaf prediction")
            return PolicyValueOutput(
                tuple(logits[0, :count].softmax(-1).cpu().tolist()), float(values[0]))


def select_policy(kind, path, device, *, search_budget=0, search_rollout_depth=8,
                  search_leaf_mode="heuristic"):
    from hsa import HeuristicPolicy
    if kind == "heuristic":
        policy = HeuristicPolicy()
        return lambda game, actions, counts: policy.choose(game)
    if kind == "legacy":
        from hsa.torch_model import TorchPolicyValueModel
        model = TorchPolicyValueModel.from_checkpoint(str(path), str(device))

        def choose_legacy(game, actions, counts):
            priors = model.predict(game, actions).priors
            if len(priors) != len(actions) or not all(math.isfinite(p) and p >= 0 for p in priors):
                raise ValueError("invalid legacy policy output")
            if sum(priors) <= 0:
                raise ValueError("zero legacy probability mass")
            return actions[max(range(len(actions)), key=lambda i: priors[i])]
        return choose_legacy
    import torch
    from hsa.entity_model import EntityPolicyValueNet, collate_views
    from hsa.observer_view import observer_view
    from hsa.policy_value import PolicyValueOutput
    model = EntityPolicyValueNet.from_payload(torch.load(path, map_location="cpu", weights_only=False))
    model.to(device).eval()
    if search_budget < 0 or search_rollout_depth < 0:
        raise ValueError("search budget and rollout depth must be nonnegative")
    if search_leaf_mode not in {"heuristic", "entity_value"}:
        raise ValueError("unknown search leaf mode")

    def choose_entity(game, actions, counts):
        view = observer_view(game, actions=actions, known_deck=counts)
        with torch.no_grad():
            logits, values = model(collate_views([view], model.card_ids, device))
            if not torch.isfinite(logits).all():
                raise ValueError("non-finite entity logits")
            choose_entity.last_value = float(values[0])
            index = int(logits[0].argmax())
            if search_budget:
                import hashlib
                from hsa.mcts import InformationSetMCTSPolicy
                priors = tuple(logits[0, :len(actions)].softmax(-1).cpu().tolist())
                seed = int.from_bytes(hashlib.sha256(repr(view).encode("utf-8")).digest()[:8], "big")
                search = InformationSetMCTSPolicy(samples=4,
                    iterations_per_sample=(search_budget + 3) // 4,
                    max_total_iterations=search_budget, min_simulations_per_root_action=1,
                    tree_depth=8, rollout_depth=search_rollout_depth, seed=seed,
                    policy_value_model=(EntityValueAdapter(model, device)
                                        if search_leaf_mode == "entity_value" else None),
                    use_model_value=search_leaf_mode == "entity_value",
                    neural_prior_depth=1, prior_uniform_mix=.1)
                choose_entity.last_search = search
                return search.choose(game,
                    root_prediction=PolicyValueOutput(priors, float(values[0])),
                    root_actions=tuple(actions))
            choose_entity.last_value = float(values[0])
        return actions[index]
    return choose_entity


def baseline_mulligan_action(game, actions):
    """Match the engine's existing >=4-cost mulligan on an explicit choice."""
    pending = game.pending_choice
    if not pending or pending.get("kind") != "MULLIGAN":
        raise ValueError("baseline mulligan requested outside mulligan")
    costly = {card.entity_id for card in game.players[game.current].hand
              if card.definition.cost >= 4}
    selected = set(pending.get("selected", ()))
    for action in actions:
        if action.kind == "MULLIGAN_TOGGLE" and action.source in costly - selected:
            return action
    return next(action for action in actions if action.kind == "MULLIGAN_CONFIRM")


def single_flip_mulligan_action(game, actions):
    """Randomize one visible offered card relative to the baseline rule.

    The choice is deterministic for a game seed and actor, uses no hidden
    zones, and consumes no game RNG. Matched baseline games therefore share
    the same initial shuffle and offered hand.
    """
    import hashlib
    pending = game.pending_choice
    if not pending or pending.get("kind") != "MULLIGAN":
        raise ValueError("single-card flip requested outside mulligan")
    offered = tuple(sorted(pending["options"]))
    if not offered:
        return next(action for action in actions if action.kind == "MULLIGAN_CONFIRM")
    token = f"{game.seed}:{game.current}:single_flip".encode()
    index = int.from_bytes(hashlib.sha256(token).digest()[:8], "big") % len(offered)
    flipped = offered[index]
    target = {card.entity_id for card in game.players[game.current].hand
              if card.definition.cost >= 4}
    target.symmetric_difference_update((flipped,))
    selected = set(pending.get("selected", ()))
    for action in actions:
        if action.kind == "MULLIGAN_TOGGLE" and action.source in target - selected:
            return action
    return next(action for action in actions if action.kind == "MULLIGAN_CONFIRM")


def play_job(job, candidate, opponent, decks, args):
    from hsa import DragonMirrorGame
    from benchmark_mcts import configure_search_beliefs
    from trace_search_match import compact_state
    from train_entity_selfplay import constrain_mulligan_actions
    started = time.perf_counter()
    counts_a, class_a = decks[job["candidate_deck"]]
    counts_b, class_b = decks[job["opponent_deck"]]
    seat = job["candidate_seat"]
    counts = (counts_a, counts_b) if seat == 0 else (counts_b, counts_a)
    classes = (class_a, class_b) if seat == 0 else (class_b, class_a)
    game = None
    trace = {**job, "steps": [], "schema_version": 1,
             "policy_mode": "entity_root_search" if getattr(args, "candidate_search_budget", 0) else "greedy_without_search",
             "audit_is_omniscient": True}
    result = {**job, "status": "failed", "winner": None, "steps": 0,
              "candidate_goes_first": None, "decision_seconds": [],
              "candidate_value_predictions": [], "mulligan_forced_confirms": 0}
    try:
        game = DragonMirrorGame(args.cards, job["seed"], deck_counts=counts, player_classes=classes,
                                manual_mulligan=args.manual_mulligan)
        configure_search_beliefs(game, args.deck_config)
        result["candidate_goes_first"] = game.first_player == seat
        trace["initial_state"] = compact_state(game.snapshot())
        mulligan_steps = {0: 0, 1: 0}
        while not game.finished and result["steps"] < args.max_actions:
            if time.perf_counter() - started > args.max_game_seconds:
                break
            actor = game.current
            actions = game.legal_actions()
            if args.manual_mulligan:
                actions = constrain_mulligan_actions(game, actions)
            policy = candidate if actor == seat else opponent
            mulligan_policy = (args.candidate_mulligan_policy if actor == seat
                               else args.opponent_mulligan_policy)
            decision_start = time.perf_counter()
            if (args.manual_mulligan and game.pending_choice
                    and game.pending_choice.get("kind") == "MULLIGAN"
                    and mulligan_policy in {"baseline", "single_flip"}):
                action = (baseline_mulligan_action if mulligan_policy == "baseline"
                          else single_flip_mulligan_action)(game, actions)
            else:
                action = policy(game, actions, counts[actor])
            if (args.manual_mulligan and game.pending_choice
                    and game.pending_choice.get("kind") == "MULLIGAN"):
                # Toggling is reversible by design; a weak greedy policy can
                # otherwise toggle forever. This guard is evaluation/live
                # safety only and does not alter engine legality or training.
                if mulligan_steps[actor] >= args.mulligan_max_actions:
                    action = next(a for a in actions if a.kind == "MULLIGAN_CONFIRM")
                    result["mulligan_forced_confirms"] += 1
                elif action.kind == "MULLIGAN_TOGGLE":
                    mulligan_steps[actor] += 1
            if actor == seat and hasattr(policy, "last_value"):
                result["candidate_value_predictions"].append(policy.last_value)
            result["decision_seconds"].append(time.perf_counter() - decision_start)
            if action not in actions:
                raise ValueError("policy selected an illegal action")
            row = {"step": result["steps"] + 1, "turn_before": game.turn, "actor": actor + 1,
                   "description": game.describe_action(action), "legal_action_count": len(actions),
                   "action_key": action.key(), "choose_seconds": result["decision_seconds"][-1],
                   "candidate_acted": actor == seat}
            if args.save_traces:
                row["state_before"] = compact_state(game.snapshot())
            trace["steps"].append(row)
            game.step(action)
            if action.kind == "MULLIGAN_CONFIRM":
                mulligan_steps[actor] = 0
            result["steps"] += 1
            if args.save_traces:
                row["state_after"] = compact_state(game.snapshot())
        result.update(status="complete" if game.finished else "truncated", winner=game.winner,
                      turns=game.turn, invalid_actions=game.invalid_actions)
        if game.invalid_actions:
            result["status"] = "failed"
    except Exception as exc:
        result.update(error=f"{type(exc).__name__}: {exc}", traceback=traceback.format_exc())
    result["wall_seconds"] = time.perf_counter() - started
    trace.update(winner=result["winner"], status=result["status"],
                 invalid_actions=game.invalid_actions if game else None)
    # Always retain attempted actions, including failures. Full snapshots are opt-in.
    path = args.output / f"trace-{job['pair_id']:04d}-seat{seat}.json"
    path.write_text(json.dumps(trace, ensure_ascii=False), encoding="utf-8")
    result["trace"] = str(path)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", type=Path, required=True)
    p.add_argument("--candidate-search-budget", type=int, default=0,
                   help="Root ISMCTS simulations per candidate decision; 0 uses greedy entity logits")
    p.add_argument("--candidate-search-rollout-depth", type=int, default=8)
    p.add_argument("--candidate-search-leaf-mode", choices=("heuristic", "entity_value"),
                   default="heuristic")
    p.add_argument("--opponent-kind", choices=("entity", "legacy", "heuristic"), required=True)
    p.add_argument("--opponent", type=Path)
    p.add_argument("--device", default="cpu")
    p.add_argument("--deck-config", type=Path, default=ROOT / "config/decision_quality_pair_decks_20260928.json")
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--pairs-per-matchup", type=int, default=2)
    p.add_argument("--seed", type=int, default=202609299000)
    p.add_argument("--max-actions", type=int, default=400)
    p.add_argument("--max-game-seconds", type=float, default=120)
    p.add_argument("--save-traces", action="store_true")
    p.add_argument("--manual-mulligan", action="store_true",
                   help="Expose mulligan choices during evaluation instead of engine auto-mulligan")
    p.add_argument("--candidate-mulligan-policy", choices=("model", "baseline", "single_flip"), default="model")
    p.add_argument("--opponent-mulligan-policy", choices=("model", "baseline"), default="model")
    p.add_argument("--mulligan-max-actions", type=int, default=8,
                   help="Maximum model toggles per player before evaluator forces confirm")
    p.add_argument("--split", choices=("development", "confirmation"), default="development")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.opponent_kind != "heuristic" and not args.opponent:
        p.error("checkpoint opponent requires --opponent")
    if min(args.pairs_per_matchup, args.max_actions, args.max_game_seconds) <= 0:
        p.error("counts/time limits must be positive")
    if args.mulligan_max_actions < 0:
        p.error("mulligan-max-actions must be nonnegative")
    if args.candidate_search_budget < 0 or (args.candidate_search_budget and args.candidate_search_budget < 4):
        p.error("candidate search budget must be zero or at least four")
    if args.candidate_search_rollout_depth < 0:
        p.error("candidate search rollout depth must be nonnegative")
    from benchmark_mcts import _decoded_decks
    from train_entity_selfplay import select_device, file_digest, constrain_mulligan_actions
    import torch
    torch.set_num_threads(2)
    decks = _decoded_decks(args.deck_config)
    schedule = make_schedule(sorted(decks), args.pairs_per_matchup, args.seed)
    args.output.mkdir(parents=True, exist_ok=False)
    device = select_device(args.device)
    candidate = select_policy("entity", args.candidate, device,
                              search_budget=args.candidate_search_budget,
                              search_rollout_depth=args.candidate_search_rollout_depth,
                              search_leaf_mode=args.candidate_search_leaf_mode)
    opponent = select_policy(args.opponent_kind, args.opponent, device)
    report = {"status": "running", "evaluation_only": True, "automatic_promotion": False,
              "split": args.split,
              "policy_mode": "entity_root_search" if args.candidate_search_budget else "greedy_without_search",
              "mulligan": "manual_policy" if args.manual_mulligan else "existing_engine_default_not_learned",
              "parameters": {k: str(v) if isinstance(v, Path) else v for k, v in vars(args).items()},
              "checkpoint_sha256": {"candidate": file_digest(args.candidate),
                                    "opponent": file_digest(args.opponent) if args.opponent else None},
              "source_sha256": {str(path.relative_to(ROOT)): file_digest(path)
                                for path in (ROOT / "src/hsa").rglob("*.py")},
              "deck_config_sha256": file_digest(args.deck_config),
              "planned_games": len(schedule), "games": []}
    started = time.perf_counter()

    def progress():
        report.update(summary=summary(report["games"]), matchups=grouped_summary(report["games"]),
                      by_candidate_deck=candidate_deck_summary(report["games"]),
                      value_calibration=value_calibration_summary(report["games"]),
                      elapsed_seconds=time.perf_counter() - started)
        report["by_candidate_deck_value_calibration"] = {
            deck: value_calibration_summary([game for game in report["games"]
                                             if game["candidate_deck"] == deck])
            for deck in sorted(decks)}
        report["by_initiative"] = {name: summary([g for g in report["games"] if g["candidate_goes_first"] is flag])
                                   for name, flag in (("first", True), ("second", False))}
        timings = [s for g in report["games"] for s in g["decision_seconds"]]
        if timings:
            ordered = sorted(timings)
            report["decision_timing"] = {"mean_seconds": statistics.mean(timings),
                                         "p95_seconds": ordered[math.ceil(.95 * len(ordered)) - 1]}
        temporary = args.output / "evaluation.tmp"
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(args.output / "evaluation.json")

    progress()
    for job in schedule:
        result = play_job(job, candidate, opponent, decks, args)
        report["games"].append(result)
        progress()
        print(json.dumps({"completed_jobs": len(report["games"]), "summary": report["summary"]}), flush=True)
    report["status"] = "complete" if all(g["status"] == "complete" for g in report["games"]) else "complete_with_failures"
    progress()
    return 0 if report["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
