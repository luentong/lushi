#!/usr/bin/env python3
"""Compare full-game outcomes after forcing each action at a recorded root.

This is a diagnostic continuation experiment, not a benchmark or model update.
"""
from __future__ import annotations

import argparse
import enum
import json
import sys
import time
from pathlib import Path

try:
    from enum import StrEnum  # noqa: F401
except ImportError:  # Python 3.10 on some shared Ascend images
    class StrEnum(str, enum.Enum):
        def __str__(self) -> str:
            return self.value

    enum.StrEnum = StrEnum

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from hsa import DragonMirrorGame, InformationSetMCTSPolicy
from benchmark_mcts import matchup_deck_counts, configure_search_beliefs
from trace_search_match import compact_state
from hsa.torch_model import TorchPolicyValueModel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--cards", type=Path, required=True)
    parser.add_argument("--device", default="npu:0")
    parser.add_argument("--iterations", type=int, default=8)
    parser.add_argument("--tree-depth", type=int, default=6)
    parser.add_argument("--games-per-action", type=int, default=1)
    parser.add_argument("--forced-prefix", nargs="*", default=None,
                        help="Force these exact action descriptions before model continuation.")
    parser.add_argument("--max-actions", type=int, default=240)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    trace = json.loads(args.trace.read_text(encoding="utf-8"))
    (deck_a, class_a), (deck_b, class_b) = matchup_deck_counts(
        args.deck_config, trace["deck_a"], trace["deck_b"]
    )
    base = DragonMirrorGame(
        args.cards, trace["seed"], deck_counts=(deck_a, deck_b),
        player_classes=(class_a, class_b),
    )
    configure_search_beliefs(base, args.deck_config)
    for recorded in trace["steps"][: args.step - 1]:
        if compact_state(base.snapshot()) != recorded["state_before"]:
            raise RuntimeError(f"state drift before trace step {recorded['step']}")
        matches = [a for a in base.legal_actions()
                   if base.describe_action(a) == recorded["description"]]
        if not matches:
            raise RuntimeError(f"no legal match for trace step {recorded['step']}")
        matched = []
        for action in matches:
            candidate = base.clone(include_history=False, record_events=False)
            candidate.step(action)
            if compact_state(candidate.snapshot()) == recorded["state_after"]:
                matched.append(candidate)
        if not matched:
            raise RuntimeError(f"state drift after trace step {recorded['step']}")
        base = matched[0]
    root = base.clone(include_history=False, record_events=False)
    legal = root.legal_actions()
    descriptions = [root.describe_action(a) for a in legal]
    if compact_state(root.snapshot()) != trace["steps"][args.step - 1]["state_before"]:
        raise RuntimeError("reconstructed root does not match recorded state")

    print(f"Loading checkpoint on {args.device}...", flush=True)
    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    result = {
        "trace": args.trace.name, "step": args.step,
        "checkpoint": str(args.checkpoint), "device": args.device,
        "iterations": args.iterations, "tree_depth": args.tree_depth,
        "root_state": compact_state(root.snapshot()),
        "root_legal_actions": descriptions, "runs": [],
    }
    started_all = time.monotonic()
    sequences = (
        [args.forced_prefix] if args.forced_prefix
        else [[description] for description in descriptions]
    )
    for action_index, sequence in enumerate(sequences):
        for game_index in range(args.games_per_action):
            game = root.clone(include_history=False, record_events=False)
            initial_events = []
            forced_states = []
            for description in sequence:
                matches = [action for action in game.legal_actions()
                           if game.describe_action(action) == description]
                if len(matches) != 1:
                    raise RuntimeError(
                        f"forced action {description!r}: expected one legal match, got {len(matches)}"
                    )
                offset = len(game.events)
                game.step(matches[0])
                initial_events.extend(game.events[offset:])
                forced_states.append({
                    "action": description,
                    "state": compact_state(game.snapshot()),
                    "legal_actions": [game.describe_action(a) for a in game.legal_actions()],
                })
            policies = [
                InformationSetMCTSPolicy(
                    samples=1, iterations_per_sample=args.iterations,
                    tree_depth=args.tree_depth, rollout_depth=0,
                    seed=2026092800 + action_index * 100 + game_index * 2 + seat,
                    policy_value_model=model, use_model_value=True,
                    min_simulations_per_root_action=1,
                )
                for seat in range(2)
            ]
            continuation = []
            while not game.finished and len(continuation) < args.max_actions:
                actor = game.current
                options = game.legal_actions()
                chosen = policies[actor].choose(game)
                text = game.describe_action(chosen)
                event_offset = len(game.events)
                game.step(chosen)
                continuation.append({
                    "actor": actor + 1, "action": text,
                    "state": compact_state(game.snapshot()),
                    "events": game.events[event_offset:],
                })
            row = {
                "forced_root_action": " | ".join(sequence), "replicate": game_index + 1,
                "winner": game.winner, "finished": game.finished,
                "invalid_actions": game.invalid_actions,
                "actions_after_root": len(continuation),
                "root_events": initial_events,
                "forced_prefix_states": forced_states,
                "continuation": continuation,
                "elapsed_seconds": round(time.monotonic() - started_all, 3),
            }
            result["runs"].append(row)
            print(json.dumps({k: row[k] for k in (
                "forced_root_action", "replicate", "winner", "finished",
                "invalid_actions", "actions_after_root", "elapsed_seconds"
            )}, ensure_ascii=False), flush=True)
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result["total_elapsed_seconds"] = round(time.monotonic() - started_all, 3)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
