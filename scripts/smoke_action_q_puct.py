#!/usr/bin/env python3
"""Verify that a trained action-Q head actually reaches PUCT root children."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame, InformationSetMCTSPolicy
from hsa.torch_model import TorchPolicyValueModel


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--device", default="cpu")
    args = parser.parse_args()

    model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    if not model.action_value_trained:
        raise ValueError("checkpoint does not declare a trained action-Q head")
    game = DragonMirrorGame(args.cards, 20261012)
    search = InformationSetMCTSPolicy(
        samples=1,
        iterations_per_sample=4,
        tree_depth=2,
        rollout_depth=0,
        seed=20261012,
        policy_value_model=model,
        use_model_value=True,
        use_action_value_estimates=True,
        force_uniform_expansion=False,
        neural_prior_depth=1,
    )
    action = search.choose(game)
    stats = search.last_search["root_action_stats"]
    weighted = [row for row in stats if row["prior_value_weight"] > 0]
    if not weighted:
        raise AssertionError("action-Q values did not reach any root child")
    print(json.dumps({
        "action": str(action),
        "root_actions": len(stats),
        "q_weighted_root_actions": len(weighted),
        "nonzero_q_values": sum(abs(row["prior_value"]) > 1e-8 for row in weighted),
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
