#!/usr/bin/env python3
"""Windows read-only Power.log companion with fail-closed belief advice.

The companion never controls the Hearthstone client.  It creates one
simulator hypothesis per declared opponent deck and only emits an advisory
move when the public snapshot validates and those hypotheses agree.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.live_adapter import PowerLogStateAdapter
from hsa.live_state import reconstruct_game
from hsa.live_replay import extract_replay_events
from hsa.live_replay import build_simulator_action_plan
from hsa.live_session import check_initial_decks
from hsa.belief_state import build_beliefs
from hsa.recommendation_gate import evaluate_gate
from hsa.belief_consensus import choose_consensus
from hsa.live_bridge import build_snapshot_hypothesis
from hsa.live_recommendation import recommend_puct_state, recommend_replayed_state
from hsa.torch_model import TorchPolicyValueModel
from hsa.powerlog_watcher import PowerLogTailer


def find_latest_power_log(root: Path) -> Path | None:
    """Find the newest timestamped Hearthstone directory's Power.log."""
    candidates = [p for p in root.glob("Hearthstone_*/Power.log") if p.is_file()]
    if not candidates:
        candidates = [p for p in root.rglob("Power.log") if p.is_file()]
    return max(candidates, key=lambda p: p.stat().st_mtime, default=None)


