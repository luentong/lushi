#!/usr/bin/env python3
"""Audit search labels with paired, independently continued game outcomes.

This is an *outcome diagnostic*, not a proof that one action is optimal. Each
candidate starts from the same sampled hidden world for a replicate, then both
players use the same continuation policy. Truncated games are never scored as
wins or losses.
"""
from __future__ import annotations

import argparse
import json
import random
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from hsa.belief import PublicBelief
from hsa.policy import HeuristicPolicy
from replay_trace_state import replay_trace_state


class ModelGreedyPolicy:
    """Follow the learned policy without search; each actor sees its own view."""

    def __init__(self, model):
        self.model = model

    def choose(self, game):
        actions = game.legal_actions()
        if not actions:
            raise RuntimeError("policy requested action in a terminal state")
        if len(actions) == 1:
            return actions[0]
        priors = self.model.predict(game, tuple(actions)).priors
        if len(priors) != len(actions):
            raise RuntimeError("model policy output does not match legal actions")
        return max(zip(actions, priors, strict=True),
                   key=lambda pair: (pair[1], pair[0].key()))[0]


class EntityGreedyPolicy:
    """Entity checkpoint inference with the actor's known starting deck."""

    def __init__(self, checkpoint: Path, device: str):
        import torch
        from hsa.entity_model import EntityPolicyValueNet
        self.torch = torch
        self.device = device
        self.model = EntityPolicyValueNet.from_payload(
            torch.load(checkpoint, map_location="cpu", weights_only=False))
        self.model.to(device).eval()
        self._cache: dict[str, int] = {}
        self.predictions = 0
        self.cache_hits = 0
        self.view_seconds = 0.0
        self.collate_seconds = 0.0
        self.transfer_seconds = 0.0
        self.forward_seconds = 0.0

    def choose(self, game):
        actions = game.legal_actions()
        if not actions:
            raise RuntimeError("policy requested action in a terminal state")
        if len(actions) == 1:
            return actions[0]
        from hsa.entity_model import collate_views
        from hsa.observer_view import observer_view
        view = observer_view(game, actions=actions,
                             known_deck=game.deck_counts[game.current])
        cache_key = json.dumps(view, sort_keys=True, separators=(",", ":"))
        if cache_key in self._cache:
            self.cache_hits += 1
            return actions[self._cache[cache_key]]
        with self.torch.no_grad():
            logits, _ = self.model(collate_views(
                [view], self.model.card_ids, self.device))
            if not self.torch.isfinite(logits).all():
                raise ValueError("non-finite entity logits")
            index = int(logits[0].argmax())
        self.predictions += 1
        if len(self._cache) >= 4096:
            self._cache.clear()
        self._cache[cache_key] = index
        return actions[index]

    def choose_batch(self, games):
        """One padded NPU forward for all nontrivial, uncached decisions."""
        from hsa.entity_model import collate_views
        from hsa.observer_view import observer_view
        chosen = [None] * len(games)
        pending = []
        view_start = time.perf_counter()
        for position, game in enumerate(games):
            actions = game.legal_actions()
            if not actions:
                raise RuntimeError("policy requested action in a terminal state")
            if len(actions) == 1:
                chosen[position] = actions[0]
                continue
            view = observer_view(game, actions=actions,
                                 known_deck=game.deck_counts[game.current])
            cache_key = json.dumps(view, sort_keys=True, separators=(",", ":"))
            if cache_key in self._cache:
                self.cache_hits += 1
                chosen[position] = actions[self._cache[cache_key]]
            else:
                pending.append((position, actions, view, cache_key))
        self.view_seconds += time.perf_counter() - view_start
        if pending:
            collate_start = time.perf_counter()
            batch_cpu = collate_views(
                [item[2] for item in pending], self.model.card_ids,
                "cpu")
            self.collate_seconds += time.perf_counter() - collate_start
            transfer_start = time.perf_counter()
            batch = {key: value.to(self.device)
                     for key, value in batch_cpu.items()}
            self.transfer_seconds += time.perf_counter() - transfer_start
            forward_start = time.perf_counter()
            with self.torch.no_grad():
                logits, _ = self.model(batch)
                if not self.torch.isfinite(logits).all():
                    raise ValueError("non-finite entity logits")
                for batch_index, (position, actions, _, key) in enumerate(pending):
                    index = int(logits[batch_index].argmax())
                    chosen[position] = actions[index]
                    if len(self._cache) >= 4096:
                        self._cache.clear()
                    self._cache[key] = index
            self.forward_seconds += time.perf_counter() - forward_start
            self.predictions += 1
        return chosen


def _summarize_outcomes(results):
    for row in results:
        decided = row["wins"] + row["losses"] + row["draws"]
        row["decided_games"] = decided
        row["score_per_decided_game"] = (
            (row["wins"] + 0.5 * row["draws"]) / decided if decided else None)
    return results


def _outcome_status(game, root_player):
    if not game.finished:
        return "truncated"
    if game.winner is None:
        return "draws"
    return "wins" if game.winner == root_player else "losses"


