from __future__ import annotations

import json
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.live_bridge import build_snapshot_hypothesis
from hsa.live_state import LiveStateCursor, reconstruct_game
from hsa.encoding import encode_state


CARDS = ROOT / "cards.251332.enUS.json"


def _live_damage_snapshot():
    cards = {card["id"]: card for card in json.loads(CARDS.read_text(encoding="utf-8"))}
    minion_id = "CORE_CS2_182"
    definition = cards[minion_id]
    preamble = [
        {"kind": "FullEntity", "entity": 1, "card_id": "HERO_01",
         "tags": [{"tag": "CONTROLLER", "value": 1}, {"tag": "ZONE", "value": "PLAY"},
                  {"tag": "CARDTYPE", "value": "HERO"}, {"tag": "HEALTH", "value": 30},
                  {"tag": "DAMAGE", "value": 0}]},
        {"kind": "FullEntity", "entity": 2, "card_id": "HERO_08",
         "tags": [{"tag": "CONTROLLER", "value": 2}, {"tag": "ZONE", "value": "PLAY"},
                  {"tag": "CARDTYPE", "value": "HERO"}, {"tag": "HEALTH", "value": 30},
                  {"tag": "DAMAGE", "value": 0}]},
        {"kind": "FullEntity", "entity": 3, "card_id": "GAME_005",
         "tags": [{"tag": "CARDTYPE", "value": "GAME"}, {"tag": "TURN", "value": 3},
                  {"tag": "CURRENT_PLAYER", "value": 1}]},
        {"kind": "FullEntity", "entity": 4, "card_id": "PLAYER_01",
         "tags": [{"tag": "CONTROLLER", "value": 1}, {"tag": "CARDTYPE", "value": "PLAYER"},
                  {"tag": "RESOURCES", "value": 3}, {"tag": "MAXRESOURCES", "value": 3}]},
        {"kind": "FullEntity", "entity": 5, "card_id": "PLAYER_02",
         "tags": [{"tag": "CONTROLLER", "value": 2}, {"tag": "CARDTYPE", "value": "PLAYER"},
                  {"tag": "RESOURCES", "value": 3}, {"tag": "MAXRESOURCES", "value": 3}]},
    ]
    for entity in (10, 11):
        preamble.append({"kind": "FullEntity", "entity": entity, "card_id": minion_id,
                         "tags": [{"tag": "CONTROLLER", "value": 1},
                                  {"tag": "ZONE", "value": "PLAY"},
                                  {"tag": "CARDTYPE", "value": "MINION"},
                                  {"tag": "ATK", "value": definition["attack"]},
                                  {"tag": "HEALTH", "value": definition["health"]},
                                  {"tag": "DAMAGE", "value": 0}]})
    blocks = [
        {"block_type": "TURN_START", "turn": 3, "player": 1},
        {"block_type": "TRIGGER", "effects": [
            {"kind": "TagChange", "entity": 1, "tag": "DAMAGE", "value": 1},
            {"kind": "TagChange", "entity": 10, "tag": "DAMAGE", "value": 1},
            {"kind": "TagChange", "entity": 11, "tag": "DAMAGE", "value": 1},
        ]},
    ]
    return reconstruct_game({"preamble": preamble, "blocks": blocks})


class LiveBridgeDamageTests(unittest.TestCase):
    def test_open_block_cursor_records_only_new_damage_deltas(self):
        cursor = LiveStateCursor()
        base = {
            "preamble": [{"kind": "FullEntity", "entity": 10,
                          "card_id": "CORE_CS2_182",
                          "tags": [{"tag": "CONTROLLER", "value": 1},
                                   {"tag": "ZONE", "value": "PLAY"},
                                   {"tag": "CARDTYPE", "value": "MINION"},
                                   {"tag": "DAMAGE", "value": 0}]}],
            "blocks": [
                {"packet_id": 1, "block_type": "TURN_START", "turn": 3,
                 "player": 1},
                {"packet_id": 2, "block_type": "TRIGGER", "effects": [
                    {"kind": "TagChange", "entity": 10,
                     "tag": "DAMAGE", "value": 1},
                ]},
            ],
        }
        first = cursor.apply_game(base)
        self.assertEqual(1, len(first.damage_history))
        extended = {
            **base,
            "blocks": [base["blocks"][0], {
                **base["blocks"][1], "effects": [
                    *base["blocks"][1]["effects"],
                    {"kind": "TagChange", "entity": 10,
                     "tag": "DAMAGE", "value": 2},
                ],
            }],
        }
        second = cursor.apply_game(extended)
        self.assertEqual(2, len(second.damage_history))
        self.assertEqual([2, 2], [event["packet_id"] for event in second.damage_history])

    def test_explicit_current_turn_damage_reaches_v5_simulator_state(self):
        state = _live_damage_snapshot()
        self.assertEqual(3, len(state.damage_history))
        self.assertTrue(all(item["turn"] == 3 and item["active_player"] == 1
                            for item in state.damage_history))

        result = build_snapshot_hypothesis(
            cards_path=CARDS,
            state=state,
            own_deck={"CORE_CS2_182": 30},
            opponent_deck={"CORE_CS2_182": 30},
            player_classes=("WARRIOR", "MAGE"),
            self_controller=1,
        )
        self.assertTrue(result.available, result.reason)
        self.assertEqual(
            {"hero:0", "minion:10", "minion:11"},
            result.game.players[0].damaged_characters_this_turn,
        )
        no_progress = result.game.clone()
        no_progress.players[0].damaged_characters_this_turn.clear()
        self.assertNotEqual(encode_state(result.game), encode_state(no_progress))
        self.assertEqual(
            encode_state(result.game, schema_version=4),
            encode_state(no_progress, schema_version=4),
        )

    def test_damage_during_opponents_turn_does_not_count_for_owner(self):
        state = _live_damage_snapshot()
        state.apply_game({"preamble": [], "blocks": [
            {"block_type": "TURN_START", "turn": 4, "player": 2,
             "effects": [
                 {"kind": "TagChange", "entity": 3, "tag": "TURN", "value": 4},
                 {"kind": "TagChange", "entity": 3, "tag": "CURRENT_PLAYER", "value": 2},
             ]},
            {"block_type": "TRIGGER", "effects": [
                {"kind": "TagChange", "entity": 10, "tag": "DAMAGE", "value": 2},
            ]},
            {"block_type": "TURN_START", "turn": 5, "player": 1,
             "effects": [
                 {"kind": "TagChange", "entity": 3, "tag": "TURN", "value": 5},
                 {"kind": "TagChange", "entity": 3, "tag": "CURRENT_PLAYER", "value": 1},
             ]},
        ]})
        self.assertEqual(4, state.damage_history[-1]["turn"])
        self.assertEqual(2, state.damage_history[-1]["active_player"])

        result = build_snapshot_hypothesis(
            cards_path=CARDS,
            state=state,
            own_deck={"CORE_CS2_182": 30},
            opponent_deck={"CORE_CS2_182": 30},
            player_classes=("WARRIOR", "MAGE"),
            self_controller=1,
        )
        self.assertTrue(result.available, result.reason)
        self.assertEqual(set(), result.game.players[0].damaged_characters_this_turn)


if __name__ == "__main__":
    unittest.main()
