#!/usr/bin/env python3
"""Build soft policy/action-Q targets from covered, repeated tactical roots.

Input is an audit_search_tactics.py report containing multiple independent
search seeds.  Per-action Q targets are visit-weighted across those seeds;
the policy target is a temperature-softmax over their aggregate Q means.
Unvisited actions stay masked rather than receiving an invented value.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from audit_search_tactics import CASES, make_case  # noqa: E402
from hsa.encoding import (  # noqa: E402
    configure_card_vocab,
    encode_action,
    encode_state,
    feature_schema,
)


def _softmax(values: list[float], valid: list[bool], temperature: float) -> list[float]:
    available = [value for value, keep in zip(values, valid, strict=True) if keep]
    if not available:
        return [0.0] * len(values)
    maximum = max(available)
    weights = [
        math.exp(max(-80.0, (value - maximum) / temperature)) if keep else 0.0
        for value, keep in zip(values, valid, strict=True)
    ]
    total = sum(weights)
    return [weight / total for weight in weights]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--fixture-seed", type=int, default=202609281337)
    parser.add_argument("--temperature", type=float, default=0.25)
    parser.add_argument("--min-seeds", type=int, default=3)
    parser.add_argument("--min-visits-per-action", type=int, default=3)
    parser.add_argument(
        "--card-vocab", choices=("legacy", "expanded-executable"),
        default="legacy",
        help="Frozen identity vocabulary used by the correction shard.",
    )
    parser.add_argument(
        "--schema-version", type=int, default=6, choices=(4, 6),
        help="Model schema to match the base training corpus.",
    )
    args = parser.parse_args()
    if args.temperature <= 0 or args.min_seeds < 2 or args.min_visits_per_action < 1:
        parser.error("temperature must be positive, min-seeds >=2 and visits >=1")
    audit = json.loads(args.audit.read_text(encoding="utf-8"))
    configure_card_vocab(args.card_vocab)
    selected = [row for row in audit.get("rows", ()) if row.get("budget") == args.budget]
    seed_set = sorted({int(row["seed"]) for row in selected})
    if len(seed_set) < args.min_seeds:
        raise ValueError(f"audit has only {len(seed_set)} independent seeds")
    rows = []
    audit_details = []
    for case in CASES:
        case_rows = [row for row in selected if row.get("case") == case]
        if not case_rows:
            continue
        by_seed = {int(row["seed"]): row for row in case_rows}
        if len(by_seed) < args.min_seeds:
            raise ValueError(f"{case}: only {len(by_seed)} seeds")
        game, expected, label = make_case(case, args.fixture_seed)
        actions = game.legal_actions()
        descriptions = [game.describe_action(action) for action in actions]
        q_by_seed: dict[str, list[float | None]] = {}
        weighted_sum = [0.0] * len(actions)
        visits_sum = [0] * len(actions)
        seed_count = [0] * len(actions)
        for seed in seed_set:
            row = by_seed.get(seed)
            values: list[float | None] = [None] * len(actions)
            if row:
                for alternative in row.get("alternatives", ()):
                    try:
                        index = descriptions.index(alternative["action"])
                    except ValueError as error:
                        raise ValueError(
                            f"{case}: audit action does not match fixture: "
                            f"{alternative['action']}"
                        ) from error
                    visits = int(alternative.get("visits", 0))
                    if visits > 0:
                        value = float(alternative["mean_value"])
                        values[index] = value
                        weighted_sum[index] += value * visits
                        visits_sum[index] += visits
                        seed_count[index] += 1
            q_by_seed[str(seed)] = values
        mean_q = [weighted_sum[i] / max(1, visits_sum[i]) for i in range(len(actions))]
        valid = [visits_sum[i] >= args.min_visits_per_action
                 and seed_count[i] >= args.min_seeds for i in range(len(actions))]
        target_source = "cross-seed-q"
        proven_policy_case = (
            case == "reserve_mana_for_lethal"
            or (
                case == "spend_remaining_mana_hero_power"
                and all(row.get("counterattack_proven") for row in case_rows)
            )
        )
        if proven_policy_case:
            # The search teacher undervalued a line whose rules-level
            # counterattack proof is deterministic. Keep this as policy-only
            # supervision; do not manufacture action-Q targets from it.
            target_source = "proof-only-policy"
            valid = [bool(expected(action)) for action in actions]
            target = [1.0 / sum(valid) if keep else 0.0 for keep in valid]
            chosen = next(i for i, keep in enumerate(valid) if keep)
        elif not any(valid):
            # The tactical precheck can prove a unique forced move without
            # entering MCTS, leaving no honest Q estimate to aggregate.
            # Preserve that narrow proof label as policy-only supervision.
            proven = [i for i, action in enumerate(actions) if expected(action)]
            if not proven or any(row.get("passed") is not True for row in case_rows):
                audit_details.append({"case": case, "label": label,
                                      "skipped": "insufficient multi-seed root coverage"})
                continue
            target_source = "proof-only-policy"
            valid = [i in proven for i in range(len(actions))]
            target = [1.0 / len(proven) if i in proven else 0.0
                      for i in range(len(actions))]
            chosen = proven[0]
        else:
            target = _softmax(mean_q, valid, args.temperature)
            chosen = max((i for i, ok in enumerate(valid) if ok), key=lambda i: mean_q[i])
        rows.append({
            "state": list(encode_state(
                game, game.current, schema_version=args.schema_version,
            )),
            "actions": [list(encode_action(
                game, action, schema_version=args.schema_version,
            )) for action in actions],
            "chosen_action": chosen,
            "policy_target": target,
            "value_target": 0.0,
            "value_target_valid": False,
            "teacher_action_values": [
                mean_q[i] if valid[i] and target_source == "cross-seed-q" else 0.0
                for i in range(len(actions))
            ],
            "teacher_action_visits": [
                visits_sum[i] if valid[i] and target_source == "cross-seed-q" else 0
                for i in range(len(actions))
            ],
            "actor": game.current,
            "game_seed": args.fixture_seed,
            "winner": None,
            "conditional": case in {
                "conditional_threshold_trigger", "after_generation_unaffordable",
                "spend_remaining_mana_hero_power",
            },
            "case": case, "target_source": target_source,
        })
        by_action = []
        for i, action in enumerate(actions):
            values = [q_by_seed[str(seed)][i] for seed in seed_set
                      if q_by_seed[str(seed)][i] is not None]
            mean = sum(values) / len(values) if values else None
            std = (sum((value - mean) ** 2 for value in values) / len(values)) ** .5 if values else None
            by_action.append({
                "action": descriptions[i], "valid": valid[i], "target_source": target_source,
                "mean_q": mean_q[i] if valid[i] and target_source == "cross-seed-q" else None,
                "between_seed_std": std,
                "seeds_visited": seed_count[i], "total_visits": visits_sum[i],
                "policy_target": target[i],
            })
        audit_details.append({"case": case, "label": label, "seed_count": len(by_seed),
                              "actions": by_action})

    if not rows:
        raise ValueError("audit contains none of the registered tactical cases")
    schema = feature_schema(args.schema_version)
    max_actions = max(len(record["actions"]) for record in rows)
    n = len(rows)
    states = torch.tensor([row["state"] for row in rows], dtype=torch.float32)
    action_size = int(schema["action_size"])
    actions_tensor = torch.zeros((n, max_actions, action_size), dtype=torch.float32)
    mask = torch.zeros((n, max_actions), dtype=torch.bool)
    q_values = torch.zeros((n, max_actions), dtype=torch.float32)
    q_visits = torch.zeros((n, max_actions), dtype=torch.int32)
    q_mask = torch.zeros((n, max_actions), dtype=torch.bool)
    targets = torch.zeros((n, max_actions), dtype=torch.float32)
    chosen = torch.zeros(n, dtype=torch.long)
    values = torch.zeros(n, dtype=torch.float32)
    actors = torch.zeros(n, dtype=torch.int8)
    valid_values = torch.zeros(n, dtype=torch.bool)
    conditional = torch.zeros(n, dtype=torch.bool)
    game_seeds = torch.full((n,), args.fixture_seed, dtype=torch.int64)
    winners = torch.full((n,), -1, dtype=torch.int8)
    for i, record in enumerate(rows):
        count = len(record["actions"])
        actions_tensor[i, :count] = torch.tensor(record["actions"], dtype=torch.float32)
        mask[i, :count] = True
        targets[i, :count] = torch.tensor(record["policy_target"], dtype=torch.float32)
        chosen[i] = record["chosen_action"]
        actors[i] = record["actor"]
        conditional[i] = record["conditional"]
        for j, (q, visits) in enumerate(zip(
            record["teacher_action_values"], record["teacher_action_visits"], strict=True
        )):
            if visits:
                q_values[i, j] = q
                q_visits[i, j] = visits
                q_mask[i, j] = True
    output = {
        "header": {
            "feature_schema": schema,
            "teacher": "cross-seed-covered-counterfactual-root-q-v1",
            "audit_report": str(args.audit),
            "audit_budget": args.budget,
            "audit_seeds": seed_set,
            "policy_target_temperature": args.temperature,
            "min_visits_per_action": args.min_visits_per_action,
            "min_seeds": args.min_seeds,
            "value_target": "masked; root action values are separate Q targets",
        },
        "states": states, "actions": actions_tensor, "mask": mask,
        "chosen": chosen, "values": values, "actor": actors,
        "value_valid": valid_values, "conditional": conditional,
        "game_seed": game_seeds, "winner": winners,
        "action_values": q_values, "action_value_visits": q_visits,
        "action_value_mask": q_mask, "policy_targets": targets, "count": n,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(output, args.output)
    report = {
        "records": n, "audit_budget": args.budget, "audit_seeds": seed_set,
        "fixture_seed": args.fixture_seed, "temperature": args.temperature,
        "schema": schema, "cases": audit_details,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"records": n, "max_actions": max_actions,
                      "output": str(args.output), "report": str(args.report)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
