#!/usr/bin/env python3
"""Render a compact search-match JSON trace as readable zh-CN Markdown."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

GIFT_NAMES = {
    "waking_terror": "惊醒恐惧（+3攻击力并获得吸血）",
    "well_rested": "充分休息（+2/+2并获得扰魔）",
    "sleepwalker": "梦游（获得冲锋）",
    "persisting_horror": "挥之不去的恐惧（获得复生）",
    "rude_awakening": "粗暴唤醒（战吼触发两次）",
}


def load_names(path: Path) -> dict[str, str]:
    cards = json.loads(path.read_text(encoding="utf-8"))
    return {
        card["id"]: card["name"]
        for card in cards
        if card.get("id") and card.get("name")
    }


def localized_name(card_id: str | None, names: dict[str, str]) -> str:
    if not card_id:
        return "未知卡牌"
    return f'{names.get(card_id, card_id)}[{card_id}]'


def translate_action(
    description: str,
    english_names: dict[str, str],
    chinese_names: dict[str, str],
) -> str:
    result = description.replace(
        "HERO_POWER Armor Up", "使用英雄技能“全副武装！”"
    )
    replacements = sorted(
        (
            (english_name, chinese_names.get(card_id, english_name))
            for card_id, english_name in english_names.items()
            if english_name in result
        ),
        key=lambda item: len(item[0]),
        reverse=True,
    )
    for english_name, chinese_name in replacements:
        result = result.replace(english_name, chinese_name)
    phrases = (
        ("MULLIGAN_REPLACE", "起手替换"),
        ("MULLIGAN_KEEP", "起手保留"),
        ("MULLIGAN_CONFIRM", "确认起手牌"),
        ("HERO_ATTACK", "英雄攻击"),
        ("DISCOVER_PICK", "发现并选择"),
        ("GEDDON_DRAW_PICK", "选择抽取"),
        ("REWIND_KEEP", "保留回溯结果"),
        ("REWIND_RETRY", "重新进行回溯"),
        ("AMMUNITION_PICK", "选择弹药模式"),
        ("CORPSE_SPEND", "消耗尸体"),
        ("END_TURN", "结束回合"),
        ("PREPARE", "准备"),
        ("LOCATION", "使用地标"),
        ("TRADE", "交易"),
        ("ATTACK", "攻击"),
        ("PLAY", "打出"),
        ("hero", "英雄"),
    )
    for source, target in phrases:
        result = result.replace(source, target)
    result = re.sub(r"P([12])", r"玩家\1", result)
    result = result.replace(" -> -", "").replace(" -> ", " → ")
    gift_match = re.search(r" \+ ([a-z_]+)$", result)
    if gift_match:
        code = gift_match.group(1)
        result = result[:gift_match.start()] + f"；附带礼物效果：{GIFT_NAMES.get(code, code)}"
    return result


def player_number(event: dict) -> int:
    return int(event.get("player", 0)) + 1


def event_text(event: dict, names: dict[str, str]) -> str:
    kind = event["kind"]
    player = player_number(event)
    card = localized_name(event.get("card"), names)
    if kind == "turn_start":
        return f"玩家{player}的回合开始"
    if kind == "turn_end":
        return f"玩家{player}的回合结束"
    if kind == "draw":
        return f"玩家{player}抽到{card}"
    if kind == "play":
        origin = "初始牌库" if event.get("started_in_deck") else "衍生牌"
        return f"玩家{player}打出{card}（来源：{origin}）"
    if kind == "minion_died":
        return f"玩家{player}的{card}死亡（实体#{event.get('entity')}）"
    if kind == "gain_armor":
        return f"玩家{player}获得{event.get('amount', 0)}点护甲"
    if kind == "hero_power":
        return f"玩家{player}使用英雄技能"
    if kind == "equip_weapon":
        return (
            f"玩家{player}装备{card}，攻击力/耐久度="
            f"{event.get('attack')}/{event.get('durability')}"
        )
    if kind == "weapon_destroyed":
        return f"玩家{player}的武器{card}被摧毁"
    if kind == "generated_to_hand":
        return (
            f"玩家{player}获得衍生牌{card}并置入手牌"
            f"（来源：{localized_name(event.get('source'), names)}）"
        )
    if kind == "returned_to_hand":
        return f"玩家{player}的{card}返回手牌"
    if kind == "awaken":
        return f"玩家{player}的{card}苏醒（实体#{event.get('entity')}）"
    if kind == "discover_offer":
        options = "、".join(
            localized_name(option.get("card"), names)
            for option in event.get("options", [])
        )
        return f"向玩家{player}提供发现选项：{options}"
    if kind == "discover_pick":
        gifts = "、".join(
            GIFT_NAMES.get(gift, gift) for gift in event.get("gifts", [])
        )
        suffix = f"；礼物效果={gifts}" if gifts else ""
        return f"玩家{player}发现并选择{card}{suffix}"
    if kind == "rewind_offer":
        outcome = "、".join(
            f'{names.get(item.get("card"), item.get("name", "未知"))}'
            f' {item.get("attack")}/{item.get("durability")}'
            for item in event.get("outcome", [])
        )
        return f"向玩家{player}展示回溯结果：{outcome}"
    if kind == "rewind_pick":
        decision = "保留" if event.get("decision") == "keep" else "重试"
        return f"玩家{player}选择{decision}本次回溯结果"
    translated = dict(event)
    translated["事件"] = translated.pop("kind")
    return json.dumps(translated, ensure_ascii=False, sort_keys=True)


def card_label(card: dict, names: dict[str, str]) -> str:
    return names.get(card["id"], card["name"])


def player_line(player: dict, names: dict[str, str]) -> str:
    weapon = player["weapon"]
    weapon_text = "无"
    if weapon is not None:
        weapon_text = (
            f'{names.get(weapon["card"], weapon["name"])} '
            f'{weapon["attack"]}/{weapon["durability"]}'
        )
    board = "、".join(
        f'{card_label(card, names)}#{card["entity"]} '
        f'{card["attack"]}/{card["health"]}'
        for card in player["board"]
    ) or "空"
    hand = "、".join(
        f'{card_label(card, names)}({card["cost"]}费)'
        for card in player["hand"]
    ) or "空"
    return (
        f'玩家{player["player"]}：生命={player["health"]}，护甲={player["armor"]}，'
        f'法力={player["mana"][0]}/{player["mana"][1]}，牌库={player["deck_count"]}；'
        f'武器={weapon_text}；场面={board}；手牌={hand}'
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("trace", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--english-cards", type=Path, default=ROOT / "cards.251332.enUS.json")
    parser.add_argument("--chinese-cards", type=Path, default=ROOT / "cards.zhCN.json")
    args = parser.parse_args()
    document = json.loads(args.trace.read_text(encoding="utf-8"))
    english_names = load_names(args.english_cards)
    chinese_names = load_names(args.chinese_cards)
    output = args.output or args.trace.with_name(args.trace.stem + ".zhCN.md")

    candidate = document["candidate_seat"] + 1
    winner = document["winner"] + 1 if document["winner"] is not None else "平局"
    lines = [
        "# 神经策略先验 PUCT 对普通 ISMCTS：完整操作轨迹", "",
        f'- 随机种子：`{document["seed"]}`',
        f"- 神经策略先验所在座位：`玩家{candidate}`",
        f"- 获胜方：`玩家{winner}`" if winner != "平局" else "- 结果：`平局`",
        f'- 神经策略先验获胜：`{"是" if document["candidate_win"] else "否"}`',
        f'- 总操作数：`{len(document["steps"])}`',
        f'- 非法操作数：`{document["invalid_actions"]}`', "",
        "> 访问比例表示本次低预算搜索在根节点分配给各操作的访问次数占比；",
        "> 它不是经过充分搜索后的精确胜率。局面估值范围约为 -1 到 1，越高越有利于当前决策方。",
        "",
    ]
    previous_turn = None
    for step in document["steps"]:
        state = step["state_after"]
        if state["turn"] != previous_turn:
            lines.extend([f'## 第 {state["turn"]} 回合', ""])
            previous_turn = state["turn"]
        agent = (
            "神经策略先验 PUCT"
            if step["agent"] == "policy-prior-puct-v1"
            else "普通 ISMCTS"
        )
        action = translate_action(step["description"], english_names, chinese_names)
        lines.extend([
            f'### 第 {step["step"]} 步：{agent}', "", f"**{action}**", "",
            f'合法操作数：{step["legal_action_count"]}；'
            f'搜索节点数：{step["search"].get("nodes", 0)}；'
            f'所选操作估值：{step["search"].get("selected_value", 0):.4f}', "",
        ])
        if step["ranked_alternatives"]:
            lines.extend(["根节点访问比例最高的操作：", ""])
            for option in step["ranked_alternatives"][:5]:
                translated = translate_action(
                    option["action"], english_names, chinese_names
                )
                selected = " **← 最终选择**" if option.get("selected") else ""
                details = (
                    f'；访问次数={option.get("visits", 0)}'
                    f'；分支均值={option.get("mean_value", 0):.4f}'
                    f'；神经先验={option.get("prior", 0):.4f}'
                    if "visits" in option else ""
                )
                lines.append(
                    f'- `{option["visit_share"]:.3f}` — {translated}'
                    f'{selected}{details}'
                )
            lines.append("")
        if step["events"]:
            lines.extend(["本步结算事件：", ""])
            lines.extend(
                f"- {event_text(event, chinese_names)}"
                for event in step["events"]
            )
            lines.append("")
        lines.extend(
            f"- {player_line(player, chinese_names)}"
            for player in state["players"]
        )
        lines.append("")
    output.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
