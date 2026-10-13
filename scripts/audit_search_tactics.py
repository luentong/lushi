#!/usr/bin/env python3
"""Fixed decision suite with per-action search evidence and honest pass labels.

Does not train on the evaluation cases. Labels describe immediate tactics or
a stated sequencing preference, not an oracle for full-game optimal play.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa import DragonMirrorGame, InformationSetMCTSPolicy
from hsa.dragon_mirror import Action, DRAGON_DECK_COUNTS
from hsa.policy_value import HeuristicPolicyValueModel, PolicyValueOutput


def make_case(name, fixture_seed=202609260501):
    game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", fixture_seed)
    game.turn = 9
    game.current = 0
    game.pending_choice = None
    game.events.clear()
    for player in game.players:
        player.hand = []; player.board = []; player.locations = []
        player.weapon = None; player.health = 30; player.armor = 0
        player.mana = player.max_mana = 2
        player.hero_attack_bonus = 0
        player.hero_power_used = False
        player.hero_attacks_this_turn = 0
    # Declared closed test opponent has no cards in hand. All future draw
    # contents still come from a public candidate, never its private order.
    game.search_deck_hypotheses = {i: [(1.0, dict(DRAGON_DECK_COUNTS))] for i in (0, 1)}
    def hand(card_id):
        card = game._entity(card_id); game.players[0].hand.append(card); return card
    def board(seat, card_id):
        card = game._entity(card_id); card.summoned_turn = game.turn - 2
        game.players[seat].board.append(card); return card
    if name == "information_before_commitment":
        carrier = hand("CATA_556"); hand("CAP_107")
        expected = lambda a: a.kind == "PLAY" and a.source == carrier.entity_id
        label = ("unscored sequencing preference: this two-mana fixture cannot "
                 "spend mana on the generated dragon after both one-cost cards")
    elif name == "immediate_lethal":
        board(0, "CAP_107"); game.players[1].health = 3
        expected = lambda a: a.kind == "ATTACK" and a.target_player == 1 and a.target_entity is None
        label = "proven: immediate lethal attack"
    elif name == "prevent_board_lethal":
        board(0, "CAP_107"); enemy = board(1, "CAP_107")
        game.players[0].health = 1; game.players[0].mana = 0
        # Isolate board defense: there is no unseen burn/rush topdeck in this
        # synthetic test. This is a tactical fixture, not a legal ladder deck.
        game.players[1].deck = [game._entity("CORE_CS2_231") for _ in range(10)]
        game.search_deck_hypotheses[0] = [(1., {"CORE_CS2_231": 10})]
        expected = lambda a: a.kind == "ATTACK" and a.target_entity == enemy.entity_id
        label = "proven: remove the only lethal board attacker"
    elif name == "reserve_mana_for_lethal":
        spell = hand("CATA_582"); hand("CAP_107")
        game.players[1].health = 3
        expected = lambda a: a.kind == "PLAY" and a.source == spell.entity_id
        label = "proven: spend two mana for +3 hero attack, then lethal"
    elif name == "after_generation_lethal":
        # A separate generic spell-generation scenario, not a Whelp outcome.
        spell = hand("CORE_CS2_029"); spell.created_by = "RANDOM_SPELL"
        game.players[0].mana = game.players[0].max_mana = 4
        game.players[1].health = 6
        expected = lambda a: a.kind == "PLAY" and a.source == spell.entity_id and a.target_player == 1 and a.target_entity is None
        label = "proven: use the newly observed generated spell for lethal"
    elif name == "after_generation_unaffordable":
        hand("CATA_111"); cannon = hand("CAP_107")
        game.players[0].mana = 1; game.players[0].max_mana = 2
        expected = lambda a: a.kind == "PLAY" and a.source == cannon.entity_id
        label = "preference: develop the playable body when the generated dragon costs three"
    elif name == "spend_remaining_mana_hero_power":
        game.players[0].mana = game.players[0].max_mana = 2
        game.players[0].health = 2
        threat = board(1, "CAP_107")
        game.players[1].deck = [game._entity("CORE_CS2_231") for _ in range(10)]
        game.search_deck_hypotheses[1] = [(1.0, {"CORE_CS2_231": 10})]
        expected = lambda a: a.kind == "HERO_POWER"
        label = "proven: spend the unused two mana on Warrior hero power to survive the known 3-attack threat"
    elif name == "conditional_threshold_trigger":
        # A generic conditional-payoff fixture: a trade that supplies the
        # fourth distinct friendly character damaged this turn summons a
        # Charge minion. The rule is not encoded in the policy or evaluator.
        attacker = board(0, "CAP_107")
        target = board(1, "CAP_107")
        target.damage = max(0, target.max_health - 1)
        game.players[0].hand = [game._entity("JAIL_421")]
        game.players[0].damaged_characters_this_turn = {
            "hero:0", "minion:9001", "minion:9002",
        }
        expected = lambda a: (a.kind == "ATTACK" and a.source == attacker.entity_id
                              and a.target_entity == target.entity_id)
        label = "proven: take a profitable trade that completes a four-character damage threshold"
    else:
        raise ValueError(name)
    return game, expected, label


CASES = ("information_before_commitment", "immediate_lethal",
         "prevent_board_lethal", "reserve_mana_for_lethal",
         "after_generation_lethal", "after_generation_unaffordable",
         "conditional_threshold_trigger", "spend_remaining_mana_hero_power")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--checkpoint", type=Path)
    p.add_argument("--device", default="cpu")
    p.add_argument("--budgets", type=int, nargs="+", default=[8, 64, 256])
    p.add_argument("--samples", type=int, default=1,
                   help="Hidden-state samples; each budget is total simulations and must be divisible by samples")
    p.add_argument("--seeds", type=int, nargs="+", default=[71, 113, 197])
    p.add_argument("--cases", nargs="+", choices=CASES, default=CASES)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--heuristic-leaves", action="store_true")
    p.add_argument("--disable-tactical-precheck", action="store_true")
    p.add_argument("--root-min-visits", type=int, default=0)
    p.add_argument("--root-outcome-min-visits", type=int, default=0)
    p.add_argument("--observed-action-min-visits", type=int, default=0,
                   help="In each sampled own-turn outcome of a stochastic root action, cover each legal continuation this many times.")
    p.add_argument("--model-rollout-depth", type=int, default=0)
    p.add_argument("--use-action-value-estimates", action="store_true",
                   help="Use a checkpoint's separately trained action-Q head as PUCT first-play urgency; ignored when absent/untrained.")
    p.add_argument("--prior-temperature", type=float, default=1.0,
                   help="Power-temperature applied to neural PUCT priors; >1 flattens them.")
    p.add_argument("--prior-uniform-mix", type=float, default=0.0,
                   help="Mix this fraction of uniform probability into each calibrated prior.")
    p.add_argument("--audit-turn", action="store_true",
                   help="For the sequencing preference, record the actual continuation and whether both cards are played.")
    p.add_argument("--trace-root", type=Path,
                   help="Replay a saved default dragon mirror trace to its selected step; fail on any state drift.")
    p.add_argument("--trace-step", type=int, default=8)
    p.add_argument("--trace-deck-config", type=Path)
    p.add_argument("--prior-mode", choices=("model", "uniform", "heuristic"), default="model")
    p.add_argument("--fixture-seed", type=int, default=202609260501,
                   help="Seed for the deterministic constructed tactical roots.")
    args = p.parse_args()
    if args.samples < 1 or any(budget < 1 or budget % args.samples for budget in args.budgets):
        p.error("each positive total simulation budget must be divisible by --samples")
    trace_game = None
    if args.trace_root:
        from replay_trace_state import replay_trace_state
        trace_game = replay_trace_state(args.trace_root, args.trace_step, args.trace_deck_config)
    def sha256(path):
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest()
    provenance = {
        "checkpoint_sha256": sha256(args.checkpoint) if args.checkpoint else None,
        "card_database_sha256": sha256(ROOT / "cards.251332.enUS.json"),
        "source_sha256": {str(path.relative_to(ROOT)): sha256(path) for path in (
            Path(__file__).resolve(), ROOT / "src/hsa/mcts.py",
            ROOT / "scripts/replay_trace_state.py",
            ROOT / "src/hsa/belief.py", ROOT / "src/hsa/search_deck.py",
            ROOT / "src/hsa/tactical_lethal.py",
            ROOT / "src/hsa/dragon_mirror.py", ROOT / "src/hsa/rules.py")},
    }
    if args.trace_deck_config:
        provenance["trace_deck_config_sha256"] = sha256(args.trace_deck_config)
    if args.checkpoint:
        from hsa.torch_model import TorchPolicyValueModel
        model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), args.device)
    else:
        model = HeuristicPolicyValueModel()
    if args.prior_mode != "model":
        class PriorAblation:
            def predict(self, game, actions):
                value = 0. if args.heuristic_leaves else model.predict(game, actions).value
                priors = (tuple(1. / len(actions) for _ in actions)
                          if args.prior_mode == "uniform" else
                          HeuristicPolicyValueModel().predict(game, actions).priors)
                return PolicyValueOutput(priors, value)
        search_model = PriorAblation()
    else:
        search_model = model
    rows = []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for name in args.cases:
        for budget in args.budgets:
            for seed in args.seeds:
                game, expected, label = make_case(name, args.fixture_seed)
                if trace_game is not None:
                    if name != "information_before_commitment":
                        p.error("trace-root only supports the information sequencing audit")
                    game = trace_game.clone()
                    carrier = next(c for c in game.players[game.current].hand if c.card_id == "CATA_556")
                    expected = lambda a: a.kind == "PLAY" and a.source == carrier.entity_id
                actions = game.legal_actions()
                policy = InformationSetMCTSPolicy(
                    samples=args.samples, iterations_per_sample=budget // args.samples,
                    tree_depth=6,
                    rollout_depth=4 if args.heuristic_leaves else 0,
                    policy_value_model=search_model, use_model_value=not args.heuristic_leaves,
                    seed=seed, max_total_iterations=budget,
                    tactical_precheck=not args.disable_tactical_precheck,
                    min_simulations_per_root_action=args.root_min_visits,
                    model_rollout_depth=args.model_rollout_depth,
                    use_action_value_estimates=args.use_action_value_estimates,
                    prior_temperature=args.prior_temperature,
                    prior_uniform_mix=args.prior_uniform_mix,
                    min_visits_per_root_outcome=args.root_outcome_min_visits,
                    min_visits_per_observed_action=args.observed_action_min_visits,
                    collect_plan_diagnostics=args.audit_turn,
                )
                start = time.perf_counter()
                chosen = policy.choose(game)
                passed = expected(chosen)
                threshold_triggered = None
                if name == "conditional_threshold_trigger":
                    after = game.clone(include_history=False, record_events=False)
                    after.step(chosen)
                    threshold_triggered = any(
                        card.card_id == "JAIL_421" for card in after.players[0].board
                    )
                    passed = passed and threshold_triggered
                row = {"case": name, "label": label, "budget": budget,
                       "samples": args.samples,
                       "seed": seed, "passed": passed,
                       "action": game.describe_action(chosen),
                       "seconds": time.perf_counter() - start,
                       "alternatives": [dict(action=game.describe_action(a), **stats)
                                        for a, stats in zip(actions, policy.last_search.get("root_action_stats", []))],
                       "search": policy.last_search}
                if name == "conditional_threshold_trigger":
                    row["threshold_triggered_after_action"] = threshold_triggered
                if name == "spend_remaining_mana_hero_power":
                    threat_entity_id = game.players[1].board[0].entity_id
                    after = game.clone(include_history=False, record_events=False)
                    after.step(chosen)
                    row["armor_after_action"] = after.players[0].armor
                    def counterattack_outcome(first_action):
                        sim = game.clone(include_history=False, record_events=False)
                        sim.step(first_action)
                        if not sim.finished and sim.current == 0:
                            end = next(a for a in sim.legal_actions()
                                       if a.kind == "END_TURN")
                            sim.step(end)
                        if not sim.finished and sim.current == 1:
                            attack = next(a for a in sim.legal_actions()
                                          if a.kind == "ATTACK"
                                          and a.source == threat_entity_id
                                          and a.target_player == 0
                                          and a.target_entity is None)
                            sim.step(attack)
                        return {"finished": sim.finished, "winner": sim.winner,
                                "health": sim.players[0].health,
                                "armor": sim.players[0].armor}
                    pass_action = next(a for a in actions if a.kind == "END_TURN")
                    hero_power_action = next(a for a in actions if a.kind == "HERO_POWER")
                    pass_outcome = counterattack_outcome(pass_action)
                    hero_power_outcome = counterattack_outcome(hero_power_action)
                    row["pass_counterattack_outcome"] = pass_outcome
                    row["hero_power_counterattack_outcome"] = hero_power_outcome
                    row["counterattack_proven"] = (
                        pass_outcome["winner"] == 1
                        and not hero_power_outcome["finished"]
                        and hero_power_outcome["armor"] == 0
                    )
                    passed = (passed and after.players[0].armor == 2
                              and row["counterattack_proven"])
                    row["passed"] = passed
                if name == "information_before_commitment":
                    row["first_action_matches_preference"] = row["passed"]
                    row["passed"] = None
                    row["conditional_order_status"] = "not_audited"
                    row["quality_failure_proven"] = False
                if trace_game is not None:
                    row["trace_root"] = {"path": str(args.trace_root),
                                         "sha256": sha256(args.trace_root),
                                         "step": args.trace_step, "recorded_state_match": True,
                                         "hidden_state_independently_verified": False}
                if args.audit_turn and name == "information_before_commitment":
                    # The preference is conditional on playing both. A plan
                    # that substitutes Cannoneer is not evidence of wrong
                    # sequencing of Whelp and Cannonmaster.
                    turn, actor = game.turn, game.current
                    committed = []
                    descriptions = []
                    action = chosen
                    game.rng.seed(f"{seed}:observed-continuation")
                    for _ in range(12):
                        descriptions.append(game.describe_action(action))
                        if action.kind == "PLAY":
                            committed.append(next(c.card_id for c in game.players[actor].hand
                                                  if c.entity_id == action.source))
                        game.step(action)
                        if game.finished or game.turn != turn or game.current != actor:
                            break
                        action = policy.choose(game)
                    both = all(c in committed for c in ("CATA_556", "CAP_107"))
                    row["continuation"] = {
                        "actions": descriptions, "both_played": both,
                        "preferred_order": (committed.index("CATA_556") < committed.index("CAP_107"))
                                           if both else None,
                    }
                    row["conditional_order_status"] = (
                        "preferred_order_observed" if both and row["continuation"]["preferred_order"]
                        else "reverse_order_observed" if both else "not_applicable")
                    # Sequence preference is not an optimality oracle. In this
                    # fixture both cards exhaust two mana, and every generated
                    # Dragon costs at least one. Do not count the reverse order
                    # as a tactical failure without an observed payoff gap.
                    row["passed"] = None
                rows.append(row)
                # Incremental audit output remains useful if a later case fails.
                args.output.write_text(json.dumps({
                    "checkpoint": str(args.checkpoint), "device": args.device,
                    "samples": args.samples,
                    "heuristic_leaves": args.heuristic_leaves,
                    "prior_mode": args.prior_mode,
                    "prior_temperature": args.prior_temperature,
                    "prior_uniform_mix": args.prior_uniform_mix,
                    "suite_version": 3,
                    "tactical_precheck": not args.disable_tactical_precheck,
                    "root_min_visits": args.root_min_visits,
                    "root_outcome_min_visits": args.root_outcome_min_visits,
                    "observed_action_min_visits": args.observed_action_min_visits,
                    "model_rollout_depth": args.model_rollout_depth,
                    "provenance": provenance,
                    "complete": False, "rows": rows,
                }, ensure_ascii=False, indent=2), encoding="utf-8")
                print(json.dumps({k: row[k] for k in ("case", "budget", "seed", "passed", "action", "seconds")}), flush=True)
    result = json.loads(args.output.read_text(encoding="utf-8"))
    result["complete"] = True
    result["summary"] = {
        str(b): {"passed": sum(r["passed"] is True for r in rows if r["budget"] == b),
                 "total": sum(r["budget"] == b and r["passed"] is not None for r in rows),
                 "not_scored": sum(r["budget"] == b and r["passed"] is None for r in rows)}
        for b in args.budgets
    }
    # Preferences (such as information-first sequencing) are not optimality
    # proofs. Keep them separate from immediate tactical expectations.
    result["summary_by_label"] = {
        category: {str(b): {
            "passed": sum(r["passed"] is True for r in rows if r["budget"] == b and r["label"].startswith(category)),
            "total": sum(r["budget"] == b and r["passed"] is not None and r["label"].startswith(category) for r in rows),
        } for b in args.budgets} for category in ("proven:", "preference:", "unscored sequencing preference:")
    }
    ordered = [r["continuation"] for r in rows if "continuation" in r]
    if ordered:
        result["conditional_order_summary"] = {
            "applicable": sum(r["both_played"] for r in ordered),
            "preferred_order_observed": sum(r["preferred_order"] is True for r in ordered),
            "reverse_order_observed": sum(r["preferred_order"] is False for r in ordered),
            "not_applicable": sum(not r["both_played"] for r in ordered),
        }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
