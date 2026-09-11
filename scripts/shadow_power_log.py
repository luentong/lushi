#!/usr/bin/env python3
"""Produce a fail-closed advisory report from a sanitized Power.log export."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.shadow_advisor import analyze_payload, jsonl_backlog


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path, help="sanitized Power.log JSON from import_power_log.py")
    parser.add_argument("--coverage", type=Path, default=ROOT / "reports" / "standard_rule_coverage.json")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--backlog", type=Path, help="optional JSONL engineering-task export")
    args = parser.parse_args()
    payload = json.loads(args.input.read_text(encoding="utf-8"))
    coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
    report = analyze_payload(payload, coverage)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.backlog:
        args.backlog.parent.mkdir(parents=True, exist_ok=True)
        args.backlog.write_text(jsonl_backlog(report["backlog"]), encoding="utf-8")
    print(json.dumps({"output": str(args.output), "summary": report["summary"]}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
