"""Reconstruct a recorded decision, rejecting observable state drift."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa import DragonMirrorGame


def replay_trace_state(path: Path, step: int, deck_config: Path | None = None):
    from trace_search_match import compact_state
    trace = json.loads(path.read_text(encoding="utf-8"))
    if not 1 <= step <= len(trace["steps"]):
        raise ValueError("Requested step is outside the recorded trajectory")
    deck_kwargs = {}
    if trace.get("deck_a") or trace.get("deck_b"):
        if deck_config is None:
            raise ValueError("Named trace decks require a deck configuration")
        from benchmark_mcts import matchup_deck_counts
        (a, ca), (b, cb) = matchup_deck_counts(deck_config, trace["deck_a"], trace["deck_b"])
        deck_kwargs = {"deck_counts": (a, b), "player_classes": (ca, cb)}
    game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", trace["seed"], **deck_kwargs)
    if deck_config is not None:
        from benchmark_mcts import configure_search_beliefs
        configure_search_beliefs(game, deck_config)
    if compact_state(game.snapshot()) != trace["initial_state"]:
        raise RuntimeError("Initial trace state differs")
    for recorded in trace["steps"][:step - 1]:
        if compact_state(game.snapshot()) != recorded["state_before"]:
            raise RuntimeError(f"State drift before step {recorded['step']}")
        actions = [a for a in game.legal_actions() if game.describe_action(a) == recorded["description"]]
        if not actions:
            raise RuntimeError(f"Step {recorded['step']} has no matching legal action")
        if len(actions) == 1:
            game.step(actions[0])
            if compact_state(game.snapshot()) != recorded["state_after"]:
                raise RuntimeError(f"State drift after step {recorded['step']}")
            continue

        # Human-readable action labels omit hand-entity identity, so two
        # copies of the same card aimed at the same target have the same
        # description. Try each equivalent candidate on an isolated clone,
        # then use the recorded public after-state to disambiguate. This also
        # catches genuine state drift instead of arbitrarily replaying a copy.
        matching_games = []
        for action in actions:
            candidate = game.clone(include_history=False, record_events=False)
            try:
                candidate.step(action)
            except ValueError:
                continue
            if compact_state(candidate.snapshot()) == recorded["state_after"]:
                matching_games.append(candidate)
        if not matching_games:
            raise RuntimeError(
                f"State drift after ambiguous step {recorded['step']} "
                f"({len(actions)} same-description legal actions)"
            )
        # If equivalent copies lead to the same observable state, either
        # entity is a valid representative for continuing the replay.
        game = matching_games[0]
    if compact_state(game.snapshot()) != trace["steps"][step - 1]["state_before"]:
        raise RuntimeError("Requested root differs from the recorded state")
    return game
