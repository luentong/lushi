from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from summarize_shard_root_audit import sign_p, summarize


class ShardRootSummaryTests(unittest.TestCase):
    def test_sign_probability_and_holm(self):
        self.assertAlmostEqual(0.03125, sign_p(6, 0))
        report = {"schema": "teacher-shard-paired-root-audit-v1",
                  "manifest": "m.json", "continuation_policy": "heuristic",
                  "replay_status": [{"status": "verified", "fingerprint_drift": True}],
                  "audits": [{"game_index": 0, "game_seed": 17,
                              "deck_a": "a", "deck_b": "b", "ply": 3,
                              "teacher_selected": "end",
                              "teacher_selected_key": ["END_TURN"],
                              "teacher_action_values": [0.1, 0.3],
                              "teacher_action_visits": [8, 2],
                              "results": [
                                  {"action_key": ["END_TURN"]},
                                  {"action_key": ["PLAY", 1]}],
                              "paired_comparisons": [
                                  {"alternative": "play", "paired_decided": 6,
                                   "alternative_better": 6, "selected_better": 0,
                                   "tied": 0, "mean_score_difference": 1.0},
                                  {"alternative": "trade", "paired_decided": 6,
                                   "alternative_better": 3, "selected_better": 3,
                                   "tied": 0, "mean_score_difference": 0.0}]}]}
        result = summarize(report)
        self.assertEqual(1, result["fingerprint_drifted_verified_games"])
        self.assertEqual(2, result["inspected_alternatives"])
        self.assertEqual(1, result["teacher_selected_not_max_sampled_q"])
        play = next(row for row in result["candidates"] if row["alternative"] == "play")
        self.assertAlmostEqual(0.0625, play["paired_sign_p_holm"])
        self.assertEqual(0, result["holm_positive_alternatives"])

    def test_rejects_bad_pair_counts(self):
        report = {"schema": "teacher-shard-paired-root-audit-v1",
                  "manifest": "m.json", "continuation_policy": "heuristic",
                  "replay_status": [], "audits": [
                      {"game_index": 0, "game_seed": 1, "deck_a": "a",
                       "deck_b": "b", "ply": 0, "teacher_selected": "end",
                       "paired_comparisons": [{"alternative": "play",
                                               "paired_decided": 2,
                                               "alternative_better": 2,
                                               "selected_better": 1, "tied": 0,
                                               "mean_score_difference": 0.5}]}]}
        with self.assertRaisesRegex(ValueError, "do not add up"):
            summarize(report)


if __name__ == "__main__":
    unittest.main()
