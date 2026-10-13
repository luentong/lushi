#!/usr/bin/env python3
"""A/B audit of a trained action-Q head as PUCT first-play urgency."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa import InformationSetMCTSPolicy
from hsa.torch_model import TorchPolicyValueModel
from replay_trace_state import replay_trace_state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--step", type=int, required=True)
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--deck-config", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--budgets", type=int, nargs="+", default=[32, 128])
    parser.add_argument("--q-prior-weight", type=float, default=2.0)
    parser.add_argument("--heuristic-prior-mix", type=float, nargs="+", default=[0.0])
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 41, 73])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    game = replay_trace_state(args.trace, args.step, args.deck_config)
    actions = game.legal_actions()
    model = TorchPolicyValueModel.from_checkpoint(
        str(args.checkpoint), args.device
    )
    prediction = model.predict(game, actions)
    results = []
    for budget in args.budgets:
        for seed in args.seeds:
            for use_q in (False, True):
                for heuristic_mix in args.heuristic_prior_mix:
                    policy = InformationSetMCTSPolicy(
                        samples=1, iterations_per_sample=budget, tree_depth=6,
                        rollout_depth=0, policy_value_model=model,
                        use_model_value=True, neural_prior_depth=1,
                        tactical_precheck=False, max_total_iterations=budget,
                        seed=seed, use_action_value_estimates=use_q,
                        action_value_prior_weight=args.q_prior_weight,
                        heuristic_prior_mix=heuristic_mix,
                    )
                    selected = policy.choose(game.clone())
                    stats = policy.last_search.get("root_action_stats", ())
                    alternatives = []
                    for action, row in zip(actions, stats):
                        alternatives.append({
                            "action": game.describe_action(action),
                            "prior": row.get("prior"),
                            "q_prior": row.get("prior_value"),
                            "visits": row.get("visits"),
                            "mean_value": row.get("mean_value"),
                            "selected": row.get("selected"),
                        })
                    results.append({
                        "budget": budget, "seed": seed,
                        "use_action_q": use_q,
                        "heuristic_prior_mix": heuristic_mix,
                        "selected": game.describe_action(selected),
                        "search_value": policy.last_search.get("selected_value"),
                        "alternatives": alternatives,
                    })
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps({
        "step": args.step,
        "trace": str(args.trace),
        "checkpoint": str(args.checkpoint),
        "action_value_trained": model.action_value_trained,
        "q_prior_weight": args.q_prior_weight,
        "heuristic_prior_mix": args.heuristic_prior_mix,
        "root_value": prediction.value,
        "root_actions": [{
            "action": game.describe_action(action),
            "prior": prediction.priors[index],
            "q_value": prediction.action_values[index]
            if len(prediction.action_values) == len(actions) else None,
        } for index, action in enumerate(actions)],
        "results": results,
        "caution": "Action-Q is a learned approximation to the search teacher, not ground-truth game-theoretic value. This A/B alone cannot establish stronger play.",
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "rows": len(results), "action_value_trained": model.action_value_trained,
        "root_value": prediction.value, "output": str(args.output),
    }))


if __name__ == "__main__":
    main()
