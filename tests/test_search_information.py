"""Information-boundary regressions: changing hidden truth cannot guide search."""
from __future__ import annotations

import copy
import json
import random
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from hsa import DragonMirrorGame, PublicBelief, InformationSetMCTSPolicy
from hsa.dragon_mirror import DRAGON_DECK_COUNTS, Action
from hsa.search_deck import SearchDeck
from hsa.mcts import _InformationNode
from hsa.standard_catalog import STANDARD_SETS_BUILD_251332
from generate_policy_value_data import independent_conditional_targets

CARDS = ROOT / "cards.251332.enUS.json"


class SearchInformationTests(unittest.TestCase):
    def game(self):
        return DragonMirrorGame(CARDS, 202609260501)

    def test_prior_temperature_is_normalized_and_default_is_unchanged(self):
        base = InformationSetMCTSPolicy()
        flat = InformationSetMCTSPolicy(prior_temperature=2.0)
        sharp = InformationSetMCTSPolicy(prior_temperature=0.5)
        self.assertEqual([0.8, 0.2], base._calibrate_priors([0.8, 0.2]))
        self.assertAlmostEqual(2.0 / 3.0, flat._calibrate_priors([0.8, 0.2])[0])
        self.assertAlmostEqual(16.0 / 17.0, sharp._calibrate_priors([0.8, 0.2])[0])
        self.assertEqual([0.5, 0.5], flat._calibrate_priors([0.0, 0.0]))

    def test_prior_temperature_rejects_invalid_values(self):
        for temperature in (0.0, -1.0, float("inf"), float("nan")):
            with self.subTest(temperature=temperature):
                with self.assertRaises(ValueError):
                    InformationSetMCTSPolicy(prior_temperature=temperature)

    def test_uniform_prior_mixture_is_normalized_and_optional(self):
        base = InformationSetMCTSPolicy()
        mixed = InformationSetMCTSPolicy(prior_uniform_mix=0.5)
        self.assertEqual([0.8, 0.2], base._calibrate_priors([0.8, 0.2]))
        self.assertEqual([0.65, 0.35], mixed._calibrate_priors([0.8, 0.2]))
        self.assertEqual([0.5, 0.5], InformationSetMCTSPolicy(
            prior_uniform_mix=1.0
        )._calibrate_priors([0.8, 0.2]))

    def test_uniform_prior_mixture_rejects_invalid_values(self):
        for mixture in (-0.01, 1.01, float("inf"), float("nan")):
            with self.subTest(mixture=mixture):
                with self.assertRaises(ValueError):
                    InformationSetMCTSPolicy(prior_uniform_mix=mixture)

    def test_conditional_root_action_label_tolerates_unmapped_choice_key(self):
        game = self.game()
        policy = InformationSetMCTSPolicy()
        path = [
            _InformationNode(),
            _InformationNode(action_key=("RULE_CHOICE_PICK", ("literal", 5), ("none",))),
        ]
        label = policy._conditional_root_action_label(game, {}, path)
        self.assertIn("unmapped root action", label)
        self.assertIn("RULE_CHOICE_PICK", label)

    def test_future_rng_is_independent_reproducible_and_root_safe(self):
        game = self.game()
        before = game.rng.getstate()
        belief = PublicBelief.from_game(game, 0)
        samples = [belief.sample_determinization(game, seed=s) for s in range(24)]
        self.assertEqual(before, game.rng.getstate())
        self.assertTrue(all(s.rng.getstate() != before for s in samples))
        self.assertEqual(24, len({s.rng.random() for s in samples}))
        a = belief.sample_determinization(game, seed=42)
        b = belief.sample_determinization(game, seed=42)
        self.assertEqual(a.rng.getstate(), b.rng.getstate())

    def test_carrier_whelp_samples_multiple_real_generation_outcomes(self):
        game = self.game()
        game.players[0].hand = [game._entity("CATA_556")]
        game.players[0].mana = 2
        belief = PublicBelief.from_game(game, 0)
        outcomes = set()
        for seed in range(24):
            branch = belief.sample_determinization(game, seed=seed)
            branch.step(Action("PLAY", branch.players[0].hand[0].entity_id))
            outcomes.add(branch.players[0].hand[-1].card_id)
        self.assertGreater(len(outcomes), 1)

    def test_conditional_collector_keeps_runtime_states_out_of_search_report(self):
        game = self.game()
        game.players[0].hand = [game._entity("CATA_556")]
        game.players[0].mana = 4
        before = game.snapshot()
        policy = InformationSetMCTSPolicy(
            samples=1,
            iterations_per_sample=32,
            tree_depth=3,
            rollout_depth=0,
            collect_conditional_training_examples=True,
            conditional_training_min_visits=1,
        )
        policy.choose(game)

        self.assertEqual(before, game.snapshot())
        self.assertTrue(policy.conditional_training_states)
        self.assertLessEqual(len(policy.conditional_training_states), 2)
        # Search diagnostics remain plain JSON even though the opt-in training
        # channel separately retains branch game objects for independent
        # belief-resampled continuation searches.
        json.dumps(policy.last_search)
        for branch in policy.conditional_training_states:
            self.assertEqual(0, branch["game"].current)
            self.assertIsNone(branch["game"].pending_choice)
        targets = independent_conditional_targets(
            policy,
            0,
            SimpleNamespace(
                conditional_training_max_branches=2,
                conditional_training_repeats=2,
                conditional_training_iterations=8,
                rollout_depth=0,
                search_seed=1234,
            ),
            seed=202609260501,
            ply=0,
        )
        self.assertTrue(targets)
        for target in targets:
            self.assertAlmostEqual(1.0, sum(target["policy_target"]))
            self.assertEqual(
                "independent_public_belief_search",
                target["conditional_target_source"],
            )
            self.assertGreaterEqual(
                target["conditional_target_top_action_agreement"], 0.5
            )
            self.assertGreaterEqual(target["conditional_target_entropy"], 0.0)
            self.assertGreaterEqual(target["conditional_target_mean_value_std"], 0.0)

    def test_conditional_collector_covers_random_outcomes_after_prior_actions(self):
        game = self.game()
        game.players[0].hand = [game._entity("CATA_556"), game._entity("CAP_107")]
        game.players[0].mana = 4
        policy = InformationSetMCTSPolicy(
            samples=1,
            iterations_per_sample=128,
            tree_depth=5,
            rollout_depth=0,
            min_simulations_per_root_action=8,
            min_visits_per_observed_action=1,
            collect_conditional_training_examples=True,
            conditional_training_min_visits=1,
            conditional_training_max_branches=32,
        )
        policy.choose(game)

        examples = policy.last_search["conditional_training_examples"]
        self.assertTrue(examples)
        # The fixture can search Cannonmaster -> Carrier Whelp, so at least
        # one public reveal must be represented below the root outcome layer.
        self.assertTrue(any(row["conditional_trigger_depth"] >= 2 for row in examples))
        self.assertTrue(any("PLAY Cannonmaster" in row["conditional_root_action"]
                            and row["conditional_trigger_depth"] >= 2
                            for row in examples))
        for row in examples:
            self.assertEqual(len(row["actions"]), len(row["policy_target"]))
            self.assertAlmostEqual(1.0, sum(row["policy_target"]))

    def test_hidden_own_order_and_rng_cannot_change_sample(self):
        a = self.game()
        b = a.clone(include_history=True)
        b.players[0].deck.reverse()
        b.rng.seed(999999)
        sa = PublicBelief.from_game(a, 0).sample_determinization(a, seed=12)
        sb = PublicBelief.from_game(b, 0).sample_determinization(b, seed=12)
        self.assertEqual([c.card_id for c in sa.players[0].deck],
                         [c.card_id for c in sb.players[0].deck])
        self.assertEqual(sa.rng.getstate(), sb.rng.getstate())
        self.assertEqual(Counter(c.card_id for c in a.players[0].deck),
                         Counter(c.card_id for c in sa.players[0].deck))

    def test_known_top_survives_search_and_is_next_actual_draw(self):
        game = self.game()
        card = game._entity("CATA_556")
        card.gifts.append("sweet_dreams")
        game._add_generated(game.players[0], card)
        belief = PublicBelief.from_game(game, 0)
        for seed in range(12):
            branch = belief.sample_determinization(game, seed=seed, record_event=False)
            self.assertEqual(card.entity_id, branch.players[0].deck[-1].entity_id)
            branch._draw(branch.players[0])
            self.assertEqual(card.entity_id, branch.players[0].hand[-1].entity_id)

    def test_deck_knowledge_copy_draw_and_shuffle_lifecycle(self):
        deck = SearchDeck(self.game().players[0].deck)
        deck.reveal(-1, (0,))
        deck.reveal(-2, (0,))
        clone = copy.deepcopy(deck)
        clone.pop()
        self.assertEqual(1, len(clone.known[0]))
        self.assertEqual(2, len(deck.known[0]))
        random.Random(12).shuffle(clone)
        self.assertEqual({}, clone.known)
        clone = copy.deepcopy(deck)
        clone[:] = list(reversed(clone))
        self.assertEqual({}, clone.known)

    def test_enemy_known_top_is_preserved_but_not_read_by_other_observer(self):
        game = self.game()
        top = game.players[1].deck[-1]
        game.players[1].deck.reveal(-1, (0,))
        belief = PublicBelief.from_game(game, 0)
        for seed in range(12):
            branch = belief.sample_determinization(game, seed=seed)
            self.assertEqual(top.entity_id, branch.players[1].deck[-1].entity_id)
        self.assertNotIn(1, game.players[1].deck.known)

    def test_custom_game_does_not_assume_a_fixed_dragon_list(self):
        deck = dict(DRAGON_DECK_COUNTS)
        game = DragonMirrorGame(CARDS, 31, deck_counts=(deck, deck))
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual({}, belief.starting_cards_remaining)
        self.assertEqual((), belief.deck_hypotheses)
        self.assertGreater(belief.unresolved_hidden_slots, 0)
        self.assertTrue(all(game.card_defs[c].card_set in STANDARD_SETS_BUILD_251332
                            for c in belief.fallback_pool))

    def test_unresolved_slots_do_not_count_union_of_exclusive_candidates(self):
        game = self.game()
        game.search_deck_hypotheses[0] = [(1., {"CAP_107": 15}), (1., {"CATA_556": 15})]
        belief = PublicBelief.from_game(game, 0)
        expected = (belief.opponent_hand_size + belief.opponent_deck_size - 15
                    - int(belief.known_coin_in_hand) - sum(belief.known_extra_cards.values()))
        self.assertEqual(expected, belief.unresolved_hidden_slots)

    def test_uct_exploration_depends_on_visits_not_just_availability(self):
        rare = _InformationNode(visits=1, availability=100)
        frequent = _InformationNode(visits=25, availability=100)
        bonus = InformationSetMCTSPolicy._uct_bonus
        self.assertAlmostEqual(bonus(rare), 5 * bonus(frequent))
        self.assertGreater(bonus(rare), bonus(_InformationNode(visits=1, availability=10)))

    def test_explicit_candidate_weights_and_public_elimination(self):
        game = self.game()
        game.search_deck_hypotheses[0] = [
            (0.8, {"CAP_107": 30}), (0.2, {"CATA_556": 30})]
        # Hidden truth and initial constructor deck do not enter the candidates.
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual(2, len(belief.deck_hypotheses))
        self.assertEqual([.8, .2], belief.as_dict()["candidate_weights"])
        game._event("play", player=1, card="CAP_107", started_in_deck=True)
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual(1, len(belief.deck_hypotheses))
        self.assertEqual({"CAP_107": 29}, belief.starting_cards_remaining)
        game._event("play", player=1, card="CATA_556", started_in_deck=True)
        self.assertEqual({}, PublicBelief.from_game(game, 0).starting_cards_remaining)

    def test_generated_public_play_does_not_eliminate_a_candidate(self):
        game = self.game()
        game.search_deck_hypotheses[0] = [(1.0, {"CAP_107": 30})]
        game._event("play", player=1, card="CATA_556", started_in_deck=False)
        self.assertEqual(1, len(PublicBelief.from_game(game, 0).deck_hypotheses))

    def test_invalid_candidate_weights_rejected(self):
        game = self.game()
        for weight in (0, -1, float("nan"), float("inf")):
            game.search_deck_hypotheses[0] = [(weight, {"CAP_107": 30})]
            with self.assertRaises(ValueError):
                PublicBelief.from_game(game, 0)

    def test_empty_opponent_hand_cannot_gain_a_stale_coin(self):
        game = self.game()
        game.players[1].hand = []
        game._event("coin_given", player=1)
        belief = PublicBelief.from_game(game, 0)
        self.assertFalse(belief.known_coin_in_hand)
        sample = belief.sample_determinization(game, seed=19)
        self.assertEqual([], sample.players[1].hand)
        self.assertEqual(len(game.players[1].deck), len(sample.players[1].deck))

    def test_search_cannot_read_true_future_rng_or_own_order(self):
        a = self.game()
        b = a.clone(include_history=True)
        b.rng.seed(424242)
        b.players[0].deck.reverse()
        pa = InformationSetMCTSPolicy(samples=1, iterations_per_sample=16, rollout_depth=2)
        pb = InformationSetMCTSPolicy(samples=1, iterations_per_sample=16, rollout_depth=2)
        self.assertEqual(pa.choose(a), pb.choose(b))
        self.assertEqual(pa.last_search, pb.last_search)

    def test_followup_keys_distinguish_visible_outcomes_not_hidden_truth(self):
        a = self.game()
        b = a.clone(include_history=True)
        b.players[1].hand[0] = b._entity("CATA_556")
        b.players[0].deck.reverse()
        key = InformationSetMCTSPolicy._observation_key
        self.assertEqual(key(a), key(b))
        b.players[0].hand.append(b._entity("CATA_556"))
        self.assertNotEqual(key(a), key(b))

    def test_opponent_turn_keys_do_not_split_on_sampled_private_hands(self):
        a = self.game(); a.current = 1
        b = a.clone(include_history=True)
        b.players[1].hand[0] = b._entity("CATA_556")
        key = InformationSetMCTSPolicy._observation_key
        self.assertEqual(key(a, 0), key(b, 0))

    def test_observation_keys_normalize_dataclass_card_references(self):
        a = self.game()
        b = a.clone(include_history=True)
        a.players[0].active_quests["TEST_REFERENCE"] = {
            "card": a.players[0].hand[0],
        }
        b.players[0].active_quests["TEST_REFERENCE"] = {
            "card": b.players[0].hand[0],
        }
        key = InformationSetMCTSPolicy._observation_key
        a_key = key(a)
        self.assertEqual(a_key, key(b))
        self.assertIn(a.players[0].hand[0].card_id, a_key)


if __name__ == "__main__":
    unittest.main()