def paired_outcomes_batched(root, actions, *, replicates, max_actions, seed,
                            continuation_policy):
    """Advance forced alternatives together, batching their model decisions."""
    if replicates < 1 or max_actions < 1 or not actions:
        raise ValueError("positive limits and at least one action are required")
    root_player = root.current
    belief = PublicBelief.from_game(root, root_player)
    results = [{"action_key": list(action.key()),
                "description": root.describe_action(action),
                "wins": 0, "losses": 0, "draws": 0,
                "truncated": 0, "invalid": 0, "outcomes": []}
               for action in actions]
    for replicate in range(replicates):
        sampled = belief.sample_determinization(
            root, seed=seed + replicate, record_event=False)
        sampled.rng = random.Random(f"paired-root:{seed + replicate}:future")
        games = []
        steps = [0] * len(actions)
        errors = [None] * len(actions)
        for index, action in enumerate(actions):
            game = sampled.clone(include_history=False, record_events=False)
            games.append(game)
            try:
                legal = {candidate.key(): candidate for candidate in game.legal_actions()}
                if action.key() not in legal:
                    raise ValueError("root action absent from sampled world")
                game.step(legal[action.key()])
                steps[index] = 1
            except (ValueError, RuntimeError) as error:
                errors[index] = str(error)
        while True:
            active = [index for index, game in enumerate(games)
                      if errors[index] is None and not game.finished
                      and steps[index] < max_actions]
            if not active:
                break
            try:
                selected = continuation_policy.choose_batch([games[i] for i in active])
                if len(selected) != len(active):
                    raise RuntimeError("batched policy returned wrong number of actions")
            except (ValueError, RuntimeError) as error:
                for index in active:
                    errors[index] = str(error)
                break
            for index, action in zip(active, selected, strict=True):
                try:
                    games[index].step(action)
                    steps[index] += 1
                except (ValueError, RuntimeError) as error:
                    errors[index] = str(error)
        for index, (game, row) in enumerate(zip(games, results, strict=True)):
            if errors[index] is not None:
                row["invalid"] += 1
                row["outcomes"].append({"replicate": replicate,
                                        "status": "invalid", "error": errors[index]})
                continue
            status = _outcome_status(game, root_player)
            row[status] += 1
            row["outcomes"].append({"replicate": replicate, "status": status,
                                    "winner": game.winner if game.finished else None,
                                    "actions": steps[index]})
    return _summarize_outcomes(results)


def paired_outcomes(root, actions, *, replicates: int, max_actions: int,
                    seed: int, continuation_policy=None):
    if replicates < 1 or max_actions < 1:
        raise ValueError("replicates and max_actions must be positive")
    if not actions:
        raise ValueError("at least one root action is required")
    continuation_policy = continuation_policy or HeuristicPolicy()
    if hasattr(continuation_policy, "choose_batch"):
        return paired_outcomes_batched(
            root, actions, replicates=replicates, max_actions=max_actions,
            seed=seed, continuation_policy=continuation_policy)
    root_player = root.current
    belief = PublicBelief.from_game(root, root_player)
    results = [{"action_key": list(action.key()),
                "description": root.describe_action(action),
                "wins": 0, "losses": 0, "draws": 0,
                "truncated": 0, "invalid": 0, "outcomes": []}
               for action in actions]
    for replicate in range(replicates):
        # One determinization is shared by *every* candidate action. This
        # reduces variance without letting the actor inspect hidden zones.
        sampled = belief.sample_determinization(
            root, seed=seed + replicate, record_event=False)
        # Belief sampling randomizes hidden zones, but the cloned game may
        # retain the recorded future RNG state. Give each replicate an
        # independent chance stream, shared across its forced root actions.
        sampled.rng = random.Random(f"paired-root:{seed + replicate}:future")
        for action, row in zip(actions, results, strict=True):
            game = sampled.clone(include_history=False, record_events=False)
            legal = {candidate.key(): candidate for candidate in game.legal_actions()}
            recent_actions = []
            steps = 0
            pre_target = None
            try:
                if action.key() not in legal:
                    raise ValueError("root action absent from sampled world")
                recent_actions.append(game.describe_action(legal[action.key()]))
                game.step(legal[action.key()])
                steps = 1
                while not game.finished and steps < max_actions:
                    selected = continuation_policy.choose(game)
                    recent_actions.append(game.describe_action(selected))
                    if len(recent_actions) > 12:
                        recent_actions.pop(0)
                    pre_target = None
                    if selected.target_entity is not None and selected.target_player in (0, 1):
                        pre_target = next(({"id": m.entity_id, "card": m.card_id,
                                            "health": m.health, "damage": m.damage}
                                           for m in game.players[selected.target_player].board
                                           if m.entity_id == selected.target_entity), None)
                    game.step(selected)
                    steps += 1
            except (ValueError, RuntimeError) as error:
                row["invalid"] += 1
                row["outcomes"].append({"replicate": replicate, "status": "invalid",
                                        "error": str(error), "recent_actions": recent_actions,
                                        "steps_before_error": steps,
                                        "pre_target": pre_target,
                                        "post_board": [
                                            [{"id": m.entity_id, "card": m.card_id,
                                              "health": m.health, "damage": m.damage}
                                             for m in player.board]
                                            for player in game.players],
                                        "traceback": traceback.format_exc()})
                continue
            if not game.finished:
                status = "truncated"
            elif game.winner is None:
                status = "draws"
            elif game.winner == root_player:
                status = "wins"
            else:
                status = "losses"
            row[status] += 1
            row["outcomes"].append({"replicate": replicate, "status": status,
                                    "winner": game.winner if game.finished else None,
                                    "actions": steps})
    return _summarize_outcomes(results)


