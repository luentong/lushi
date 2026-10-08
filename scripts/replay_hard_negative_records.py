"""Replay high-budget traces and emit encoder-compatible corrective records.

The hard-negative scanner stores compact human-readable states.  This script
replays each trace from its seed and deck pair so the canonical engine encoder
produces the real state/action tensors required by training.
"""
from __future__ import annotations

import argparse
import gzip
import json
import math
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from benchmark_mcts import matchup_deck_counts, configure_search_beliefs
from hsa import DragonMirrorGame
from hsa.encoding import (
    configure_card_vocab, encode_action, encode_state, feature_schema,
)
from hsa.lineage import ruleset_manifest


def _softmax(values: list[float], temperature: float = 0.5) -> list[float]:
    if not values:
        return []
    scale = max(temperature, 1e-6)
    top = max(values)
    exps = [math.exp((x - top) / scale) for x in values]
    total = sum(exps)
    return [x / total for x in exps]


def _action_match(descriptions: list[str], requested: str) -> int:
    """Match exact first, then tolerate entity-id drift after random effects."""
    try:
        return descriptions.index(requested)
    except ValueError:
        normalize = lambda text: re.sub(r"#\d+", "#?", text)
        wanted = normalize(requested)
        matches = [i for i, text in enumerate(descriptions)
                   if normalize(text) == wanted]
        if len(matches) == 1:
            return matches[0]
        raise


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--candidates", type=Path, required=True)
    p.add_argument("--trace-root", type=Path, required=True)
    p.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    p.add_argument("--deck-config", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--ruleset-label", default="hard_negative_high_budget_v1")
    p.add_argument("--schema-version", type=int, default=4,
                   help="Use the checkpoint's frozen encoder schema (v4 for the current v5 model).")
    args = p.parse_args()

    configure_card_vocab("expanded-executable")
    payload = json.loads(args.candidates.read_text(encoding="utf-8"))
    grouped: dict[str, list[dict]] = defaultdict(list)
    for candidate in payload.get("candidates", []):
        grouped[Path(str(candidate["source"])).name].append(candidate)

    records: list[dict] = []
    errors: list[dict] = []
    for filename, wanted in sorted(grouped.items()):
        trace_path = args.trace_root / filename
        try:
            trace = json.loads(trace_path.read_text(encoding="utf-8"))
            (counts_a, class_a), (counts_b, class_b) = matchup_deck_counts(
                args.deck_config, trace["deck_a"], trace["deck_b"]
            )
            game = DragonMirrorGame(
                args.cards, int(trace["seed"]),
                deck_counts=(counts_a, counts_b),
                player_classes=(class_a, class_b),
            )
            configure_search_beliefs(game, args.deck_config)
            by_step = {int(c["step"]): c for c in wanted}
            for step in trace.get("steps", []):
                step_no = int(step["step"])
                legal = game.legal_actions()
                decision_state = encode_state(
                    game, game.current, schema_version=args.schema_version
                )
                decision_actions = tuple(
                    encode_action(game, action, schema_version=args.schema_version)
                    for action in legal
                )
                descriptions = [game.describe_action(action) for action in legal]
                chosen_description = str(step["description"])
                try:
                    replay_index = _action_match(descriptions, chosen_description)
                except ValueError as exc:
                    raise RuntimeError(
                        f"step {step_no}: action not reproducible: {chosen_description}"
                    ) from exc
                candidate = by_step.get(step_no)
                if candidate is not None:
                    alternatives = step.get("ranked_alternatives", [])
                    values = [0.0] * len(legal)
                    visits = [0] * len(legal)
                    for alt in alternatives:
                        action_text = str(alt.get("action", ""))
                        try:
                            index = _action_match(descriptions, action_text)
                        except ValueError:
                            continue
                        if alt.get("mean_value") is not None:
                            values[index] = float(alt["mean_value"])
                        visits[index] = int(alt.get("visits", 0))
                    total_visits = sum(visits)
                    target = (
                        [v / total_visits for v in visits]
                        if total_visits else _softmax(values)
                    )
                    if not any(target):
                        target = [0.0] * len(legal)
                        target[replay_index] = 1.0
                    actor = int(step["actor"]) - 1
                    winner = trace.get("winner")
                    value = (
                        0.0 if winner is None else
                        1.0 if int(winner) == actor else -1.0
                    )
                    if winner is None:
                        value = max(-1.0, min(1.0, float(candidate.get("selected_mean_value", 0.0))))
                    records.append({
                        "record_type": "decision",
                        "game_seed": int(trace["seed"]),
                        "ply": step_no - 1,
                        "actor": actor,
                        "state": list(decision_state),
                        "actions": [list(action) for action in decision_actions],
                        "chosen_action": replay_index,
                        "executed_action": replay_index,
                        "policy_target": target,
                        "teacher_action_values": values,
                        "teacher_action_visits": visits,
                        "teacher_simulations": int(step.get("search", {}).get("iterations", 0)),
                        "value_target": value,
                        "winner": winner,
                        "hard_negative_reasons": candidate.get("reasons", []),
                        "regret_gap": float(candidate.get("regret_gap", 0.0)),
                        "source_trace": filename,
                    })
                game.step(legal[replay_index])
        except Exception as exc:  # preserve all successful records from other traces
            errors.append({"trace": filename, "error": repr(exc)})

    args.output.parent.mkdir(parents=True, exist_ok=True)
    header = {
        "record_type": "header", "dataset_schema_version": 3,
        "ruleset": args.ruleset_label,
        "ruleset_fingerprint": ruleset_manifest(ROOT)["fingerprint_sha256"],
        "teacher": "high_budget_trace_replay", "behavior": "trace_replay",
        "feature_schema": feature_schema(args.schema_version), "records": len(records),
        "source_candidates": len(payload.get("candidates", [])),
        "replay_errors": errors,
    }
    with gzip.open(args.output, "wt", encoding="utf-8") as handle:
        handle.write(json.dumps(header, ensure_ascii=False, separators=(",", ":")) + "\n")
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n")
    print(json.dumps({"records": len(records), "errors": len(errors), "output": str(args.output)}, ensure_ascii=False))
    return 0 if records and not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
