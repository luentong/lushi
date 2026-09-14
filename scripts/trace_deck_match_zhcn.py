#!/usr/bin/env python3
"""Replay the fixed Dragon Warrior vs Dirty Priest match as Chinese steps."""
from __future__ import annotations

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from benchmark_mcts import matchup_deck_counts
from hsa.dragon_mirror import DragonMirrorGame
from hsa.policy import HeuristicPolicy


LABELS = {
    "PLAY": "打出",
    "ATTACK": "随从攻击",
    "HERO_ATTACK": "英雄攻击",
    "HERO_POWER": "使用英雄技能",
    "END_TURN": "结束回合",
    "LOCATION": "使用地标",
    "PREPARE": "准备",
    "TRADE": "交易",
    "DISCOVER_PICK": "选择发现牌",
    "RULE_CHOICE_PICK": "选择规则选项",
    "MULLIGAN_TOGGLE": "调度选择",
    "MULLIGAN_CONFIRM": "确认调度",
}


def main() -> int:
    (deck_a, class_a), (deck_b, class_b) = matchup_deck_counts(
        ROOT / "config" / "decks.json", "dragon_warrior", "dirty_priest"
    )
    game = DragonMirrorGame(
        ROOT / "cards.251332.enUS.json", 202609140001,
        deck_counts=(deck_a, deck_b), player_classes=(class_a, class_b),
    )
    policies = [HeuristicPolicy(), HeuristicPolicy()]
    zh_names = {
        row["id"]: row.get("name", row["id"])
        for row in json.loads((ROOT / "cards.zhCN.json").read_text(encoding="utf-8"))
    }

    def find(entity_id):
        if entity_id is None:
            return None
        for player in game.players:
            for zone in (player.hand, player.board, player.deck, player.locations):
                for card in zone:
                    if card.entity_id == entity_id:
                        return card
            if player.weapon and getattr(player.weapon, "entity_id", None) == entity_id:
                return player.weapon
        return None

    def name(entity_id):
        card = find(entity_id)
        if card is None:
            return str(entity_id) if entity_id is not None else ""
        definition = getattr(card, "definition", None)
        return zh_names.get(card.card_id, definition.name if definition is not None else card.card_id)

    def pending_name(entity_id):
        pending = game.pending_choice or {}
        for option in pending.get("options", []):
            if getattr(option, "entity_id", None) == entity_id:
                return zh_names.get(option.card_id, option.definition.name)
        return name(entity_id)

    lines = ["# 龙战 vs 脏牧：完整中文操作轨迹", "", "固定 seed：202609140001", ""]
    action_no = 0
    while not game.finished and action_no < 300:
        action = policies[game.current].choose(game)
        label = LABELS.get(action.kind, action.kind)
        source = pending_name(action.source) if action.kind.endswith("PICK") else name(action.source)
        text = f"{label}【{source}】" if source else label
        if action.target_entity is not None:
            text += f" → 【{name(action.target_entity)}】"
        lines.append(f"{action_no + 1}. 玩家{game.current + 1}：{text}")
        game.step(action)
        action_no += 1
    winner = f"玩家{game.winner + 1}" if game.winner is not None else "无（未结束）"
    lines += ["", f"结果：{action_no} 步，{game.turn} 回合；获胜：{winner}；非法动作：{game.invalid_actions}。"]
    output = ROOT / "reports" / "dragon-vs-dirty-priest-one-game.zhCN.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
