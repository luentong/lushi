#!/usr/bin/env python3
"""Write auditable model-match traces.

The compact mode is intended for timing diagnosis. ``--full-training-records``
also emits the exact state/action tensors and teacher labels used by the
policy/value training pipeline, together with engine snapshots and event
deltas for rule auditing.  The latter deliberately separates an actor-visible
model observation from the omniscient engine snapshot: a policy must never
consume the opponent's hidden hand identities.
"""
from __future__ import annotations

import argparse
import faulthandler
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from benchmark_mcts import matchup_deck_counts
from hsa import DragonMirrorGame, InformationSetMCTSPolicy
from hsa.encoding import encode_decision, feature_schema
from hsa.torch_model import TorchPolicyValueModel


def _json_default(value):
    """Make engine event payloads auditable without serializing object graphs.

    A few legacy event hooks retain a CardInstance in their payload.  Training
    tensors and snapshots are already primitive-only; this adapter preserves
    the useful identity of those event values instead of falling back to an
    opaque repr or aborting a full trace halfway through a match.
    """
    if hasattr(value, "card_id") and hasattr(value, "entity_id"):
        definition = getattr(value, "definition", None)
        return {
            "entity": value.entity_id,
            "id": value.card_id,
            "name": getattr(definition, "name", value.card_id),
        }
    if hasattr(value, "key") and callable(value.key):
        return {"action_key": value.key()}
    if isinstance(value, set):
        return sorted(value, key=str)
    return repr(value)


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--deck-a", required=True); p.add_argument("--deck-b", required=True)
    p.add_argument("--swap-decks", action="store_true")
    p.add_argument("--seed", type=int, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument(
        "--baseline-checkpoint", type=Path,
        help="optional separate checkpoint for the opposing seat",
    )
    p.add_argument("--device", default="npu:0")
    p.add_argument(
        "--baseline-device",
        help="device for --baseline-checkpoint; defaults to --device",
    )
    p.add_argument(
        "--policy-only", action="store_true",
        help="use policy priors with heuristic rollouts instead of model values",
    )
    p.add_argument("--iterations", type=int, default=4)
    p.add_argument("--tree-depth", type=int, default=4)
    p.add_argument(
        "--rollout-depth", type=int, default=0,
        help="heuristic rollout depth; use 8 to match benchmark_mcts defaults",
    )
    p.add_argument(
        "--search-seed", type=int, default=20260909,
        help="base ISMCTS seed; match benchmark_mcts.py for exact replay",
    )
    p.add_argument("--max-actions", type=int, default=250)
    p.add_argument(
        "--search-stack-after-seconds", type=float,
        help="dump Python stacks if one policy decision exceeds this duration",
    )
    p.add_argument(
        "--full-training-records", action="store_true",
        help=("Include exact model tensors, legal-action encodings, neural "
              "output, ISMCTS teacher labels, engine snapshots, and event deltas."),
    )
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    (a, class_a), (b, class_b) = matchup_deck_counts(args.deck_config, args.deck_a, args.deck_b)
    if args.swap_decks:
        a, b, class_a, class_b = b, a, class_b, class_a
    game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", args.seed,
                            deck_counts=(a, b), player_classes=(class_a, class_b))
    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    baseline_model = TorchPolicyValueModel.from_checkpoint(
        str(args.baseline_checkpoint or args.checkpoint),
        args.baseline_device or args.device,
    )
    policies = [
        InformationSetMCTSPolicy(samples=1, iterations_per_sample=args.iterations,
                                 tree_depth=args.tree_depth,
                                 rollout_depth=args.rollout_depth,
                                 seed=args.search_seed + args.seed * 2 + seat,
                                 policy_value_model=(model if seat == 0 else baseline_model),
                                 use_model_value=not args.policy_only,
                                 max_total_iterations=args.iterations,
                                 neural_prior_depth=1,
                                 # Match benchmark_mcts' production setting:
                                 # enumerate unvisited legal actions before
                                 # allowing a prior to revisit one branch.
                                 force_uniform_expansion=True)
        for seat in (0, 1)
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    trace_records: list[dict] = []
    with args.output.open("w", encoding="utf-8") as out:
        out.write(json.dumps({
            "kind": "header",
            "seed": args.seed,
            "p0": args.deck_b if args.swap_decks else args.deck_a,
            "p1": args.deck_a if args.swap_decks else args.deck_b,
            "trace_schema": "hsa-auditable-training-trace-v1"
                if args.full_training_records else "hsa-compact-action-trace-v1",
            "model_feature_schema": feature_schema(
                schema_version=model.state_schema_version
            ) if args.full_training_records else None,
            "model_observation_rule": (
                "The policy tensor contains the actor's hand identities and "
                "public enemy information only. engine_state_before/after are "
                "omniscient audit snapshots and are not model inputs."
                if args.full_training_records else None
            ),
            "policy_only": args.policy_only,
            "baseline_checkpoint": str(args.baseline_checkpoint or args.checkpoint),
        }, ensure_ascii=False, default=_json_default) + "\n")
        out.flush()
        for step in range(args.max_actions):
            if game.finished: break
            policy = policies[game.current]
            actor = game.current
            legal_before = game.legal_actions()
            legal_descriptions = [
                game.describe_action(candidate) for candidate in legal_before
            ]
            # Persist the state before search as well as the selected action.
            # A stalled policy.choose() otherwise leaves no evidence of the
            # decision that triggered it; this compact trace is specifically
            # used for reproducing such pathological branches.
            if not args.full_training_records:
                out.write(json.dumps({
                    "kind": "decision_start",
                    "step": step + 1,
                    "turn": game.turn,
                    "actor": actor,
                    "state_before": game.snapshot(),
                    "legal_action_details": legal_descriptions,
                }, ensure_ascii=False, default=_json_default) + "\n")
                out.flush()
            decision = encode_decision(game) if args.full_training_records else None
            if decision is not None:
                # This is the same forward contract used by the MCTS root:
                # one encoded state plus one encoded row for every legal action.
                neural = model.predict(game, legal_before)
                state_before = game.snapshot()
                event_offset = len(game.events)
            if args.search_stack_after_seconds:
                faulthandler.dump_traceback_later(
                    args.search_stack_after_seconds, repeat=True,
                )
            started = time.perf_counter()
            try:
                action = policy.choose(game)
            finally:
                if args.search_stack_after_seconds:
                    faulthandler.cancel_dump_traceback_later()
            choose_seconds = time.perf_counter() - started
            description = game.describe_action(action)
            before_turn = game.turn
            chosen_action = (
                decision.action_keys.index(action.key())
                if decision is not None else None
            )
            game.step(action)
            record = {"step": step + 1, "turn": before_turn,
                      "actor": actor, "action": description,
                      "choose_seconds": choose_seconds,
                      "legal_actions": len(game.legal_actions()),
                      "finished": game.finished,
                      "winner": game.winner}
            if decision is not None:
                search = dict(policy.last_search)
                # Keep these names byte-for-byte compatible with a generated
                # training decision, then add human/audit-only fields.
                record.update({
                    "record_type": "decision",
                    "game_seed": args.seed,
                    "ply": step,
                    "training_record": {
                        "state": decision.state,
                        "actions": decision.actions,
                        "action_keys": decision.action_keys,
                        "chosen_action": chosen_action,
                        "executed_action": chosen_action,
                        "policy_target": search.get("root_policy"),
                        "teacher_simulations": int(search.get("iterations", 0)),
                        "teacher_adaptive_simulations": int(search.get("adaptive_iterations", 0)),
                        "teacher_action_values": [
                            float(item["mean_value"])
                            for item in search.get("root_action_stats", ())
                        ],
                        "teacher_action_visits": [
                            int(item["visits"])
                            for item in search.get("root_action_stats", ())
                        ],
                        "legal_action_count": len(decision.actions),
                    },
                    "model_root_prediction": {
                        "policy_priors": neural.priors,
                        "value": neural.value,
                    },
                    "legal_action_details": [
                        {
                            "index": index,
                            "key": action_candidate.key(),
                            "description": legal_description,
                        }
                        for index, (action_candidate, legal_description) in enumerate(
                            zip(legal_before, legal_descriptions, strict=True)
                        )
                    ],
                    "engine_state_before": state_before,
                    "engine_state_after": game.snapshot(),
                    "events_emitted": game.events[event_offset:],
                    "teacher_search": search,
                })
            trace_records.append(record)
            if not args.full_training_records:
                out.write(json.dumps(
                    record, ensure_ascii=False, default=_json_default
                ) + "\n")
                out.flush()
        if args.full_training_records:
            for record in trace_records:
                training = record["training_record"]
                training["value_target"] = (
                    0.0 if game.winner is None
                    else 1.0 if game.winner == record["actor"] else -1.0
                )
                training["winner"] = game.winner
                out.write(json.dumps(
                    record, ensure_ascii=False, default=_json_default
                ) + "\n")
                out.flush()
        out.write(json.dumps({"kind": "final", "finished": game.finished,
                              "winner": game.winner, "turn": game.turn,
                              "invalid_actions": game.invalid_actions},
                             default=_json_default) + "\n")


if __name__ == "__main__":
    main()
