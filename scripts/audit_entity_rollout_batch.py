#!/usr/bin/env python3
"""Balanced, review-only paired-root screen across on-policy deck families."""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from audit_entity_rollout_root import audit
from audit_paired_root_outcomes import HeuristicPolicy
from replay_entity_rollout import verify_report_inputs


def load_decision_metadata(path):
    grouped = defaultdict(list)
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            grouped[row["game_seed"]].append({
                "chosen_probability": math.exp(row["logp"]),
                "legal_actions": len(row["view"]["actions"]),
                "actor": row["actor"],
                "trace_step": row.get("trace_step"),
                "action_key": row.get("action_key"),
            })
    return grouped


def select_roots(records, decisions, *, max_root_actions, seed):
    """One root per game, alternating lower-probability and middle-probability plays."""
    rng = random.Random(seed)
    deck_slots = Counter()
    selected = []
    for game_index, record in enumerate(records):
        deck = record["deck_a"] if record["learner_seat"] == 0 else record["deck_b"]
        learner_steps = [step for step, action in enumerate(record["action_trace"])
                         if action["actor"] == record["learner_seat"]]
        rows = decisions.get(record["seed"], [])
        if len(rows) != len(learner_steps):
            raise ValueError(f"learner decision/trace count mismatch at seed {record['seed']}")
        candidates = []
        for step, row in zip(learner_steps, rows, strict=True):
            if row.get("trace_step") is not None and row["trace_step"] != step:
                raise ValueError(f"learner trace step mismatch at seed {record['seed']}")
            if (row.get("action_key") is not None
                    and list(row["action_key"]) != list(record["action_trace"][step]["action"])):
                raise ValueError(f"learner action key mismatch at seed {record['seed']}")
            probability = row["chosen_probability"]
            if (row["actor"] != record["learner_seat"]
                    or not 2 <= row["legal_actions"] <= max_root_actions
                    or not math.isfinite(probability) or not 0 < probability <= 1):
                continue
            candidates.append((step, row))
        if not candidates:
            continue
        if deck_slots[deck] % 2 == 0:
            # Inspect a sampled unlikely action, not a hard-coded card combo.
            candidates.sort(key=lambda pair: (pair[1]["chosen_probability"],
                                              rng.random()))
            stratum = "low_chosen_probability"
        else:
            candidates.sort(key=lambda pair: (abs(pair[1]["chosen_probability"] - 0.5),
                                              rng.random()))
            stratum = "middle_chosen_probability"
        step, row = candidates[0]
        deck_slots[deck] += 1
        selected.append({"game_index": game_index, "game_seed": record["seed"],
                         "learner_deck": deck, "step": step,
                         "selected_action_key": record["action_trace"][step]["action"],
                         "chosen_probability": row["chosen_probability"],
                         "legal_actions": row["legal_actions"], "stratum": stratum})
    return selected


def paired_sign_pvalue(better, worse):
    """Exact two-sided sign test on discordant paired continuations."""
    n = better + worse
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(min(better, worse) + 1))
    return min(1.0, 2.0 * tail / (2 ** n))


def holm_adjust(comparisons):
    ordered = sorted(comparisons, key=lambda item: item["sign_pvalue"])
    running = 0.0
    count = len(ordered)
    for index, item in enumerate(ordered):
        running = max(running, min(1.0, (count - index) * item["sign_pvalue"]))
        item["holm_pvalue"] = running


