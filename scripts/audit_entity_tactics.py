#!/usr/bin/env python3
"""Diagnostic fixed tactical roots for an entity policy (not training data)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from audit_search_tactics import CASES, make_case
from hsa.dragon_mirror import DRAGON_DECK_COUNTS
from hsa.observer_view import observer_view
from train_entity_selfplay import select_device


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", type=Path, action="append", required=True)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    import torch
    from hsa.entity_model import EntityPolicyValueNet, collate_views

    torch.set_num_threads(2)
    device = select_device(args.device)
    cases = []
    for name in CASES:
        game, expected, label = make_case(name)
        actions = game.legal_actions()
        if not any(expected(action) for action in actions):
            raise ValueError(f"{name}: expected action not legal")
        cases.append((name, game, actions, expected, label))
    report = {"diagnostic_only": True, "cases": list(CASES), "models": []}
    for path in args.checkpoint:
        model = EntityPolicyValueNet.from_payload(torch.load(path, map_location="cpu", weights_only=False))
        model.to(device).eval()
        records = []
        with torch.no_grad():
            for name, game, actions, expected, label in cases:
                view = observer_view(game, actions=actions, known_deck=DRAGON_DECK_COUNTS)
                logits, _ = model(collate_views([view], model.card_ids, device))
                selected_index = int(logits[0].argmax())
                probabilities = logits[0].softmax(-1)
                expected_indices = [i for i, action in enumerate(actions) if expected(action)]
                records.append({"case": name, "label": label,
                                "pass": bool(expected(actions[selected_index])),
                                "selected": game.describe_action(actions[selected_index]),
                                "expected_probability": float(probabilities[expected_indices].sum()),
                                "legal_actions": len(actions)})
        report["models"].append({"checkpoint": str(path),
                                 "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                                 "passed": sum(row["pass"] for row in records),
                                 "total": len(records), "records": records})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"models": [(m["checkpoint"], m["passed"], m["total"])
                                 for m in report["models"]], "output": str(args.output)}))


if __name__ == "__main__":
    main()
