#!/usr/bin/env python3
"""Generate a compact, auditable zh-CN trace for any configured deck pair.

Both seats use the deterministic heuristic policy.  This is a rules-audit
tool, not teacher-data generation, so it remains quick and readable.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from benchmark_mcts import matchup_deck_counts
from hsa.dragon_mirror import DragonMirrorGame
from hsa.policy import HeuristicPolicy


LABELS = {
    "PLAY": "打出", "ATTACK": "随从攻击", "HERO_ATTACK": "英雄攻击",
    "HERO_POWER": "使用英雄技能", "END_TURN": "结束回合",
    "LOCATION": "使用地标", "PREPARE": "预备", "TRADE": "交易",
    "DISCOVER_PICK": "选择发现牌", "RULE_CHOICE_PICK": "选择规则选项",
    "MULLIGAN_TOGGLE": "调度选择", "MULLIGAN_CONFIRM": "确认调度",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--deck-config", type=Path,
                        default=ROOT / "config" / "decks_20260920_multi.json")
    parser.add_argument("--deck-a", default="dragon_warrior")
    parser.add_argument("--deck-b", default="dirty_priest")
    parser.add_argument("--seed", type=int, default=202609140001)
    parser.add_argument("--max-actions", type=int, default=300)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    (deck_a, class_a), (deck_b, class_b) = matchup_deck_counts(
        args.deck_config, args.deck_a, args.deck_b
    )
    game = DragonMirrorGame(
        ROOT / "cards.251332.enUS.json", args.seed,
        deck_counts=(deck_a, deck_b), player_classes=(class_a, class_b),
    )
    policies = [HeuristicPolicy(), HeuristicPolicy()]
    def card_name(card) -> str:
        definition = getattr(card, "definition", None)
        return definition.name if definition is not None else card.card_id

    def find(entity_id):
        if entity_id is None:
            return None
        for player in game.players:
            for zone in (player.hand, player.board, player.deck, player.locations):
                for card in zone:
                    if card.entity_id == entity_id:
                        return card
        return None

    def option_or_zone_name(entity_id):
        card = find(entity_id)
        if card is not None:
            return card_name(card)
        for option in (game.pending_choice or {}).get("options", []):
            if getattr(option, "entity_id", None) == entity_id:
                return card_name(option)
        return str(entity_id) if entity_id is not None else ""

    def card_text(card, player, *, in_hand: bool) -> str:
        bits: list[str] = []
        if card.definition.card_type == "MINION":
            bits.append(f"{card.attack}/{card.health}")
        if in_hand:
            bits.append(f"{game._effective_cost(player, card)}费")
        if card.damage:
            bits.append(f"受伤{card.damage}")
        if card.dormant_turns:
            bits.append(f"休眠{card.dormant_turns}")
        if card.prepared:
            bits.append("已预备")
        return f"{card_name(card)}（{'，'.join(bits)}）" if bits else card_name(card)

    def player_summary(player) -> str:
        hand = "、".join(card_text(card, player, in_hand=True) for card in player.hand) or "无"
        board = "、".join(card_text(card, player, in_hand=False) for card in player.board) or "无"
        weapon = "无" if player.weapon is None else (
            f"{player.weapon.name} "
            f"{player.weapon.attack}/{player.weapon.durability}"
        )
        locations = "、".join(
            f"{location.card_id}"
            f"（耐久{location.durability}，冷却{location.cooldown}）"
            for location in player.locations
        ) or "无"
        pending = ""
        if player.pending_sham_trials:
            pending = "；待结算试炼：" + "、".join(
                f"{trial.card_id}（己方第{trial.sham_trial_due_owner_turn}回合）"
                for trial in player.pending_sham_trials
            )
        if player.slime_resummon:
            pending += "；Slime 'em!待复活：" + "、".join(
                card_text(card, player, in_hand=False) for card in player.slime_resummon
            )
        return (
            f"P{player.index + 1} HP {player.health}/{player.max_health}，护甲 {player.armor}，"
            f"法力 {player.mana}/{player.max_mana}；手牌[{len(player.hand)}]：{hand}；"
            f"场面：{board}；武器：{weapon}；地标：{locations}；牌库：{len(player.deck)}{pending}"
        )

    def action_text(action) -> str:
        label = LABELS.get(action.kind, action.kind)
        source = option_or_zone_name(action.source)
        text = f"P{game.current + 1} {label}" + (f"【{source}】" if source else "")
        if action.target_entity is not None:
            text += f" → 【{option_or_zone_name(action.target_entity)}】"
        elif action.target_player is not None and action.kind in {"HERO_ATTACK", "HERO_POWER"}:
            text += f" → P{action.target_player + 1} 英雄"
        return text

    output = args.output or ROOT / "reports" / (
        f"trace-{args.deck_a}-vs-{args.deck_b}-{args.seed}.zhCN.md"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {args.deck_a}（P1）vs {args.deck_b}（P2）", "",
        f"固定 seed：`{args.seed}`；策略：双方启发式（规则审计，不写入教师数据）。", "",
    ]
    active_turn: int | None = None
    wrote_turn = False
    for _ in range(args.max_actions):
        if game.finished:
            break
        if active_turn != game.turn:
            if wrote_turn:
                lines.extend(("", f"结束 — {player_summary(game.players[0])}", "",
                              f"结束 — {player_summary(game.players[1])}", ""))
            active_turn = game.turn
            wrote_turn = True
            lines.extend((f"## 回合 {game.turn}：P{game.current + 1}", "",
                          f"开始 — {player_summary(game.players[0])}", "",
                          f"开始 — {player_summary(game.players[1])}", "",
                          "实际动作：", ""))
        action = policies[game.current].choose(game)
        lines.append(f"- {action_text(action)}")
        game.step(action)
    if wrote_turn:
        lines.extend(("", f"结束 — {player_summary(game.players[0])}", "",
                      f"结束 — {player_summary(game.players[1])}", ""))
    winner = "无（达到动作上限）" if not game.finished else (
        "平局" if game.winner is None else f"P{game.winner + 1} 获胜"
    )
    lines.extend(("## 结果", "", f"{winner}；{game.turn} 回合；非法动作：{game.invalid_actions}。", ""))
    output.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"output": str(output), "finished": game.finished,
                      "winner": game.winner, "turn": game.turn,
                      "invalid_actions": game.invalid_actions}, ensure_ascii=False))
    return 0 if game.finished and game.invalid_actions == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
