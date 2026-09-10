#!/usr/bin/env python3
"""Convert compatible policy datasets between feature-schema revisions."""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.encoding import (  # noqa: E402
    ACTION_KINDS,
    CARD_VOCAB,
    MAX_HAND_SLOTS,
    ZONE_NAMES,
    feature_schema,
)


TARGET_ZONE_OFFSET = (
    len(ACTION_KINDS)
    + len(ZONE_NAMES)
    + 2
    + len(CARD_VOCAB)
    + MAX_HAND_SLOTS
)


def v4_action_to_v3(action: list[float]) -> list[float]:
    source_size = int(feature_schema(4)["action_size"])
    if len(action) != source_size:
        raise ValueError(
            f"expected schema-v4 action size {source_size}, got {len(action)}"
        )
    return (
        action[:TARGET_ZONE_OFFSET]
        + action[TARGET_ZONE_OFFSET + len(ZONE_NAMES):]
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--target-schema", type=int, choices=(3,), default=3)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    records = 0
    with gzip.open(args.input, "rt", encoding="utf-8") as source:
        header = json.loads(next(source))
        source_schema = header["feature_schema"]
        if int(source_schema["schema_version"]) != 4:
            raise ValueError("this converter currently requires schema v4 input")
        converted_header = dict(header)
        converted_header["feature_schema"] = feature_schema(args.target_schema)
        converted_header["converted_from_feature_schema"] = source_schema
        converted_header["feature_conversion"] = "drop_action_target_zone_v4_to_v3"
        with gzip.open(args.output, "wt", encoding="utf-8") as target:
            target.write(json.dumps(converted_header, separators=(",", ":")) + "\n")
            for line in source:
                record = json.loads(line)
                if record.get("record_type") == "decision":
                    record["actions"] = [
                        v4_action_to_v3(action) for action in record["actions"]
                    ]
                    records += 1
                target.write(json.dumps(record, separators=(",", ":")) + "\n")
    print(json.dumps({
        "input": str(args.input),
        "output": str(args.output),
        "records": records,
        "source_schema": 4,
        "target_schema": args.target_schema,
        "source_action_size": feature_schema(4)["action_size"],
        "target_action_size": feature_schema(args.target_schema)["action_size"],
    }, indent=2))


if __name__ == "__main__":
    main()
