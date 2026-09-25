#!/usr/bin/env python3
"""Windows read-only Power.log companion with fail-closed belief advice.

The companion never controls the Hearthstone client.  It creates one
simulator hypothesis per declared opponent deck and only emits an advisory
move when the public snapshot validates and those hypotheses agree.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
import sys
from types import SimpleNamespace
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.live_adapter import PowerLogStateAdapter
from hsa.live_state import EntityView, LiveStateCursor
from hsa.live_replay import extract_replay_events
from hsa.live_replay import build_simulator_action_plan
from hsa.live_session import check_initial_decks
from hsa.belief_state import build_beliefs
from hsa.recommendation_gate import evaluate_gate
from hsa.belief_consensus import choose_consensus
from hsa.live_bridge import build_snapshot_hypothesis
from hsa.live_recommendation import (
    recommend_puct_state, recommend_replayed_state, recommend_replayed_states,
)
from hsa.torch_model import TorchPolicyValueModel
from hsa.incremental_powerlog import IncrementalPowerLogImporter
from hsa.powerlog_watcher import PowerLogTailer
from hsa.shadow_advisor import analyze_payload, jsonl_backlog


def find_latest_power_log(root: Path) -> Path | None:
    """Find the newest timestamped Hearthstone directory's Power.log."""
    candidates = [p for p in root.glob("Hearthstone_*/Power.log") if p.is_file()]
    if not candidates:
        candidates = [p for p in root.rglob("Power.log") if p.is_file()]
    return max(candidates, key=lambda p: p.stat().st_mtime, default=None)

