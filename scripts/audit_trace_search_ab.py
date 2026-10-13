#!/usr/bin/env python3
"""Compare value/search settings on exact recorded public decision roots.

This is a diagnostic, not a strength benchmark: it freezes the simulator state
from a trace and varies root budget, root-action coverage, and leaf evaluation.
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

from hsa import InformationSetMCTSPolicy
from hsa.policy_value import PolicyValueOutput
from hsa.torch_model import TorchPolicyValueModel
from replay_trace_state import replay_trace_state


class NeutralValueWithModelPrior:
    """Keep learned action priors while removing the learned leaf value."""

    name = "model-prior-neutral-value"

    def __init__(self, model):
        self.model = model

    def predict(self, game, actions):
        output = self.model.predict(game, actions)
        return PolicyValueOutput(
            priors=output.priors,
            value=0.0,
            action_values=(),
        )


class ScaledValueWithModelPrior:
    """Keep learned priors but shrink the scalar leaf value toward neutral."""

    def __init__(self, model, scale: float):
        self.model = model
        self.scale = scale
        self.name = f"model-prior-value-x{scale:g}"

    def predict(self, game, actions):
        output = self.model.predict(game, actions)
        return PolicyValueOutput(
            priors=output.priors,
            value=output.value * self.scale,
            action_values=(),
        )


class RootPerspectiveValueWithModelPrior:
    """Keep policy/Q outputs but evaluate leaves from the fixed root view."""

    name = "model-prior-root-perspective-value"

    def __init__(self, model, observer: int):
        self.model = model
        self.observer = observer

    def predict(self, game, actions):
        output = self.model.predict(game, actions)
        return PolicyValueOutput(
            priors=output.priors,
            value=output.value,
            action_values=output.action_values,
        )

    def predict_value(self, game, observer: int) -> float:
        return self.model.predict_value(game, self.observer)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--steps", type=int, nargs="+", required=True,
                        help="Recorded step numbers; state is replayed to before each action.")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--budgets", type=int, nargs="+", default=[16, 64, 128])
    parser.add_argument("--root-min-visits", type=int, nargs="+", default=[0, 2])
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 29, 41])
    parser.add_argument("--modes", nargs="+", choices=(
                            "model", "half", "quarter", "neutral", "rootview", "rollout"),
                        default=["model", "neutral", "rollout"])
    parser.add_argument("--rollout-depth", type=int, default=6)
    parser.add_argument("--tree-depth", type=int, default=12,
                        help="Maximum search tree depth; 12 reaches roughly 1-3 own turns.")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    neutral_model = NeutralValueWithModelPrior(model)
    scaled_models = {
        "half": ScaledValueWithModelPrior(model, 0.5),
        "quarter": ScaledValueWithModelPrior(model, 0.25),
    }
    rows: list[dict[str, object]] = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for step in args.steps:
        for budget in args.budgets:
            for minimum in args.root_min_visits:
                for mode in args.modes:
                    for seed in args.seeds:
                        game = replay_trace_state(args.trace, step, args.deck_config)
                        search_model = (
                            neutral_model if mode == "neutral"
                            else RootPerspectiveValueWithModelPrior(model, game.current)
                            if mode == "rootview"
                            else scaled_models.get(mode, model)
                        )
                        policy = InformationSetMCTSPolicy(
                            samples=1,
                            iterations_per_sample=budget,
                            max_total_iterations=budget,
                            tree_depth=args.tree_depth,
                            rollout_depth=args.rollout_depth if mode == "rollout" else 0,
                            policy_value_model=search_model,
                            use_model_value=mode != "rollout",
                            root_perspective_model_value=mode == "rootview",
                            min_simulations_per_root_action=minimum,
                            tactical_precheck=False,
                            seed=seed,
                        )
                        started = time.perf_counter()
                        chosen = policy.choose(game)
                        seconds = time.perf_counter() - started
                        actions = game.legal_actions()
                        stats = policy.last_search.get("root_action_stats", [])
                        # A fallback/terminal root can expose fewer stats than
                        # legal actions. Keep those actions in the audit with
                        # zero visits instead of aborting the whole trajectory.
                        alternatives = []
                        for index, action in enumerate(actions):
                            row = stats[index] if index < len(stats) else {
                                "visits": 0, "mean_value": 0.0,
                                "visit_share": 0.0, "selected": False,
                            }
                            alternatives.append({
                                "action": game.describe_action(action),
                                **row,
                            })
                        state = game.snapshot()
                        players = state["players"]
                        row = {
                            "step": step,
                            "turn": game.turn,
                            "actor": game.current + 1,
                            "budget": budget,
                            "root_min_visits": minimum,
                            "mode": mode,
                            "seed": seed,
                            "legal_actions": len(actions),
                            "chosen": game.describe_action(chosen),
                            "seconds": seconds,
                            "players": [
                                {
                                    "player": p["player"],
                                    "health": p["health"],
                                    "armor": p["armor"],
                                    "mana": [p["mana"], p["max_mana"]],
                                    "hand": [c["name"] for c in p["hand"]],
                                    "board": [
                                        f'{c["name"]} {c["attack"]}/{c["health"]}'
                                        for c in p["board"]
                                    ],
                                }
                                for p in players
                            ],
                            "search": policy.last_search,
                            "alternatives": alternatives,
                        }
                        rows.append(row)
                        args.output.write_text(json.dumps({
                            "trace": str(args.trace),
                            "checkpoint": str(args.checkpoint),
                            "device": args.device,
                            "complete": False,
                            "rows": rows,
                        }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
                        print(json.dumps({
                            "step": step, "budget": budget,
                            "root_min_visits": minimum, "mode": mode,
                            "seed": seed, "chosen": row["chosen"],
                            "legal_actions": len(actions),
                            "seconds": round(seconds, 3),
                        }, ensure_ascii=False), flush=True)
    args.output.write_text(json.dumps({
        "trace": str(args.trace),
        "checkpoint": str(args.checkpoint),
        "device": args.device,
        "complete": True,
        "rows": rows,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
