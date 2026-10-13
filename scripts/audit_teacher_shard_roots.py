#!/usr/bin/env python3
"""Replay teacher shards exactly, then audit sampled root actions across decks.

Only rows whose encoded state, concrete legal actions, and observer view match
the current ruleset are eligible. A drift rejects the entire game, rather than
continuing from a fabricated state.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from hsa import DragonMirrorGame
from hsa.encoding import configure_card_vocab, encode_state, feature_schema
from hsa.lineage import ruleset_manifest
from hsa.observer_view import observer_view
from audit_paired_root_outcomes import (
    EntityGreedyPolicy, paired_comparisons, paired_outcomes,
)
from benchmark_mcts import configure_search_beliefs, matchup_deck_counts


def read_records(path: Path):
    with path.open("rb") as source:
        compressed = source.read(2) == b"\x1f\x8b"
    opener = gzip.open if compressed else open
    with opener(path, "rt", encoding="utf-8") as source:
        for line in source:
            if line.strip():
                yield json.loads(line)


def replay_shard(path: Path, *, cards: Path, deck_config: Path,
                 deck_a: str, deck_b: str, seed: int,
                 selection_seed: int, min_ply: int, max_root_actions: int,
                 allow_fingerprint_drift: bool = False,
                 target_ply: int | None = None):
    (counts_a, class_a), (counts_b, class_b) = matchup_deck_counts(
        deck_config, deck_a, deck_b)
    game = DragonMirrorGame(cards, seed,
                            deck_counts=(counts_a, counts_b),
                            player_classes=(class_a, class_b))
    configure_search_beliefs(game, deck_config)
    choices = {"END_TURN": None, "OTHER": None}
    if target_ply is not None:
        choices["TARGET"] = None
    seen = {"END_TURN": 0, "OTHER": 0}
    chooser = random.Random(selection_seed)
    decisions = 0
    conditional = 0
    outcomes = []
    records = iter(read_records(path))
    header = next(records, None)
    if header is None or header.get("record_type") != "header":
        raise ValueError("shard has no dataset header")
    current_ruleset = ruleset_manifest(ROOT)["fingerprint_sha256"]
    fingerprint_drift = header.get("ruleset_fingerprint") not in (None, current_ruleset)
    if fingerprint_drift and not allow_fingerprint_drift:
        raise ValueError("ruleset fingerprint differs from dataset header")
    frozen = header.get("feature_schema", {})
    card_ids = frozen.get("card_vocab_ids")
    if not card_ids:
        raise ValueError("shard lacks a frozen card vocabulary")
    configure_card_vocab("frozen", vocabulary=card_ids)
    if (feature_schema().get("card_vocab_sha256")
            != frozen.get("card_vocab_sha256")):
        raise ValueError("shard card vocabulary hash mismatch")
    for row in records:
        if row.get("record_type") != "decision":
            continue
        if row.get("conditional"):
            conditional += 1
            continue
        if row.get("game_seed") != seed or row.get("ply") != decisions:
            raise ValueError(f"seed/ply drift at decision {decisions}")
        if row.get("actor") != game.current:
            raise ValueError(f"actor drift at decision {decisions}")
        if list(encode_state(game, game.current)) != row.get("state"):
            raise ValueError(f"encoded state drift at decision {decisions}")
        actions = game.legal_actions()
        action_keys = [list(action.key()) for action in actions]
        if action_keys != row.get("action_keys"):
            raise ValueError(f"legal action drift at decision {decisions}")
        if len(actions) != row.get("legal_action_count"):
            raise ValueError(f"legal action count drift at decision {decisions}")
        view = observer_view(game, actions=actions,
                             known_deck=game.deck_counts[game.current])
        if view != row.get("observer_view"):
            raise ValueError(f"observer view drift at decision {decisions}")
        selected = row["chosen_action"]
        executed = row["executed_action"]
        if not (0 <= selected < len(actions) and 0 <= executed < len(actions)):
            raise ValueError(f"action index drift at decision {decisions}")
        outcomes.append((row.get("winner"), row.get("value_target"), game.current))
        if decisions >= min_ply and 2 <= len(actions) <= max_root_actions:
            category = ("END_TURN" if actions[selected].kind == "END_TURN"
                        else "OTHER")
            seen[category] += 1
            if chooser.randrange(seen[category]) == 0:
                choices[category] = {
                    "game": game.clone(include_history=False, record_events=False),
                    "actions": actions,
                    "row": row,
                }
        if decisions == target_ply:
            if not 2 <= len(actions) <= max_root_actions:
                raise ValueError("target ply has no eligible root-action set")
            choices["TARGET"] = {
                "game": game.clone(include_history=False, record_events=False),
                "actions": actions, "row": row,
            }
        game.step(actions[executed])
        decisions += 1
    if decisions == 0:
        raise ValueError("shard has no ordinary decisions")
    if target_ply is not None and choices["TARGET"] is None:
        raise ValueError("target ply absent from verified decisions")
    if not game.finished:
        raise ValueError("replayed shard did not reach a terminal state")
    if game.invalid_actions:
        raise ValueError("replayed shard contains invalid actions")
    for winner, value, actor in outcomes:
        expected = (0.0 if game.winner is None else
                    1.0 if game.winner == actor else -1.0)
        if winner != game.winner or value != expected:
            raise ValueError("recorded terminal outcome/value drift")
    return {"decisions": decisions, "conditional": conditional,
            "candidate_counts": seen, "choices": choices,
            "winner": game.winner, "invalid_actions": game.invalid_actions,
            "fingerprint_drift": fingerprint_drift,
            "recorded_fingerprint": header.get("ruleset_fingerprint"),
            "current_fingerprint": current_ruleset}


def verified_jobs(manifest: dict, manifest_path: Path, max_games: int | None):
    jobs = sorted(manifest["jobs"], key=lambda job: job["index"])
    if max_games is not None:
        jobs = jobs[:max_games]
    for job in jobs:
        if job.get("exit_code") != 0:
            raise ValueError(f"game {job['index']} did not complete successfully")
        path = Path(job["data"])
        if not path.is_absolute():
            path = manifest_path.parent / path
        if not path.is_file():
            raise FileNotFoundError(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != job.get("data_sha256"):
            raise ValueError(f"shard hash mismatch for game {job['index']}")
        yield job, path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--max-games", type=int)
    parser.add_argument("--max-roots", type=int, default=8)
    parser.add_argument("--min-ply", type=int, default=3)
    parser.add_argument("--max-root-actions", type=int, default=12)
    parser.add_argument("--replicates", type=int, default=8)
    parser.add_argument("--max-actions", type=int, default=240)
    parser.add_argument("--continuation", choices=("heuristic", "entity-greedy"),
                        default="heuristic")
    parser.add_argument("--checkpoint", type=Path)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--seed", type=int, default=20260929)
    parser.add_argument("--focus-game-index", type=int)
    parser.add_argument("--focus-ply", type=int)
    parser.add_argument("--allow-fingerprint-drift-if-exact-replay", action="store_true",
                        help="Audit only: permit a code-hash mismatch, but still reject any "
                             "state/action/observer/terminal replay drift")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.max_roots < 1 or args.replicates < 1:
        parser.error("--max-roots and --replicates must be positive")
    if (args.focus_game_index is None) != (args.focus_ply is None):
        parser.error("--focus-game-index and --focus-ply must be specified together")
    if args.continuation == "entity-greedy" and args.checkpoint is None:
        parser.error("--checkpoint is required for entity-greedy continuation")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    config_digest = hashlib.sha256(args.deck_config.read_bytes()).hexdigest()
    if config_digest != manifest.get("deck_config_sha256"):
        raise ValueError("deck configuration hash does not match manifest")
    groups = defaultdict(list)
    focused = []
    replay_status = []
    for job, path in verified_jobs(manifest, args.manifest, args.max_games):
        if args.focus_game_index is not None and job["index"] != args.focus_game_index:
            continue
        try:
            replay = replay_shard(
                path, cards=args.cards, deck_config=args.deck_config,
                deck_a=job["deck_a"], deck_b=job["deck_b"], seed=job["seed"],
                selection_seed=args.seed + job["index"], min_ply=args.min_ply,
                max_root_actions=args.max_root_actions,
                allow_fingerprint_drift=args.allow_fingerprint_drift_if_exact_replay,
                target_ply=args.focus_ply)
        except (ValueError, KeyError) as error:
            replay_status.append({"game_index": job["index"], "status": "rejected",
                                  "reason": str(error)})
            continue
        replay_status.append({"game_index": job["index"], "status": "verified",
                              "decisions": replay["decisions"],
                              "conditional": replay["conditional"],
                              "fingerprint_drift": replay["fingerprint_drift"],
                              "recorded_fingerprint": replay["recorded_fingerprint"],
                              "current_fingerprint": replay["current_fingerprint"],
                              "candidate_counts": replay["candidate_counts"]})
        if args.focus_game_index is not None:
            focused.append((job, replay["choices"]["TARGET"]))
            continue
        for category, choice in replay["choices"].items():
            if choice is not None:
                groups[(job["deck_a"], job["deck_b"], category)].append(
                    (job, choice))
    # Round-robin avoids letting a long game or one matchup dominate the audit.
    ordered = []
    buckets = [groups[key] for key in sorted(groups)]
    sampler = random.Random(args.seed)
    for bucket in buckets:
        sampler.shuffle(bucket)
    used_games = set()
    while buckets and len(ordered) < args.max_roots:
        next_buckets = []
        for bucket in buckets:
            if bucket and len(ordered) < args.max_roots:
                index = next((i for i, (job, _) in enumerate(bucket)
                              if job["index"] not in used_games), 0)
                selected = bucket.pop(index)
                ordered.append(selected)
                used_games.add(selected[0]["index"])
            if bucket:
                next_buckets.append(bucket)
        buckets = next_buckets
    if args.focus_game_index is not None:
        ordered = focused
        if not ordered:
            raise ValueError("focused root was not verified")
    continuation = (EntityGreedyPolicy(args.checkpoint, args.device)
                    if args.continuation == "entity-greedy" else None)
    audits = []
    for job, choice in ordered:
        root = choice["game"]
        selected = choice["actions"][choice["row"]["chosen_action"]]
        results = paired_outcomes(
            root, choice["actions"], replicates=args.replicates,
            max_actions=args.max_actions,
            seed=args.seed + job["index"] * 1000 + choice["row"]["ply"],
            continuation_policy=continuation)
        selected_key = list(selected.key())
        audits.append({
            "game_index": job["index"], "deck_a": job["deck_a"],
            "deck_b": job["deck_b"], "game_seed": job["seed"],
            "ply": choice["row"]["ply"], "actor": root.current,
            "teacher_selected": root.describe_action(selected),
            "teacher_selected_key": selected_key,
            "teacher_simulations": choice["row"].get("teacher_simulations"),
            "teacher_action_visits": choice["row"].get("teacher_action_visits"),
            "teacher_action_values": choice["row"].get("teacher_action_values"),
            "results": results,
            "paired_comparisons": paired_comparisons(results, selected_key),
        })
        print(f"audited game {job['index']} ply {choice['row']['ply']}", flush=True)
    output = {
        "schema": "teacher-shard-paired-root-audit-v1",
        "manifest": str(args.manifest), "deck_config": str(args.deck_config),
        "seed": args.seed, "replicates": args.replicates,
        "focus_game_index": args.focus_game_index, "focus_ply": args.focus_ply,
        "continuation_policy": ("entity-greedy" if continuation is not None
                                else "heuristic-tempo-v1"),
        "checkpoint": str(args.checkpoint) if args.checkpoint else None,
        "fingerprint_drift_override": args.allow_fingerprint_drift_if_exact_replay,
        "limitations": ["Continuation-policy dependent; not optimal-action labels.",
                        "Shards with replay drift are rejected, not estimated.",
                        "Audit roots are sampled; this is not a dataset-wide error rate.",
                        "A fingerprint override proves equality only on replayed decisions, not on every possible game state."],
        "replay_status": replay_status, "audits": audits,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"verified_games": sum(r["status"] == "verified" for r in replay_status),
                      "rejected_games": sum(r["status"] == "rejected" for r in replay_status),
                      "audited_roots": len(audits)}, ensure_ascii=False), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
