import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from evaluate_entity_policy import (make_schedule, outcome_score, summary,
                                    candidate_deck_summary, value_calibration_summary,
                                    baseline_mulligan_action, single_flip_mulligan_action)


class EntityEvaluationTests(unittest.TestCase):
    def game(self, pair, seat, winner=None, status="complete"):
        return {"pair_id": pair, "candidate_seat": seat, "winner": winner, "status": status}

    def test_schedule_swaps_seats_without_changing_candidate_deck(self):
        jobs = make_schedule(["a", "b"], 2, 100)
        self.assertEqual(16, len(jobs))
        for i in range(0, len(jobs), 2):
            a, b = jobs[i:i + 2]
            self.assertEqual(a["seed"], b["seed"])
            self.assertEqual(a["candidate_deck"], b["candidate_deck"])
            self.assertEqual((0, 1), (a["candidate_seat"], b["candidate_seat"]))

    def test_truncation_is_not_a_draw(self):
        self.assertEqual(.5, outcome_score(self.game(0, 0)))
        self.assertIsNone(outcome_score(self.game(0, 0, status="truncated")))
        result = summary([self.game(0, 0, 0), self.game(0, 1, status="truncated")])
        self.assertEqual(1, result["completed_games"])
        self.assertEqual(0, result["draws"])
        self.assertEqual(0, result["complete_pairs"])
        self.assertIsNone(result["pair_hoeffding_95_interval"])

    def test_pair_is_the_unit_of_uncertainty(self):
        result = summary([self.game(0, 0, 0), self.game(0, 1, 1),
                          self.game(1, 0, 1), self.game(1, 1, 0)])
        self.assertEqual(2, result["complete_pairs"])
        self.assertEqual(.5, result["pair_score_mean"])
        self.assertEqual([0.0, 1.0], result["pair_hoeffding_95_interval"])

    def test_duplicate_seats_rejected(self):
        with self.assertRaises(ValueError):
            summary([self.game(0, 0, 0), self.game(0, 0, 0)])

    def test_empty_result_is_not_zero_winrate(self):
        self.assertIsNone(summary([])["win_rate"])
        self.assertIsNone(summary([])["pair_score_mean"])

    def test_per_deck_summary_does_not_hide_bad_subgroup(self):
        games = [{**self.game(0, 0, 0), "candidate_deck": "a"},
                 {**self.game(0, 1, 1), "candidate_deck": "a"},
                 {**self.game(1, 0, 1), "candidate_deck": "b"},
                 {**self.game(1, 1, 0), "candidate_deck": "b"}]
        result = candidate_deck_summary(games)
        self.assertEqual(1, result["a"]["score_rate"])
        self.assertEqual(0, result["b"]["score_rate"])

    def test_critic_calibration_uses_completed_games_as_units(self):
        games = [{**self.game(0, 0, 0), "candidate_value_predictions": [1.0]},
                 {**self.game(1, 0, 1), "candidate_value_predictions": [1.0, 1.0]}]
        result = value_calibration_summary(games)
        self.assertEqual(2, result["games"])
        self.assertAlmostEqual(.5, result["game_macro_brier"])
        self.assertAlmostEqual(.5, result["observed_score"])

    def test_explicit_baseline_mulligan_matches_engine_default(self):
        from hsa import DragonMirrorGame
        cards = Path(__file__).resolve().parents[1] / "cards.251332.enUS.json"
        for seed in (17, 29, 43):
            automatic = DragonMirrorGame(cards, seed)
            manual = DragonMirrorGame(cards, seed, manual_mulligan=True)
            while manual.pending_choice and manual.pending_choice["kind"] == "MULLIGAN":
                manual.step(baseline_mulligan_action(manual, manual.legal_actions()))
            self.assertEqual(automatic.first_player, manual.first_player)
            for old, new in zip(automatic.players, manual.players):
                self.assertEqual([c.card_id for c in old.hand], [c.card_id for c in new.hand])
                self.assertEqual([c.card_id for c in old.deck], [c.card_id for c in new.deck])

    def test_single_flip_changes_exactly_one_opening_card(self):
        from hsa import DragonMirrorGame
        cards = Path(__file__).resolve().parents[1] / "cards.251332.enUS.json"
        for seed in (17, 29, 43):
            game = DragonMirrorGame(cards, seed, manual_mulligan=True)
            offered = {card.entity_id: card.definition.cost for card in game.players[0].hand}
            original = {entity for entity, cost in offered.items() if cost >= 4}
            while game.pending_choice and game.pending_choice["player"] == 0:
                game.step(single_flip_mulligan_action(game, game.legal_actions()))
            selected = [event for event in game.events
                        if event["kind"] == "mulligan_toggle" and event["player"] == 0]
            actual = {event["entity"] for event in selected if event["replace"]}
            self.assertEqual(1, len(original ^ actual))


if __name__ == "__main__":
    unittest.main()
