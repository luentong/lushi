from pathlib import Path
import importlib.util
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from replay_entity_rollout import file_digest, replay_game_prefix, verify_report_inputs


class ReplayProvenanceTests(unittest.TestCase):
    def test_replay_rejects_wrong_deck_fingerprint(self):
        with tempfile.TemporaryDirectory() as directory:
            cards = Path(directory) / "cards.json"
            decks = Path(directory) / "decks.json"
            cards.write_text("[]", encoding="utf-8")
            decks.write_text("{}", encoding="utf-8")
            sources = {"old-cards": file_digest(cards), "old-decks": file_digest(decks)}
            for path in (ROOT / "src/hsa").rglob("*.py"):
                sources[str(path)] = file_digest(path)
            report = {"config": {"cards": "old-cards", "deck_config": "old-decks"},
                      "provenance": {"source_sha256": sources}}
            verify_report_inputs(report, cards, decks)
            decks.write_text('{"changed": true}', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "deck_config differs"):
                verify_report_inputs(report, cards, decks)


@unittest.skipUnless(importlib.util.find_spec("hearthstone") or (ROOT / ".deps/hearthstone").is_dir(),
                     "hearthstone deckstrings unavailable")
class ReplayEntityRolloutTests(unittest.TestCase):
    def test_prefix_replays_concrete_action_and_rejects_drift(self):
        from hsa import DragonMirrorGame
        from benchmark_mcts import _decoded_decks, configure_search_beliefs

        cards = ROOT / "cards.251332.enUS.json"
        config = ROOT / "config/decks_20260925_smoke8.json"
        decks = _decoded_decks(config)
        name = "龙战_01"
        counts, cls = decks[name]
        game = DragonMirrorGame(cards, 2391, deck_counts=(counts, counts),
                                player_classes=(cls, cls))
        configure_search_beliefs(game, config)
        action = game.legal_actions()[0]
        record = {"seed": 2391, "deck_a": name, "deck_b": name,
                  "action_trace": [{"actor": game.current, "turn": game.turn,
                                    "action": list(action.key())}],
                  "steps": 1, "winner": None}
        game.step(action)
        restored = replay_game_prefix(record, cards, config, until=1)
        self.assertEqual(game.current, restored.current)
        self.assertEqual(game.turn, restored.turn)
        with self.assertRaisesRegex(ValueError, "state drift"):
            replay_game_prefix({**record, "action_trace": [
                {**record["action_trace"][0], "actor": 1 - record["action_trace"][0]["actor"]}]},
                cards, config, until=1)
        with self.assertRaisesRegex(ValueError, "lacks complete action_trace"):
            replay_game_prefix({**record, "action_trace": None}, cards, config, until=0)


if __name__ == "__main__":
    unittest.main()
