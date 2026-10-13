#!/usr/bin/env python3
"""Streaming structural checks for observer-exported teacher data.

These checks supplement, not replace, simulator privacy/semantic tests.
No Torch, tensor conversion, source mutation, or training is performed.
"""
from __future__ import annotations

import argparse
from collections import Counter
import gzip
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.observer_view import SCHEMA


def committed_paths(manifest):
    """Do not glob a live directory: temporary gzip shards are not committed data."""
    return [Path(job["data"]) for job in sorted(manifest["jobs"], key=lambda j: j["index"])
            if job["exit_code"] == 0]


def check_decision(row, *, policy_only=False):
    view = row["observer_view"]
    if view.get("schema") != SCHEMA or view.get("to_act") != 0:
        raise ValueError("wrong schema or nonacting observer")
    entities, actions = view["entities"], view["actions"]
    target = row["policy_target"]
    if not actions or len(actions) != len(target) or len(actions) != row["legal_action_count"]:
        raise ValueError("action/target length mismatch")
    for field in ("actions", "teacher_action_values", "teacher_action_visits"):
        if field in row and len(row[field]) != len(actions):
            raise ValueError(f"{field}/observer action length mismatch")
    if "action_keys" in row:
        keys = [tuple(key) for key in row["action_keys"]]
        if len(keys) != len(actions) or len(set(keys)) != len(keys):
            raise ValueError("duplicate/misaligned concrete action keys")
    if not all(isinstance(p, (int, float)) and math.isfinite(p) and p >= 0 for p in target):
        raise ValueError("non-finite/negative policy target")
    if abs(sum(target) - 1.0) > 1e-5:
        raise ValueError("policy target is not normalized")
    for key in ("chosen_action", "executed_action"):
        if not isinstance(row.get(key), int) or not 0 <= row[key] < len(actions):
            raise ValueError(f"invalid {key}")
    if row.get("winner") not in (None, 0, 1) or row.get("actor") not in (0, 1):
        raise ValueError("invalid actor/winner")
    if policy_only:
        if (not row.get("conditional") or row.get("value_target_valid") is not False
                or row.get("value_target") is not None):
            raise ValueError("conditional row must have no terminal value label")
    else:
        expected = 0.0 if row["winner"] is None else 1.0 if row["actor"] == row["winner"] else -1.0
        if row.get("value_target") != expected:
            raise ValueError("terminal reward/player perspective mismatch")
    by_zone = Counter()
    for entity in entities:
        zone, owner = entity["zone"], entity["owner"]
        by_zone[(zone, owner)] += 1
        if owner not in (0, 1):
            raise ValueError("invalid relative owner")
        if zone in ("hand", "secret", "known_starting_deck", "choice") and owner != 0:
            raise ValueError("private opponent zone contains identities")
        if zone == "hand" and entity["numeric"].get("effective_cost") is None:
            raise ValueError("missing effective hand cost in frozen pilot export")
        if not all(v is None or isinstance(v, (int, float)) and math.isfinite(v)
                   for v in entity["numeric"].values()):
            raise ValueError("non-finite entity numeric feature")
    if by_zone[("hero", 0)] != 1 or by_zone[("hero", 1)] != 1:
        raise ValueError("missing/duplicate hero entity")
    if by_zone[("hand", 0)] != view["players"][0]["numeric"]["hand_count"]:
        raise ValueError("own hand count mismatch")
    bound_source_kinds = {"PLAY", "ATTACK", "HERO_ATTACK", "HERO_POWER", "LOCATION", "PREPARE", "TRADE"}
    for action in actions:
        for field in ("source", "target"):
            if not isinstance(action[field], int) or not -1 <= action[field] < len(entities):
                raise ValueError("invalid entity reference")
        if action["kind"] in bound_source_kinds and action["source"] == -1:
            raise ValueError("unbound action source")
    return len(actions)


def audit(paths):
    rows = actions = visited = 0
    seeds = set()
    errors = []
    teachers = set()
    conditional = 0
    conditional_valid = 0
    selection_sources = {}
    for path in paths:
        header = None
        try:
            with gzip.open(path, "rt", encoding="utf-8") as stream:
                for line_no, line in enumerate(stream, 1):
                    row = json.loads(line)
                    if row.get("record_type") == "header":
                        header = row
                        teachers.add((row.get("neural_teacher") or {}).get("sha256"))
                        continue
                    if row.get("conditional"):
                        conditional += 1
                        if row.get("observer_view") is not None:
                            try:
                                check_decision(row, policy_only=True)
                                conditional_valid += 1
                            except (KeyError, ValueError, TypeError) as exc:
                                errors.append({"path": str(path), "line": line_no, "error": str(exc)})
                        elif header and header.get("observer_schema"):
                            errors.append({"path": str(path), "line": line_no,
                                           "error": "conditional row missing observer view"})
                        continue
                    if row.get("record_type") != "decision":
                        continue
                    try:
                        count = check_decision(row)
                    except (KeyError, ValueError, TypeError) as exc:
                        errors.append({"path": str(path), "line": line_no, "error": str(exc)})
                        continue
                    rows += 1
                    seeds.add(row["game_seed"])
                    actions += count
                    visited += sum(v > 0 for v in row.get("teacher_action_visits", []))
                    source = row.get("teacher_selection_source", "unspecified")
                    statistics = selection_sources.setdefault(source, {"decisions": 0, "actions": 0,
                                                                       "visited_actions": 0})
                    statistics["decisions"] += 1
                    statistics["actions"] += count
                    statistics["visited_actions"] += sum(v > 0 for v in row.get("teacher_action_visits", []))
            if header is None:
                errors.append({"path": str(path), "error": "missing dataset header"})
        except (OSError, EOFError, ValueError) as exc:
            errors.append({"path": str(path), "error": f"{type(exc).__name__}: {exc}"})
    return {"status": "passed" if rows and not errors else "failed",
            "files": len(paths), "valid_decisions": rows, "unique_game_seeds": len(seeds),
            "conditional_rows_excluded": conditional, "legal_actions": actions,
            "conditional_valid_rows": conditional_valid,
            "visited_teacher_actions": visited,
            "teacher_action_coverage": visited / actions if actions else None,
            "selection_sources": selection_sources,
            "coverage_note": "Forced single actions and proven lethal use no visits; equivalent actions may be collapsed. Coverage is not optimality.",
            "teacher_checkpoint_sha256": sorted(teachers, key=str), "errors": errors,
            "scope": "structural data contract; not proof of optimal teacher play or complete rules"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", type=Path, nargs="*")
    parser.add_argument("--manifest", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if bool(args.paths) == bool(args.manifest):
        parser.error("supply either paths or --manifest, not both")
    paths = committed_paths(json.loads(args.manifest.read_text(encoding="utf-8"))) if args.manifest else args.paths
    result = audit(paths)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as handle:
            json.dump(result, handle, ensure_ascii=False, indent=2)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
