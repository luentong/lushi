from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.shadow_advisor import analyze_payload, jsonl_backlog


class ShadowAdvisorTests(unittest.TestCase):
    def setUp(self):
        self.coverage = {
            "cards_build": 1,
            "cards": [
                {"card_id": "READY", "name": "Ready", "class": "WARRIOR", "type": "MINION", "collectible": True, "playable_ready": True},
                {"card_id": "MISSING", "name": "Missing", "class": "PRIEST", "type": "SPELL", "collectible": True, "playable_ready": False},
            ],
        }

    def test_played_unimplemented_card_becomes_red_backlog_task(self):
        report = analyze_payload({"games": [{"game_index": 0, "revealed_cards": ["READY", "MISSING"], "blocks": [{"packet_id": 9, "block_type": "PLAY", "source_card": "MISSING"}]}]}, self.coverage)
        self.assertEqual("red", report["games"][0]["confidence"])
        task = report["backlog"][0]
        self.assertEqual("MISSING", task["card_id"])
        self.assertEqual("played_card_missing_rule", task["reason"])
        self.assertEqual("red", task["severity"])
        self.assertFalse(report["games"][0]["action_recommendation"]["available"])

    def test_ready_cards_remain_amber_until_general_replay_exists(self):
        report = analyze_payload({"games": [{"game_index": 0, "revealed_cards": ["READY"], "blocks": [{"packet_id": 1, "block_type": "PLAY", "source_card": "READY"}]}]}, self.coverage)
        self.assertEqual("amber", report["games"][0]["confidence"])
        self.assertEqual([], report["backlog"])

    def test_unknown_card_is_deduplicated_and_jsonl_is_safe(self):
        report = analyze_payload({"games": [{"game_index": 3, "revealed_cards": ["NEW", "NEW"], "blocks": [{"packet_id": 2, "block_type": "TRIGGER", "source_card": "NEW"}]}]}, self.coverage)
        reasons = {task["reason"] for task in report["backlog"]}
        self.assertIn("unknown_card_id", reasons)
        self.assertEqual(1, len(report["backlog"]))
        self.assertEqual(2, report["backlog"][0]["occurrences"])
        self.assertTrue(jsonl_backlog(report["backlog"]).endswith("\n"))


if __name__ == "__main__":
    unittest.main()
