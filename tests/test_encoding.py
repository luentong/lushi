from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from hsa import DragonMirrorGame
from hsa.dragon_mirror import Action
from hsa.encoding import (
    CARD_SEMANTIC_FEATURE_SIZE, CARD_TEXT_EFFECT_PATTERNS,
    card_semantic_features, encode_action,
    encode_decision, encode_state, feature_schema,
)
from hsa.policy_value import HeuristicPolicyValueModel
from convert_policy_dataset_schema import v4_action_to_v3


CARDS = ROOT / "cards.251332.enUS.json"


class EncodingTests(unittest.TestCase):
    def test_state_encoding_does_not_read_opponent_hidden_identity(self):
        first = DragonMirrorGame(CARDS, 301)
        second = first.clone(include_history=True)
        second.players[1].hand[0] = second._entity("CORE_CS2_065")
        self.assertEqual(encode_state(first, 0), encode_state(second, 0))

    def test_state_and_action_sizes_match_versioned_schema(self):
        game = DragonMirrorGame(CARDS, 303)
        decision = encode_decision(game)
        schema = feature_schema()
        self.assertEqual(schema["state_size"], len(decision.state))
        self.assertTrue(decision.actions)
        self.assertTrue(all(
            len(action) == schema["action_size"] for action in decision.actions
        ))
        self.assertEqual(7, schema["schema_version"])
        self.assertEqual(42, schema["entity_card_slot_count"])
        self.assertEqual(867, len(encode_state(game, schema_version=1)))
        self.assertEqual(1217, len(encode_state(game, schema_version=2)))
        self.assertEqual(1217, len(encode_state(game, schema_version=3)))
        self.assertEqual(1217, len(encode_state(game, schema_version=4)))
        self.assertEqual(1500, feature_schema(5)["state_size"])
        self.assertEqual(618, feature_schema(5)["action_size"])
        self.assertEqual(
            1500 + 4 * CARD_SEMANTIC_FEATURE_SIZE + 42,
            schema["state_size"],
        )
        self.assertEqual(618 + 2 * CARD_SEMANTIC_FEATURE_SIZE, schema["action_size"])
        self.assertEqual(
            feature_schema(6)["state_size"],
            len(encode_state(game, schema_version=6)),
        )
        self.assertEqual(2 * CARD_SEMANTIC_FEATURE_SIZE,
                         schema["action_size"] - feature_schema(5)["action_size"])
        self.assertEqual(
            feature_schema(3)["action_size"] + 6,
            feature_schema(4)["action_size"],
        )

    def test_v5_encodes_turn_damage_progress_but_preserves_v4(self):
        first = DragonMirrorGame(CARDS, 30301)
        first.current = 0
        second = first.clone(include_history=True)
        second.players[0].damaged_characters_this_turn = {
            "hero:0", "minion:101", "minion:102",
        }

        self.assertEqual(
            encode_state(first, 0, schema_version=4),
            encode_state(second, 0, schema_version=4),
        )
        self.assertNotEqual(encode_state(first, 0), encode_state(second, 0))

    def test_v6_semantics_encode_cards_outside_frozen_identity_vocab(self):
        game = DragonMirrorGame(CARDS, 30303)
        self.assertIn("JAIL_421", game.card_defs)
        semantic = card_semantic_features(game.card_defs["JAIL_421"])
        self.assertEqual(CARD_SEMANTIC_FEATURE_SIZE, len(semantic))
        self.assertGreater(sum(semantic), 0.0)
        altered = game.clone(include_history=True)
        altered.players[altered.current].hand[0] = altered._entity("JAIL_421")
        self.assertNotEqual(encode_state(game, schema_version=6),
                            encode_state(altered, schema_version=6))

    def test_v6_text_effect_features_distinguish_effect_families(self):
        features = card_semantic_features({
            "type": "SPELL", "cardClass": "MAGE", "cost": 3,
            "attack": 0, "health": 0, "rarity": "COMMON",
            "text": "Deal 3 damage to a random enemy minion.\nSummon a 1/1.",
        })
        self.assertEqual(CARD_SEMANTIC_FEATURE_SIZE, len(features))
        # The original metadata dimensions are retained as a stable prefix;
        # effect families are appended, so older learned semantics stay aligned.
        metadata_width = CARD_SEMANTIC_FEATURE_SIZE - len(CARD_TEXT_EFFECT_PATTERNS)
        self.assertEqual(90, metadata_width)
        effect = features[metadata_width:]
        self.assertEqual(1.0, effect[0])  # damage
        self.assertEqual(1.0, effect[3])  # summon
        random_index = CARD_TEXT_EFFECT_PATTERNS.index(r"\brandom(?:ly)?\b")
        self.assertEqual(1.0, effect[random_index])

    def test_v6_action_has_id_independent_source_and_target_semantics(self):
        game = DragonMirrorGame(CARDS, 30304)
        source = game._entity("JAIL_421")
        target = game._entity("CORE_CS2_231")
        game.players[game.current].hand.append(source)
        game.players[1 - game.current].board.append(target)
        action = Action("PLAY", source=source.entity_id, target_entity=target.entity_id)
        encoded = encode_action(game, action, schema_version=6)
        old = encode_action(game, action, schema_version=5)
        self.assertEqual(len(encoded) - len(old), 2 * CARD_SEMANTIC_FEATURE_SIZE)
        self.assertGreater(sum(encoded[-2 * CARD_SEMANTIC_FEATURE_SIZE:]), 0.0)

    def test_v5_exposes_own_remaining_deck_not_opponent_deck(self):
        first = DragonMirrorGame(CARDS, 30302)
        second = first.clone(include_history=True)
        self.assertTrue(first.players[0].deck)
        second.players[0].deck[0] = second._entity("JAIL_421")
        self.assertEqual(
            encode_state(first, 0, schema_version=4),
            encode_state(second, 0, schema_version=4),
        )
        self.assertNotEqual(encode_state(first, 0), encode_state(second, 0))

        hidden_variant = first.clone(include_history=True)
        self.assertTrue(hidden_variant.players[1].deck)
        hidden_variant.players[1].deck[0] = hidden_variant._entity("JAIL_421")
        self.assertEqual(encode_state(first, 0), encode_state(hidden_variant, 0))

    def test_v3_action_players_are_relative_to_the_actor(self):
        game = DragonMirrorGame(CARDS, 3031)
        game.current = 0
        first = encode_action(
            game, Action("HERO_ATTACK", target_player=1), schema_version=3
        )
        first_legacy = encode_action(
            game, Action("HERO_ATTACK", target_player=1), schema_version=2
        )
        game.current = 1
        second = encode_action(
            game, Action("HERO_ATTACK", target_player=0), schema_version=3
        )
        second_legacy = encode_action(
            game, Action("HERO_ATTACK", target_player=0), schema_version=2
        )
        self.assertEqual(first, second)
        self.assertNotEqual(first_legacy, second_legacy)

    def test_v4_action_identifies_target_zone(self):
        game = DragonMirrorGame(CARDS, 3032)
        own = game.players[game.current]
        hand_action = Action("PLAY", target_entity=own.hand[0].entity_id)
        board_card = game._entity(own.hand[0].card_id)
        own.board.append(board_card)
        board_action = Action("PLAY", target_entity=board_card.entity_id)
        self.assertEqual(
            encode_action(game, hand_action, schema_version=3),
            encode_action(game, board_action, schema_version=3),
        )
        self.assertNotEqual(
            encode_action(game, hand_action, schema_version=4),
            encode_action(game, board_action, schema_version=4),
        )

    def test_v4_to_v3_dataset_conversion_only_drops_target_zone(self):
        game = DragonMirrorGame(CARDS, 3033)
        own = game.players[game.current]
        target = game._entity(own.hand[0].card_id)
        own.board.append(target)
        action = Action("PLAY", own.hand[0].entity_id, game.current, target.entity_id)
        encoded_v4 = encode_action(game, action, schema_version=4)
        encoded_v3 = encode_action(game, action, schema_version=3)
        self.assertEqual(list(encoded_v3), v4_action_to_v3(list(encoded_v4)))

    def test_v2_observes_temporary_hero_attack_missing_from_v1(self):
        first = DragonMirrorGame(CARDS, 304)
        second = first.clone(include_history=True)
        second.players[second.current].hero_attack_bonus = 3
        self.assertEqual(
            encode_state(first, schema_version=1),
            encode_state(second, schema_version=1),
        )
        self.assertNotEqual(encode_state(first), encode_state(second))

    def test_legal_action_encodings_are_distinct(self):
        game = DragonMirrorGame(CARDS, 305)
        decision = encode_decision(game)
        self.assertEqual(len(decision.actions), len(set(decision.actions)))

    def test_heuristic_policy_value_output_is_normalized_and_bounded(self):
        game = DragonMirrorGame(CARDS, 307)
        legal = game.legal_actions()
        output = HeuristicPolicyValueModel().predict(game, legal)
        self.assertAlmostEqual(1.0, sum(output.priors))
        self.assertEqual(len(legal), len(output.priors))
        self.assertLessEqual(abs(output.value), 1.0)


if __name__ == "__main__":
    unittest.main()
