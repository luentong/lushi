#!/usr/bin/env python3
"""Compare agreed search picks with greedy picks under paired continuations.

Diagnostic only: a continuation policy is not an optimal opponent, and an
agreement filter alone is not sufficient to turn these actions into labels.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import gzip
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from audit_paired_root_outcomes import EntityGreedyPolicy, paired_outcomes
from hsa.policy import HeuristicPolicy
from replay_entity_rollout import replay_game_prefix, verify_report_inputs


def choose_rows(rows, limit):
    """Balance by deck and choose only disagreements worth comparing."""
    by_deck = defaultdict(list)
    for row in rows:
        if row["search_agree"] and row["teacher_target"] != row["model_pick"]:
            by_deck[row["deck"]].append(row)
    result = []
    while len(result) < limit and any(by_deck.values()):
        for deck in sorted(by_deck):
            if by_deck[deck] and len(result) < limit:
                result.append(by_deck[deck].pop(0))
    return result


def paired_score(results, teacher_key, model_key):
    teacher = next(item for item in results if item["action_key"] == teacher_key)
    model = next(item for item in results if item["action_key"] == model_key)
    score = {"wins": 1.0, "draws": .5, "losses": 0.0}
    differences = []
    for a, b in zip(teacher["outcomes"], model["outcomes"], strict=True):
        if a["replicate"] != b["replicate"]:
            raise ValueError("paired outcomes lost replicate alignment")
        if a["status"] in score and b["status"] in score:
            differences.append(score[a["status"]] - score[b["status"]])
    return {"paired_decided": len(differences),
            "teacher_better": sum(d > 0 for d in differences),
            "model_better": sum(d < 0 for d in differences),
            "tied": sum(d == 0 for d in differences),
            "score_delta": sum(differences) / len(differences) if differences else None}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--audit-rows", type=Path, required=True)
    p.add_argument("--rollout-report", type=Path, required=True)
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--max-roots", type=int, default=8)
    p.add_argument("--root", action="append", default=[], metavar="GAME_SEED:STEP",
                   help="Confirm only these previously identified roots, with fresh future seeds.")
    p.add_argument("--replicates", type=int, default=8)
    p.add_argument("--max-actions", type=int, default=320)
    p.add_argument("--seed", type=int, default=204301010000)
    p.add_argument("--continuation", choices=("heuristic", "entity-greedy"),
                   default="heuristic")
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--device", default="cpu")
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.max_roots < 1 or args.replicates < 1 or args.max_actions < 1:
        p.error("limits must be positive")
    if args.continuation == "entity-greedy" and args.checkpoint is None:
        p.error("--checkpoint is required for entity-greedy continuation")
    if args.output.exists():
        p.error("output already exists")
    report = json.loads(args.rollout_report.read_text(encoding="utf-8"))
    verify_report_inputs(report, args.cards, args.deck_config)
    records = {game["seed"]: game for game in report["history"][-1]["games"]}
    with gzip.open(args.audit_rows, "rt", encoding="utf-8") as handle:
        rows = [json.loads(line) for line in handle]
    requested = set()
    for item in args.root:
        try:
            game_seed, step = (int(part) for part in item.split(":"))
        except (ValueError, TypeError):
            p.error(f"invalid --root {item!r}; expected GAME_SEED:STEP")
        requested.add((game_seed, step))
    selected = choose_rows(rows, len(rows) if requested else args.max_roots)
    if requested:
        selected = [row for row in selected
                    if (row["game_seed"], row["step"]) in requested]
        if {(row["game_seed"], row["step"]) for row in selected} != requested:
            p.error("requested root is absent from agreed search/model disagreements")
        if len(selected) > args.max_roots:
            p.error("requested roots exceed --max-roots")
    continuation = (HeuristicPolicy() if args.continuation == "heuristic"
                    else EntityGreedyPolicy(args.checkpoint, args.device))
    output = {"status": "running", "schema": "broad-teacher-outcomes-v1",
              "source_audit": str(args.audit_rows), "replicates": args.replicates,
              "seed": args.seed,
              "max_actions": args.max_actions, "continuation": args.continuation,
              "checkpoint": str(args.checkpoint) if args.checkpoint else None,
              "training_authorized": False, "rows": []}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for position, row in enumerate(selected):
        game = replay_game_prefix(records[row["game_seed"]], args.cards,
                                  args.deck_config, until=row["step"])
        actions = game.legal_actions()
        teacher = actions[row["teacher_target"]]
        model = actions[row["model_pick"]]
        results = paired_outcomes(game, [teacher, model],
                                  replicates=args.replicates,
                                  max_actions=args.max_actions,
                                  seed=args.seed + position * (args.replicates + 1000),
                                  continuation_policy=continuation)
        comparison = paired_score(results, list(teacher.key()), list(model.key()))
        output["rows"].append({"deck": row["deck"], "game_seed": row["game_seed"],
            "step": row["step"], "turn": row["turn"],
            "teacher_action": game.describe_action(teacher),
            "model_action": game.describe_action(model),
            "comparison": comparison,
            "outcomes": results})
        args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"root": position + 1, "deck": row["deck"],
                          **comparison}, ensure_ascii=False), flush=True)
    compared = [row["comparison"] for row in output["rows"]]
    output["status"] = "complete"
    output["summary"] = {"roots": len(compared),
        "paired_decided": sum(row["paired_decided"] for row in compared),
        "teacher_better": sum(row["teacher_better"] for row in compared),
        "model_better": sum(row["model_better"] for row in compared),
        "tied": sum(row["tied"] for row in compared),
        "roots_favoring_teacher": sum((row["score_delta"] or 0) > 0 for row in compared),
        "roots_favoring_model": sum((row["score_delta"] or 0) < 0 for row in compared),
        "roots_tied_or_undecided": sum(row["score_delta"] is None or row["score_delta"] == 0
                                     for row in compared),
        "limitations": ["The frozen continuation policy is not an optimal player.",
                        "Paired replicates share sampled hidden worlds, not the real hand.",
                        "Roots are selected for search/model disagreement; not a win-rate sample."]}
    if isinstance(continuation, EntityGreedyPolicy):
        output["summary"]["model_inference"] = {
            "forward_passes": continuation.predictions,
            "exact_view_cache_hits": continuation.cache_hits,
            "model_forward_seconds": round(continuation.forward_seconds, 3),
        }
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