def paired_comparisons(results, selected_action_key):
    """Compare only replicates that finished for both the selected and peer action."""
    selected = next(row for row in results
                    if row["action_key"] == selected_action_key)

    def score(status):
        return {"wins": 1.0, "draws": 0.5, "losses": 0.0}.get(status)

    baseline = {item["replicate"]: score(item["status"])
                for item in selected["outcomes"]}
    comparisons = []
    for row in results:
        if row is selected:
            continue
        differences = [score(item["status"]) - baseline[item["replicate"]]
                       for item in row["outcomes"]
                       if score(item["status"]) is not None
                       and baseline[item["replicate"]] is not None]
        comparisons.append({
            "alternative": row["description"],
            "paired_decided": len(differences),
            "alternative_better": sum(value > 0 for value in differences),
            "selected_better": sum(value < 0 for value in differences),
            "tied": sum(value == 0 for value in differences),
            "mean_score_difference": (
                sum(differences) / len(differences) if differences else None),
        })
    return comparisons


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--deck-config", type=Path)
    parser.add_argument("--replicates", type=int, default=8)
    parser.add_argument("--max-actions", type=int, default=240)
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument("--max-root-actions", type=int, default=12)
    parser.add_argument("--continuation", choices=("heuristic", "model-greedy",
                                                   "entity-greedy"),
                        default="heuristic")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = replay_trace_state(args.trace, args.step, args.deck_config)
    actions = root.legal_actions()
    if len(actions) > args.max_root_actions:
        raise ValueError(
            f"{len(actions)} root actions exceed --max-root-actions; "
            "select a smaller root rather than silently dropping alternatives")
    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    recorded = trace["steps"][args.step - 1]
    if args.continuation in {"model-greedy", "entity-greedy"}:
        if args.checkpoint is None:
            parser.error("--checkpoint is required for model continuation")
        if args.continuation == "entity-greedy":
            continuation = EntityGreedyPolicy(args.checkpoint, args.device)
        else:
            from hsa.torch_model import TorchPolicyValueModel
            continuation = ModelGreedyPolicy(
                TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device))
    else:
        continuation = HeuristicPolicy()
    audit_started = time.perf_counter()
    results = paired_outcomes(
        root, actions, replicates=args.replicates,
        max_actions=args.max_actions, seed=args.seed,
        continuation_policy=continuation)
    audit_seconds = time.perf_counter() - audit_started
    selected = recorded["description"]
    selected_matches = [row for row in results if row["description"] == selected]
    if len(selected_matches) != 1:
        raise RuntimeError(
            "recorded selected action description is not uniquely legal; "
            "the trace needs its concrete action key to audit this root")
    selected_row = selected_matches[0]
    comparisons = paired_comparisons(results, selected_row["action_key"])
    result = {
        "schema": "paired-root-outcome-audit-v1",
        "trace": str(args.trace), "step": args.step,
        "actor": root.current, "recorded_action": selected,
        "continuation_policy": ("heuristic-tempo-v1" if args.continuation == "heuristic"
                                else args.continuation),
        "checkpoint": str(args.checkpoint) if args.checkpoint else None,
        "replicates": args.replicates, "max_actions": args.max_actions,
        "seed": args.seed,
        "audit_seconds": round(audit_seconds, 3),
        "limitations": [
            "Outcome ranks depend on the continuation policy, which is not an optimal player.",
            "Each replicate shares one sampled hidden world across root actions, not the actual opponent hand.",
            "A truncated or invalid game is excluded from scored outcomes.",
        ],
        "teacher_ranked_alternatives": recorded.get("ranked_alternatives"),
        "teacher_root_policy": recorded.get("search", {}).get("root_policy"),
        "results": results,
        "paired_comparisons_to_recorded_action": comparisons,
    }
    if isinstance(continuation, EntityGreedyPolicy):
        result["model_inference"] = {
            "forward_passes": continuation.predictions,
            "exact_view_cache_hits": continuation.cache_hits,
            "observer_view_seconds": round(continuation.view_seconds, 3),
            "collate_seconds": round(continuation.collate_seconds, 3),
            "transfer_seconds": round(continuation.transfer_seconds, 3),
            "model_forward_seconds": round(continuation.forward_seconds, 3),
        }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"selected": selected,
                      "results": [{key: row[key] for key in (
                          "description", "wins", "losses", "draws", "truncated",
                          "invalid", "score_per_decided_game")}
                          for row in results]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
