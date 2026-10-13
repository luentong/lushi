#!/usr/bin/env python3
"""Compare a frozen entity policy with public-belief root search on fixed roots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from audit_search_tactics import CASES, make_case
from evaluate_entity_policy import EntityValueAdapter
from hsa.dragon_mirror import DRAGON_DECK_COUNTS
from hsa.mcts import InformationSetMCTSPolicy
from hsa.observer_view import observer_view
from hsa.policy_value import PolicyValueOutput
from train_entity_selfplay import select_device


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--budget", type=int, default=64)
    parser.add_argument("--tree-depth", type=int, default=8)
    parser.add_argument("--rollout-depth", type=int, default=8)
    parser.add_argument("--leaf-mode", choices=("heuristic", "entity_value"),
                        default="heuristic")
    parser.add_argument("--seeds", type=int, nargs="+", default=[71, 100071])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.budget < 4 or not args.seeds:
        parser.error("budget >= 4 and at least one seed are required")
    if args.tree_depth < 1 or args.rollout_depth < 0:
        parser.error("tree depth must be positive and rollout depth nonnegative")
    if any(abs(a - b) < args.budget for i, a in enumerate(args.seeds)
           for b in args.seeds[i + 1:]):
        parser.error("search seed ranges must not overlap")
    import torch
    from hsa.entity_model import EntityPolicyValueNet, collate_views

    torch.set_num_threads(2)
    device = select_device(args.device)
    model = EntityPolicyValueNet.from_payload(torch.load(
        args.checkpoint, map_location="cpu", weights_only=False)).to(device).eval()
    results = []
    for name in CASES:
        game, expected, label = make_case(name)
        actions = tuple(game.legal_actions())
        view = observer_view(game, actions=actions, known_deck=DRAGON_DECK_COUNTS)
        with torch.no_grad():
            logits, value = model(collate_views([view], model.card_ids, device))
            prior = tuple(logits[0, :len(actions)].softmax(-1).cpu().tolist())
            root_value = float(value[0])
        prediction = PolicyValueOutput(prior, root_value)
        greedy = actions[max(range(len(actions)), key=prior.__getitem__)]
        trials = []
        for seed in args.seeds:
            search = InformationSetMCTSPolicy(samples=4,
                iterations_per_sample=(args.budget + 3) // 4,
                max_total_iterations=args.budget, min_simulations_per_root_action=1,
                tree_depth=args.tree_depth, rollout_depth=args.rollout_depth, seed=seed,
                policy_value_model=(EntityValueAdapter(model, device)
                                    if args.leaf_mode == "entity_value" else None),
                use_model_value=args.leaf_mode == "entity_value",
                neural_prior_depth=1, prior_uniform_mix=.1)
            started = time.monotonic()
            selected = search.choose(game, root_prediction=prediction, root_actions=actions)
            trials.append({"seed": seed, "pass": bool(expected(selected)),
                "selected": game.describe_action(selected),
                "iterations": search.last_search.get("iterations"),
                "selection_source": search.last_search.get("selection_source"),
                "seconds": time.monotonic() - started})
        results.append({"case": name, "label": label,
            "greedy_pass": bool(expected(greedy)), "greedy_selected": game.describe_action(greedy),
            "expected_prior": sum(p for p, a in zip(prior, actions) if expected(a)),
            "search": trials})
        print(json.dumps({"case": name, "greedy": bool(expected(greedy)),
            "search": [r["pass"] for r in trials]}, ensure_ascii=False), flush=True)
    report = {"checkpoint": str(args.checkpoint), "budget": args.budget,
        "tree_depth": args.tree_depth, "rollout_depth": args.rollout_depth,
        "leaf_mode": args.leaf_mode,
        "seeds": args.seeds, "results": results, "diagnostic_only": True}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
