#!/usr/bin/env python3
"""Preflight checks required before starting pooled multi-deck self-play.

The checks intentionally sit between unit tests and a long data-generation
run:

1. targeted rules expose only targets their effect can consume;
2. every action kind emitted by the engine can be encoded by the frozen model
   schema; and
3. every configured deck participates in a complete low-budget smoke game.

This is a gate, not a benchmark.  It exits non-zero on the first failed gate
and writes a compact JSON audit report for CI and remote training jobs.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / ".deps"))

from hsa import DragonMirrorGame, InformationSetMCTSPolicy  # noqa: E402
from hsa.dragon_mirror import Action  # noqa: E402
from hsa.encoding import (  # noqa: E402
    configure_card_vocab,
    encode_action,
    encode_decision,
    feature_schema,
)
from hsa.rules import TargetKind, build_rule_registry  # noqa: E402
from generate_policy_value_data import matchup_deck_counts  # noqa: E402


def _typed(definition) -> bool:
    return bool(definition.race or definition.races)


def _first_card(game: DragonMirrorGame, predicate) -> str:
    for card_id in sorted(game.executable_card_ids):
        definition = game.card_defs.get(card_id)
        if definition is not None and predicate(definition):
            return card_id
    raise RuntimeError("could not find representative card in executable pool")


def _new_game(cards: Path, seed: int) -> DragonMirrorGame:
    game = DragonMirrorGame(cards, seed)
    game.current = 0
    game.players[0].mana = 10
    game.players[0].max_mana = 10
    game.players[0].board.clear()
    game.players[1].board.clear()
    return game


def _put_hand(game: DragonMirrorGame, card_id: str):
    card = game._entity(card_id)
    game.players[0].hand.append(card)
    return card


def _put_board(game: DragonMirrorGame, player: int, card_id: str):
    card = game._entity(card_id)
    game.players[player].board.append(card)
    return card


def _entity_exists(game: DragonMirrorGame, owner: int, entity_id: int) -> bool:
    player = game.players[owner]
    return (
        any(card.entity_id == entity_id for card in player.board + player.hand)
        or any(location.entity_id == entity_id for location in player.locations)
    )


def check_target_pools(cards: Path, seed: int) -> dict[str, object]:
    """Validate generic target enumeration and known typed-state predicates."""
    game = _new_game(cards, seed)
    registry = build_rule_registry()
    checked_rules = 0
    target_actions = 0
    for rule in registry.all_rules():
        if rule.targeting is None or rule.card_id not in game.card_defs:
            continue
        card = game._entity(rule.card_id)
        targets = game._rule_targets(game.players[0], card, rule.targeting.kind)
        for owner, entity_id in targets:
            if owner not in (0, 1):
                raise AssertionError(f"{rule.card_id}: invalid target owner {owner}")
            if entity_id is not None:
                if not _entity_exists(game, owner, entity_id):
                    raise AssertionError(
                        f"{rule.card_id}: target entity {entity_id} is not in a visible zone"
                    )
            target_actions += 1
        checked_rules += 1

    # Regression probes for the target/effect mismatches found during the
    # first pooled run.  These are deliberately stateful rather than only
    # inspecting enum values.
    beast_id = _first_card(game, lambda d: d.card_type == "MINION" and d.race == "BEAST" or "BEAST" in d.races)
    untyped_id = _first_card(game, lambda d: d.card_type == "MINION" and not _typed(d))
    typed_id = _first_card(game, lambda d: d.card_type == "MINION" and _typed(d))

    torch_game = _new_game(cards, seed + 1)
    damaged = _put_board(torch_game, 1, typed_id)
    damaged.damage = 1
    healthy = _put_board(torch_game, 1, untyped_id)
    torch = _put_hand(torch_game, "CATA_585")
    torch_targets = {
        action.target_entity
        for action in torch_game.legal_actions()
        if action.kind == "PLAY" and action.source == torch.entity_id
    }
    if damaged.entity_id not in torch_targets or healthy.entity_id in torch_targets:
        raise AssertionError("CATA_585 target pool is not restricted to damaged minions")

    beast_game = _new_game(cards, seed + 2)
    beast = _put_board(beast_game, 0, beast_id)
    vanilla = _put_board(beast_game, 0, untyped_id)
    bugs_game = _new_game(cards, seed + 3)
    enemy_typed = _put_board(bugs_game, 1, typed_id)
    enemy_vanilla = _put_board(bugs_game, 1, untyped_id)
    herb = _put_hand(beast_game, "DINO_419")
    bugs = _put_hand(bugs_game, "TLC_633")
    herb_targets = {
        action.target_entity
        for action in beast_game.legal_actions()
        if action.kind == "PLAY" and action.source == herb.entity_id
    }
    bugs_targets = {
        action.target_entity
        for action in bugs_game.legal_actions()
        if action.kind == "PLAY" and action.source == bugs.entity_id
    }
    if beast.entity_id not in herb_targets or vanilla.entity_id in herb_targets:
        raise AssertionError("DINO_419 exposes a non-Beast target")
    if enemy_typed.entity_id not in bugs_targets or enemy_vanilla.entity_id in bugs_targets:
        raise AssertionError("TLC_633 exposes an untyped enemy target")

    choose_game = _new_game(cards, seed + 4)
    choose = _put_hand(choose_game, "EDR_570")
    choose_game.step(Action("PLAY", choose.entity_id))
    choose_actions = choose_game.legal_actions()
    if Action("RULE_CHOICE_PICK", 1) in choose_actions:
        raise AssertionError("EDR_570 exposes its damaged-minion branch without a target")

    gift_game = _new_game(cards, seed + 5)
    low_attack_id = _first_card(
        gift_game,
        lambda d: d.card_type == "MINION" and d.attack < 3,
    )
    high_attack_id = _first_card(
        gift_game,
        lambda d: d.card_type == "MINION" and d.attack >= 3,
    )
    low_attack = _put_board(gift_game, 0, low_attack_id)
    high_attack = _put_board(gift_game, 0, high_attack_id)
    gift_card = _put_hand(gift_game, "EDR_100t2")
    gift_targets = {
        action.target_entity
        for action in gift_game.legal_actions()
        if action.kind == "PLAY" and action.source == gift_card.entity_id
    }
    if high_attack.entity_id not in gift_targets or low_attack.entity_id in gift_targets:
        raise AssertionError("EDR_100t2 exposes an ineligible short_claws target")
    return {
        "status": "passed",
        "registry_target_rules_checked": checked_rules,
        "enumerated_target_actions": target_actions,
        "regression_probes": [
            "CATA_585", "DINO_419", "TLC_633", "EDR_570", "EDR_100t2",
        ],
    }


def check_action_encoding(cards: Path, seed: int) -> dict[str, object]:
    configure_card_vocab("expanded-executable")
    game = _new_game(cards, seed)
    source = game.players[0].hand[0].entity_id
    actions = [
        Action("MULLIGAN_TOGGLE", source), Action("MULLIGAN_CONFIRM"),
        Action("TRADE", source), Action("PLAY", source), Action("PREPARE", source),
        Action("ATTACK", source, 1, None), Action("HERO_ATTACK", target_player=1),
        Action("LOCATION", source), Action("HERO_POWER"),
        Action("DISCOVER_PICK", source), Action("REWIND_KEEP"),
        Action("REWIND_RETRY"), Action("AMMUNITION_PICK", 0),
        Action("CORPSE_SPEND", 1), Action("RULE_CHOICE_PICK", source),
        Action("CATACLYSM_PICK", -1), Action("EARTHEN_ROAR_PICK", source),
        Action("DISCARD_PICK", source), Action("HAND_PICK", source),
    ]
    for action in actions:
        encoded = encode_action(game, action)
        if len(encoded) != feature_schema()["action_size"]:
            raise AssertionError(f"{action.kind}: encoded size mismatch")
    # The current initial decision must also remain fully encodable.
    decision = encode_decision(game)
    if not decision.actions:
        raise AssertionError("initial decision has no encoded actions")
    return {"status": "passed", "action_kinds_checked": len(actions)}


def check_deck_smoke(cards: Path, config: Path, seed: int, iterations: int) -> dict[str, object]:
    configure_card_vocab("expanded-executable")
    payload = json.loads(config.read_text(encoding="utf-8"))
    decks = [item["id"] for item in payload["decks"]]
    if len(decks) < 2:
        raise ValueError("smoke requires at least two configured decks")
    results = []
    for index, deck_a in enumerate(decks):
        deck_b = decks[(index + 1) % len(decks)]
        (counts_a, class_a), (counts_b, class_b) = matchup_deck_counts(config, deck_a, deck_b)
        game = DragonMirrorGame(
            cards, seed + index, deck_counts=(counts_a, counts_b),
            player_classes=(class_a, class_b),
        )
        policies = [
            InformationSetMCTSPolicy(samples=1, iterations_per_sample=iterations,
                                     rollout_depth=2, seed=seed + index * 2 + seat)
            for seat in (0, 1)
        ]
        plies = 0
        while not game.finished and plies < 1000:
            decision = encode_decision(game)
            action = policies[game.current].choose(game)
            if action.key() not in decision.action_keys:
                raise AssertionError(f"{deck_a} vs {deck_b}: policy chose illegal action")
            game.step(action)
            plies += 1
        if not game.finished:
            raise RuntimeError(f"{deck_a} vs {deck_b}: exceeded 1000 actions")
        results.append({"deck_a": deck_a, "deck_b": deck_b,
                        "plies": plies, "winner": game.winner})
    return {"status": "passed", "games": results}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--deck-config", type=Path, default=ROOT / "config" / "decks_20260920_multi.json")
    parser.add_argument("--seed", type=int, default=202609200500)
    parser.add_argument("--iterations", type=int, default=4)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "preflight_multideck.json")
    args = parser.parse_args()
    started = time.perf_counter()
    report: dict[str, object] = {"schema_version": 1, "status": "failed"}
    try:
        report["target_pools"] = check_target_pools(args.cards, args.seed)
        report["action_encoding"] = check_action_encoding(args.cards, args.seed + 10)
        report["deck_smoke"] = check_deck_smoke(args.cards, args.deck_config, args.seed + 20, args.iterations)
        report["status"] = "passed"
    except Exception as exc:
        report["error"] = {"type": type(exc).__name__, "message": str(exc)}
        raise
    finally:
        report["elapsed_seconds"] = time.perf_counter() - started
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
