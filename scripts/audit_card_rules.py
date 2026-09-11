#!/usr/bin/env python3
"""Audit declarative rules and reusable upstream card implementations."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import EXECUTABLE_CARD_IDS
from hsa.rules import build_rule_registry


UPSTREAMS = (
    {
        "name": "RosettaStone",
        "root": ROOT / "vendor" / "RosettaStone",
        "scan": "Sources/Rosetta/PlayMode/CardSets",
        "extensions": {".cpp", ".hpp"},
        "commit": "e10749b5f0c08d3a6135bce317cb11d1738846ad",
        "license": "AGPL-3.0",
    },
    {
        "name": "fireplace",
        "root": ROOT / "vendor" / "fireplace",
        "scan": "fireplace/cards",
        "extensions": {".py"},
        "commit": "47a2572a000db66645bb74a425a090d51f1004fa",
        "license": "AGPL-3.0",
    },
)


def test_function_names() -> set[str]:
    names: set[str] = set()
    for path in sorted((ROOT / "tests").glob("test_*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        names.update(
            node.name for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        )
    return names


def aliases(card_id: str) -> tuple[str, ...]:
    result = [card_id]
    if card_id.startswith("CORE_"):
        result.append(card_id.removeprefix("CORE_"))
    if card_id.startswith("VAN_"):
        result.append(card_id.removeprefix("VAN_"))
    return tuple(dict.fromkeys(result))


def scan_upstreams(card_ids: set[str]) -> dict[str, list[dict]]:
    alias_to_cards: dict[str, set[str]] = {}
    for card_id in card_ids:
        for alias in aliases(card_id):
            alias_to_cards.setdefault(alias, set()).add(card_id)
    pattern = re.compile(
        r"(?<![A-Z0-9_])(" + "|".join(
            sorted(map(re.escape, alias_to_cards), key=len, reverse=True)
        ) + r")(?![A-Z0-9_])"
    )
    found: dict[str, list[dict]] = {card_id: [] for card_id in card_ids}
    for upstream in UPSTREAMS:
        scan_root = upstream["root"] / upstream["scan"]
        if not scan_root.exists():
            continue
        for path in scan_root.rglob("*"):
            if not path.is_file() or path.suffix not in upstream["extensions"]:
                continue
            try:
                lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            except OSError:
                continue
            for line_no, line in enumerate(lines, 1):
                for match in pattern.finditer(line):
                    matched_id = match.group(1)
                    for card_id in alias_to_cards[matched_id]:
                        hit = {
                            "repository": upstream["name"],
                            "commit": upstream["commit"],
                            "license": upstream["license"],
                            "matched_id": matched_id,
                            "match_kind": (
                                "exact" if matched_id == card_id
                                else "historical_alias"
                            ),
                            "path": path.relative_to(upstream["root"]).as_posix(),
                            "line": line_no,
                        }
                        if hit not in found[card_id]:
                            found[card_id].append(hit)
    return found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json", type=Path,
        default=ROOT / "reports" / "card_rule_manifest.json",
    )
    parser.add_argument(
        "--csv", type=Path,
        default=ROOT / "reports" / "card_rule_manifest.csv",
    )
    args = parser.parse_args()

    declarative = {
        row["card_id"]: row for row in build_rule_registry().manifest()
    }
    known_tests = test_function_names()
    missing_tests = sorted({
        test_name
        for rule in declarative.values()
        for test_name in rule["source"]["verification"]
        if test_name not in known_tests
    })
    if missing_tests:
        raise RuntimeError(
            "declarative rules reference missing tests: "
            + ", ".join(missing_tests)
        )
    upstream = scan_upstreams(set(EXECUTABLE_CARD_IDS))
    rows = []
    for card_id in sorted(EXECUTABLE_CARD_IDS):
        rule = declarative.get(card_id)
        implementation = (
            "declarative" if rule and rule["hooks"]
            else "legacy_special_case" if rule
            else "legacy_compatibility"
        )
        rows.append({
            "card_id": card_id,
            "implementation": implementation,
            "hooks": [] if rule is None else rule["hooks"],
            "effects": {} if rule is None else rule["effects"],
            "rule_source": (
                {
                    "kind": "local_legacy",
                    "reference": "src/hsa/dragon_mirror.py",
                    "verification": ["unittest regression suite"],
                }
                if rule is None else rule["source"]
            ),
            "metadata_source": "HearthstoneJSON build 251332",
            "upstream_matches": upstream[card_id],
            "verification_status": (
                "focused_test_and_regression" if rule
                else "regression_suite_only"
            ),
        })

    payload = {
        "schema_version": 1,
        "summary": {
            "supported_cards": len(rows),
            "declarative_rules": sum(
                row["implementation"] == "declarative" for row in rows
            ),
            "legacy_special_case_rules": sum(
                row["implementation"] == "legacy_special_case" for row in rows
            ),
            "legacy_compatibility_rules": sum(
                row["implementation"] == "legacy_compatibility" for row in rows
            ),
            "cards_with_upstream_match": sum(
                bool(row["upstream_matches"]) for row in rows
            ),
        },
        "cards": rows,
    }
    args.json.parent.mkdir(parents=True, exist_ok=True)
    args.json.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    with args.csv.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "card_id", "implementation", "hooks", "source_kind",
            "upstream_repositories", "upstream_match_count",
            "verification_status",
        ))
        writer.writeheader()
        for row in rows:
            writer.writerow({
                "card_id": row["card_id"],
                "implementation": row["implementation"],
                "hooks": ",".join(row["hooks"]),
                "source_kind": row["rule_source"]["kind"],
                "upstream_repositories": ",".join(sorted({
                    hit["repository"] for hit in row["upstream_matches"]
                })),
                "upstream_match_count": len(row["upstream_matches"]),
                "verification_status": row["verification_status"],
            })
    print(json.dumps(payload["summary"], ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
