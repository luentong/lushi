from __future__ import annotations

import gzip
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from hsa import DragonMirrorGame
from hsa.dragon_mirror import DRAGON_DECK_COUNTS
from hsa.encoding import (
    configure_card_vocab, encode_state, feature_schema,
)
from hsa.observer_view import observer_view
from hsa.policy import HeuristicPolicy
from audit_teacher_shard_roots import replay_shard
from hsa.lineage import ruleset_manifest


class TeacherShardReplayTests(unittest.TestCase):
    def setUp(self):
        configure_card_vocab("legacy")

    def tearDown(self):
        configure_card_vocab("legacy")

    def _synthetic_rows(self):
        game = DragonMirrorGame(
            ROOT / "cards.251332.enUS.json", 42,
            deck_counts=(DRAGON_DECK_COUNTS, DRAGON_DECK_COUNTS),
            player_classes=("WARRIOR", "WARRIOR"))
        policy = HeuristicPolicy()
        rows = [{"record_type": "header", "feature_schema": feature_schema()}]
        ply = 0
        while not game.finished and ply < 240:
            actions = game.legal_actions()
            selected = policy.choose(game)
            index = actions.index(selected)
            rows.append({
                "record_type": "decision", "game_seed": 42,
                "ply": ply, "actor": game.current,
                "state": list(encode_state(game, game.current)),
                "action_keys": [list(action.key()) for action in actions],
                "observer_view": observer_view(
                    game, actions=actions,
                    known_deck=game.deck_counts[game.current]),
                "chosen_action": index, "executed_action": index,
                "legal_action_count": len(actions),
            })
            game.step(selected)
            ply += 1
        self.assertTrue(game.finished)
        for row in rows[1:]:
            row["winner"] = game.winner
            row["value_target"] = (0.0 if game.winner is None else
                                   1.0 if game.winner == row["actor"] else -1.0)
        return rows

    def _replay(self, rows, path):
        with gzip.open(path, "wt", encoding="utf-8") as out:
            for row in rows:
                out.write(json.dumps(row) + "\n")
        with patch("audit_teacher_shard_roots.matchup_deck_counts",
                   return_value=((DRAGON_DECK_COUNTS, "WARRIOR"),
                                 (DRAGON_DECK_COUNTS, "WARRIOR"))), \
             patch("audit_teacher_shard_roots.configure_search_beliefs"):
            return replay_shard(
                path, cards=ROOT / "cards.251332.enUS.json",
                deck_config=ROOT / "config/decks.json",
                deck_a="dragon", deck_b="dragon", seed=42,
                selection_seed=7, min_ply=3, max_root_actions=12)

    def test_complete_shard_replays_and_samples_reproducibly(self):
        rows = self._synthetic_rows()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "teacher.jsonl.gz"
            first = self._replay(rows, path)
            second = self._replay(rows, path)
        self.assertEqual(first["decisions"], len(rows) - 1)
        self.assertEqual(first["candidate_counts"], second["candidate_counts"])
        for category in ("END_TURN", "OTHER"):
            a, b = first["choices"][category], second["choices"][category]
            self.assertEqual(a["row"]["ply"] if a else None,
                             b["row"]["ply"] if b else None)

    def test_action_drift_rejects_whole_game(self):
        rows = self._synthetic_rows()
        rows[2]["action_keys"] = [["fabricated"]]
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "legal action drift"):
                self._replay(rows, Path(directory) / "corrupt.jsonl.gz")

    def test_wrong_terminal_value_rejects_whole_game(self):
        rows = self._synthetic_rows()
        rows[1]["value_target"] *= -1
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "terminal outcome/value drift"):
                self._replay(rows, Path(directory) / "wrong-value.jsonl.gz")

    def test_fingerprint_override_still_requires_exact_replay(self):
        rows = self._synthetic_rows()
        rows[0]["ruleset_fingerprint"] = "old-code-hash"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "old.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8") as out:
                for row in rows:
                    out.write(json.dumps(row) + "\n")
            with patch("audit_teacher_shard_roots.matchup_deck_counts",
                       return_value=((DRAGON_DECK_COUNTS, "WARRIOR"),
                                     (DRAGON_DECK_COUNTS, "WARRIOR"))), \
                 patch("audit_teacher_shard_roots.configure_search_beliefs"):
                kwargs = dict(cards=ROOT / "cards.251332.enUS.json",
                              deck_config=ROOT / "config/decks.json",
                              deck_a="dragon", deck_b="dragon", seed=42,
                              selection_seed=7, min_ply=3, max_root_actions=12)
                with self.assertRaisesRegex(ValueError, "fingerprint differs"):
                    replay_shard(path, **kwargs)
                replayed = replay_shard(path, allow_fingerprint_drift=True, **kwargs)
                self.assertTrue(replayed["fingerprint_drift"])
                self.assertEqual(ruleset_manifest(ROOT)["fingerprint_sha256"],
                                 replayed["current_fingerprint"])
                rows[2]["action_keys"] = [["fabricated"]]
                with gzip.open(path, "wt", encoding="utf-8") as out:
                    for row in rows:
                        out.write(json.dumps(row) + "\n")
                with self.assertRaisesRegex(ValueError, "legal action drift"):
                    replay_shard(path, allow_fingerprint_drift=True, **kwargs)

    def test_target_ply_replays_exact_root(self):
        rows = self._synthetic_rows()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "target.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8") as out:
                for row in rows:
                    out.write(json.dumps(row) + "\n")
            with patch("audit_teacher_shard_roots.matchup_deck_counts",
                       return_value=((DRAGON_DECK_COUNTS, "WARRIOR"),
                                     (DRAGON_DECK_COUNTS, "WARRIOR"))), \
                 patch("audit_teacher_shard_roots.configure_search_beliefs"):
                result = replay_shard(
                    path, cards=ROOT / "cards.251332.enUS.json",
                    deck_config=ROOT / "config/decks.json",
                    deck_a="dragon", deck_b="dragon", seed=42,
                    selection_seed=7, min_ply=0, max_root_actions=12,
                    target_ply=3)
            self.assertEqual(3, result["choices"]["TARGET"]["row"]["ply"])


if __name__ == "__main__":
    unittest.main()