def card_class_index(cards_path: Path) -> dict[str, str]:
    """Load card classes for candidate-deck selection, not for game inference."""
    payload = json.loads(cards_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return {}
    return {
        str(card.get("id") or card.get("cardId")): str(
            card.get("cardClass") or card.get("playerClass") or ""
        ).upper()
        for card in payload if isinstance(card, dict)
        and (card.get("id") or card.get("cardId"))
    }


def card_text_index(cards_path: Path) -> dict[str, str]:
    """Load card text only for classifying client-generic choice packets."""
    payload = json.loads(cards_path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        return {}
    return {
        str(card.get("id") or card.get("cardId")): str(card.get("text") or "")
        for card in payload if isinstance(card, dict)
        and (card.get("id") or card.get("cardId"))
    }


def normalise_open_choice_kind(event, state, card_text: dict[str, str]) -> str | None:
    """Map client GENERIC packets to Discover only when public evidence agrees."""
    kind = (event.choice_type or event.kind or "").upper()
    if kind != "GENERAL":
        return kind
    source_text = card_text.get(event.source_card or "", "").upper()
    option_tags = [
        state.entities.get(str(entity_id)).tags
        for entity_id in event.choices
        if state.entities.get(str(entity_id)) is not None
    ]
    if "DISCOVER" in source_text or any(tags.get("WAS_DISCOVER_OPTION") for tags in option_tags):
        return "DISCOVER"
    return kind


def is_observable_deck_play(action: dict[str, Any], state: Any) -> bool:
    """Return whether an action is evidence about a starting deck list.

    A Power.log PLAY is followed by a POWER resolution for the same card. The
    resolution is not a second copy. Hero powers, Coins, Discover results and
    tokens likewise are public actions but not evidence that a candidate deck
    contains their card ID.
    """
    if action.get("kind") != "PLAY":
        return False
    entity = (state.entities.get(str(action.get("source_entity")))
              or state.entity_registry.get(str(action.get("source_entity"))))
    if entity is None or entity.card_type not in {"MINION", "SPELL", "WEAPON", "LOCATION"}:
        return False
    creator = entity.tags.get("CREATOR")
    return not (str(creator).lstrip("-").isdigit() and int(creator) != 0)


def filter_candidates_for_class(
    candidates: list[dict[str, int]], card_classes: dict[str, str], target_class: str,
) -> list[dict[str, int]]:
    """Keep same-class deck hypotheses when a supplied candidate pool is mixed.

    Neutral cards do not vote.  If metadata cannot identify any matching deck,
    callers retain the original list rather than silently discarding coverage.
    """
    target = target_class.upper()
    matching: list[dict[str, int]] = []
    for deck in candidates:
        votes: dict[str, int] = {}
        for card_id, count in deck.items():
            card_class = card_classes.get(str(card_id), "")
            if card_class in {"", "NEUTRAL", "INVALID"}:
                continue
            votes[card_class] = votes.get(card_class, 0) + int(count)
        primary = max(votes, key=votes.get) if votes else None
        if primary == target:
            matching.append(deck)
    return matching or candidates


def class_matched_candidates(
    candidates: list[dict[str, int]], card_classes: dict[str, str], target_class: str,
) -> tuple[list[dict[str, int]], bool]:
    """Return only verified same-class candidates and whether coverage exists.

    The older filtering helper intentionally retains the original pool for
    offline callers.  Live advice must not simulate a Hunter as another
    class merely because the configured candidate file lacks Hunter decks.
    """
    target = target_class.upper()
    matching: list[dict[str, int]] = []
    for deck in candidates:
        votes: dict[str, int] = {}
        for card_id, count in deck.items():
            card_class = card_classes.get(str(card_id), "")
            if card_class in {"", "NEUTRAL", "INVALID"}:
                continue
            votes[card_class] = votes.get(card_class, 0) + int(count)
        primary = max(votes, key=votes.get) if votes else None
        if primary == target:
            matching.append(deck)
    return matching, bool(matching)


def filter_complete_candidates(candidates: list[dict[str, int]]) -> list[dict[str, int]]:
    """Discard truncated decklists when at least one complete list is present."""
    complete = [deck for deck in candidates if sum(map(int, deck.values())) >= 30]
    return complete or candidates


def configured_known_deck(payload: dict[str, Any]) -> dict[str, int]:
    """Return the one configured local deck, independent of controller key."""
    for deck in payload.values():
        if isinstance(deck, dict):
            return {str(card): int(count) for card, count in deck.items()}
    return {}


def configured_candidate_decks(payload: dict[str, Any]) -> list[dict[str, int]]:
    """Return configured opponent hypotheses, independent of controller key."""
    for decks in payload.values():
        if isinstance(decks, list):
            return [
                {str(card): int(count) for card, count in deck.items()}
                for deck in decks if isinstance(deck, dict)
            ]
    return []


def infer_local_controller(state) -> int | None:
    """Identify the local player from Power.log hand visibility.

    The local client knows its own hand card ids; the opponent's hand remains
    anonymous.  Refuse to guess until that asymmetry is visible.
    """
    hand_visibility: dict[int, tuple[int, int]] = {}
    for controller in (1, 2):
        hand = [entity for entity in state.entities.values()
                if entity.controller == controller and entity.zone == "HAND"]
        identified = sum(bool(entity.card_id) for entity in hand)
        hidden = len(hand) - identified
        hand_visibility[controller] = (identified, hidden)
    candidates = [
        controller for controller, (identified, hidden) in hand_visibility.items()
        if identified > 0 and hidden == 0
        and hand_visibility[3 - controller][1] > 0
    ]
    return candidates[0] if len(candidates) == 1 else None


def infer_player_classes(state, card_classes: dict[str, str]) -> dict[int, str]:
    """Read each public hero's class from its hero card id."""
    classes: dict[int, str] = {}
    for entity in state.entities.values():
        if entity.controller not in (1, 2) or not entity.card_id:
            continue
        if entity.card_type == "HERO":
            card_class = card_classes.get(entity.card_id, "")
            if card_class and card_class not in {"NEUTRAL", "INVALID"}:
                classes[entity.controller] = card_class
    return classes


def describe_action(game, action: dict) -> str:
    """Stable human-readable label; entity ids remain in JSON for auditing."""
    source_id = action.get("source")
    target_id = action.get("target_entity")
    cards = [card for player in game.players for card in player.hand + player.board]
    source = next((card.definition.name for card in cards if card.entity_id == source_id), None)
    target = next((card.definition.name for card in cards if card.entity_id == target_id), None)
    kind = action.get("kind", "ACTION")
    if kind == "DISCOVER_PICK":
        pending = getattr(game, "pending_choice", None) or {}
        option = next((card for card in pending.get("options", ())
                       if card.entity_id == source_id), None)
        return f"Choose {option.definition.name if option else 'Discover option'}"
    if kind == "END_TURN":
        return "End turn"
    if kind == "HERO_POWER":
        result = "Use Hero Power"
    elif kind == "HERO_ATTACK":
        result = "Hero attacks"
    elif kind == "ATTACK":
        result = f"Attack with {source or 'minion'}"
    elif kind == "PLAY":
        result = f"Play {source or 'card'}"
    elif kind == "LOCATION":
        result = f"Use {source or 'Location'}"
    else:
        result = kind.replace("_", " ").title()
    if target:
        return f"{result} -> {target}"
    if action.get("target_player") is not None:
        return f"{result} -> Player {int(action['target_player']) + 1} hero"
    return result


def summarize_legal_actions(game) -> dict[str, Any]:
    """Expose the action set supplied to policy scoring for local diagnosis."""
    actions = [
        {
            "kind": action.kind,
            "source": action.source,
            "target_player": action.target_player,
            "target_entity": action.target_entity,
        }
        for action in game.legal_actions()
    ]
    kinds: dict[str, int] = {}
    for action in actions:
        kinds[action["kind"]] = kinds.get(action["kind"], 0) + 1
    return {
        "count": len(actions),
        "kinds": kinds,
        "actions": [describe_action(game, action) for action in actions],
    }


def format_recommendation_banner(
    recommendation: dict[str, Any], decision_state: dict[str, Any] | None,
) -> str:
    """Put the actionable local advisory after the diagnostic JSON record."""
    action = recommendation.get("description") or recommendation.get("kind", "Unknown action")
    support = float(recommendation.get("hypothesis_support", 0.0)) * 100
    hypotheses = recommendation.get("hypotheses", 0)
    turn = (decision_state or {}).get("turn", "?")
    source = recommendation.get("source")
    source_line = f"Card entity: #{source}" if source is not None else None
    lines = [
        "=" * 72,
        "LOCAL HEARTHSTONE ADVISORY (read-only)",
        f"Turn: {turn}",
        f"Recommended action: {action}",
    ]
    if source_line:
        lines.append(source_line)
    lines.extend((
        f"Candidate agreement: {support:.0f}% ({hypotheses} hypotheses)",
        "=" * 72,
    ))
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--power-log", type=Path,
                   default=Path(r"C:\Program Files (x86)\Hearthstone\Logs"))
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--interval", type=float, default=0.2,
                   help="Power.log polling interval in seconds")
    p.add_argument("--settle-delay", type=float, default=0.15,
                   help="Wait for a quiet decision boundary before rebuilding live state")
    p.add_argument("--once", action="store_true")
    p.add_argument("--coverage", type=Path,
                   default=ROOT / "reports" / "standard_rule_coverage.json")
    p.add_argument("--output-directory", type=Path,
                   default=Path.home() / "AppData" / "Local" / "LushiAgent" / "shadow")
    p.add_argument("--line-only", action="store_true",
                   help="Skip hslog full-file import and only emit incremental line state.")
    p.add_argument("--verbose", action="store_true",
                   help="Include full local replay diagnostics in console output.")
    p.add_argument("--known-decks", type=Path, default=None,
                   help="JSON mapping controller to complete known deck counts.")
    p.add_argument("--candidate-decks", type=Path, default=None,
                   help="JSON mapping controller to a list of candidate deck counts.")
    p.add_argument("--mode", choices=("closed", "belief"), default="belief",
                   help="closed requires both decks; belief requires the known side and opponent candidates.")
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--self-controller", type=int, choices=(1, 2), default=1)
    p.add_argument("--player-classes", default="WARRIOR,WARRIOR",
                   help="classes in Power.log controller order, e.g. WARRIOR,PRIEST")
    p.add_argument("--self-class", default=None,
                   help="local player's class; enables automatic controller mapping")
    p.add_argument("--opponent-class", default=None,
                   help="optional fallback when the public opponent hero has not appeared yet")
    p.add_argument("--setaside-policy", choices=("strict", "advisory"), default="strict",
                   help="strict rejects all unresolved SETASIDE; advisory ignores inert reset debris")
    p.add_argument("--device", default="cuda",
                   help="PyTorch device for the checkpoint; use cpu if CUDA is unavailable")
    p.add_argument("--belief-min-support", type=float, default=0.0,
                   help="Optional consensus floor. Default 0 emits the plurality action and reports support.")
    p.add_argument("--max-hypotheses", type=int, default=12)
    p.add_argument("--search-iterations", type=int, default=8,
                   help="Bounded policy-prior ISMCTS simulations per hypothesis; 0 means policy only.")
    p.add_argument("--tree-depth", type=int, default=4)
    args = p.parse_args()
    power_log_root = args.power_log if args.power_log.is_dir() else None
    if args.power_log.is_dir():
        selected = find_latest_power_log(args.power_log)
        if selected is None:
            raise SystemExit(f"no Power.log found under: {args.power_log}")
        args.power_log = selected
    if not args.checkpoint.exists():
        raise SystemExit(f"checkpoint not found: {args.checkpoint}")
    if not args.cards.exists():
        raise SystemExit(f"card metadata not found: {args.cards}")
    card_classes = card_class_index(args.cards)
    card_text = card_text_index(args.cards)
    classes = tuple(x.strip().upper() for x in args.player_classes.split(","))
    if len(classes) != 2 or not all(classes):
        raise SystemExit("--player-classes must contain exactly two comma-separated classes")
    configured_self_class = (args.self_class or classes[args.self_controller - 1]).upper()
    configured_opponent_class = (args.opponent_class or classes[2 - args.self_controller]).upper()
    # Bootstrap from the current log on startup.  The importer below keeps
    # only the final CREATE_GAME segment, so this reconstructs an in-progress
    # game after a companion restart instead of waiting for its next packet.
    tailer = PowerLogTailer(args.power_log, from_end=False, from_last_create_game=True)
    adapter = PowerLogStateAdapter()
    incremental_importer = IncrementalPowerLogImporter()
    state_cursor: LiveStateCursor | None = None
    args.output_directory.mkdir(parents=True, exist_ok=True)
    model = None
    last_recommendation_signature: tuple[Any, ...] | None = None
    refresh_pending = False
    last_log_update_at: float | None = None
    print(json.dumps({"mode": "belief-shadow", "advice_available": False,
                      "reason": "awaiting a verified public snapshot and candidate consensus",
                      "checkpoint": str(args.checkpoint)}, ensure_ascii=False), flush=True)
    while True:
        if power_log_root is not None and not args.once:
            selected = find_latest_power_log(power_log_root)
            if selected is not None and selected != args.power_log:
                args.power_log = selected
                # A newly selected timestamped directory may already contain
                # CREATE_GAME and mulligan packets when the watcher notices
                # it.  Read them once to establish a fresh public baseline.
                tailer = PowerLogTailer(
                    args.power_log, from_end=False, from_last_create_game=True)
                adapter = PowerLogStateAdapter()
                incremental_importer.reset()
                state_cursor = None
                print(json.dumps({"mode": "belief-shadow", "event": "power_log_switched",
                                  "power_log": str(args.power_log)}, ensure_ascii=False), flush=True)
        new_lines = tailer.poll()
        if new_lines:
            # hslog's player registry is game-scoped. When the current log
            # moves to the next CREATE_GAME, retain only that game instead of
            # letting reused controller IDs contaminate the new snapshot.
            latest_game_start = max(
                (index for index, item in enumerate(new_lines)
                 if "GameState.DebugPrintPower() - CREATE_GAME" in item.text),
                default=None,
            )
            if latest_game_start is not None:
                incremental_importer.reset()
                state_cursor = None
                new_lines = new_lines[latest_game_start:]
            incremental_importer.consume(item.text for item in new_lines)
        for item in new_lines:
            snapshot = adapter.consume(item.text)
            if snapshot.decision_boundary:
                refresh_pending = True
                last_log_update_at = time.monotonic()
            if args.line_only and snapshot.decision_boundary:
                print(json.dumps({"offset": item.offset, **snapshot.as_dict(),
                                  "recommendation": None}, ensure_ascii=False), flush=True)
        if args.once and new_lines and args.line_only:
            print(json.dumps({"offset": new_lines[-1].offset, **adapter.snapshot.as_dict(),
                              "recommendation": None}, ensure_ascii=False), flush=True)
        # A card resolution can span many Power.log lines. Wait until the log
        # is quiet after a known decision boundary, then rebuild exactly once
        # from that stable public snapshot. This prevents stale half-actions
        # from consuming a full seven-hypothesis evaluation.
        should_refresh = (
            not args.line_only
            and ((args.once and bool(new_lines))
                 or (refresh_pending and last_log_update_at is not None
                     and time.monotonic() - last_log_update_at >= args.settle_delay))
        )
        if should_refresh:
            refresh_started_at = time.perf_counter()
            timing_ms: dict[str, float] = {}
            sanitized = args.output_directory / "live.sanitized.json"
            report = args.output_directory / "live.shadow.json"
            backlog = args.output_directory / "live.shadow.backlog.jsonl"
            try:
                refresh_stage = "normalize"
                sanitized_payload = incremental_importer.payload()
                if not sanitized_payload.get("games"):
                    raise RuntimeError("no CREATE_GAME packet found")
                sanitized.write_text(
                    json.dumps(sanitized_payload, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                refresh_stage = "shadow_analysis"
                coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
                shadow = analyze_payload(sanitized_payload, coverage)
                report.write_text(
                    json.dumps(shadow, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8",
                )
                backlog.write_text(jsonl_backlog(shadow["backlog"]), encoding="utf-8")
                refresh_stage = "public_state"
                state_summary = None
                state_object = None
                runtime_mapping = None
                replay_summary = None
                action_plan_summary = None
                session_gate = None
                belief_summary = None
                recommendation_gate = None
                recommendation = None
                bridge_summary = None
                consensus = None
                open_choice = None
                choice_ready = False
                if sanitized_payload.get("games"):
                    latest_game = sanitized_payload["games"][-1]
                    if state_cursor is None:
                        state_cursor = LiveStateCursor()
                    state_object = state_cursor.apply_game(latest_game)
                    state_summary = state_object.visible()
                    diagnostics = extract_replay_events(latest_game)
                    replay_summary = diagnostics.as_dict()
                    open_choice = next((event for event in reversed(diagnostics.events)
                                        if event.choices and not event.chosen), None)
                    # hslog keeps a Choice packet inside its parent PLAY block
                    # until that block closes. While the user is looking at a
                    # Discover prompt, that can be several seconds later. The
                    # line adapter retains the same public choice packet so
                    # we can score it before the click without serializing a
                    # raw Power.log line.
                    live_choice = adapter.snapshot.open_choice
                    if open_choice is None and live_choice:
                        options = tuple(
                            int(option["entity"])
                            for option in live_choice.get("options", ())
                            if option.get("entity") is not None
                        )
                        for option in live_choice.get("options", ()):
                            entity_id = option.get("entity")
                            if entity_id is None:
                                continue
                            key = str(entity_id)
                            entity = state_object.entities.get(key)
                            if entity is None:
                                entity = EntityView(key, controller=None, zone="SETASIDE")
                                state_object.entities[key] = entity
                            if option.get("card_id"):
                                entity.card_id = str(option["card_id"])
                        source_entity = live_choice.get("source_entity")
                        source_card = live_choice.get("source_card")
                        if not source_card and source_entity is not None:
                            source = state_object.entities.get(str(source_entity))
                            source_card = source.card_id if source else None
                        open_choice = SimpleNamespace(
                            choice_id=live_choice.get("id"),
                            choice_type=live_choice.get("choice_type"),
                            kind="POWER",
                            source_entity=source_entity,
                            source_card=source_card,
                            choices=options,
                            task_list=None,
                        )
                    open_choice_kind = (
                        normalise_open_choice_kind(open_choice, state_object, card_text)
                        if open_choice else None
                    )
                    choice_ready = bool(
                        open_choice and open_choice_kind in {"DISCOVER", "CHOOSE_ONE"}
                        and not diagnostics.hidden_randomness and not diagnostics.unsupported_blocks
                    )
                    stream_ready = bool(diagnostics.event_stream_closed or choice_ready)
                    configured_known = {}
                    if args.known_decks and args.known_decks.exists():
                        configured_known = configured_known_deck(
                            json.loads(args.known_decks.read_text(encoding="utf-8")))
                    configured_candidates: list[dict[str, int]] = []
                    if args.candidate_decks and args.candidate_decks.exists():
                        configured_candidates = configured_candidate_decks(
                            json.loads(args.candidate_decks.read_text(encoding="utf-8")))
                    inferred_self_controller = infer_local_controller(state_object)
                    # Legacy controller order remains available for static
                    # configurations.  Explicit self/opponent classes opt in
                    # to the safer per-game automatic mapping.
                    mapping_verified = (
                        inferred_self_controller is not None or not args.self_class
                    )
                    runtime_self_controller = (
                        inferred_self_controller
                        if inferred_self_controller is not None else args.self_controller
                    )
                    candidate_controller = str(3 - runtime_self_controller)
                    detected_classes = infer_player_classes(state_object, card_classes)
                    runtime_self_class = detected_classes.get(
                        runtime_self_controller, configured_self_class)
                    runtime_opponent_class = detected_classes.get(
                        int(candidate_controller), configured_opponent_class)
                    runtime_classes = (
                        (runtime_self_class, runtime_opponent_class)
                        if runtime_self_controller == 1
                        else (runtime_opponent_class, runtime_self_class)
                    )
                    runtime_mapping = {
                        "verified": mapping_verified,
                        "self_controller": runtime_self_controller,
                        "opponent_controller": int(candidate_controller),
                        "self_class": runtime_self_class,
                        "opponent_class": runtime_opponent_class,
                        "detected_controller_classes": detected_classes,
                    }
                    known = ({str(runtime_self_controller): configured_known}
                             if configured_known else {})
                    candidates = ({candidate_controller: configured_candidates}
                                  if configured_candidates else {})
                    for controller, cards in known.items():
                        replay_summary.setdefault("deck_counts", {})[str(controller)] = cards
                    plans = build_simulator_action_plan(diagnostics)
                    blocked = next((p for p in plans if not p.mappable), None)
                    action_plan_summary = {
                        "total": len(plans),
                        "mappable": sum(1 for p in plans if p.mappable),
                        "first_blocked": ({"index": blocked.index, "reason": blocked.reason}
                                           if blocked else None),
                    }
                    session_gate = check_initial_decks(replay_summary.get("deck_counts", {})).__dict__
                    belief_decks = dict(replay_summary.get("deck_counts", {}))
                    if candidate_controller in candidates:
                        belief_decks.setdefault(candidate_controller, {})
                    beliefs = build_beliefs(
                        belief_decks,
                        replay_summary.get("unknown_deck_slots", {}),
                        candidate_decks=candidates,
                    )
                    for action in state_summary.get("action_history", []) if state_summary else []:
                        controller = str(action.get("controller")) if action.get("controller") is not None else None
                        card = action.get("source_card")
                        if (controller in beliefs and card
                                and is_observable_deck_play(action, state_object)):
                            beliefs[controller].observe_played(card)
                    belief_summary = {key: value.summary() for key, value in beliefs.items()}
                    session_ready = bool(session_gate and session_gate.get("ready"))
                    if args.mode == "belief":
                        missing = (session_gate or {}).get("missing_slots", {})
                        session_ready = session_ready or (str(runtime_self_controller) not in missing)
                    all_candidates = list(candidates.get(candidate_controller, ()))
                    opponent_class = runtime_classes[int(candidate_controller) - 1]
                    class_candidates, class_coverage = class_matched_candidates(
                        all_candidates, card_classes, opponent_class)
                    complete_candidates = filter_complete_candidates(class_candidates)
                    raw_candidates = (complete_candidates[:args.max_hypotheses]
                                      if class_coverage else [])
                    hypothesis_actions = []
                    bridge_attempts = []
                    first_viable_legal_actions = None
                    own = known.get(str(runtime_self_controller), {}) if args.known_decks else {}
                    local_turn_ready = bool(
                        state_summary
                        and state_summary.get("active_player") == runtime_self_controller
                        and state_summary.get("game_phase") == "MAIN_ACTION"
                    )
                    if (args.mode == "belief" and own and raw_candidates and
                            stream_ready and state_summary and mapping_verified
                            and local_turn_ready):
                        refresh_stage = "model_load"
                        # Model load is delayed until the first viable local
                        # decision; this keeps passive log watching cheap.
                        if model is None:
                            model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), device=args.device)
                        viable_hypotheses = []
                        refresh_stage = "bridge"
                        bridge_started_at = time.perf_counter()
                        for number, candidate in enumerate(raw_candidates):
                            bridge = build_snapshot_hypothesis(
                                cards_path=args.cards, state=state_object, own_deck=own,
                                opponent_deck=candidate, player_classes=runtime_classes,
                                self_controller=runtime_self_controller, seed=number + 1,
                                open_choice_kind=open_choice_kind,
                                open_choice_entities=open_choice.choices if open_choice else (),
                                setaside_policy=args.setaside_policy,
                            )
                            bridge_attempts.append({"candidate": number, "available": bridge.available,
                                                    "reason": bridge.reason,
                                                    "public_match": bridge.public_match,
                                                    "notes": bridge.hypothesis_notes})
                            if bridge.available:
                                viable_hypotheses.append((number, bridge))
                                if first_viable_legal_actions is None:
                                    first_viable_legal_actions = summarize_legal_actions(
                                        bridge.game)
                        timing_ms["bridge"] = round(
                            (time.perf_counter() - bridge_started_at) * 1000, 1)
                        score_started_at = time.perf_counter()
                        if args.search_iterations == 0:
                            refresh_stage = "batch_policy"
                            fast_games = [bridge.game for _, bridge in viable_hypotheses]
                            fast_items = recommend_replayed_states(
                                fast_games, str(args.checkpoint), device=args.device, model=model,
                            )
                            scored_hypotheses = zip(viable_hypotheses, fast_items)
                        else:
                            scored_hypotheses = []
                            for number, bridge in viable_hypotheses:
                                if bridge.game.pending_choice:
                                    item = recommend_replayed_state(
                                        bridge.game, str(args.checkpoint), device=args.device, model=model,
                                    ).as_dict()
                                else:
                                    item = recommend_puct_state(
                                        bridge.game, str(args.checkpoint), device=args.device, model=model,
                                        iterations=args.search_iterations, tree_depth=args.tree_depth,
                                    ).as_dict()
                                scored_hypotheses.append(((number, bridge), item))
                        timing_ms["model_search"] = round(
                            (time.perf_counter() - score_started_at) * 1000, 1)
                        for (number, bridge), item in scored_hypotheses:
                            item = item.as_dict() if hasattr(item, "as_dict") else item
                            if item["available"]:
                                hypothesis_actions.append(item["action"] | {
                                    "probability": item["probability"], "value": item["value"],
                                    "candidate": number, "search": item.get("search"),
                                    "description": describe_action(bridge.game, item["action"]),
                                })
                        consensus = choose_consensus(hypothesis_actions,
                                                     min_support=args.belief_min_support)
                        bridge_summary = {"attempted": len(raw_candidates), "viable": len(hypothesis_actions),
                                          "candidate_class": opponent_class,
                                          "candidate_pool_size": len(all_candidates),
                                          "class_filtered_pool_size": len(class_candidates),
                                          "complete_pool_size": len(complete_candidates),
                                          "hypotheses": bridge_attempts,
                                          "first_viable_legal_actions": first_viable_legal_actions,
                                          "consensus_support": consensus.support}
                    elif not mapping_verified:
                        bridge_summary = {
                            "attempted": 0,
                            "viable": 0,
                            "failure_reasons": [
                                "local controller cannot yet be inferred from hand visibility"
                            ],
                        }
                    elif not local_turn_ready:
                        bridge_summary = {
                            "attempted": 0,
                            "viable": 0,
                            "failure_reasons": [
                                "waiting for a verified local MAIN_ACTION turn"
                            ],
                        }
                    elif not class_coverage:
                        bridge_summary = {
                            "attempted": 0,
                            "viable": 0,
                            "failure_reasons": [
                                f"candidate deck configuration has no {opponent_class} deck"
                            ],
                        }
                    # Belief uncertainty is information, not a reason to
                    # hide the model's best estimate.  With the default 0
                    # floor, choose_consensus returns the plurality action
                    # and exposes its support to the player.
                    if bridge_summary and consensus is not None and consensus.action is not None:
                        recommendation = consensus.action | {
                            "hypothesis_support": consensus.support,
                            "hypotheses": consensus.hypotheses,
                            "consensus_threshold_met": consensus.available,
                            "advisory_only": True,
                        }
                        risk_flags = sorted({note for attempt in bridge_attempts
                                             for note in attempt.get("notes", ())
                                             if str(note).startswith("advisory:")})
                        if risk_flags:
                            recommendation["confidence"] = "advisory"
                            recommendation["risk_flags"] = risk_flags
                    recommendation_gate = evaluate_gate(
                        event_stream_closed=stream_ready,
                        session_ready=session_ready,
                        beliefs=beliefs,
                        state_matches=False,
                        mode=args.mode,
                        belief_action_consensus=bool(recommendation),
                        opponent_controller=candidate_controller,
                    )
                timing_ms["total"] = round(
                    (time.perf_counter() - refresh_started_at) * 1000, 1)
                result = {
                    "mode": shadow.get("mode", "shadow-advisory-only"),
                    "game_count": shadow.get("game_count", 0),
                    "summary": shadow.get("summary", {}),
                    "state_reconstructed": state_summary is not None,
                    "state_summary": state_summary,
                    "runtime_mapping": runtime_mapping,
                    "replay_summary": replay_summary,
                    "open_choice": ({"id": open_choice.choice_id,
                                     "kind": open_choice_kind,
                                     "task_list": open_choice.task_list,
                                     "options": list(open_choice.choices)}
                                    if open_choice else None),
                    "action_plan_summary": action_plan_summary,
                    "session_gate": session_gate,
                    "belief_summary": belief_summary,
                    "recommendation_gate": recommendation_gate,
                    "bridge_summary": bridge_summary,
                    "recommendation_reason": (
                        "event_stream_not_closed" if replay_summary and not replay_summary["event_stream_closed"] and not choice_ready
                        else ("local_controller_not_yet_inferred"
                              if runtime_mapping and not runtime_mapping["verified"]
                        else ("no_viable_candidate_snapshot"
                              if not recommendation else None))
                    ),
                    "timing_ms": timing_ms,
                    "recommendation": recommendation,
                }
                if not args.verbose:
                    replay = replay_summary or {}
                    bridge_failures = []
                    if bridge_summary:
                        bridge_failures = sorted({
                            str(item.get("reason")) for item in bridge_summary.get("hypotheses", ())
                            if not item.get("available") and item.get("reason")
                        })
                    result = {
                        "mode": result["mode"],
                        "game_count": result["game_count"],
                        "state_reconstructed": result["state_reconstructed"],
                        "runtime_mapping": result["runtime_mapping"],
                        "decision_state": ({
                            "turn": result["state_summary"].get("turn"),
                            "active_player": result["state_summary"].get("active_player"),
                            "game_phase": result["state_summary"].get("game_phase"),
                        } if result["state_summary"] else None),
                        "replay": {
                            key: replay.get(key)
                            for key in ("event_count", "hidden_randomness",
                                        "unresolved_choices", "event_stream_closed")
                        },
                        "open_choice": result["open_choice"],
                        "session_gate": result["session_gate"],
                        "recommendation_gate": result["recommendation_gate"],
                        "bridge": ({"attempted": bridge_summary.get("attempted", 0),
                                    "viable": bridge_summary.get("viable", 0),
                                    "failure_reasons": bridge_failures,
                                    "first_viable_legal_actions": bridge_summary.get(
                                        "first_viable_legal_actions")}
                                   if bridge_summary else None),
                        "recommendation_reason": result["recommendation_reason"],
                        "timing_ms": result["timing_ms"],
                        "recommendation": result["recommendation"],
                    }
                print(json.dumps(result, ensure_ascii=False), flush=True)
                # Keep structured diagnostics for later inspection, then put
                # the human-facing advice last so Get-Content -Wait makes it
                # obvious during a live turn.  A state fingerprint prevents
                # repeated polling from printing the same advice forever.
                if result.get("recommendation"):
                    action = result["recommendation"]
                    decision = result.get("decision_state") or {}
                    signature = (
                        decision.get("turn"), decision.get("active_player"),
                        action.get("kind"), action.get("source"),
                        action.get("target_player"), action.get("target_entity"),
                    )
                    if signature != last_recommendation_signature:
                        print(format_recommendation_banner(action, decision), flush=True)
                        last_recommendation_signature = signature
                else:
                    last_recommendation_signature = None
            except (OSError, RuntimeError, ValueError) as exc:
                # Do not log the exception text: parser exceptions can embed a
                # raw Power.log line. The type is enough to diagnose local
                # control flow without exposing account or client data.
                print(json.dumps({"mode": "line-shadow",
                                  "import_error": "Power.log import failed",
                                  "error_type": type(exc).__name__,
                                  "stage": refresh_stage,
                                  "recommendation": None}, ensure_ascii=False), flush=True)
            finally:
                refresh_pending = False
        if args.once:
            return 0
        time.sleep(max(0.2, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
