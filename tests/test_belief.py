from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa import DragonMirrorGame, PublicBelief
from hsa.dragon_mirror import DRAGON_IDS, SPECIAL_TOKEN_IDS


CARDS = ROOT / "cards.251332.enUS.json"


class PublicBeliefTests(unittest.TestCase):
    def test_initial_belief_ignores_private_deal_and_mulligan_identities(self):
        first = PublicBelief.from_game(DragonMirrorGame(CARDS, 201), 0)
        second = PublicBelief.from_game(DragonMirrorGame(CARDS, 203), 0)
        self.assertEqual(first.starting_cards_remaining, second.starting_cards_remaining)
        self.assertEqual(
            31,
            sum(first.starting_cards_remaining.values())
            + sum(first.known_extra_cards.values()),
        )
        self.assertTrue(first.known_coin_in_hand)
        self.assertEqual(0, first.unresolved_hidden_slots)

    def test_public_started_card_play_removes_one_candidate(self):
        game = DragonMirrorGame(CARDS, 205)
        card = game._entity("CATA_556", started_in_deck=True)
        game.players[1].hand.append(card)
        game._event(
            "play", player=1, card=card.card_id, entity=card.entity_id,
            controller=1, started_in_deck=True,
        )
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual(1, belief.starting_cards_remaining["CATA_556"])

    def test_unknown_generated_hidden_card_becomes_unresolved_slot(self):
        game = DragonMirrorGame(CARDS, 207)
        game.players[1].hand.append(
            game._entity("CORE_CS2_065", created_by="TEST")
        )
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual(1, belief.unresolved_hidden_slots)
        self.assertNotIn("CORE_CS2_065", str(belief.as_dict()))

    def test_unknown_fallback_never_samples_special_tokens(self):
        game = DragonMirrorGame(CARDS, 208)
        game.players[1].hand.append(
            game._entity("CORE_CS2_065", created_by="TEST")
        )
        belief = PublicBelief.from_game(game, 0)
        for seed in range(200):
            sampled = belief.sample_determinization(game, seed=seed)
            unknown = [
                card for card in sampled.players[1].hand + sampled.players[1].deck
                if card.created_by == "UNKNOWN_PUBLIC_GENERATOR"
            ]
            self.assertTrue(unknown)
            self.assertFalse({card.card_id for card in unknown} & SPECIAL_TOKEN_IDS)

    def test_deterministic_generation_creates_a_known_candidate_slot(self):
        game = DragonMirrorGame(CARDS, 209)
        card = game._entity("CAP_107t", created_by="CAP_107")
        game.players[1].hand.append(card)
        game._event(
            "generated_to_hand", player=1, card=card.card_id,
            entity=card.entity_id, source="CAP_107",
        )
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual(0, belief.unresolved_hidden_slots)
        self.assertEqual(("CAP_107t",), belief.generated_cards[0].candidates)

    def test_discover_belief_uses_source_pool_not_private_pick(self):
        beliefs = []
        for seed, picked in ((211, "TLC_600"), (213, "TIME_034")):
            game = DragonMirrorGame(CARDS, seed)
            card = game._entity(picked, created_by="EDR_456")
            game.players[1].hand.append(card)
            game._event(
                "discover_pick", player=1, card=picked,
                entity=card.entity_id, source="EDR_456", destination="hand",
            )
            beliefs.append(PublicBelief.from_game(game, 0))
        self.assertEqual(beliefs[0].as_dict(), beliefs[1].as_dict())
        self.assertEqual(
            tuple(sorted(DRAGON_IDS)), beliefs[0].generated_cards[0].candidates
        )

    def test_public_play_consumes_the_matching_generated_slot(self):
        game = DragonMirrorGame(CARDS, 215)
        card = game._entity("CAP_107t", created_by="CAP_107")
        game._event(
            "generated_to_hand", player=1, card=card.card_id,
            entity=card.entity_id, source="CAP_107",
        )
        game._event(
            "play", player=1, card=card.card_id, entity=card.entity_id,
            controller=1, started_in_deck=False, created_by="CAP_107",
        )
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual((), belief.generated_cards)
        self.assertEqual(0, belief.unresolved_hidden_slots)

    def test_public_sampler_does_not_depend_on_true_opponent_cards(self):
        first = DragonMirrorGame(CARDS, 217)
        second = first.clone(include_history=True)
        second.players[1].hand[0] = second._entity("CORE_CS2_065")
        first_sample = PublicBelief.from_game(first, 0).sample_determinization(
            first, seed=99
        )
        second_sample = PublicBelief.from_game(second, 0).sample_determinization(
            second, seed=99
        )
        first_ids = [c.card_id for c in first_sample.players[1].hand]
        second_ids = [c.card_id for c in second_sample.players[1].hand]
        self.assertEqual(first_ids, second_ids)
        self.assertEqual(
            [c.card_id for c in first_sample.players[1].deck],
            [c.card_id for c in second_sample.players[1].deck],
        )

    def test_public_burn_removes_a_starting_deck_candidate(self):
        game = DragonMirrorGame(CARDS, 219)
        card = next(
            c for c in game.players[1].hand + game.players[1].deck
            if c.card_id == "CATA_556"
        )
        zone = game.players[1].hand if card in game.players[1].hand else game.players[1].deck
        zone.remove(card)
        game._event(
            "burn", player=1, card=card.card_id, entity=card.entity_id,
            started_in_deck=True, created_by=None,
        )
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual(1, belief.starting_cards_remaining["CATA_556"])
        self.assertEqual(0, belief.unresolved_hidden_slots)

    def test_random_pirate_generation_tracks_pool_without_pick_identity(self):
        beliefs = []
        for seed, picked in ((221, "CAP_104"), (223, "CAP_107")):
            game = DragonMirrorGame(CARDS, seed)
            card = game._entity(picked, created_by="CORE_DRG_024")
            game.players[1].hand.append(card)
            game._event(
                "generated_from_pool", player=1, card=picked,
                entity=card.entity_id, source="CORE_DRG_024",
                destination="hand",
            )
            beliefs.append(PublicBelief.from_game(game, 0))
        self.assertEqual(beliefs[0].as_dict(), beliefs[1].as_dict())
        self.assertGreater(len(beliefs[0].generated_cards[0].candidates), 1)

    def test_returned_spell_becomes_a_generated_hidden_slot(self):
        game = DragonMirrorGame(CARDS, 225)
        card = next(
            c for c in game.players[1].hand + game.players[1].deck
            if c.card_id == "CATA_585"
        )
        zone = game.players[1].hand if card in game.players[1].hand else game.players[1].deck
        zone.remove(card)
        game._event(
            "play", player=1, card=card.card_id, entity=card.entity_id,
            controller=1, started_in_deck=True, created_by=None,
        )
        card.started_in_deck = False
        card.created_by = card.card_id
        game.players[1].hand.append(card)
        game._event(
            "returned_to_hand", player=1, card=card.card_id,
            entity=card.entity_id, source=card.card_id, destination="hand",
        )
        belief = PublicBelief.from_game(game, 0)
        self.assertEqual(("CATA_585",), belief.generated_cards[0].candidates)
        self.assertEqual(0, belief.unresolved_hidden_slots)

    def test_hand_buff_sampling_uses_aggregate_count_not_private_entities(self):
        beliefs = []
        for affected in ([9001, 9002], [42, 84]):
            game = DragonMirrorGame(CARDS, 227)
            game._event(
                "zone_buff", player=1, source="END_021", zone="hand",
                attack=2, health=0, card_types=["MINION"],
                require_attribute=None, affected_count=2, affected=affected,
            )
            beliefs.append(PublicBelief.from_game(game, 0))
        self.assertEqual(beliefs[0].as_dict(), beliefs[1].as_dict())
        sampled = beliefs[0].sample_determinization(game, seed=101)
        buffed = [
            card for card in sampled.players[1].hand
            if card.definition.card_type == "MINION" and card.attack_delta == 2
        ]
        eligible = [
            card for card in sampled.players[1].hand
            if card.definition.card_type == "MINION"
        ]
        self.assertEqual(min(2, len(eligible)), len(buffed))

    def test_void_soul_determinization_preserves_public_cost(self):
        game = DragonMirrorGame(CARDS, 229)
        game._event(
            "void_soul_generated", player=1, card="JAIL_732",
            entity=9001, source="JAIL_730", destination="hand", cost=3,
        )
        game.players[1].hand.append(
            game._entity("JAIL_732", created_by="JAIL_730")
        )
        game.players[1].hand[-1].void_soul_cost = 3
        belief = PublicBelief.from_game(game, 0)
        soul_slots = [
            slot for slot in belief.generated_cards
            if slot.source_card_id == "JAIL_730"
        ]
        self.assertEqual(3, soul_slots[0].void_soul_cost)
        sampled = belief.sample_determinization(game, seed=103)
        souls = [
            card for card in sampled.players[1].hand + sampled.players[1].deck
            if card.card_id == "JAIL_732"
        ]
        self.assertTrue(souls)
        self.assertTrue(all(card.void_soul_cost == 3 for card in souls))


if __name__ == "__main__":
    unittest.main()
