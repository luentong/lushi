#!/usr/bin/env python3
"""Paired action-order diagnostics; estimates are not optimality labels."""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa.belief import PublicBelief
from hsa.encoding import encode_state
from hsa import encoding
from hsa.policy_value import HeuristicPolicyValueModel, PolicyValueOutput
from hsa.mcts import evaluate_state
from replay_trace_state import replay_trace_state
from trace_search_match import compact_state


def fixed_order(game, actions, model):
    """Execute legal root actions; expose post-reveal alternatives and value."""
    actor = game.current
    rows = []
    for action in actions:
        if action not in game.legal_actions():
            return {"legal": False, "steps": rows}, game
        description = game.describe_action(action)
        before_rng = game.rng.getstate()
        game.step(action)
        legal = game.legal_actions()
        prediction = (PolicyValueOutput((), evaluate_state(game, game.current))
                      if game.finished else model.predict(game, legal))
        rows.append({
            "action": description,
            "consumed_rng": before_rng != game.rng.getstate(),
            "value_for_root_actor": prediction.value if game.current == actor else -prediction.value,
            "alternatives": [{"action": game.describe_action(a), "prior": float(p)}
                             for a, p in zip(legal, prediction.priors, strict=True)],
            "state": compact_state(game.snapshot()),
            "own_hand_ids_outside_checkpoint_vocab": sorted({
                c.card_id for c in game.players[actor].hand if c.card_id not in encoding.CARD_INDEX
            }),
        })
        if game.finished or game.current != actor or game.pending_choice is not None:
            return {"legal": False, "steps": rows, "reason": "turn ended or pending choice"}, game
    result = {"legal": True, "steps": rows,
              "final_value": rows[-1]["value_for_root_actor"]}
    # A real END_TURN is safer than manually swapping game.current to probe
    # perspective: turn triggers, mana refresh and draws must still execute.
    end = next((a for a in game.legal_actions() if a.kind == "END_TURN"), None)
    if end is not None:
        probe = game.clone()
        probe.step(end)
        prediction = (PolicyValueOutput((), evaluate_state(probe, probe.current))
                      if probe.finished else model.predict(probe, probe.legal_actions()))
        root_value = prediction.value if probe.current == actor else -prediction.value
        result["end_turn_probe"] = {
            "value_for_root_actor": root_value,
            "shift_from_before_end_turn": root_value - result["final_value"],
            "state": compact_state(probe.snapshot()),
            "warning": "The next turn includes legitimate triggers and draws; a shift alone is not proof of a value bug.",
        }
    return result, game


def inventory_signature(game):
    """Diagnostic only: ignoring position is NOT a general equivalence proof."""
    view = compact_state(game.snapshot())
    for player in view["players"]:
        for zone in ("hand", "board", "locations"):
            def remove_ids(value):
                if isinstance(value, dict):
                    return {k: remove_ids(v) for k, v in value.items() if k != "entity"}
                if isinstance(value, list):
                    return [remove_ids(v) for v in value]
                return value
            player[zone] = sorted((remove_ids(card) for card in player[zone]),
                                  key=lambda c: json.dumps(c, sort_keys=True))
    return json.dumps(view, sort_keys=True)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--step", type=int, default=8)
    parser.add_argument("--deck-config", type=Path)
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seeds", nargs="+", type=int, default=[71, 113, 197])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = replay_trace_state(args.trace, args.step, args.deck_config)
    if args.checkpoint:
        from hsa.torch_model import TorchPolicyValueModel
        model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    else:
        model = HeuristicPolicyValueModel()
    actions = [a for a in root.legal_actions() if a.kind == "PLAY"]
    belief = PublicBelief.from_game(root, root.current)
    result = {"schema_version": 1, "complete": False, "step": args.step,
              "warning": "Paired diagnostic only; neither network value nor inventory match proves optimal ordering.",
              "provenance": {"trace_sha256": sha(args.trace),
                             "checkpoint_sha256": sha(args.checkpoint) if args.checkpoint else None,
                             "deck_config_sha256": sha(args.deck_config) if args.deck_config else None,
                             "source_sha256": {str(p.relative_to(ROOT)): sha(p) for p in (
                                 Path(__file__).resolve(), ROOT / "scripts/replay_trace_state.py",
                                 ROOT / "src/hsa/encoding.py", ROOT / "src/hsa/belief.py",
                                 ROOT / "src/hsa/dragon_mirror.py")}}, "rows": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for seed in args.seeds:
        sampled = belief.sample_determinization(root, seed=seed, record_event=False)
        for a, b in itertools.combinations(actions, 2):
            # Both orders share the same sampled world and future RNG state.
            ab, end_ab = fixed_order(sampled.clone(), (a, b), model)
            ba, end_ba = fixed_order(sampled.clone(), (b, a), model)
            row = {"seed": seed, "pair": [root.describe_action(a), root.describe_action(b)],
                   "ab": ab, "ba": ba}
            if ab["legal"] and ba["legal"]:
                va = encode_state(end_ab, root.current)
                vb = encode_state(end_ba, root.current)
                row.update(value_delta=ab["final_value"] - ba["final_value"],
                           different_encoded_features=sum(x != y for x, y in zip(va, vb, strict=True)),
                           inventory_match_ignoring_positions_and_entity_ids=
                           inventory_signature(end_ab) == inventory_signature(end_ba))
            result["rows"].append(row)
            args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    result["complete"] = True
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"pairs": len(result["rows"]), "output": str(args.output)}))


if __name__ == "__main__":
    main()
