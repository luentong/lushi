#!/usr/bin/env python3
"""Render an auditable training trace as a compact human-readable match log."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path


def _card(card: dict) -> str:
    bits = [card["name"]]
    if card.get("attack") is not None and card.get("max_health") is not None:
        bits.append(f"{card['attack']}/{card['health']}")
    if card.get("cost") is not None:
        bits.append(f"{card['cost']}费")
    if card.get("attack_delta", 0):
        bits.append(f"攻击修正{card['attack_delta']:+d}")
    if card.get("health_delta", 0):
        bits.append(f"生命修正{card['health_delta']:+d}")
    if card.get("damage", 0):
        bits.append(f"受伤{card['damage']}")
    if card.get("dormant_turns", 0):
        bits.append(f"休眠{card['dormant_turns']}")
    if card.get("prepared"):
        bits.append("已预备")
    if card.get("keywords"):
        bits.append("/".join(card["keywords"]))
    return "（".join((bits[0], "，".join(bits[1:]) + "）")) if len(bits) > 1 else bits[0]


def _cards(cards: list[dict]) -> str:
    return "、".join(_card(card) for card in cards) if cards else "无"


def _player(player: dict, *, show_hand: bool = True) -> str:
    hero = (
        f"P{player['player']} HP {player['health']}/{player['max_health']}"
        f"，护甲 {player['armor']}，法力 {player['mana']}/{player['max_mana']}"
    )
    weapon = player.get("weapon")
    weapon_text = (
        f"{weapon['name']} {weapon['attack']}/{weapon['durability']}"
        if weapon else "无"
    )
    locations = "、".join(
        f"{item['id']}（耐久{item['durability']}，冷却{item['cooldown']}）"
        for item in player.get("locations", [])
    ) or "无"
    text = [hero]
    if show_hand:
        text.append(f"手牌[{len(player['hand'])}]：{_cards(player['hand'])}")
    text.extend((
        f"场面：{_cards(player['board'])}",
        f"武器：{weapon_text}",
        f"地标：{locations}",
        f"牌库：{player['deck_count']}",
    ))
    pending_slime = player.get("pending_slime_resummon", [])
    if pending_slime:
        text.append(f"Slime 'em! 待复活：{_cards(pending_slime)}")
    pending_trials = player.get("pending_sham_trials", [])
    if pending_trials:
        text.append("待结算 Trial：" + "、".join(
            f"{trial['id']}（己方第{trial['due_owner_turn']}回合；"
            f"{','.join(trial['effects'])}）"
            for trial in pending_trials
        ))
    return "；".join(text)


def _action(text: str) -> str:
    replacements = (
        (" END_TURN", " 结束回合"),
        (" PLAY ", " 打出 "),
        (" ATTACK ", " 攻击 "),
        (" HERO_ATTACK", " 英雄攻击"),
        (" HERO_POWER ", " 使用英雄技能："),
        (" PREPARE ", " 预备 "),
        (" CHOOSE_ONE ", " 选择："),
        (" DISCOVER_PICK ", " 发现选择："),
        (" DECK_CARD_DISCOVER_PICK ", " 从牌库发现选择："),
        (" -> P1 hero", " → P1 英雄"),
        (" -> P2 hero", " → P2 英雄"),
        (" -> -", ""),
    )
    for before, after in replacements:
        text = text.replace(before, after)
    return text


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.input.read_text(encoding="utf-8").splitlines()]
    header = rows[0]
    decisions = [row for row in rows if row.get("record_type") == "decision"]
    final = next(row for row in reversed(rows) if row.get("kind") == "final")
    by_turn: dict[int, list[dict]] = defaultdict(list)
    for row in decisions:
        by_turn[row["turn"]].append(row)

    lines = [
        f"# {header['p0']}（P1）vs {header['p1']}（P2）",
        "",
        f"种子：`{header['seed']}`。这是模拟器的完整可见状态摘要；每回合仅展示实际执行的动作。",
        "",
    ]
    for turn, records in by_turn.items():
        first, last = records[0], records[-1]
        actor = first["actor"] + 1
        before_players = first["engine_state_before"]["players"]
        after_players = last["engine_state_after"]["players"]
        lines.extend((
            f"## 回合 {turn}：P{actor}",
            "",
            f"开始 — {_player(before_players[0])}",
            "",
            f"开始 — {_player(before_players[1])}",
            "",
            "实际动作：",
            "",
        ))
        for row in records:
            lines.append(f"- {_action(row['action'])}")
        lines.extend((
            "",
            f"结束 — {_player(after_players[0])}",
            "",
            f"结束 — {_player(after_players[1])}",
            "",
        ))
    winner = "平局" if final["winner"] is None else f"P{final['winner'] + 1} 获胜"
    lines.extend((f"## 结果", "", f"{winner}；结束于第 {final['turn']} 回合；非法动作：{final['invalid_actions']}。", ""))
    args.output.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
