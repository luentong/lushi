from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import Action, DragonMirrorGame, Weapon


CARDS = ROOT / "cards.251332.enUS.json"


class FirstStandardCardBatchTests(unittest.TestCase):
    def game(self) -> DragonMirrorGame:
        game = DragonMirrorGame(CARDS, 29)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    def add_hand(self, game: DragonMirrorGame, card_id: str):
        card = game._entity(card_id)
        game.players[0].hand.append(card)
        return card

    def add_board(
        self, game: DragonMirrorGame, card_id: str, player: int, *, attack=0
    ):
        card = game._entity(card_id)
        card.summoned_turn = game.turn - 1
        card.attack_delta += attack
        game.players[player].board.append(card)
        return card

    def test_power_word_shield(self):
        game = self.game()
        target = self.add_board(game, "CAP_107t", 0)
        spell = self.add_hand(game, "CORE_CS2_004")
        before_hand = len(game.players[0].hand)
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertEqual(3, target.max_health)
        self.assertEqual(before_hand, len(game.players[0].hand))

    def test_hellfire_damages_all_characters(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_CS2_065", 0)
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        enemy_health = enemy.health
        spell = self.add_hand(game, "CORE_CS2_062")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual((27, 27), (
            game.players[0].health, game.players[1].health
        ))
        self.assertNotIn(friendly, game.players[0].board)
        self.assertEqual(enemy_health - 3, enemy.health)

    def test_shadow_word_ruin_uses_current_attack(self):
        game = self.game()
        small = self.add_board(game, "CAP_107t", 0, attack=3)
        large = self.add_board(game, "CAP_107t", 1, attack=4)
        spell = self.add_hand(game, "CORE_EX1_197")
        game.step(Action("PLAY", spell.entity_id))
        self.assertIn(small, game.players[0].board)
        self.assertNotIn(large, game.players[1].board)

    def test_drain_soul_has_lifesteal_and_requires_a_minion(self):
        game = self.game()
        game.players[0].health = 20
        target = self.add_board(game, "CORE_LOOT_137", 1)
        target_health = target.health
        spell = self.add_hand(game, "CORE_ICC_055")
        legal = game.legal_actions()
        self.assertNotIn(
            Action("PLAY", spell.entity_id, 1, None), legal
        )
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertEqual(23, game.players[0].health)
        self.assertEqual(target_health - 3, target.health)

    def test_spell_targeting_respects_enemy_stealth_and_elusive(self):
        game = self.game()
        friendly = self.add_board(game, "CAP_107t", 0)
        stealth = self.add_board(game, "CORE_EX1_010", 1)
        elusive = self.add_board(game, "CORE_NEW1_023", 1)
        spell = self.add_hand(game, "CORE_CS2_004")
        targets = {
            (action.target_player, action.target_entity)
            for action in game.legal_actions()
            if action.kind == "PLAY" and action.source == spell.entity_id
        }
        self.assertIn((0, friendly.entity_id), targets)
        self.assertNotIn((1, stealth.entity_id), targets)
        self.assertNotIn((1, elusive.entity_id), targets)

    def test_rustrot_viper_destroys_opposing_weapon(self):
        game = self.game()
        game.players[1].weapon = Weapon("CS2_082", "Wicked Knife", 1, 2)
        viper = self.add_hand(game, "CORE_SW_072")
        game.step(Action("PLAY", viper.entity_id))
        self.assertIsNone(game.players[1].weapon)

    def test_temporary_mana_spells(self):
        for card_id in ("CORE_EX1_169", "TLC_COIN1"):
            with self.subTest(card_id=card_id):
                game = self.game()
                game.players[0].mana = 0
                spell = self.add_hand(game, card_id)
                game.step(Action("PLAY", spell.entity_id))
                self.assertEqual(1, game.players[0].mana)

    def test_forest_gift_scales_with_friendly_board(self):
        game = self.game()
        target = self.add_board(game, "CAP_107t", 0)
        self.add_board(game, "CORE_CS2_065", 0)
        attack, health = target.attack, target.max_health
        spell = self.add_hand(game, "CATA_138")
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertEqual(attack + 2, target.attack)
        self.assertEqual(health + 2, target.max_health)

    def test_panther_mask_sets_stats_stealth_and_draws(self):
        game = self.game()
        target = self.add_board(game, "CORE_CS2_065", 1)
        spell = self.add_hand(game, "DINO_432")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertEqual((5, 4, True), (
            target.attack, target.max_health, target.stealth,
        ))
        self.assertEqual(2, len(game.players[0].hand))

    def test_corrupted_dream_shuffles_without_death(self):
        game = self.game()
        target = self.add_board(game, "CORE_CS2_065", 1)
        deck_size = len(game.players[1].deck)
        spell = self.add_hand(game, "EDR_846t2")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertEqual(deck_size + 1, len(game.players[1].deck))
        self.assertFalse(any(
            event["kind"] == "death" and event.get("entity") == target.entity_id
            for event in game.events
        ))

    def test_corrupted_awakening_damages_only_enemies(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_LOOT_137", 0)
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        friendly_health, enemy_health = friendly.health, enemy.health
        spell = self.add_hand(game, "EDR_846t4")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual((30, 25), (
            game.players[0].health, game.players[1].health,
        ))
        self.assertEqual(friendly_health, friendly.health)
        self.assertEqual(enemy_health - 5, enemy.health)

    def test_press_the_advantage_all_effects(self):
        game = self.game()
        spell = self.add_hand(game, "END_007")
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(29, game.players[1].health)
        self.assertEqual(1, game.players[0].hero_attack_bonus)
        self.assertEqual(1, game.players[0].armor)
        self.assertEqual(1, len(game.players[0].hand))

    def test_feral_rage_choose_one(self):
        attack_game = self.game()
        spell = self.add_hand(attack_game, "CORE_OG_047")
        attack_game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(
            ["hero_attack_4", "armor_8"],
            attack_game.snapshot()["pending_choice"]["options"],
        )
        attack_game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(4, attack_game.players[0].hero_attack_bonus)
        self.assertEqual(0, attack_game.players[0].armor)

        armor_game = self.game()
        spell = self.add_hand(armor_game, "CORE_OG_047")
        armor_game.step(Action("PLAY", spell.entity_id))
        armor_game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual(0, armor_game.players[0].hero_attack_bonus)
        self.assertEqual(8, armor_game.players[0].armor)

    def test_felwood_treant_tracks_mana_spent_while_held(self):
        permanent = self.game()
        permanent.players[0].max_mana = 5
        treant = self.add_hand(permanent, "CATA_131")
        expensive = self.add_hand(permanent, "CORE_LOOT_137")
        permanent.step(Action("PLAY", expensive.entity_id))
        self.assertGreaterEqual(treant.mana_spent_while_held, 4)
        permanent.step(Action("PLAY", treant.entity_id))
        self.assertEqual(6, permanent.players[0].max_mana)

        temporary = self.game()
        temporary.players[0].max_mana = 5
        treant = self.add_hand(temporary, "CATA_131")
        temporary.step(Action("PLAY", treant.entity_id))
        self.assertEqual(5, temporary.players[0].max_mana)

    def test_ebb_and_flow_tracks_minion_played_while_held(self):
        game = self.game()
        spell = self.add_hand(game, "TIME_702")
        minion = self.add_hand(game, "CORE_CS2_065")
        game.step(Action("PLAY", minion.entity_id))
        self.assertTrue(spell.minion_played_while_held)
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(27, game.players[1].health)
        self.assertEqual(5, game.players[0].armor)

    def test_declarative_spell_damage_is_applied(self):
        game = self.game()
        self.add_board(game, "CORE_EX1_012", 0)
        spell = self.add_hand(game, "END_007")
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(28, game.players[1].health)


if __name__ == "__main__":
    unittest.main()