def describe_action(game, action: dict) -> str:
    """Stable human-readable label; entity ids remain in JSON for auditing."""
    source_id = action.get("source")
    target_id = action.get("target_entity")
    cards = [card for player in game.players for card in player.hand + player.board]
    source = next((card.definition.name for card in cards if card.entity_id == source_id), None)
    target = next((card.definition.name for card in cards if card.entity_id == target_id), None)
    kind = action.get("kind", "ACTION")
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


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--power-log", type=Path,
                   default=Path(r"C:\Program Files (x86)\Hearthstone\Logs"))
    p.add_argument("--checkpoint", type=Path, required=True)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--once", action="store_true")
    p.add_argument("--coverage", type=Path,
                   default=ROOT / "reports" / "standard_rule_coverage.json")
    p.add_argument("--output-directory", type=Path,
                   default=Path.home() / "AppData" / "Local" / "LushiAgent" / "shadow")
    p.add_argument("--line-only", action="store_true",
                   help="Skip hslog full-file import and only emit incremental line state.")
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
    p.add_argument("--device", default="cuda",
                   help="PyTorch device for the checkpoint; use cpu if CUDA is unavailable")
    p.add_argument("--belief-min-support", type=float, default=0.0,
                   help="Optional consensus floor. Default 0 emits the plurality action and reports support.")
    p.add_argument("--max-hypotheses", type=int, default=12)
    p.add_argument("--search-iterations", type=int, default=8,
                   help="Bounded policy-prior ISMCTS simulations per hypothesis; 0 means policy only.")
    p.add_argument("--tree-depth", type=int, default=4)
    args = p.parse_args()
    if args.power_log.is_dir():
        selected = find_latest_power_log(args.power_log)
        if selected is None:
            raise SystemExit(f"no Power.log found under: {args.power_log}")
        args.power_log = selected
    if not args.checkpoint.exists():
        raise SystemExit(f"checkpoint not found: {args.checkpoint}")
    if not args.cards.exists():
        raise SystemExit(f"card metadata not found: {args.cards}")
    classes = tuple(x.strip().upper() for x in args.player_classes.split(","))
    if len(classes) != 2 or not all(classes):
        raise SystemExit("--player-classes must contain exactly two comma-separated classes")
    tailer = PowerLogTailer(args.power_log, from_end=not args.once)
    adapter = PowerLogStateAdapter()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    model = None
    print(json.dumps({"mode": "belief-shadow", "advice_available": False,
                      "reason": "awaiting a verified public snapshot and candidate consensus",
                      "checkpoint": str(args.checkpoint)}, ensure_ascii=False), flush=True)
    while True:
        new_lines = tailer.poll()
        for item in new_lines:
            snapshot = adapter.consume(item.text)
            if snapshot.decision_boundary or args.once:
                print(json.dumps({"offset": item.offset, **snapshot.as_dict(),
                                  "recommendation": None}, ensure_ascii=False), flush=True)
        if new_lines and not args.line_only:
            sanitized = args.output_directory / "live.sanitized.json"
            report = args.output_directory / "live.shadow.json"
            backlog = args.output_directory / "live.shadow.backlog.jsonl"
            importer = ROOT / "scripts" / "import_power_log.py"
            analyzer = ROOT / "scripts" / "shadow_power_log.py"
            try:
                subprocess.run(
                    [sys.executable, str(importer), str(args.power_log),
                     "--output", str(sanitized)], check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                )
                subprocess.run(
                    [sys.executable, str(analyzer), str(sanitized),
                     "--coverage", str(args.coverage), "--output", str(report),
                     "--backlog", str(backlog)], check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                )
                shadow = json.loads(report.read_text(encoding="utf-8"))
                state_summary = None
                replay_summary = None
                action_plan_summary = None
                session_gate = None
                belief_summary = None
                recommendation_gate = None
                recommendation = None
                bridge_summary = None
                open_choice = None
                choice_ready = False
                sanitized_payload = json.loads(sanitized.read_text(encoding="utf-8"))
                if sanitized_payload.get("games"):
                    latest_game = sanitized_payload["games"][-1]
                    state_summary = reconstruct_game(latest_game).visible()
                    diagnostics = extract_replay_events(latest_game)
                    replay_summary = diagnostics.as_dict()
                    open_choice = next((event for event in reversed(diagnostics.events)
                                        if event.choices and not event.chosen), None)
                    choice_ready = bool(
                        open_choice and open_choice.kind in {"DISCOVER", "CHOOSE_ONE"}
                        and not diagnostics.hidden_randomness and not diagnostics.unsupported_blocks
                    )
                    stream_ready = bool(diagnostics.event_stream_closed or choice_ready)
                    if args.known_decks and args.known_decks.exists():
                        known = json.loads(args.known_decks.read_text(encoding="utf-8"))
                        for controller, cards in known.items():
                            replay_summary.setdefault("deck_counts", {})[str(controller)] = {
                                str(card): int(count) for card, count in cards.items()
                            }
                    plans = build_simulator_action_plan(diagnostics)
                    blocked = next((p for p in plans if not p.mappable), None)
                    action_plan_summary = {
                        "total": len(plans),
                        "mappable": sum(1 for p in plans if p.mappable),
                        "first_blocked": ({"index": blocked.index, "reason": blocked.reason}
                                           if blocked else None),
                    }
                    session_gate = check_initial_decks(replay_summary.get("deck_counts", {})).__dict__
                    candidates = {}
                    if args.candidate_decks and args.candidate_decks.exists():
                        candidates = json.loads(args.candidate_decks.read_text(encoding="utf-8"))
                    belief_decks = dict(replay_summary.get("deck_counts", {}))
                    candidate_controller = str(3 - args.self_controller)
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
                        if controller in beliefs and card:
                            beliefs[controller].observe_played(card)
                    belief_summary = {key: value.summary() for key, value in beliefs.items()}
                    session_ready = bool(session_gate and session_gate.get("ready"))
                    if args.mode == "belief":
                        missing = (session_gate or {}).get("missing_slots", {})
                        session_ready = session_ready or (str(args.self_controller) not in missing)
                    raw_candidates = list(candidates.get(candidate_controller, ()))[:args.max_hypotheses]
                    hypothesis_actions = []
                    bridge_attempts = []
                    own = known.get(str(args.self_controller), {}) if args.known_decks else {}
                    if (args.mode == "belief" and own and raw_candidates and
                            stream_ready and state_summary):
                        # Model load is delayed until the first viable local
                        # decision; this keeps passive log watching cheap.
                        if model is None:
                            model = TorchPolicyValueModel.from_checkpoint(str(args.checkpoint), device=args.device)
                        state_object = reconstruct_game(latest_game)
                        for number, candidate in enumerate(raw_candidates):
                            bridge = build_snapshot_hypothesis(
                                cards_path=args.cards, state=state_object, own_deck=own,
                                opponent_deck=candidate, player_classes=classes,
                                self_controller=args.self_controller, seed=number + 1,
                                open_choice_kind=open_choice.kind if open_choice else None,
                                open_choice_entities=open_choice.choices if open_choice else (),
                            )
                            bridge_attempts.append({"candidate": number, "available": bridge.available,
                                                    "reason": bridge.reason,
                                                    "public_match": bridge.public_match,
                                                    "notes": bridge.hypothesis_notes})
                            if bridge.available:
                                if bridge.game.pending_choice:
                                    item = recommend_replayed_state(
                                        bridge.game, str(args.checkpoint), device=args.device, model=model,
                                    ).as_dict()
                                else:
                                    item = recommend_puct_state(
                                        bridge.game, str(args.checkpoint), device=args.device, model=model,
                                        iterations=args.search_iterations, tree_depth=args.tree_depth,
                                    ).as_dict()
                                if item["available"]:
                                    hypothesis_actions.append(item["action"] | {
                                        "probability": item["probability"], "value": item["value"],
                                        "candidate": number, "search": item.get("search"),
                                        "description": describe_action(bridge.game, item["action"]),
                                    })
                        consensus = choose_consensus(hypothesis_actions,
                                                     min_support=args.belief_min_support)
                        bridge_summary = {"attempted": len(raw_candidates), "viable": len(hypothesis_actions),
                                          "hypotheses": bridge_attempts,
                                          "consensus_support": consensus.support}
                        # Belief uncertainty is information, not a reason to
                        # hide the model's best estimate.  With the default
                        # 0 floor, choose_consensus returns the plurality
                        # action and exposes its support to the player.  A
                        # user may opt into a stricter floor on the command
                        # line for a quieter companion.
                        if consensus.action is not None:
                            recommendation = consensus.action | {
                                "hypothesis_support": consensus.support,
                                "hypotheses": consensus.hypotheses,
                                "consensus_threshold_met": consensus.available,
                                "advisory_only": True,
                            }
                    recommendation_gate = evaluate_gate(
                        event_stream_closed=stream_ready,
                        session_ready=session_ready,
                        beliefs=beliefs,
                        state_matches=False,
                        mode=args.mode,
                        belief_action_consensus=bool(recommendation),
                    )
                print(json.dumps({
                    "mode": shadow.get("mode", "shadow-advisory-only"),
                    "game_count": shadow.get("game_count", 0),
                    "summary": shadow.get("summary", {}),
                    "state_reconstructed": state_summary is not None,
                    "state_summary": state_summary,
                    "replay_summary": replay_summary,
                    "open_choice": ({"kind": open_choice.kind, "options": list(open_choice.choices)}
                                    if open_choice else None),
                    "action_plan_summary": action_plan_summary,
                    "session_gate": session_gate,
                    "belief_summary": belief_summary,
                    "recommendation_gate": recommendation_gate,
                    "bridge_summary": bridge_summary,
                    "recommendation_reason": (
                        "event_stream_not_closed" if replay_summary and not replay_summary["event_stream_closed"] and not choice_ready
                        else ("no_viable_candidate_snapshot"
                              if not recommendation else None)
                    ),
                    "recommendation": recommendation,
                }, ensure_ascii=False), flush=True)
            except subprocess.CalledProcessError as exc:
                print(json.dumps({"mode": "line-shadow", "import_error": exc.stderr[-500:] if exc.stderr else str(exc),
                                  "recommendation": None}, ensure_ascii=False), flush=True)
        if args.once:
            return 0
        time.sleep(max(0.2, args.interval))


if __name__ == "__main__":
    raise SystemExit(main())
