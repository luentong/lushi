"""Exact tiny information games; these are NOT Hearthstone card rules.

A hidden fair bit is revealed by action 1. Actions 2/3 guess its value and
terminate. Action 4, when present, is a known guaranteed winning alternative.
This isolates observation branching from card implementation and learned value.
"""
from __future__ import annotations

import copy
import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from hsa.dragon_mirror import Action
from hsa.mcts import InformationSetMCTSPolicy
from hsa.policy_value import PolicyValueOutput


class BitGame:
    def __init__(self, bit=0, safe=False):
        self.bit, self.safe, self.revealed = bit, safe, False
        self.current, self.turn, self.finished, self.winner = 0, 1, False, None
        self.pending_choice = None
        cards = [SimpleNamespace(entity_id=i, card_id=f"TEST_BIT_ACTION_{i}")
                 for i in range(1, 5 if safe else 4)]
        self.players = [SimpleNamespace(index=0, hand=cards, board=[], locations=[]),
                        SimpleNamespace(index=1, hand=[], board=[], locations=[])]

    def clone(self):
        return copy.deepcopy(self)

    def legal_actions(self):
        if self.finished:
            return []
        return [Action("PLAY", c.entity_id) for c in self.players[0].hand]

    def step(self, action):
        if action not in self.legal_actions():
            raise ValueError("illegal toy action")
        self.players[0].hand = [c for c in self.players[0].hand if c.entity_id != action.source]
        if action.source == 1:
            self.revealed = True
        else:
            self.finished = True
            self.winner = 0 if action.source == 4 or action.source - 2 == self.bit else 1

    def observation(self, observer):
        hand = [{"id": c.card_id, "entity": c.entity_id} for c in self.players[0].hand]
        if self.revealed:
            hand.append({"id": f"TEST_VISIBLE_BIT_{self.bit}", "entity": 100})
        return {"players": [{"player": 0, "hand": hand}, {"player": 1, "hand": []}],
                "pending_choice": None}


class BitBelief:
    deck_hypotheses = ()
    unresolved_hidden_slots = 1

    def sample_determinization(self, game, *, seed, record_event=False):
        sample = game.clone()
        # The actual hidden bit is never consulted before its public reveal.
        sample.bit = game.bit if game.revealed else random.Random(seed).randrange(2)
        return sample


class ZeroValueModel:
    name = "toy-uniform-zero-value"

    def predict(self, game, actions):
        weights = [9. if a.source == 4 else 1. for a in actions]
        return PolicyValueOutput(tuple(w / sum(weights) for w in weights), 0.)


class InformationDecisionTests(unittest.TestCase):
    def search(self, game, seed=77, **overrides):
        options = dict(
            samples=1, iterations_per_sample=512, tree_depth=3, rollout_depth=0,
            policy_value_model=ZeroValueModel(), tactical_precheck=False,
            min_simulations_per_root_action=16, seed=seed,
        )
        options.update(overrides)
        policy = InformationSetMCTSPolicy(**options)
        with patch("hsa.belief.PublicBelief.from_game", return_value=BitBelief()):
            action = policy.choose(game)
        return action, policy.last_search

    def test_outcome_coverage_samples_both_revealed_continuations(self):
        action, diagnostics = self.search(BitGame(), min_visits_per_root_outcome=8,
                                          collect_plan_diagnostics=True)
        self.assertEqual(1, action.source)
        self.assertTrue(diagnostics["root_outcome_coverage_complete"])
        revealed = diagnostics["root_action_stats"][0]
        self.assertEqual(2, revealed["observed_outcome_groups"])
        self.assertGreaterEqual(min(revealed["observed_outcome_visit_counts"]), 8)
        self.assertEqual("chance_candidates_outcome_coverage_v6", diagnostics["search_rules_version"])
        followups = revealed["own_turn_followups"]
        self.assertEqual(2, len(followups))
        self.assertEqual({"TEST_BIT_ACTION_2", "TEST_BIT_ACTION_3"}, {
            node["top_actions"][0]["information_action_key"][1][2] for node in followups})

    def test_outcome_coverage_respects_budget_and_reports_shortfall(self):
        _, diagnostics = self.search(BitGame(), iterations_per_sample=4,
                                     max_total_iterations=4, min_visits_per_root_outcome=8)
        self.assertEqual(4, diagnostics["iterations"])
        self.assertFalse(diagnostics["root_outcome_coverage_complete"])
        with self.assertRaises(ValueError):
            InformationSetMCTSPolicy(min_visits_per_root_outcome=-1)
        with self.assertRaises(ValueError):
            InformationSetMCTSPolicy(tree_depth=1, min_visits_per_root_outcome=1)

    def test_forced_chance_coverage_is_not_a_vote_for_information_first(self):
        action, diagnostics = self.search(
            BitGame(safe=True), iterations_per_sample=32, max_total_iterations=32,
            min_simulations_per_root_action=0, min_visits_per_root_outcome=8,
        )
        self.assertEqual(4, action.source)
        self.assertGreater(diagnostics["coverage_forced_iterations"], 0)
        self.assertEqual("non_coverage_visits", diagnostics["root_policy_visit_basis"])
        stats = diagnostics["root_action_stats"]
        denominator = sum(s["selection_visits"] for s in stats)
        for row, probability in zip(stats, diagnostics["root_policy"], strict=True):
            self.assertEqual(row["visits"] - row["coverage_forced_visits"], row["selection_visits"])
            self.assertAlmostEqual(row["selection_visits"] / denominator, probability)

    def test_search_prefers_reveal_when_it_enables_correct_conditional_guess(self):
        game = BitGame()
        action, diagnostics = self.search(game)
        self.assertEqual(1, action.source)
        self.assertGreaterEqual(diagnostics["outcome_branches"], 2)
        for stats in diagnostics["root_action_stats"]:
            for field in ("tree_depth_counts", "turn_delta_counts", "rollout_step_counts", "value_source_counts"):
                self.assertEqual(stats["visits"], sum(stats[field].values()))
            self.assertTrue(all(1 <= depth <= 3 for depth in stats["tree_depth_counts"]))
        self.assertFalse(game.revealed)
        self.assertFalse(game.finished)

    def test_replans_differently_for_each_actual_observed_outcome(self):
        for bit in (0, 1):
            game = BitGame(bit)
            game.step(Action("PLAY", 1))
            action, _ = self.search(game)
            self.assertEqual(bit + 2, action.source)
            game.step(action)
        self.assertEqual(0, game.winner)

    def test_unknown_actual_bit_cannot_change_search_before_reveal(self):
        a, da = self.search(BitGame(0))
        b, db = self.search(BitGame(1))
        self.assertEqual(a, b)
        self.assertEqual(da, db)

    def test_known_winning_alternative_need_not_reveal_information_first(self):
        action, _ = self.search(BitGame(safe=True))
        self.assertEqual(4, action.source)


if __name__ == "__main__":
    unittest.main()
