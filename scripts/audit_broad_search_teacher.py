#!/usr/bin/env python3
"""Audit independent public-belief search labels on stratified self-play roots."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from benchmark_mcts import _decoded_decks
from hsa.mcts import InformationSetMCTSPolicy
from hsa.observer_view import observer_view
from hsa.policy_value import PolicyValueOutput
from replay_entity_rollout import replay_game_prefix, verify_report_inputs
from train_entity_selfplay import select_device


def candidate_roots(games, roots_per_deck, seed):
    rng = random.Random(seed)
    grouped = defaultdict(list)
    for game in games:
        if game.get("status") != "complete":
            continue
        seat = game["learner_seat"]
        deck = game["deck_a"] if seat == 0 else game["deck_b"]
        steps = [(i, row["turn"]) for i, row in enumerate(game["action_trace"])
                 if row["actor"] == seat and row["action"][0] not in
                 {"MULLIGAN_TOGGLE", "MULLIGAN_CONFIRM", "END_TURN"}]
        if not steps:
            continue
        # Sample one position per game so long games do not dominate labels.
        by_phase = defaultdict(list)
        for index, turn in steps:
            by_phase[min(2, (turn - 1) // 6)].append(index)
        for phase in sorted(by_phase):
            grouped[(deck, phase)].append((game, rng.choice(by_phase[phase])))
    result = []
    for deck in sorted({deck for deck, _ in grouped}):
        selected_seeds = set()
        for position in range(roots_per_deck):
            phase = position % 3
            candidates = [item for item in grouped[(deck, phase)]
                          if item[0]["seed"] not in selected_seeds]
            if not candidates:
                candidates = [item for (key_deck, _), rows in grouped.items()
                              if key_deck == deck for item in rows
                              if item[0]["seed"] not in selected_seeds]
            if not candidates:
                break
            game, step = rng.choice(candidates)
            selected_seeds.add(game["seed"])
            result.append((deck, game, step))
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--rollout-report", type=Path, required=True)
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--device", default="cpu")
    p.add_argument("--roots-per-deck", type=int, default=8)
    p.add_argument("--budget", type=int, default=32)
    p.add_argument("--rollout-depth", type=int, default=8)
    p.add_argument("--seed", type=int, default=204101010000)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.roots_per_deck < 1 or args.budget < 4 or args.rollout_depth < 0 or args.output.exists():
        p.error("invalid root count/budget or output exists")
    import torch
    from hsa.entity_model import EntityPolicyValueNet, collate_views
    torch.set_num_threads(2)
    report = json.loads(args.rollout_report.read_text(encoding="utf-8"))
    verify_report_inputs(report, args.cards, args.deck_config)
    games = report["history"][-1]["games"]
    roots = candidate_roots(games, args.roots_per_deck, args.seed)
    known_decks = _decoded_decks(args.deck_config)
    device = select_device(args.device)
    model = EntityPolicyValueNet.from_payload(torch.load(
        args.checkpoint, map_location="cpu", weights_only=False)).to(device).eval()
    rows = []
    for deck, record, step in roots:
        game = replay_game_prefix(record, args.cards, args.deck_config, until=step)
        if game.current != record["learner_seat"]:
            raise ValueError("replayed root does not belong to learner")
        actions = tuple(game.legal_actions())
        if len(actions) < 2:
            continue
        view = observer_view(game, game.current, actions=actions,
                             known_deck=known_decks[deck][0])
        with torch.no_grad():
            logits, value = model(collate_views([view], model.card_ids, device))
            probs = tuple(logits[0, :len(actions)].softmax(-1).cpu().tolist())
            estimate = float(value[0])
        prediction = PolicyValueOutput(probs, estimate)
        picks = []
        seed_base = args.seed + record["seed"] * 3 + step * 2
        seed_stride = max(1_000_003, args.budget * 10)
        for replica in range(2):
            search = InformationSetMCTSPolicy(samples=4,
                iterations_per_sample=(args.budget + 3) // 4,
                max_total_iterations=args.budget, min_simulations_per_root_action=1,
                tree_depth=8, rollout_depth=args.rollout_depth,
                seed=seed_base + replica * seed_stride,
                use_model_value=False, prior_uniform_mix=.1)
            selected = search.choose(game, root_prediction=prediction, root_actions=actions)
            picks.append(next(i for i, action in enumerate(actions)
                              if action.key() == selected.key()))
        rows.append({"deck": deck, "game_seed": record["seed"], "step": step,
            "turn": game.turn, "action_count": len(actions),
            "search_seeds": [seed_base, seed_base + seed_stride],
            "model_pick": max(range(len(actions)), key=probs.__getitem__),
            "search_picks": picks, "search_agree": picks[0] == picks[1],
            "view": view if picks[0] == picks[1] else None,
            "teacher_target": picks[0] if picks[0] == picks[1] else None})
        print(json.dumps({"root": len(rows), "planned": len(roots), "deck": deck,
            "search_agree": picks[0] == picks[1],
            "model_agrees": picks[0] == picks[1] and picks[0] == rows[-1]["model_pick"]},
            ensure_ascii=False), flush=True)
    args.output.mkdir(parents=True)
    accepted = [row for row in rows if row["search_agree"]]
    with gzip.open(args.output / "agreed-roots.jsonl.gz", "wt", encoding="utf-8") as handle:
        for row in accepted:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")
    audit = {"status": "complete", "checkpoint": str(args.checkpoint),
        "rollout_report": str(args.rollout_report), "budget_per_search": args.budget,
        "rollout_depth": args.rollout_depth,
        "search_seed_stride": max(1_000_003, args.budget * 10),
        "planned_roots": len(roots), "evaluated_roots": len(rows),
        "search_agreement": len(accepted),
        "model_agreement_when_search_agrees": sum(row["teacher_target"] == row["model_pick"]
            for row in accepted),
        "by_deck": dict(Counter(row["deck"] for row in rows)),
        "training_authorized": False,
        "caveat": "Two same-budget seeds agreeing is a label filter, not proof of optimal play."}
    (args.output / "audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2),
                                            encoding="utf-8")
    print(json.dumps(audit, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
