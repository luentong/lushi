import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_mulligan_counterfactuals import analyze


class CounterfactualOpeningAuditTests(unittest.TestCase):
    def test_single_replaced_card_is_attributed_to_that_card(self):
        with tempfile.TemporaryDirectory() as folder:
            paths = [Path(folder) / name for name in ("flip.json", "base.json")]
            hand = [{"id": "EARLY", "cost": 1}, {"id": "LATE", "cost": 5}]
            initial = {"players": [{"hand": hand}, {"hand": hand}]}
            def trace(toggle):
                return {"initial_state": initial, "steps": [
                    {"turn_before": 0, "candidate_acted": True,
                     "action_key": ["MULLIGAN_TOGGLE", 1, -1, -1],
                     "description": f"P1 MULLIGAN_REPLACE {card}[{card}]"}
                    for card in toggle]}
            paths[0].write_text(json.dumps(trace(("EARLY", "LATE"))))
            paths[1].write_text(json.dumps(trace(("LATE",))))
            def report(path, winner, opening):
                return {"checkpoint_sha256": {"candidate": "a", "opponent": "b"},
                        "source_sha256": {"rules": "c"}, "deck_config_sha256": "d",
                        "parameters": {"seed": 11, "pairs_per_matchup": 1,
                                       "deck_config": "decks.json", "cards": "cards.json",
                                       "max_actions": 350, "max_game_seconds": 300,
                                       "manual_mulligan": True,
                                       "opponent_mulligan_policy": "baseline",
                                       "candidate_mulligan_policy": opening},
                        "games": [{"pair_id": 0, "seed": 11,
                                   "candidate_deck": "deck", "opponent_deck": "other",
                                   "candidate_seat": seat, "status": "complete",
                                   "winner": (winner + seat) % 2, "trace": str(path)}
                                  for seat in (0, 1)]}
            result = analyze(report(paths[0], 0, "single_flip"),
                             report(paths[1], 1, "baseline"))
            self.assertEqual("EARLY", result["rows"][0]["card_id"])
            self.assertEqual("replace", result["rows"][0]["treatment"])
            self.assertEqual(1.0, result["effects"][0]["replace_minus_keep_mean"])
            self.assertFalse(result["effects"][0]["eligible_for_teacher"])


if __name__ == "__main__":
    unittest.main()