def screen_evidence(comparisons):
    """Separate correction candidates from support for the action already played."""
    corrections = [row for row in comparisons
                   if row["holm_pvalue"] < 0.05
                   and row["alternative_better"] > row["selected_better"]]
    supports = [row for row in comparisons
                if row["holm_pvalue"] < 0.05
                and row["selected_better"] > row["alternative_better"]]
    return {"correction_candidates": len(corrections),
            "selected_action_supported_against_alternatives": len(supports),
            "unresolved_comparisons": len(comparisons) - len(corrections) - len(supports)}


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_candidate(job):
    candidate, record, cards, deck_config, replicates, max_actions, max_root_actions, seed = job
    try:
        outcome = audit(record, cards, deck_config,
                        step=candidate["step"], replicates=replicates,
                        max_actions=max_actions,
                        seed=seed + candidate["game_index"] * 1009,
                        max_root_actions=max_root_actions,
                        continuation=HeuristicPolicy())
        return candidate, outcome, None
    except (ValueError, RuntimeError) as exc:
        return candidate, None, f"{type(exc).__name__}: {exc}"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--rollout", type=Path, required=True)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--deck-config", type=Path, required=True)
    parser.add_argument("--replicates", type=int, default=32)
    parser.add_argument("--max-actions", type=int, default=240)
    parser.add_argument("--max-root-actions", type=int, default=8)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--seed", type=int, default=202701071500)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.workers < 1:
        parser.error("workers must be positive")
    report = json.loads(args.report.read_text(encoding="utf-8"))
    verify_report_inputs(report, args.cards, args.deck_config)
    rounds = [entry for entry in report["history"] if entry["round"] == args.round]
    if len(rounds) != 1:
        raise ValueError("requested training round unavailable")
    records = rounds[0]["games"]
    decisions = load_decision_metadata(args.rollout)
    if set(decisions) != {record["seed"] for record in records}:
        raise ValueError("rollout seeds do not match report games")
    selected = select_roots(records, decisions, max_root_actions=args.max_root_actions,
                            seed=args.seed)
    results, comparisons, failures = [], [], []
    jobs = [(candidate, records[candidate["game_index"]], args.cards,
             args.deck_config, args.replicates, args.max_actions,
             args.max_root_actions, args.seed) for candidate in selected]
    if args.workers == 1:
        audited = map(audit_candidate, jobs)
    else:
        executor = ProcessPoolExecutor(max_workers=args.workers)
        audited = executor.map(audit_candidate, jobs)
    try:
        for candidate, outcome, error in audited:
            if error is None:
                record = records[candidate["game_index"]]
                results.append({**candidate, "audit": outcome})
                for alternative in outcome["paired_comparisons_to_selected"]:
                    row = {"game_seed": record["seed"], "learner_deck": candidate["learner_deck"],
                           "step": candidate["step"], **alternative}
                    row["sign_pvalue"] = paired_sign_pvalue(
                        row["alternative_better"], row["selected_better"])
                    comparisons.append(row)
            else:
                failures.append({**candidate, "error": error})
    finally:
        if args.workers != 1:
            executor.shutdown()
    holm_adjust(comparisons)
    invalid = sum(row["invalid"] for root in results for row in root["audit"]["results"])
    truncated = sum(row["truncated"] for root in results for row in root["audit"]["results"])
    result = {"schema": "entity-multideck-root-screen-v1", "report": str(args.report),
              "rollout": str(args.rollout), "round": args.round,
              "report_sha256": sha256_file(args.report),
              "rollout_sha256": sha256_file(args.rollout),
              "continuation": "heuristic-tempo-v1", "replicates": args.replicates,
              "seed": args.seed, "games": len(records), "selected_roots": len(selected),
              "audited_roots": len(results), "failed_roots": failures,
              "invalid_continuations": invalid, "truncated_continuations": truncated,
              "roots_by_learner_deck": dict(Counter(row["learner_deck"] for row in results)),
              "comparisons": comparisons, "roots": results,
              "evidence": screen_evidence(comparisons),
              "teacher_labels_approved": 0,
              "warning": "This is a screen only. A significant heuristic result still needs independent continuation-policy confirmation."}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"games": result["games"], "audited_roots": len(results),
                      "failed_roots": len(failures), "roots_by_learner_deck": result["roots_by_learner_deck"],
                      "comparisons": len(comparisons),
                      **result["evidence"],
                      "invalid_continuations": invalid,
                      "truncated_continuations": truncated},
                     ensure_ascii=False))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
