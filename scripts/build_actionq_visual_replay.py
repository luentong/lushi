#!/usr/bin/env python3
"""Build the compact interactive board replay for action-Q traces."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "reports" / "v8-three-traces-replay.html"


DECK_LABELS = {
    "dragon_warrior": ("龙战", "战士"),
    "aggro_druid": ("快攻德", "德鲁伊"),
}


def deck_label(deck_id: str) -> tuple[str, str]:
    if deck_id in DECK_LABELS:
        return DECK_LABELS[deck_id]
    if deck_id.startswith("龙战_"):
        return "龙战", "战士"
    if deck_id.startswith("快攻德_"):
        return "快攻德", "德鲁伊"
    return deck_id, "未知职业"


def load_match(path: Path) -> dict:
    doc = json.loads(path.read_text(encoding="utf-8"))
    steps = []
    for row in doc["steps"]:
        steps.append({
            "step": row["step"],
            "turn": row["state_after"]["turn"],
            "actor": row["actor"],
            "action": row["description"],
            "before": row["state_before"],
            "after": row["state_after"],
        })
    deck_a = doc.get("deck_a", "dragon_warrior")
    deck_b = doc.get("deck_b", "dragon_warrior")
    label_a, class_a = deck_label(deck_a)
    label_b, class_b = deck_label(deck_b)
    return {
        "label": f"{label_a} vs {label_b} · Seed {doc['seed']}",
        "classes": {"p1": class_a, "p2": class_b},
        "seed": doc["seed"],
        "winner": doc.get("winner"),
        "invalid_actions": doc.get("invalid_actions", 0),
        "steps": steps,
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--title",
        default="action-Q v8 三局龙战镜像对局复盘",
        help="Visible replay heading and browser document title.",
    )
    args = parser.parse_args()
    matches = [load_match(p) for p in args.paths]
    html = TEMPLATE.read_text(encoding="utf-8")
    payload = json.dumps(matches, ensure_ascii=False, separators=(",", ":"))
    html, count = re.subn(
        r"const matches = .*?;\n  const root =",
        "const matches = " + payload + ";\n  const root =",
        html,
        count=1,
        flags=re.S,
    )
    if count != 1:
        raise RuntimeError("replay template does not contain the expected matches block")
    html = html.replace("多卡组对局复盘", args.title, 1)
    html = re.sub(r"<title>.*?</title>", f"<title>{args.title}</title>", html, count=1)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
