#!/usr/bin/env python3
"""Grouped-observation, equal-turn-horizon diagnostic (not a strong teacher)."""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa.belief import PublicBelief
from hsa.mcts import InformationSetMCTSPolicy, evaluate_state
from hsa.policy_value import HeuristicPolicyValueModel
from replay_trace_state import replay_trace_state
from audit_action_order import sha


def finish_turn(state, actor):
    if state.finished:
        return state
    if state.pending_choice is not None:
        return None
    if state.current != actor:
        return state
    end = next((a for a in state.legal_actions() if a.kind == "END_TURN"), None)
    if end is None:
        return None
    state.step(end)
    return None if state.pending_choice is not None and not state.finished else state


def score_states(model, states, actor):
    values = [None] * len(states)
    requests, indices = [], []
    for i, state in enumerate(states):
        if state.finished:
            values[i] = evaluate_state(state, actor)
        else:
            indices.append(i)
            requests.append((state, state.legal_actions()))
    for start in range(0, len(requests), 32):
        batch = requests[start:start + 32]
        outputs = (model.predict_batch(batch) if hasattr(model, "predict_batch")
                   else [model.predict(g, a) for g, a in batch])
        for i, output in zip(indices[start:start + 32], outputs, strict=True):
            values[i] = output.value if states[i].current == actor else -output.value
    return values


def crossfit_options(options):
    if not options:
        return 0.0, 0, []
    size = len(options[0][1])
    if any(len(values) != size for _, values in options):
        raise ValueError("Each continuation must use the same sampled worlds")
    if size < 2:
        return 0.0, 0, []
    total, count, folds = 0.0, 0, []
    for parity in (0, 1):
        train = list(range(parity, size, 2))
        test = list(range(1 - parity, size, 2))
        selected, values = max(options, key=lambda item: statistics.mean(item[1][i] for i in train))
        held = [values[i] for i in test]
        total += sum(held)
        count += len(held)
        folds.append({"continuation": selected["continuation"], "training_samples": len(train),
                      "heldout_samples": len(test), "heldout_mean": statistics.mean(held)})
    return total, count, folds


def audit(root, model, samples=64, seed=900):
    actor = root.current
    belief = PublicBelief.from_game(root, actor)
    worlds = [belief.sample_determinization(root, seed=seed + i, record_event=False)
              for i in range(samples)]
    rows = []
    for first in root.legal_actions():
        groups = defaultdict(list)
        rejected = 0
        for world in worlds:
            state = world.clone()
            if first not in state.legal_actions():
                rejected += 1
                continue
            state.step(first)
            # Choices require deeper conditional search, outside this probe.
            if state.pending_choice is not None:
                rejected += 1
                continue
            key = InformationSetMCTSPolicy._observation_key(state, actor)
            groups[key].append(state)
        details = []
        weighted = 0.0
        accepted = 0
        crossfit_sum, crossfit_count = 0.0, 0
        for states in groups.values():
            options = []
            if states[0].finished or states[0].current != actor:
                values = score_states(model, states, actor)
                best = {"continuation": "turn already ended", "mean_value": statistics.mean(values)}
                alternatives = [best]
                options.append((best, values))
            else:
                maps = [InformationSetMCTSPolicy._legal_map(s) for s in states]
                common = set.intersection(*(set(m) for m in maps))
                alternatives = []
                for key in sorted(common, key=str):
                    leaves = []
                    for state, legal_map in zip(states, maps, strict=True):
                        leaf = state.clone()
                        leaf.step(legal_map[key])
                        leaf = finish_turn(leaf, actor)
                        if leaf is None:
                            break
                        leaves.append(leaf)
                    if len(leaves) != len(states):
                        continue
                    values = score_states(model, leaves, actor)
                    option = {
                        "continuation": states[0].describe_action(maps[0][key]),
                        "mean_value": statistics.mean(values),
                        "sample_std": statistics.stdev(values) if len(values) > 1 else None,
                    }
                    alternatives.append(option)
                    options.append((option, values))
                if not alternatives:
                    rejected += len(states)
                    continue
                best = max(alternatives, key=lambda a: a["mean_value"])
            # One shared continuation per ROOT-observed group, not one choice
            # per sampled opponent hand. Avoid hindsight/private-hand fusion.
            accepted += len(states)
            weighted += len(states) * best["mean_value"]
            # Choose on one half of a revealed group, score on the OTHER half.
            # This reduces max-over-noisy-estimates optimism. Singleton groups
            # cannot independently validate their conditional continuation.
            held_sum, held_count, folds = crossfit_options(options)
            crossfit_sum += held_sum
            crossfit_count += held_count
            details.append({"samples": len(states), "best": best, "crossfit_folds": folds,
                            "alternatives": alternatives})
        rows.append({"action": root.describe_action(first), "accepted_samples": accepted,
                     "rejected_samples": rejected, "observation_groups": len(details),
                     "conditional_model_value": weighted / accepted if accepted else None,
                     "crossfit_model_value": crossfit_sum / crossfit_count if crossfit_count else None,
                     "crossfit_samples": crossfit_count,
                     # This is a behavioral diagnostic, not an optimality
                     # claim: it tells us whether the continuation selected
                     # by the current evaluator changes across public
                     # outcomes of the first action.
                     "conditional_best_action_counts": dict(sorted(
                         ((action, sum(group["samples"] for group in details
                                       if group["best"]["continuation"] == action))
                          for action in {group["best"]["continuation"] for group in details}),
                         key=lambda item: item[0])),
                     "distinct_conditional_best_actions": len({
                         group["best"]["continuation"] for group in details}),
                     "outcome_sensitive_continuation": len({
                         group["best"]["continuation"] for group in details}) > 1,
                     "groups": details})
    return rows


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--trace", type=Path, required=True)
    p.add_argument("--deck-config", type=Path)
    p.add_argument("--step", type=int, default=8)
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--device", default="cpu")
    p.add_argument("--samples", type=int, default=64)
    p.add_argument("--seed", type=int, default=900)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.samples < 1:
        p.error("samples must be positive")
    root = replay_trace_state(args.trace, args.step, args.deck_config)
    if args.checkpoint:
        from hsa.torch_model import TorchPolicyValueModel
        model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    else:
        model = HeuristicPolicyValueModel()
    result = {"schema_version": 1, "samples": args.samples, "seed": args.seed,
              "scope": "root action + at most one continuation + actual END_TURN",
              "warning": "Learned-value diagnostic, not win rates or optimality proof. Sparse revealed groups and maximization can bias estimates.",
              "provenance": {"source_sha256": sha(Path(__file__)),
                             "trace_sha256": sha(args.trace),
                             "deck_config_sha256": sha(args.deck_config) if args.deck_config else None,
                             "card_database_sha256": sha(ROOT / "cards.251332.enUS.json"),
                             "checkpoint_sha256": sha(args.checkpoint) if args.checkpoint else None},
              "rows": audit(root, model, args.samples, args.seed)}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps([{k: r[k] for k in ("action", "conditional_model_value", "crossfit_model_value", "crossfit_samples", "observation_groups")}
                      for r in result["rows"]]))


if __name__ == "__main__":
    main()
