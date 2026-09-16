from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import (
    Action, DragonMirrorGame, Location, STANDARD_VANILLA_IDS, Weapon,
)


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

    def test_metadata_only_vanilla_standard_minions_use_normal_lifecycle(self):
        game = self.game()
        ogre = self.add_hand(game, "Core_CS2_200")
        giga = self.add_hand(game, "TLC_248")
        game.step(Action("PLAY", ogre.entity_id))
        game.step(Action("PLAY", giga.entity_id))
        self.assertIn(ogre, game.players[0].board)
        self.assertIn(giga, game.players[0].board)
        self.assertEqual((6, 7), (ogre.attack, ogre.max_health))
        self.assertEqual((14, 28), (giga.attack, giga.max_health))

    def test_all_standard_vanilla_entities_are_constructible_and_playable(self):
        # This is intentionally table-driven: adding another text-free token
        # to the tranche automatically exercises metadata loading and the
        # ordinary minion/weapon/location play path.
        for card_id in sorted(STANDARD_VANILLA_IDS):
            game = self.game()
            card = self.add_hand(game, card_id)
            game.step(Action("PLAY", card.entity_id))
            self.assertNotIn(card, game.players[0].hand, card_id)

    def test_simple_core_spell_tranche(self):
        game = self.game()
        game.players[0].health = 20
        friendly = self.add_board(game, "CAP_107t", 0)
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        heal = self.add_hand(game, "CORE_AT_055")
        game.step(Action("PLAY", heal.entity_id, 0, None))
        self.assertEqual(25, game.players[0].health)

        shot = self.add_hand(game, "CORE_DS1_185")
        game.step(Action("PLAY", shot.entity_id, 1, enemy.entity_id))
        self.assertEqual(2, enemy.damage)

        intellect = self.add_hand(game, "CORE_CS2_023")
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)] * 2
        game.step(Action("PLAY", intellect.entity_id))
        # The played spell leaves the hand, then draws two cards.
        self.assertEqual(2, len(game.players[0].hand))

        assassinate = self.add_hand(game, "CORE_CS2_076")
        game.step(Action("PLAY", assassinate.entity_id, 1, enemy.entity_id))
        self.assertNotIn(enemy, game.players[1].board)

    def test_standard_tracking_discover(self):
        game = self.game()
        deck_cards = [
            game._entity("CORE_EX1_007", started_in_deck=True),
            game._entity("CORE_CS2_033", started_in_deck=True),
            game._entity("CORE_EX1_391", started_in_deck=True),
        ]
        game.players[0].deck = deck_cards[:]
        tracking = self.add_hand(game, "CORE_DS1_184")

        game.step(Action("PLAY", tracking.entity_id))

        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("DECK_CARD_DISCOVER", game.pending_choice["kind"])
        options = list(game.pending_choice["options"])
        self.assertEqual(3, len(options))
        picked = options[0]
        game.step(Action("DISCOVER_PICK", picked.entity_id))

        self.assertIsNone(game.pending_choice)
        self.assertIn(picked, game.players[0].hand)
        self.assertEqual(2, len(game.players[0].deck))
        self.assertNotIn(picked, game.players[0].deck)
        self.assertEqual(
            {card.entity_id for card in game.players[0].deck},
            {card.entity_id for card in deck_cards[1:]}
            if picked is deck_cards[0]
            else {card.entity_id for card in deck_cards if card is not picked},
        )

    def test_standard_basic_direct_spells(self):
        game = self.game()
        game.players[1].health = 20
        strike = self.add_hand(game, "CORE_CS2_075")
        game.step(Action("PLAY", strike.entity_id))
        self.assertEqual(17, game.players[1].health)

        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True) for _ in range(4)
        ]
        sprint = self.add_hand(game, "CORE_CS2_077")
        game.step(Action("PLAY", sprint.entity_id))
        self.assertEqual(4, len(game.players[0].hand))

        game.players[0].health = 15
        light = self.add_hand(game, "CORE_CS2_089")
        game.step(Action("PLAY", light.entity_id))
        self.assertEqual(23, game.players[0].health)

    def test_standard_mana_spells(self):
        game = self.game()
        game.players[0].max_mana = 5
        game.players[0].mana = 5
        growth = self.add_hand(game, "CORE_CS2_013")
        game.step(Action("PLAY", growth.entity_id))
        self.assertEqual((6, 4), (game.players[0].max_mana, game.players[0].mana))

        game.players[0].max_mana = 8
        game.players[0].mana = 8
        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True) for _ in range(3)
        ]
        nourish = self.add_hand(game, "CORE_EX1_164")
        game.step(Action("PLAY", nourish.entity_id))
        self.assertEqual("RULE_CHOICE", game.pending_choice["kind"])
        game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual(3, len(game.players[0].hand))

    def test_standard_azure_drake_draw(self):
        game = self.game()
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        drake = self.add_hand(game, "CORE_EX1_284")
        game.step(Action("PLAY", drake.entity_id))
        self.assertIn(drake, game.players[0].board)
        self.assertEqual(1, len(game.players[0].hand))

    def test_a1_draw_and_discard_tranche(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True),
            game._entity("CORE_CS2_065", started_in_deck=True),
        ]
        chaos = self.add_hand(game, "CORE_BT_035")
        game.step(Action("PLAY", chaos.entity_id))
        self.assertEqual(2, game.players[0].hero_attack_bonus)
        self.assertGreaterEqual(len(game.players[0].hand), 1)

        target = self.add_board(game, "CAP_107t", 0)
        hand = self.add_hand(game, "CORE_BT_292")
        before = len(game.players[0].hand)
        game.step(Action("PLAY", hand.entity_id, 0, target.entity_id))
        self.assertEqual((3, 2), (target.attack, target.max_health))
        # The spell leaves hand and immediately replaces itself with one draw.
        self.assertEqual(before, len(game.players[0].hand))

        far = self.add_hand(game, "CORE_CS2_053")
        game.players[0].deck = [game._entity("CORE_CS2_065", started_in_deck=True)]
        game.step(Action("PLAY", far.entity_id))
        discounted = max(
            (card for card in game.players[0].hand if card.card_id == "CORE_CS2_065"),
            key=lambda card: card.entity_id,
        )
        self.assertEqual(-3, discounted.cost_delta)

        hoarder = self.add_hand(game, "CORE_EX1_096")
        game.step(Action("PLAY", hoarder.entity_id))
        game._damage_minion(0, hoarder, hoarder.max_health)
        game._resolve_deaths()
        self.assertGreaterEqual(len(game.players[0].hand), 1)

    def test_a2_damage_heal_tranche(self):
        game = self.game()
        game.players[0].health = 10
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        heal = self.add_hand(game, "CORE_CFM_604")
        game.step(Action("PLAY", heal.entity_id, 0, None))
        self.assertEqual(22, game.players[0].health)
        self.assertGreaterEqual(len(game.players[0].hand), 1)

        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        enemy.damage = enemy.max_health - 1
        coil = self.add_hand(game, "CORE_EX1_302")
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        game.step(Action("PLAY", coil.entity_id, 1, enemy.entity_id))
        self.assertNotIn(enemy, game.players[1].board)
        self.assertGreaterEqual(len(game.players[0].hand), 1)

        quick = self.add_hand(game, "CORE_BRM_013")
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        game.step(Action("PLAY", quick.entity_id, 1, None))
        self.assertEqual(27, game.players[1].health)

    def test_acolyte_of_pain_draws_after_nonlethal_damage(self):
        game = self.game()
        acolyte = self.add_board(game, "CORE_EX1_007", 0)
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        game._damage_minion(0, acolyte, 1)
        self.assertEqual(1, len(game.players[0].hand))

    def test_a1_undead_and_frost_draw_tranche(self):
        game = self.game()
        acolyte = self.add_board(game, "CORE_RLK_121", 0)
        undead = self.add_board(game, "CAP_800", 0)
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        game._damage_minion(0, undead, undead.max_health)
        game._resolve_deaths()
        self.assertEqual(1, len(game.players[0].hand))

        frost = self.add_hand(game, "RLK_511")
        game.players[0].deck = [game._entity("RLK_709", started_in_deck=True)]
        game.step(Action("PLAY", frost.entity_id))
        game._damage_minion(0, frost, frost.max_health)
        game._resolve_deaths()
        self.assertTrue(any(card.card_id == "RLK_709" for card in game.players[0].hand))

        winter = self.add_hand(game, "RLK_709")
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        game.step(Action("PLAY", winter.entity_id))
        self.assertEqual(28, game.players[1].health)

    def test_type_draw_tranche(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("CORE_CS2_065", started_in_deck=True),
            game._entity("CORE_AT_055", started_in_deck=True),
        ]
        spell = self.add_hand(game, "EDR_843a")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual("CORE_AT_055", game.players[0].hand[-1].card_id)
        minion = self.add_hand(game, "EDR_843b")
        game.step(Action("PLAY", minion.entity_id))
        self.assertTrue(any(card.card_id == "CORE_CS2_065" for card in game.players[0].hand))

        bulk = self.add_hand(game, "CAP_405t4")
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True) for _ in range(3)]
        game.step(Action("PLAY", bulk.entity_id))
        self.assertGreaterEqual(len(game.players[0].hand), 3)

    def test_draw_summon_tranche(self):
        game = self.game()
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True) for _ in range(4)]
        spell = self.add_hand(game, "EDR_817")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, len(game.players[0].board))

        crate = self.add_hand(game, "CAP_102")
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True) for _ in range(2)]
        game.step(Action("PLAY", crate.entity_id))
        self.assertEqual(4, len(game.players[0].board))

    def test_bottom_and_origin_draw_tranche(self):
        game = self.game()
        bottom = game._entity("GAME_005", started_in_deck=True)
        top = game._entity("CORE_AT_055", started_in_deck=True)
        game.players[0].deck = [bottom, top]
        spell = self.add_hand(game, "TIME_023")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, len(game.players[0].hand))
        self.assertEqual({"GAME_005", "CORE_AT_055"}, {c.card_id for c in game.players[0].hand})

        origin = self.add_hand(game, "EDR_251")
        game.players[0].deck = [
            game._entity("CORE_AT_055", started_in_deck=True),
            game._entity("CORE_AT_055", started_in_deck=False),
        ]
        game.step(Action("PLAY", origin.entity_id))
        self.assertEqual(3, sum(c.card_id == "CORE_AT_055" for c in game.players[0].hand))

    def test_conditional_draw_tranche(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("CORE_CS2_065", started_in_deck=True),
            game._entity("CORE_AT_055", started_in_deck=True),
        ]
        bola = self.add_hand(game, "JAIL_377")
        game.step(Action("PLAY", bola.entity_id))
        self.assertNotIn(bola, game.players[0].hand)

    def test_consumption_random_damage_draw(self):
        game = self.game()
        first = self.add_board(game, "CORE_LOOT_137", 1)
        second = self.add_board(game, "CORE_LOOT_137", 1)
        first.damage = first.max_health - 3
        second.damage = second.max_health - 3
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True) for _ in range(2)]
        spell = self.add_hand(game, "CORE_CATA_007")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, len(game.players[0].hand))
        self.assertEqual([], game.players[1].board)

        recipe = self.add_hand(game, "JAIL_866")
        game.players[0].mana = 10
        game.players[0].deck = [game._entity("CAP_107t", started_in_deck=True) for _ in range(2)]
        game.step(Action("PLAY", recipe.entity_id))
        self.assertTrue(all(card.attack_delta >= 3 for card in game.players[0].hand if card.card_id == "CAP_107t"))

    def test_second_core_spell_tranche(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        friendly = self.add_board(game, "CAP_107t", 0)
        friendly.damage = 2
        game.players[0].health = 20
        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True),
            game._entity("GAME_005", started_in_deck=True),
            game._entity("GAME_005", started_in_deck=True),
        ]

        bash = self.add_hand(game, "CORE_AT_064")
        game.step(Action("PLAY", bash.entity_id, 1, enemy.entity_id))
        self.assertEqual(3, enemy.damage)
        self.assertEqual(3, game.players[0].armor)

        smite = self.add_hand(game, "CORE_CS1_130")
        game.step(Action("PLAY", smite.entity_id, 1, enemy.entity_id))
        self.assertEqual(6, enemy.damage)

        hammer = self.add_hand(game, "CORE_CS2_094")
        before = len(game.players[0].hand)
        game.step(Action("PLAY", hammer.entity_id, 1, enemy.entity_id))
        self.assertEqual(9, enemy.damage)
        self.assertEqual(before, len(game.players[0].hand))

        shiv = self.add_hand(game, "CORE_EX1_278")
        before = len(game.players[0].hand)
        game.step(Action("PLAY", shiv.entity_id, 1, enemy.entity_id))
        self.assertEqual(10, enemy.damage)
        self.assertEqual(before, len(game.players[0].hand))

        flash = self.add_hand(game, "CORE_TRL_307")
        game.step(Action("PLAY", flash.entity_id, 0, None))
        self.assertEqual(24, game.players[0].health)

        fan = self.add_hand(game, "CORE_EX1_129")
        game.step(Action("PLAY", fan.entity_id))
        self.assertEqual(11, enemy.damage)

        consecration = self.add_hand(game, "CORE_CS2_093")
        game.step(Action("PLAY", consecration.entity_id))
        self.assertEqual(13, enemy.damage)
        self.assertEqual(28, game.players[1].health)

    def test_standard_basic_damage_draw(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True),
            game._entity("GAME_005", started_in_deck=True),
        ]
        wounded = self.add_board(game, "CORE_EX1_007", 1)
        slam = self.add_hand(game, "CORE_EX1_391")
        before = len(game.players[0].hand)
        game.step(Action("PLAY", slam.entity_id, 1, wounded.entity_id))
        self.assertEqual(before, len(game.players[0].hand))
        self.assertEqual(2, wounded.damage)

        shield = self.add_hand(game, "CORE_EX1_606")
        before = len(game.players[0].hand)
        game.step(Action("PLAY", shield.entity_id))
        self.assertEqual(5, game.players[0].armor)
        self.assertEqual(before, len(game.players[0].hand))

        game.players[0].health = 20
        lifedrinker = self.add_hand(game, "CORE_GIL_622")
        game.step(Action("PLAY", lifedrinker.entity_id))
        self.assertEqual(27, game.players[1].health)
        self.assertEqual(23, game.players[0].health)

    def test_standard_conditional_destroy(self):
        game = self.game()
        clean = self.add_board(game, "CORE_EX1_007", 1)
        backstab = self.add_hand(game, "CORE_CS2_072")
        game.step(Action("PLAY", backstab.entity_id, 1, clean.entity_id))
        self.assertEqual(2, clean.damage)
        execute = self.add_hand(game, "CORE_CS2_108")
        game.step(Action("PLAY", execute.entity_id, 1, clean.entity_id))
        self.assertNotIn(clean, game.players[1].board)

        target = self.add_board(game, "CORE_EX1_007", 1)
        siphon = self.add_hand(game, "CORE_EX1_309")
        game.players[0].health = 20
        game.step(Action("PLAY", siphon.entity_id, 1, target.entity_id))
        self.assertEqual(23, game.players[0].health)
        self.assertNotIn(target, game.players[1].board)

    def test_standard_buff_overload_weapon(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_EX1_007", 0)
        mark = self.add_hand(game, "CORE_CS2_009")
        game.step(Action("PLAY", mark.entity_id, 0, friendly.entity_id))
        self.assertEqual((3, 7), (friendly.attack, friendly.max_health))
        self.assertTrue(friendly.taunt)

        enemy = self.add_board(game, "CORE_EX1_007", 1)
        bolt = self.add_hand(game, "CORE_EX1_238")
        game.step(Action("PLAY", bolt.entity_id, 1, enemy.entity_id))
        self.assertEqual(3, enemy.damage)
        self.assertEqual(1, game.players[0].overload_next_turn)

        game._equip_weapon(game.players[0], Weapon("TEST_WEAPON", "Test Weapon", 1, 2))
        poison = self.add_hand(game, "CORE_CS2_074")
        game.step(Action("PLAY", poison.entity_id))
        self.assertEqual(3, game.players[0].weapon.attack)

    def test_standard_holy_nova_portal(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_EX1_007", 0)
        enemy = self.add_board(game, "CORE_EX1_007", 1)
        friendly.damage = 2
        game.players[0].health = 25
        nova = self.add_hand(game, "CORE_CS1_112")
        game.step(Action("PLAY", nova.entity_id))
        self.assertEqual(0, friendly.damage)
        self.assertEqual(2, enemy.damage)
        self.assertEqual(27, game.players[0].health)

        portal = self.add_hand(game, "CORE_WON_337")
        game.step(Action("PLAY", portal.entity_id))
        self.assertEqual(4, game.players[0].armor)
        self.assertTrue(game.players[0].board)

    def test_standard_deep_freeze(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_EX1_007", 1)
        spell = self.add_hand(game, "CORE_BT_072")
        game.step(Action("PLAY", spell.entity_id, 1, enemy.entity_id))
        self.assertEqual(game.turn, enemy.frozen_turn)
        self.assertEqual(2, sum(card.card_id == "CORE_CS2_033" for card in game.players[0].board))

    def test_standard_preparation_discount(self):
        game = self.game()
        game.players[0].mana = 3
        prep = self.add_hand(game, "CORE_EX1_145")
        bolt = self.add_hand(game, "CORE_EX1_238")
        game.step(Action("PLAY", prep.entity_id))
        self.assertEqual(2, game.players[0].next_spell_cost_reduction)
        self.assertEqual(0, game._effective_cost(game.players[0], bolt))
        game.step(Action("PLAY", bolt.entity_id, 1, None))
        self.assertEqual(0, game.players[0].next_spell_cost_reduction)

    def test_standard_equality_lightning_storm(self):
        game = self.game()
        first = self.add_board(game, "CORE_EX1_007", 0)
        second = self.add_board(game, "CORE_EX1_007", 1)
        equality = self.add_hand(game, "CORE_EX1_619")
        game.step(Action("PLAY", equality.entity_id))
        self.assertEqual((1, 1), (first.max_health, second.max_health))

        enemy = self.add_board(game, "CORE_EX1_007", 1)
        storm = self.add_hand(game, "CORE_EX1_259")
        game.step(Action("PLAY", storm.entity_id))
        self.assertEqual(3, enemy.damage)
        self.assertEqual(1, game.players[0].overload_next_turn)

    def test_standard_hex_transform(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_007", 1)
        target.attack_delta = 5
        hex_spell = self.add_hand(game, "CORE_EX1_246")
        game.step(Action("PLAY", hex_spell.entity_id, 1, target.entity_id))
        transformed = game.players[1].board[0]
        self.assertEqual("hexfrog", transformed.card_id)
        self.assertEqual((0, 1), (transformed.attack, transformed.max_health))
        self.assertTrue(transformed.taunt)
        self.assertEqual(target.entity_id, transformed.entity_id)

    def test_standard_power_of_the_wild(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_EX1_007", 0)
        spell = self.add_hand(game, "CORE_EX1_160")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual("RULE_CHOICE", game.pending_choice["kind"])
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual((2, 5), (friendly.attack, friendly.max_health))

        spell = self.add_hand(game, "CORE_EX1_160")
        game.step(Action("PLAY", spell.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertTrue(any(card.card_id == "EX1_160t" for card in game.players[0].board))

    def test_powerlog_cards_and_triggers(self):
        game = self.game()
        game._equip_weapon(game.players[0], Weapon("EDR_416", "Shepherd's Crook", 3, 2))
        game._dispatch_after_hero_attack(
            game.players[0], attack_amount=3, weapon=game.players[0].weapon
        )
        self.assertEqual(1, len(game.players[0].board))
        self.assertEqual("EDR_416t", game.players[0].board[0].card_id)
        self.assertEqual(2, game.players[0].board[0].dormant_turns)

        game._equip_weapon(game.players[0], Weapon("JAIL_730", "Stardust Scythe", 4, 2))
        game._dispatch_after_hero_attack(
            game.players[0], attack_amount=4, weapon=game.players[0].weapon
        )
        self.assertIn("JAIL_732", [card.card_id for card in game.players[0].hand])

    def test_latest_powerlog_simple_rules(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 0)
        target.damage = 4
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        mend = self.add_hand(game, "CATA_302")
        game.step(Action("PLAY", mend.entity_id, 0, target.entity_id))
        self.assertEqual(0, target.damage)
        self.assertEqual(1, len(game.players[0].hand))

        enemy = self.add_board(game, "CAP_107t", 1)
        sweep = self.add_hand(game, "CATA_308")
        game.step(Action("PLAY", sweep.entity_id))
        self.assertNotIn(enemy, game.players[1].board)

        game.players[0].mana = 0
        coin = self.add_hand(game, "JAIL_COIN1")
        game.step(Action("PLAY", coin.entity_id))
        self.assertEqual(1, game.players[0].mana)

    def test_latest_powerlog_choice_rules(self):
        game = self.game()
        enemy = self.add_board(game, "CAP_107t", 1)
        spell = self.add_hand(game, "EDR_463")
        game.step(Action("PLAY", spell.entity_id, 1, enemy.entity_id))
        self.assertIsNotNone(game.pending_choice)
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertNotIn(enemy, game.players[1].board)

    def test_first_flame_generates_second_flame(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        flame = self.add_hand(game, "CORE_SW_108")
        game.step(Action("PLAY", flame.entity_id, 1, target.entity_id))
        self.assertEqual(2, target.damage)
        second = game.players[0].hand[0]
        self.assertEqual("SW_108t", second.card_id)
        game.step(Action("PLAY", second.entity_id, 1, target.entity_id))
        self.assertEqual(4, target.damage)

    def test_fireball_and_flamestrike(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        fireball = self.add_hand(game, "CORE_CS2_029")
        game.step(Action("PLAY", fireball.entity_id, 1, target.entity_id))
        self.assertEqual(6, target.damage)

        enemy_a = self.add_board(game, "CAP_107t", 1)
        enemy_b = self.add_board(game, "CAP_107t", 1)
        flamestrike = self.add_hand(game, "CORE_CS2_032")
        game.step(Action("PLAY", flamestrike.entity_id))
        self.assertNotIn(enemy_a, game.players[1].board)
        self.assertNotIn(enemy_b, game.players[1].board)

    def test_fire_breath_damages_and_buffs_friendly_elementals(self):
        game = self.game()
        elemental = self.add_board(game, "TLC_249", 0)
        spell = self.add_hand(game, "DINO_406")
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(26, game.players[1].health)
        self.assertEqual((3, 2), (elemental.attack, elemental.max_health))

    def test_decimation_scales_from_minions_present_at_resolution(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_LOOT_137", 0)
        enemy_a = self.add_board(game, "CORE_LOOT_137", 1)
        enemy_b = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "CATA_581")
        game.step(Action("PLAY", spell.entity_id))
        # Base one damage, improved by the three minions at resolution.
        self.assertEqual(4, friendly.damage)
        self.assertEqual(4, enemy_a.damage)
        self.assertEqual(4, enemy_b.damage)

    def test_eternal_firebolt_lifesteals_and_returns_at_end_turn_on_kill(self):
        game = self.game()
        game.players[0].health = 20
        target = self.add_board(game, "CAP_107t", 1)
        spell = self.add_hand(game, "END_025")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertEqual(21, game.players[0].health)
        self.assertFalse(game.players[0].hand)
        game._end_turn()
        self.assertEqual(["END_025"], [card.card_id for card in game.players[0].hand])

    def test_molten_gold_transforms_after_three_spells_and_battlecries(self):
        game = self.game()
        gold = self.add_hand(game, "JAIL_801")
        coins = [self.add_hand(game, "GAME_005") for _ in range(3)]
        for coin in coins:
            game.step(Action("PLAY", coin.entity_id))
        self.assertEqual("JAIL_801t", gold.card_id)
        game.step(Action("PLAY", gold.entity_id, 1, None))
        self.assertEqual(26, game.players[1].health)

    def test_explosive_trap_triggers_after_hero_is_attacked(self):
        game = self.game()
        trap = game._entity("CORE_EX1_610")
        game.players[1].hand.append(trap)
        game.current = 1
        game.players[1].mana = 10
        game.step(Action("PLAY", trap.entity_id))
        self.assertEqual(["CORE_EX1_610"], [card.card_id for card in game.players[1].secrets])
        game._end_turn()
        attacker = self.add_board(game, "CAP_107t", 0)
        game.step(Action("ATTACK", attacker.entity_id, 1, None))
        self.assertEqual(28, game.players[0].health)
        self.assertNotIn(attacker, game.players[0].board)
        self.assertFalse(game.players[1].secrets)

    def test_freezing_trap(self):
        game = self.game()
        trap = self.add_hand(game, "CORE_EX1_611")
        game.step(Action("PLAY", trap.entity_id))
        game.step(Action("END_TURN"))
        attacker = self.add_board(game, "TLC_248", 1)
        before_health = game.players[0].health
        game.step(Action("ATTACK", attacker.entity_id, 0, None))
        self.assertEqual(before_health, game.players[0].health)
        self.assertNotIn(attacker, game.players[1].board)
        returned = next(
            card for card in game.players[1].hand
            if card.entity_id == attacker.entity_id
        )
        self.assertEqual(2, returned.cost_delta)
        self.assertEqual([], game.players[0].secrets)

    def test_snake_trap(self):
        game = self.game()
        trap = self.add_hand(game, "CORE_EX1_554")
        game.step(Action("PLAY", trap.entity_id))
        game.step(Action("END_TURN"))
        defender = self.add_board(game, "TLC_248", 0)
        attacker = self.add_board(game, "TLC_248", 1)
        game.step(Action("ATTACK", attacker.entity_id, 0, defender.entity_id))
        snakes = [card for card in game.players[0].board if card.card_id == "EX1_554t"]
        self.assertEqual(3, len(snakes))
        self.assertNotIn("CORE_EX1_554", [card.card_id for card in game.players[0].secrets])

    def test_noble_sacrifice(self):
        game = self.game()
        secret = self.add_hand(game, "CORE_EX1_130")
        game.step(Action("PLAY", secret.entity_id))
        game.step(Action("END_TURN"))
        attacker = self.add_board(game, "TLC_248", 1)
        game.step(Action("ATTACK", attacker.entity_id, 0, None))
        self.assertGreaterEqual(game.players[0].health, 20)
        self.assertFalse(game.players[0].secrets)

    def test_mirror_entity(self):
        game = self.game()
        secret = self.add_hand(game, "CORE_EX1_294")
        game.step(Action("PLAY", secret.entity_id))
        game.step(Action("END_TURN"))
        minion = game._entity("TLC_248")
        game.players[1].hand.append(minion)
        game.players[1].mana = 20
        game.step(Action("PLAY", minion.entity_id))
        copies = [card for card in game.players[0].board if card.card_id == "TLC_248"]
        self.assertEqual(1, len(copies))
        self.assertFalse(game.players[1].secrets)

    def test_avenge(self):
        game = self.game()
        secret = self.add_hand(game, "CORE_FP1_020")
        game.step(Action("PLAY", secret.entity_id))
        game.step(Action("END_TURN"))
        victim = self.add_board(game, "TLC_248", 0)
        survivor = self.add_board(game, "TLC_248", 0)
        base_attack, base_health = survivor.attack, survivor.max_health
        victim.damage = victim.max_health
        game._resolve_deaths()
        self.assertEqual(base_attack + 3, survivor.attack)
        self.assertEqual(base_health + 2, survivor.max_health)
        self.assertFalse(game.players[0].secrets)

    def test_repentance(self):
        game = self.game()
        secret = self.add_hand(game, "EX1_379")
        game.step(Action("PLAY", secret.entity_id))
        game.step(Action("END_TURN"))
        minion = game._entity("TLC_248")
        game.players[1].hand.append(minion)
        game.players[1].mana = 20
        game.step(Action("PLAY", minion.entity_id))
        self.assertEqual(1, minion.health)
        self.assertFalse(game.players[0].secrets)

    def test_redemption(self):
        game = self.game()
        secret = self.add_hand(game, "EX1_136")
        game.step(Action("PLAY", secret.entity_id))
        victim = self.add_board(game, "TLC_248", 0)
        base_max_health = victim.max_health
        victim.damage = victim.max_health
        game._resolve_deaths()
        revived = [card for card in game.players[0].board if card.card_id == "TLC_248"]
        self.assertEqual(1, len(revived))
        self.assertEqual(1, revived[0].health)
        self.assertEqual(base_max_health, revived[0].max_health)
        self.assertFalse(game.players[0].secrets)

    def test_duplicate(self):
        game = self.game()
        secret = self.add_hand(game, "FP1_018")
        game.step(Action("PLAY", secret.entity_id))
        victim = self.add_board(game, "TLC_248", 0)
        victim.damage = victim.max_health
        game._resolve_deaths()
        copies = [card for card in game.players[0].hand if card.card_id == "TLC_248"]
        self.assertEqual(2, len(copies))
        self.assertFalse(game.players[0].secrets)

    def test_vaporize(self):
        game = self.game()
        secret = self.add_hand(game, "EX1_594")
        game.step(Action("PLAY", secret.entity_id))
        game.step(Action("END_TURN"))
        attacker = self.add_board(game, "TLC_248", 1)
        before_health = game.players[0].health
        game.step(Action("ATTACK", attacker.entity_id, 0, None))
        self.assertEqual(before_health, game.players[0].health)
        self.assertNotIn(attacker, game.players[1].board)
        self.assertFalse(game.players[0].secrets)

    def test_snipe(self):
        game = self.game()
        secret = self.add_hand(game, "EX1_609")
        game.step(Action("PLAY", secret.entity_id))
        game.step(Action("END_TURN"))
        minion = game._entity("TLC_248")
        game.players[1].hand.append(minion)
        game.players[1].mana = 20
        game.step(Action("PLAY", minion.entity_id))
        self.assertEqual(minion.max_health - 6, minion.health)
        self.assertFalse(game.players[0].secrets)

    def test_cat_trick(self):
        game = self.game()
        secret = self.add_hand(game, "CORE_KAR_004")
        game.step(Action("PLAY", secret.entity_id))
        game.step(Action("END_TURN"))
        spell = game._entity("JAIL_COIN1")
        game.players[1].hand.append(spell)
        game.players[1].mana = 20
        game.step(Action("PLAY", spell.entity_id))
        cats = [card for card in game.players[0].board if card.card_id == "KAR_004a"]
        self.assertEqual(1, len(cats))
        self.assertTrue(cats[0].stealth)
        self.assertFalse(game.players[0].secrets)

    def test_shadow_of_demise_transform(self):
        game = self.game()
        shadow = self.add_hand(game, "CORE_RLK_567")
        spell = self.add_hand(game, "CORE_AT_055")
        game.step(Action("PLAY", spell.entity_id, 0, None))
        self.assertEqual("CORE_AT_055", shadow.card_id)
        self.assertEqual(1, shadow.cost)

    def test_deja_vu_discover_opponent_hand(self):
        game = self.game()
        spell = self.add_hand(game, "TIME_039")
        opponent_card = game._entity("TLC_248")
        game.players[1].hand.append(opponent_card)
        game.step(Action("PLAY", spell.entity_id))
        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertEqual(["TLC_248"], [c.card_id for c in game.pending_choice["options"]])

    def test_lotus_bookie_deathrattle_coin(self):
        game = self.game()
        bookie = self.add_board(game, "JAIL_720", 0)
        bookie.damage = bookie.max_health
        game._resolve_deaths()
        self.assertEqual(
            1,
            sum(card.card_id == "JAIL_COIN1" for card in game.players[0].hand),
        )

    def test_cultist_map_deck_discover(self):
        game = self.game()
        game.players[0].deck = [game._entity("TLC_248", started_in_deck=True)]
        map_card = self.add_hand(game, "TLC_515")
        game.step(Action("PLAY", map_card.entity_id))
        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("DECK_CARD_DISCOVER", game.pending_choice["kind"])
        self.assertEqual(["TLC_248"], [c.card_id for c in game.pending_choice["options"]])

    def test_gravedawn_sunbloom_draws_two(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("TLC_248", started_in_deck=True),
            game._entity("JAIL_720", started_in_deck=True),
        ]
        card = self.add_hand(game, "TLC_816")
        game.step(Action("PLAY", card.entity_id))
        self.assertEqual(2, len(game.players[0].hand))

    def test_illidari_studies(self):
        game = self.game()
        studies = self.add_hand(game, "CORE_YOP_001")
        game.step(Action("PLAY", studies.entity_id))
        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertEqual(1, game.players[0].next_spell_cost_reduction)

    def test_soulrest_ceremony(self):
        game = self.game()
        minion = self.add_board(game, "TLC_248", 0)
        base_attack = minion.attack
        spell = self.add_hand(game, "DINO_417")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(base_attack + 1, minion.attack)
        self.assertTrue(minion.rush)
        self.assertTrue(minion.dies_at_end_of_turn)
        game.step(Action("END_TURN"))
        self.assertNotIn(minion, game.players[0].board)

    def test_defias_smuggler_battlecry(self):
        game = self.game()
        target = self.add_board(game, "TLC_248", 0)
        base_attack = target.attack
        smuggler = self.add_hand(game, "JAIL_998")
        game.step(Action("PLAY", smuggler.entity_id, 0, target.entity_id))
        self.assertEqual(base_attack + 2, target.attack)
        self.assertTrue(target.rush)

    def test_holy_eggbearer_draws_zero_attack(self):
        game = self.game()
        zero = game._entity("CORE_EX1_100", started_in_deck=True)
        other = game._entity("TLC_248", started_in_deck=True)
        game.players[0].deck = [other, zero]
        bearer = self.add_hand(game, "DINO_411")
        game.step(Action("PLAY", bearer.entity_id))
        self.assertEqual("CORE_EX1_100", game.players[0].hand[-1].card_id)

    def test_twilight_mistress_returns_enemy_board(self):
        game = self.game()
        enemy = self.add_board(game, "TLC_248", 1)
        mistress = self.add_hand(game, "CATA_201")
        game.step(Action("PLAY", mistress.entity_id))
        self.assertFalse(game.players[1].board)
        self.assertIn(enemy, game.players[1].hand)
        self.assertEqual(0, enemy.damage)

    def test_infestation_generates_stingers(self):
        game = self.game()
        card = self.add_hand(game, "TLC_902")
        game.step(Action("PLAY", card.entity_id))
        self.assertEqual(2, sum(c.card_id == "TLC_630t" for c in game.players[0].hand))

    def test_opu_the_unseen_fan_of_knives(self):
        game = self.game()
        enemy = self.add_board(game, "TLC_248", 1)
        opu = self.add_hand(game, "TLC_522")
        before_hand = len(game.players[0].hand)
        game.step(Action("PLAY", opu.entity_id))
        self.assertEqual(enemy.max_health - 1, enemy.health)
        self.assertEqual(before_hand, len(game.players[0].hand))

    def test_opu_the_unseen_combo_casts_twice(self):
        game = self.game()
        first = self.add_hand(game, "JAIL_COIN1")
        opu = self.add_hand(game, "TLC_522")
        enemy = self.add_board(game, "TLC_248", 1)
        game.step(Action("PLAY", first.entity_id))
        game.step(Action("PLAY", opu.entity_id))
        self.assertEqual(enemy.max_health - 2, enemy.health)

    def test_rite_of_twilight_herald(self):
        game = self.game()
        rite = self.add_hand(game, "CATA_785")
        game.step(Action("PLAY", rite.entity_id))
        self.assertTrue(any(card.card_id == "CATA_580t" for card in game.players[0].board))

    def test_rite_of_twilight_combo_deals_selected_enemy_damage(self):
        game = self.game()
        coin = self.add_hand(game, "JAIL_COIN1")
        rite = self.add_hand(game, "CATA_785")
        enemy = self.add_board(game, "TLC_248", 1)
        game.step(Action("PLAY", coin.entity_id))
        before = enemy.health
        game.step(Action("PLAY", rite.entity_id, 1, enemy.entity_id))
        self.assertEqual(before - 3, enemy.health)

    def test_grim_harvest_draws_and_summons_dreadseed(self):
        game = self.game()
        drawn = game._entity("TLC_248", started_in_deck=True)
        game.players[0].deck = [drawn]
        harvest = self.add_hand(game, "EDR_840")
        game.step(Action("PLAY", harvest.entity_id))
        self.assertIn(drawn, game.players[0].hand)
        self.assertEqual(1, len(game.players[0].board))
        self.assertIn(game.players[0].board[0].card_id, {"EDR_840t", "EDR_840t1", "EDR_840t2"})
        self.assertGreater(game.players[0].board[0].dormant_turns, 0)

    def test_maniacal_follower_deathrattle_herald(self):
        game = self.game()
        follower = self.add_board(game, "CATA_158", 0)
        follower.damage = follower.max_health
        game._resolve_deaths()
        self.assertNotIn(follower, game.players[0].board)
        self.assertTrue(any(card.card_id == "CATA_580t" for card in game.players[0].board))

    def test_web_of_deception_returns_and_summons(self):
        game = self.game()
        target = self.add_board(game, "TLC_248", 0)
        spell = self.add_hand(game, "EDR_523")
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertNotIn(target, game.players[0].board)
        self.assertIn(target, game.players[0].hand)
        self.assertTrue(any(card.card_id == "EDR_523t" for card in game.players[0].board))

    def test_silent_strike_stealth_branch(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_010", 0)
        target.stealth = True
        enemy = self.add_board(game, "TLC_248", 1)
        spell = self.add_hand(game, "CAP_001")
        before = enemy.health
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertEqual(target.definition.attack + 3, target.attack)
        self.assertEqual(before - target.attack, enemy.health)

    def test_si7_supplier_draws_after_surviving_attack(self):
        game = self.game()
        supplier = self.add_board(game, "CAP_003", 0)
        filler = game._entity("TLC_248", started_in_deck=True)
        game.players[0].deck = [filler]
        game.step(Action("ATTACK", supplier.entity_id, 1, None))
        self.assertIn(filler, game.players[0].hand)

    def test_si7_slayer_buffs_stealthed_attacker(self):
        game = self.game()
        slayer = self.add_board(game, "CAP_000", 0)
        attacker = self.add_board(game, "CORE_EX1_010", 0)
        attacker.stealth = True
        enemy = self.add_board(game, "TLC_248", 1)
        before = attacker.attack
        before_health = attacker.max_health
        game.step(Action("ATTACK", attacker.entity_id, 1, None))
        self.assertEqual(before + 2, attacker.attack)
        self.assertEqual(before_health + 2, attacker.max_health)

    def test_mathias_shaw_discounts_random_hand_card(self):
        game = self.game()
        shaw = self.add_board(game, "CAP_005", 0)
        attacker = self.add_board(game, "CORE_EX1_010", 0)
        attacker.stealth = True
        held = self.add_hand(game, "TLC_248")
        before = held.cost
        game.step(Action("ATTACK", attacker.entity_id, 1, None))
        self.assertEqual(before - 3, held.cost)

    def test_follow_the_footsteps_stealth_discover(self):
        game = self.game()
        spell = self.add_hand(game, "CAP_002")
        game.step(Action("PLAY", spell.entity_id))
        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertTrue(game.pending_choice["options"])
        self.assertTrue(all(
            "STEALTH" in option.definition.mechanics or "Stealth" in option.definition.text
            for option in game.pending_choice["options"]
        ))

    def test_king_llane_draws_and_shuffles_back(self):
        game = self.game()
        drawn = game._entity("TLC_248", started_in_deck=True)
        game.players[0].deck = [drawn]
        king = self.add_hand(game, "TIME_875t")
        game.step(Action("PLAY", king.entity_id))
        self.assertIn(drawn, game.players[0].hand)
        self.assertNotIn(king, game.players[0].board)
        self.assertIn(king, game.players[0].deck)

    def test_crystal_merchant_draws_with_unspent_mana(self):
        game = self.game()
        merchant = self.add_board(game, "CORE_ULD_133", 0)
        drawn = game._entity("TLC_248", started_in_deck=True)
        game.players[0].deck = [drawn]
        game.players[0].mana = 1
        game._end_turn()
        self.assertIn(drawn, game.players[0].hand)

    def test_leyline_nexus_discounts_drawn_card(self):
        game = self.game()
        drawn = game._entity("TLC_248", started_in_deck=True)
        game.players[0].deck = [drawn]
        spell = self.add_hand(game, "MEND_504")
        game.step(Action("PLAY", spell.entity_id))
        self.assertIn(drawn, game.players[0].hand)
        self.assertEqual(drawn.definition.cost - 1, drawn.cost)

    def test_leyline_nexus_upgrade_scales_discount(self):
        game = self.game()
        game.players[0].leyline_upgrade = 2
        drawn = game._entity("TLC_248", started_in_deck=True)
        game.players[0].deck = [drawn]
        spell = self.add_hand(game, "MEND_504")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(drawn.definition.cost - 3, drawn.cost)

    def test_leyline_nexus_extra_trigger_draws_twice(self):
        game = self.game()
        game.players[0].leyline_extra_triggers = 1
        game.players[0].deck = [
            game._entity("TLC_248", started_in_deck=True),
            game._entity("TLC_248", started_in_deck=True),
        ]
        spell = self.add_hand(game, "MEND_504")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, sum(card.card_id == "TLC_248" for card in game.players[0].hand))

    def test_divination_sacrifices_wisp_and_draws(self):
        game = self.game()
        wisp = self.add_board(game, "CORE_CS2_231", 0)
        game.players[0].deck = [game._entity("TLC_248", started_in_deck=True) for _ in range(3)]
        spell = self.add_hand(game, "EDR_804")
        game.step(Action("PLAY", spell.entity_id, 0, wisp.entity_id))
        self.assertNotIn(wisp, game.players[0].board)
        self.assertEqual(3, sum(card.card_id == "TLC_248" for card in game.players[0].hand))

    def test_wispering_woods_summons_by_hand_size(self):
        game = self.game()
        self.add_hand(game, "TLC_248")
        self.add_hand(game, "TLC_248")
        spell = self.add_hand(game, "GIL_553")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, sum(card.card_id == "CORE_CS2_231" for card in game.players[0].board))

    def test_wisps_of_old_gods_offers_choice(self):
        game = self.game()
        spell = self.add_hand(game, "OG_195")
        game.step(Action("PLAY", spell.entity_id))
        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("RULE_CHOICE", game.pending_choice["kind"])
        self.assertEqual({"summon_seven_wisps", "buff_friendly_minions"},
                         {label for label, _ in game.pending_choice["options"]})

    def test_bursting_leyline_excess_damage(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_CS2_231", 1)
        spell = self.add_hand(game, "MEND_500")
        before = game.players[1].health
        game.step(Action("PLAY", spell.entity_id))
        self.assertNotIn(enemy, game.players[1].board)
        self.assertEqual(before - 3, game.players[1].health)

    def test_bursting_leyline_upgrade_scales_damage(self):
        game = self.game()
        game.players[0].leyline_upgrade = 2
        enemy = self.add_board(game, "CORE_CS2_231", 1)
        spell = self.add_hand(game, "MEND_500")
        before = game.players[1].health
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(before - 5, game.players[1].health)

    def test_ley_walker_discount_and_random_deathrattle(self):
        game = self.game()
        leyline = self.add_hand(game, "MEND_504")
        walker = self.add_hand(game, "MEND_501")
        game.step(Action("PLAY", walker.entity_id))
        self.assertEqual(leyline.definition.cost - 1, leyline.cost)
        walker = self.add_board(game, "MEND_501", 0)
        walker.damage = walker.max_health
        game._resolve_deaths()
        self.assertTrue(any(card.card_id in {"MEND_500", "MEND_502", "MEND_504"}
                            for card in game.players[0].hand))

    def test_crystallized_leyline_summons_five_cost(self):
        game = self.game()
        spell = self.add_hand(game, "MEND_502")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(1, len(game.players[0].board))
        self.assertEqual(5, game.players[0].board[0].definition.cost)

    def test_crystallized_leyline_reads_upgraded_level(self):
        game = self.game()
        game.players[0].leyline_upgrade = 2
        spell = self.add_hand(game, "MEND_502")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(7, game.players[0].board[0].definition.cost)

    def test_crystallized_leyline_extra_trigger_summons_twice(self):
        game = self.game()
        game.players[0].leyline_extra_triggers = 1
        spell = self.add_hand(game, "MEND_502")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, len(game.players[0].board))

    def test_surge_needle_adds_leyline_trigger(self):
        game = self.game()
        needle = self.add_hand(game, "MEND_503")
        game.step(Action("PLAY", needle.entity_id))
        self.assertEqual(1, game.players[0].leyline_extra_triggers)

    def test_mystic_runesaber_upgrades_leylines(self):
        game = self.game()
        saber = self.add_hand(game, "MEND_506")
        game.step(Action("PLAY", saber.entity_id))
        self.assertEqual(1, game.players[0].leyline_upgrade)

    def test_merry_moonkin_armor_scales_with_wisps(self):
        game = self.game()
        self.add_board(game, "EDR_940", 0)
        self.add_board(game, "CORE_CS2_231", 0)
        self.add_board(game, "CORE_CS2_231", 0)
        game.players[0].mana = 0
        game._end_turn()
        self.assertEqual(3, game.players[0].armor)

    def test_spirit_gatherer_gets_wisp_and_imbues(self):
        game = self.game()
        game.players[0].card_class = "MAGE"
        gatherer = self.add_hand(game, "EDR_871")
        game.step(Action("PLAY", gatherer.entity_id))
        self.assertTrue(any(card.card_id == "CORE_CS2_231" for card in game.players[0].hand))
        self.assertEqual("EDR_851p", game.players[0].hero_power_id)

    def test_leyline_manipulator_discounts_generated_cards(self):
        game = self.game()
        generated = game._entity("TLC_248", created_by="TEST")
        generated.started_in_deck = False
        original = self.add_hand(game, "TLC_248")
        original.started_in_deck = True
        game.players[0].hand.append(generated)
        manipulator = self.add_hand(game, "LOOT_537")
        game.step(Action("PLAY", manipulator.entity_id))
        self.assertEqual(original.definition.cost, original.cost)
        self.assertEqual(generated.definition.cost - 2, generated.cost)

    def test_flames_of_infinity_kills_highest_health_minion_at_enemy_end(self):
        game = self.game()
        secret = game._entity("END_024")
        game.players[1].hand.append(secret)
        game.current = 1
        game.players[1].mana = 10
        game.step(Action("PLAY", secret.entity_id))
        game._end_turn()
        high = self.add_board(game, "CORE_LOOT_137", 0)
        low = self.add_board(game, "CORE_CS2_065", 0)
        game.step(Action("END_TURN"))
        self.assertNotIn(high, game.players[0].board)
        self.assertIn(low, game.players[0].board)
        self.assertFalse(game.players[1].secrets)

    def test_explosive_runes_deals_excess_to_enemy_hero(self):
        game = self.game()
        secret = game._entity("CORE_LOOT_101")
        game.players[1].hand.append(secret)
        game.current = 1
        game.players[1].mana = 10
        game.step(Action("PLAY", secret.entity_id))
        game._end_turn()
        minion = self.add_hand(game, "CAP_107t")
        game.step(Action("PLAY", minion.entity_id))
        self.assertNotIn(minion, game.players[0].board)
        self.assertEqual(25, game.players[0].health)
        self.assertFalse(game.players[1].secrets)

    def test_searing_reflection_draws_and_summons_divine_shield_copy(self):
        game = self.game()
        dragon = game._entity("CORE_LOOT_137", started_in_deck=True)
        game.players[0].deck = [dragon]
        spell = self.add_hand(game, "FIR_941")
        game.step(Action("PLAY", spell.entity_id))
        self.assertIn(dragon, game.players[0].hand)
        self.assertEqual(1, len(game.players[0].board))
        copy = game.players[0].board[0]
        self.assertEqual("CORE_LOOT_137", copy.card_id)
        self.assertEqual((8, 8), (copy.attack, copy.max_health))
        self.assertTrue(copy.divine_shield)
        self.assertFalse(copy.started_in_deck)

    def test_flight_of_the_firehawk_draws_different_tribes_and_buffs(self):
        game = self.game()
        dragon = game._entity("CORE_LOOT_137", started_in_deck=True)
        demon = game._entity("CORE_CS2_065", started_in_deck=True)
        game.players[0].deck = [dragon, demon]
        spell = self.add_hand(game, "TLC_222")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual({"CORE_LOOT_137", "CORE_CS2_065"}, {
            card.card_id for card in game.players[0].hand
        })
        by_id = {card.card_id: card for card in game.players[0].hand}
        self.assertEqual((7, 13), (by_id["CORE_LOOT_137"].attack, by_id["CORE_LOOT_137"].max_health))
        self.assertEqual((2, 4), (by_id["CORE_CS2_065"].attack, by_id["CORE_CS2_065"].max_health))

    def test_story_of_sulfuras_last_two_uses_then_restores_hero_power(self):
        game = self.game()
        story = self.add_hand(game, "TLC_632")
        game.step(Action("PLAY", story.entity_id))
        self.assertEqual("TLC_632t", game.players[0].hero_power_id)
        game.players[0].mana = 10
        game.step(Action("HERO_POWER"))
        self.assertEqual(22, game.players[1].health)
        self.assertEqual("TLC_632t2", game.players[0].hero_power_id)
        game._end_turn()
        game._end_turn()
        game.players[0].mana = 10
        game.step(Action("HERO_POWER"))
        self.assertEqual(14, game.players[1].health)
        self.assertIsNone(game.players[0].hero_power_id)

    def test_fyrakk_is_immune_to_fire_spell_damage_only(self):
        game = self.game()
        fyrakk = self.add_board(game, "FIR_959", 1)
        fireball = self.add_hand(game, "CORE_CS2_029")
        game.step(Action("PLAY", fireball.entity_id, 1, fyrakk.entity_id))
        self.assertEqual(0, fyrakk.damage)
        game._damage_minion(1, fyrakk, 1)
        self.assertEqual(1, fyrakk.damage)

    def test_purifying_breath_heals_target_owner_on_kill(self):
        game = self.game()
        game.players[1].health = 20
        target = self.add_board(game, "CAP_107t", 1)
        breath = self.add_hand(game, "CATA_303")
        game.step(Action("PLAY", breath.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertEqual(25, game.players[1].health)

    def test_bursting_shot_hits_distinct_random_enemies(self):
        game = self.game()
        for _ in range(3):
            self.add_board(game, "CORE_LOOT_137", 1)
        shot = self.add_hand(game, "FIR_909")
        game.step(Action("PLAY", shot.entity_id))
        event = next(event for event in reversed(game.events)
                     if event["kind"] == "random_enemy_damage")
        self.assertEqual(3, len(event["targets"]))
        self.assertEqual(3, len(set(event["targets"])))

    def test_flames_of_the_firelord_uses_held_cost_threshold(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        self.add_hand(game, "CORE_LOOT_137")  # Costs 9.
        spell = self.add_hand(game, "FIR_923")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(8, target.damage)

    def test_conflagrate_damages_and_target_owner_draws(self):
        game = self.game()
        target = self.add_board(game, "CAP_107t", 1)
        game.players[1].deck = [game._entity("GAME_005", started_in_deck=True)]
        spell = self.add_hand(game, "FIR_954")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertEqual("GAME_005", game.players[1].hand[0].card_id)

    def test_crowd_control_damages_all_minions_twice(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_LOOT_137", 0)
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "JAIL_307")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual((4, 4), (friendly.damage, enemy.damage))

    def test_lava_flow_retargets_lowest_health_enemy(self):
        game = self.game()
        target = self.add_board(game, "CAP_107t", 1)
        spell = self.add_hand(game, "TLC_227")
        game.step(Action("PLAY", spell.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertEqual(26, game.players[1].health)

    def test_overheat_discards_nature_spell_for_second_buff(self):
        game = self.game()
        minion = self.add_board(game, "CAP_107t", 0)
        nature_spell = self.add_hand(game, "EDR_270")
        spell = self.add_hand(game, "FIR_906")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual((3, 3), (minion.attack, minion.max_health))
        self.assertNotIn(nature_spell, game.players[0].hand)

    def test_scorching_winds_discards_fire_spell_for_second_hit(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        fuel = self.add_hand(game, "CORE_CS2_029")
        spell = self.add_hand(game, "FIR_910")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertEqual(6, target.damage)
        self.assertNotIn(fuel, game.players[0].hand)

    def test_sizzling_swarm_summons_one_cinder_per_damage(self):
        game = self.game()
        game.players[1].health = 20
        spell = self.add_hand(game, "TLC_221")
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(17, game.players[1].health)
        cinders = [card for card in game.players[0].board if card.card_id == "TLC_249"]
        self.assertEqual(3, len(cinders))
        self.assertTrue(all((card.attack, card.max_health) == (2, 1) for card in cinders))

    def test_wickerfang_colossal_legs_grow_and_sync_their_stats(self):
        game = self.game()
        wickerfang = self.add_hand(game, "CATA_139")
        game.step(Action("PLAY", wickerfang.entity_id))
        self.assertEqual(5, len(game.players[0].board))
        self.assertEqual("CATA_139", game.players[0].board[2].card_id)
        legs = [
            card for card in game.players[0].board
            if card.colossal_parent_entity == wickerfang.entity_id
        ]
        self.assertEqual(4, len(legs))
        self.assertTrue(all((leg.attack, leg.max_health) == (0, 2) for leg in legs))

        game._end_turn()
        self.assertTrue(all((leg.attack, leg.max_health) == (1, 3) for leg in legs))
        self.assertEqual((4, 9), (wickerfang.attack, wickerfang.max_health))

    def test_wickerfang_preserves_direct_body_buff_when_a_leg_changes(self):
        game = self.game()
        wickerfang = self.add_hand(game, "CATA_139")
        game.step(Action("PLAY", wickerfang.entity_id))
        wickerfang.attack_delta += 3
        leg = next(card for card in game.players[0].board if card.colossal_parent_entity)
        leg.attack_delta += 2
        leg.health_delta += 4
        game._refresh_continuous(game.players[0])
        self.assertEqual((5, 9), (wickerfang.attack, wickerfang.max_health))

    def test_silenced_wickerfang_does_not_copy_later_leg_growth(self):
        game = self.game()
        wickerfang = self.add_hand(game, "CATA_139")
        game.step(Action("PLAY", wickerfang.entity_id))
        game._silence_minion(wickerfang)
        game._end_turn()
        self.assertEqual((0, 5), (wickerfang.attack, wickerfang.max_health))

    def test_silenced_wickerfang_leg_does_not_grow(self):
        game = self.game()
        wickerfang = self.add_hand(game, "CATA_139")
        game.step(Action("PLAY", wickerfang.entity_id))
        leg = next(card for card in game.players[0].board if card.colossal_parent_entity)
        game._silence_minion(leg)
        game._end_turn()
        self.assertEqual((0, 2), (leg.attack, leg.max_health))
        self.assertEqual((3, 8), (wickerfang.attack, wickerfang.max_health))

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

    def test_shadow_word_ruin_does_not_affect_dormant_minion(self):
        game = self.game()
        dormant = self.add_board(game, "TIME_063", 0)
        dormant.dormant_turns = 2
        dormant.attack_delta = 10
        spell = self.add_hand(game, "CORE_EX1_197")
        game.step(Action("PLAY", spell.entity_id))
        self.assertIn(dormant, game.players[0].board)
        self.assertEqual(0, dormant.damage)

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

    def test_standard_mossbinding(self):
        game = self.game()
        game.players[0].mana = 10
        spell = self.add_hand(game, "CATA_135")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(0, game.players[0].mana)
        self.assertEqual(2, len(game.players[0].board))
        self.assertTrue(all((m.attack, m.max_health) == (9, 10) for m in game.players[0].board))

    def test_standard_eldritch_tentacles(self):
        game = self.game()
        target = self.add_board(game, "TLC_248", 1)
        spell = self.add_hand(game, "CATA_491")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(6, target.damage)

    def test_standard_haunt(self):
        game = self.game()
        target = self.add_board(game, "CAP_107t", 0)
        spell = self.add_hand(game, "CAP_801")
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertEqual((3, 4), (target.attack, target.max_health))
        self.assertTrue(target.taunt)
        self.assertTrue(target.reborn)

    def test_standard_daze_bounce_lock(self):
        game = self.game()
        target = self.add_board(game, "CAP_107t", 1)
        spell = self.add_hand(game, "CATA_215")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertIn(target, game.players[1].hand)
        self.assertEqual(game.turn + 1, target.playable_after_turn)

    def test_standard_searing_fissure(self):
        game = self.game()
        target = self.add_board(game, "TLC_248", 1)
        spell = self.add_hand(game, "CATA_582")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(1, target.damage)
        self.assertEqual(3, game.players[0].hero_attack_bonus)

    def test_standard_torch_excess_return(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        target.damage = target.max_health - 1
        spell = self.add_hand(game, "CATA_585")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertTrue(any(card.card_id == "CATA_585" for card in game.players[0].hand))

    def test_standard_garona_last_stand(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_110", 1)
        self.assertEqual("LEGENDARY", target.definition.rarity)
        spell = self.add_hand(game, "CATA_203")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)

    def test_standard_earthen_roar(self):
        game = self.game()
        first = self.add_board(game, "TLC_248", 1)
        second = self.add_board(game, "CORE_LOOT_137", 1)
        dragon = game._entity("CORE_LOOT_137")
        game.players[0].hand.append(dragon)
        spell = self.add_hand(game, "CATA_554")
        game.step(Action("PLAY", spell.entity_id, 1, first.entity_id))
        self.assertEqual(1, first.max_health)
        self.assertEqual("EARTHEN_ROAR_PICK", game.pending_choice["kind"])
        game.step(Action("EARTHEN_ROAR_PICK", second.entity_id))
        self.assertEqual(1, second.max_health)

    def test_standard_sylvanas_triumph_repeat(self):
        game = self.game()
        game.players[1].health = 30
        first = self.add_hand(game, "CATA_557")
        game.step(Action("PLAY", first.entity_id))
        self.assertEqual(27, game.players[1].health)
        second = self.add_hand(game, "CATA_557")
        game.step(Action("PLAY", second.entity_id))
        self.assertEqual(24, game.players[1].health)

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

    def test_shaladrassil_generates_regular_or_corrupted_dream_set(self):
        regular = self.game()
        spell = self.add_hand(regular, "EDR_846")
        regular.step(Action("PLAY", spell.entity_id))
        self.assertEqual(
            {"DREAM_01", "DREAM_02", "DREAM_03", "DREAM_04", "DREAM_05"},
            {card.card_id for card in regular.players[0].hand},
        )

        corrupted = self.game()
        spell = self.add_hand(corrupted, "EDR_846")
        higher_cost = self.add_hand(corrupted, "JAIL_514")
        corrupted.step(Action("PLAY", higher_cost.entity_id))
        corrupted.step(Action("PLAY", spell.entity_id))
        self.assertTrue(
            {"EDR_846t1", "EDR_846t2", "EDR_846t3", "EDR_846t4", "EDR_846t5"}
            .issubset({card.card_id for card in corrupted.players[0].hand})
        )

    def test_shaladrassil_generated_dream_spells_follow_their_rules(self):
        game = self.game()
        target = self.add_board(game, "CORE_CS2_065", 1)
        nightmare = self.add_hand(game, "DREAM_05")
        game.step(Action("PLAY", nightmare.entity_id, 1, target.entity_id))
        self.assertEqual((target.definition.attack + 5, target.definition.health + 5), (target.attack, target.max_health))
        game._start_turn(1)
        game._start_turn(0)
        self.assertNotIn(target, game.players[1].board)

        game = self.game()
        target = self.add_board(game, "CORE_CS2_065", 1)
        dream = self.add_hand(game, "DREAM_04")
        game.step(Action("PLAY", dream.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertIn(target, game.players[1].hand)

        game = self.game()
        ysera = self.add_board(game, "EX1_572", 0)
        other = self.add_board(game, "CORE_LOOT_137", 1)
        awakening = self.add_hand(game, "DREAM_02")
        game.step(Action("PLAY", awakening.entity_id))
        self.assertEqual(ysera.definition.health, ysera.health)
        self.assertEqual(other.definition.health - 5, other.health)

        game = self.game()
        target = self.add_board(game, "CORE_CS2_065", 1)
        nightmare = self.add_hand(game, "EDR_846t1")
        game.step(Action("PLAY", nightmare.entity_id, 1, target.entity_id))
        self.assertTrue(target.immune)
        self.assertEqual((target.definition.attack + 5, target.definition.health + 5), (target.attack, target.max_health))
        game._start_turn(1)
        self.assertFalse(target.immune)
        self.assertEqual((target.definition.attack, target.definition.health), (target.attack, target.max_health))

    def test_corrupted_laughing_sister_makes_hero_elusive_to_spells(self):
        game = self.game()
        self.add_board(game, "EDR_846t3", 1)
        spell = self.add_hand(game, "JAIL_941t")
        targets = {
            (action.target_player, action.target_entity)
            for action in game.legal_actions()
            if action.kind == "PLAY" and action.source == spell.entity_id
        }
        self.assertNotIn((1, None), targets)

    def test_atiesh_doubles_generic_spell_damage_and_healing(self):
        damage_game = self.game()
        damage_game.players[0].weapon = Weapon("TIME_890t", "Atiesh the Greatstaff", 1, 3)
        spell = self.add_hand(damage_game, "END_007")
        damage_game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(28, damage_game.players[1].health)

        heal_game = self.game()
        heal_game.players[0].weapon = Weapon("TIME_890t", "Atiesh the Greatstaff", 1, 3)
        heal_game.players[0].health = 20
        spell = self.add_hand(heal_game, "JAIL_941")
        heal_game.step(Action("PLAY", spell.entity_id, 0, None))
        self.assertEqual(28, heal_game.players[0].health)

    def test_medivh_battlecry_and_fabled_cost_reductions(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_CS2_065", 0)
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        medivh = self.add_hand(game, "TIME_890")
        game.step(Action("PLAY", medivh.entity_id))
        self.assertIn(medivh, game.players[0].board)
        self.assertNotIn(friendly, game.players[0].board)
        self.assertNotIn(enemy, game.players[1].board)

        location = Location(99_890, "TIME_890t2", durability=2, cooldown=0)
        game.players[0].locations.append(location)
        second_medivh = game._entity("TIME_890")
        self.assertEqual(0, game._effective_cost(game.players[0], second_medivh))
        atiesh = game._entity("TIME_890t")
        self.assertEqual(0, game._effective_cost(game.players[0], atiesh))

        game.players[0].weapon = Weapon("TIME_890t", "Atiesh the Greatstaff", 1, 3)
        sanctum = game._entity("TIME_890t2")
        self.assertEqual(0, game._effective_cost(game.players[0], sanctum))

    def test_arisen_onyxia_colossal_wings_health_costs_and_replacement(self):
        game = self.game()
        onyxia = self.add_hand(game, "CATA_155")
        game.step(Action("PLAY", onyxia.entity_id))
        self.assertEqual(
            ["CATA_155t", "CATA_155", "CATA_155t1"],
            [minion.card_id for minion in game.players[0].board],
        )
        generated = list(game.players[0].hand)
        self.assertEqual(2, len(generated))
        self.assertTrue(all(card.cost == 1 for card in generated))
        self.assertTrue(all(card.costs_health_expiry_turn == 1 for card in generated))

        game.players[0].mana = 0
        health_card = game._entity("CORE_CS2_065")
        health_card.costs_health_expiry_turn = game.turn
        game.players[0].hand.append(health_card)
        game.step(Action("PLAY", health_card.entity_id))
        self.assertEqual(0, game.players[0].mana)
        self.assertEqual((30, 31), (game.players[0].health, game.players[0].max_health))

        game._damage_hero(game.players[1], 4)
        self.assertEqual(26, game.players[1].health)
        game._start_turn(1)
        self.assertTrue(all(card.costs_health_expiry_turn == -1 for card in generated if card in game.players[0].hand))

    def test_godfrey_returns_overdrawn_cards_discounted_when_space_opens(self):
        game = self.game()
        player = game.players[0]
        player.deck = [game._entity("JAIL_509")]
        game._start_of_game()
        self.assertTrue(player.recover_overdrawn_cards)
        player.hand = [game._entity("GAME_005") for _ in range(10)]
        burned = game._entity("CORE_CS2_065", started_in_deck=True)
        player.deck = [burned]
        game._draw(player)
        self.assertEqual([], player.overdrawn_cards[:-1])
        self.assertIs(player.overdrawn_cards[-1], burned)
        self.assertEqual(burned.definition.cost - 1, burned.cost)
        removed = player.hand[0]
        game._pop_hand(player, removed.entity_id)
        self.assertIn(burned, player.hand)
        self.assertFalse(player.overdrawn_cards)

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

    def test_moonwell_damages_enemies_and_heals_friends(self):
        game = self.game()
        game.players[0].health = 25
        friendly = self.add_board(game, "CORE_LOOT_137", 0)
        friendly.damage = 3
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        enemy_health = enemy.health
        spell = self.add_hand(game, "EDR_476")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual((29, 26), (
            game.players[0].health, game.players[1].health,
        ))
        self.assertEqual(friendly.max_health, friendly.health)
        self.assertEqual(enemy_health - 4, enemy.health)

    def test_spider_rider_draws_after_hero_attack(self):
        game = self.game()
        self.add_board(game, "JAIL_872", 0)
        game.players[0].hero_attack_bonus = 1
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertEqual(1, len(game.players[0].hand))

    def test_holy_embrace_heals_and_generates_dark_embrace(self):
        game = self.game()
        game.players[0].health = 20
        spell = self.add_hand(game, "JAIL_941")
        game.step(Action("PLAY", spell.entity_id, 0, None))
        self.assertEqual(24, game.players[0].health)
        self.assertEqual(["JAIL_941t"], [
            card.card_id for card in game.players[0].hand
        ])

    def test_dark_embrace_deals_damage(self):
        game = self.game()
        spell = self.add_hand(game, "JAIL_941t")
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(26, game.players[1].health)

    def test_shadowsworn_disciple_heralds_and_heals_on_death(self):
        game = self.game()
        game.players[0].health = 20
        disciple = self.add_hand(game, "CATA_725")
        game.step(Action("PLAY", disciple.entity_id))
        self.assertEqual(1, game.players[0].herald_count)
        self.assertTrue(any(
            card.card_id == "CATA_580t" for card in game.players[0].board
        ))
        disciple.damage = disciple.max_health
        game._resolve_deaths()
        self.assertEqual(23, game.players[0].health)

    def test_annihilation_destroys_all_and_summons_bottom_demons(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("CORE_SW_068"),
            game._entity("CORE_LOOT_137"),
            game._entity("JAIL_007"),
        ]
        self.add_board(game, "CORE_LOOT_137", 0)
        self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "JAIL_510")
        game.step(Action("PLAY", spell.entity_id))
        self.assertFalse(game.players[1].board)
        self.assertEqual(
            {"CORE_SW_068", "JAIL_007"},
            {card.card_id for card in game.players[0].board},
        )

    def test_caged_cranium_counts_hand_after_play(self):
        game = self.game()
        cranium = self.add_hand(game, "JAIL_513")
        self.add_hand(game, "GAME_005")
        self.add_hand(game, "GAME_005")
        game.step(Action("PLAY", cranium.entity_id))
        self.assertEqual(cranium.definition.health + 2, cranium.max_health)

    def test_acceleration_aura_grants_three_future_temporary_crystals(self):
        game = self.game()
        game.players[0].max_mana = 5
        spell = self.add_hand(game, "END_011")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(3, game.players[0].start_turn_temporary_mana_charges)
        for maximum, remaining in ((6, 2), (7, 1), (8, 0)):
            game._start_turn(0)
            self.assertEqual(maximum, game.players[0].max_mana)
            self.assertEqual(maximum + 1, game.players[0].mana)
            self.assertEqual(
                remaining, game.players[0].start_turn_temporary_mana_charges
            )
        game._start_turn(0)
        self.assertEqual(9, game.players[0].mana)

    def test_shrine_of_twilight_location_heralds_and_draws(self):
        game = self.game()
        location = Location(90_001, "CATA_492", durability=2, cooldown=0)
        game.players[0].locations.append(location)
        game.step(Action("LOCATION", location.entity_id))
        self.assertEqual(1, game.players[0].herald_count)
        self.assertEqual((1, 2), (location.durability, location.cooldown))
        self.assertEqual(1, len(game.players[0].hand))
        self.assertTrue(any(
            card.card_id == "CATA_580t" for card in game.players[0].board
        ))

    def test_waveshaping_discovers_from_deck_and_bottoms_others(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("GAME_005"),
            game._entity("CORE_CS2_065"),
            game._entity("CORE_LOOT_137"),
        ]
        spell = self.add_hand(game, "TIME_701")
        game.step(Action("PLAY", spell.entity_id))
        options = list(game.pending_choice["options"])
        chosen = options[0]
        game.step(Action("DISCOVER_PICK", chosen.entity_id))
        self.assertIn(chosen, game.players[0].hand)
        self.assertEqual(2, len(game.players[0].deck))
        self.assertFalse(chosen.temporary)
        self.assertEqual(
            [card.entity_id for card in options[1:]],
            [card.entity_id for card in game.players[0].deck],
        )

    def test_cursed_catacombs_discovers_temporary_deck_card(self):
        game = self.game()
        card = game._entity("GAME_005")
        game.players[0].deck = [card]
        spell = self.add_hand(game, "TLC_451")
        game.step(Action("PLAY", spell.entity_id))
        game.step(Action("DISCOVER_PICK", card.entity_id))
        self.assertIn(card, game.players[0].hand)
        self.assertTrue(card.temporary)
        game._end_turn()
        self.assertNotIn(card, game.players[0].hand)

    def test_unseen_atlas_costs_less_per_hand_card_and_draws(self):
        game = self.game()
        atlas = self.add_hand(game, "JAIL_514")
        self.add_hand(game, "GAME_005")
        self.add_hand(game, "GAME_005")
        self.add_hand(game, "GAME_005")
        self.assertEqual(6, game._effective_cost(game.players[0], atlas))
        game.step(Action("PLAY", atlas.entity_id))
        self.assertEqual(14, game.players[0].mana)
        self.assertEqual(6, len(game.players[0].hand))

    def test_cursed_chains_temporarily_controls_and_returns_minion(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "CATA_496")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertIn(target, game.players[0].board)
        self.assertNotIn(target, game.players[1].board)
        self.assertTrue(target.cant_attack_turn == game.turn)
        game._end_turn()  # Player 1's turn starts; control is retained.
        self.assertIn(target, game.players[0].board)
        game._end_turn()  # End of the original owner's turn returns control.
        self.assertIn(target, game.players[1].board)
        self.assertNotIn(target, game.players[0].board)

    def test_ruthless_custom_hero_power(self):
        game = self.game()
        game.players[0].hero_power_id = "CATA_190p"
        game.players[0].mana = 2
        self.assertEqual(2, game._hero_power_cost(game.players[0]))
        game.step(Action("HERO_POWER"))
        self.assertEqual(5, game.players[0].hero_attack_bonus)
        self.assertTrue(game.players[0].hero_power_used)

    def test_deathwing_worldbreaker_unleashes_distinct_cataclysms(self):
        game = self.game()
        game.players[0].herald_count = 2
        game.players[0].armor = 3
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        enemy.health_delta = 8
        deathwing = self.add_hand(game, "CATA_190h")
        game.step(Action("PLAY", deathwing.entity_id))
        self.assertEqual("CATA_190p", game.players[0].hero_power_id)
        self.assertEqual(15, game.players[0].armor)
        self.assertEqual("DEATHWING_CATACLYSM", game.pending_choice["kind"])
        self.assertEqual(2, game.pending_choice["remaining"])
        # Topple targets highest current Health.  The second choice cannot
        # select Topple again and sees the state left by the first choice.
        topple = game.pending_choice["options"].index("CATA_190t11")
        game.step(Action("CATACLYSM_PICK", topple))
        self.assertNotIn(enemy, game.players[1].board)
        self.assertEqual(1, game.pending_choice["remaining"])
        self.assertNotIn("CATA_190t11", game.pending_choice["options"])
        reign = game.pending_choice["options"].index("CATA_190t10")
        game.step(Action("CATACLYSM_PICK", reign))
        self.assertIsNone(game.pending_choice)
        self.assertTrue(any(
            minion.card_id == "CATA_190t14" for minion in game.players[0].board
        ))

    def test_deathwing_enthrall_shuffles_discounted_closed_pool_dragons(self):
        game = self.game()
        game._unleash_deathwing_cataclysm(game.players[0], "CATA_190t13")
        generated = [card for card in game.players[0].deck if card.created_by == "CATA_190t13"]
        self.assertEqual(5, len(generated))
        self.assertTrue(all(card.cost == 1 for card in generated))
        self.assertTrue(all(
            card.definition.rarity == "LEGENDARY" and card.has_race("DRAGON")
            for card in generated
        ))

    def test_lunarwing_messenger_imbues_hero_power(self):
        game = self.game()
        messenger = self.add_hand(game, "EDR_449")
        game.step(Action("PLAY", messenger.entity_id))
        self.assertEqual("EDR_449p", game.players[0].hero_power_id)
        self.assertTrue(any(x.kind == "HERO_POWER" for x in game.legal_actions()))

    def test_bitterbloom_knight_imbues_priest_power(self):
        game = self.game()
        game.players[0].card_class = "PRIEST"
        knight = self.add_hand(game, "EDR_852")
        game.step(Action("PLAY", knight.entity_id))
        self.assertEqual("EDR_449p", game.players[0].hero_power_id)

    def test_azalina_rebuilds_starting_deck_and_draws_to_hand_limit(self):
        game = DragonMirrorGame(
            CARDS, 43,
            deck_counts=(
                {"JAIL_430": 1, "GAME_005": 29},
                {"CORE_CS2_004": 30},
            ),
            player_classes=("PRIEST", "WARRIOR"),
        )
        player = game.players[0]
        all_starting_cards = player.hand + player.deck
        self.assertEqual(40, player.max_health)
        self.assertEqual(40, len(all_starting_cards))
        self.assertEqual(20, sum(
            card.created_by == "JAIL_430" for card in all_starting_cards
        ))

        game = self.game()
        for _ in range(3):
            self.add_hand(game, "GAME_005")
        azalina = self.add_hand(game, "JAIL_430")
        game.step(Action("PLAY", azalina.entity_id))
        self.assertEqual(10, len(game.players[0].hand))
        self.assertTrue(any(
            event["kind"] == "azalina_draw_to_full" and event["drawn"] == 7
            for event in game.events
        ))

    def test_azalina_copies_trigger_mind_sweeper(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        sweeper = self.add_hand(game, "JAIL_432")
        copied_location = game._entity("CORE_REV_990", started_in_deck=True)
        copied_location.copied_from_opponent = True
        copied_location.created_by = "JAIL_430"
        game.players[0].hand.append(copied_location)
        game.step(Action("PLAY", copied_location.entity_id))
        self.assertTrue(sweeper.opponent_card_copy_played_while_held)
        game.step(Action("PLAY", sweeper.entity_id))
        self.assertEqual(2, enemy.damage)

    def test_amirdrassil_increments_its_mana_refresh_each_use(self):
        game = self.game()
        location_card = self.add_hand(game, "FIR_907")
        game.step(Action("PLAY", location_card.entity_id))
        location = game.players[0].locations[0]
        # Locations enter play exhausted; make the next-turn ready state
        # explicit so this test exercises the activation rather than bypassing
        # the generic cooldown rule.
        location.cooldown = 0
        game.players[0].mana = 3
        game.step(Action("LOCATION", location.entity_id))
        self.assertEqual(4, game.players[0].mana)
        self.assertEqual(1, game.players[0].armor)
        self.assertEqual(2, location.next_refresh)
        self.assertTrue(any(
            minion.definition.cost == 1 for minion in game.players[0].board
        ))

        location.cooldown = 0
        game.players[0].mana = 3
        game.step(Action("LOCATION", location.entity_id))
        self.assertEqual(5, game.players[0].mana)
        self.assertEqual(2, game.players[0].armor)
        self.assertEqual(3, location.next_refresh)

    def test_merithra_fills_hand_with_executable_dragons_and_discount_gate(self):
        game = self.game()
        for _ in range(3):
            self.add_hand(game, "GAME_005")
        merithra = self.add_hand(game, "CATA_140")
        game.step(Action("PLAY", merithra.entity_id))
        generated = [
            card for card in game.players[0].hand
            if card.created_by == "CATA_140"
        ]
        self.assertEqual(7, len(generated))
        self.assertTrue(all(card.has_race("DRAGON") for card in generated))
        self.assertTrue(any(card.cost != 1 for card in generated))

        game = self.game()
        for _ in range(3):
            self.add_hand(game, "GAME_005")
        merithra = self.add_hand(game, "CATA_140")
        merithra.mana_spent_while_held = 25
        game.step(Action("PLAY", merithra.entity_id))
        generated = [
            card for card in game.players[0].hand
            if card.created_by == "CATA_140"
        ]
        self.assertEqual(7, len(generated))
        self.assertTrue(all(card.cost == 1 for card in generated))

    def test_infest_scullery_scales_summon_cost_with_hero_attacks(self):
        game = self.game()
        game.players[0].hero_attacks_this_game = 3
        spell = self.add_hand(game, "JAIL_200")
        game.step(Action("PLAY", spell.entity_id))
        generated = [
            minion for minion in game.players[0].board
            if minion.created_by == "JAIL_200"
        ]
        self.assertEqual(2, len(generated))
        self.assertTrue(all(minion.definition.cost == 6 for minion in generated))

        game = self.game()
        game.players[0].hero_attacks_this_game = 11
        spell = self.add_hand(game, "JAIL_200")
        game.step(Action("PLAY", spell.entity_id))
        generated = [
            minion for minion in game.players[0].board
            if minion.created_by == "JAIL_200"
        ]
        self.assertEqual(2, len(generated))
        self.assertTrue(all(minion.definition.cost == 10 for minion in generated))

    def test_blessing_of_the_moon_offers_discounted_temporary_cards(self):
        game = self.game()
        game.players[0].hero_power_id = "EDR_449p"
        game.players[0].mana = 10
        game.step(Action("HERO_POWER"))
        self.assertEqual("IMBUE_PICK", game.pending_choice["kind"])
        options = list(game.pending_choice["options"])
        self.assertEqual({"MINION", "SPELL"}, {
            card.definition.card_type for card in options
        })
        self.assertTrue(all(
            card.definition.card_class == "PRIEST"
            and card.cost == max(0, card.definition.cost - 1)
            and card.temporary
            for card in options
        ))
        chosen = options[0]
        game.step(Action("DISCOVER_PICK", chosen.entity_id))
        self.assertIn(chosen, game.players[0].hand)
        game._end_turn()
        self.assertNotIn(chosen, game.players[0].hand)

    def test_kaldorei_priestess_reduces_then_restores_enemy_attack(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        before = enemy.attack
        priestess = self.add_hand(game, "EDR_970")
        game.step(Action("PLAY", priestess.entity_id))
        self.assertEqual(before - 2, enemy.attack)
        self.assertEqual("EDR_449p", game.players[0].hero_power_id)
        game._start_turn(0)
        self.assertEqual(before, enemy.attack)

    def test_soothsayer_deathrattle_heals_and_summons_six_cost(self):
        game = self.game()
        game.players[0].health = 20
        soothsayer = self.add_hand(game, "JAIL_912")
        game.step(Action("PREPARE", soothsayer.entity_id))
        game._end_turn()
        game._end_turn()
        game.step(Action("PLAY", soothsayer.entity_id))
        game._damage_minion(0, soothsayer, soothsayer.health)
        game._resolve_deaths()
        self.assertEqual(26, game.players[0].health)
        summoned = [card for card in game.players[0].board if card != soothsayer]
        self.assertEqual(1, len(summoned))
        self.assertEqual("MINION", summoned[0].definition.card_type)
        self.assertEqual(6, summoned[0].definition.cost)

    def test_atlasaurus_deathrattle_summons_large_taunt(self):
        game = self.game()
        atlasaurus = self.add_board(game, "DINO_431", 0)
        game._damage_minion(0, atlasaurus, atlasaurus.health)
        game._resolve_deaths()
        self.assertEqual(1, len(game.players[0].board))
        summoned = game.players[0].board[0]
        self.assertGreaterEqual(summoned.definition.cost, 5)
        self.assertTrue(summoned.taunt)

    def test_harsh_sentence_applies_next_turn_tax_and_imp_formants(self):
        game = self.game()
        enemy_minion = game._entity("CORE_LOOT_137")
        game.players[1].hand.append(enemy_minion)
        sentence = self.add_hand(game, "CAP_404")
        game.step(Action("PLAY", sentence.entity_id))
        self.assertEqual(2, sum(
            card.card_id == "CAP_400t2t" for card in game.players[1].deck
        ))
        self.assertEqual(enemy_minion.definition.cost, game._effective_cost(
            game.players[1], enemy_minion
        ))
        game._end_turn()
        self.assertEqual(enemy_minion.definition.cost + 2, game._effective_cost(
            game.players[1], enemy_minion
        ))
        game._end_turn()
        self.assertEqual(enemy_minion.definition.cost, game._effective_cost(
            game.players[1], enemy_minion
        ))

    def test_mind_sweeper_tracks_opponent_card_copy_while_held(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        sweeper = self.add_hand(game, "JAIL_432")
        copied_card = self.add_hand(game, "GAME_005")
        copied_card.copied_from_opponent = True
        game.step(Action("PLAY", copied_card.entity_id))
        self.assertTrue(sweeper.opponent_card_copy_played_while_held)
        game.step(Action("PLAY", sweeper.entity_id))
        self.assertEqual(2, target.damage)

    def test_unshackle_soul_discounts_after_opponent_copy_and_destroys(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "JAIL_433")
        copied_card = self.add_hand(game, "GAME_005")
        copied_card.copied_from_opponent = True
        self.assertEqual(5, game._effective_cost(game.players[0], spell))
        game.step(Action("PLAY", copied_card.entity_id))
        self.assertEqual(1, game._effective_cost(game.players[0], spell))
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)

    def test_intertwined_fate_copies_one_card_from_each_deck(self):
        game = self.game()
        own = game._entity("GAME_005", started_in_deck=True)
        opponent = game._entity("CORE_LOOT_137", started_in_deck=True)
        game.players[0].deck = [own]
        game.players[1].deck = [opponent]
        spell = self.add_hand(game, "TIME_432")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual("INTERTWINED_FATE", game.pending_choice["kind"])
        first = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", first.entity_id))
        self.assertEqual("INTERTWINED_FATE_OPPONENT", game.pending_choice["kind"])
        second = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", second.entity_id))
        self.assertEqual(2, len(game.players[0].hand))
        self.assertFalse(first.copied_from_opponent)
        self.assertTrue(second.copied_from_opponent)
        self.assertEqual(1, len(game.players[0].deck))
        self.assertEqual(1, len(game.players[1].deck))

    def test_spire_of_solitude_summons_hand_sized_demon_and_attacks(self):
        game = self.game()
        for _ in range(3):
            self.add_hand(game, "GAME_005")
        target = self.add_board(game, "CORE_CS2_065", 1)
        location = Location(99_001, "JAIL_511", durability=2, cooldown=0)
        game.players[0].locations.append(location)
        game._use_location(Action("LOCATION", location.entity_id))
        self.assertNotIn(target, game.players[1].board)
        infiltrator = next(
            card for card in game.players[0].board if card.card_id == "JAIL_511t"
        )
        self.assertEqual((3, 3), (infiltrator.attack, infiltrator.max_health))
        self.assertEqual(1, location.durability)

    def test_staff_of_trickery_discovers_druid_card_discounted_by_attack(self):
        game = self.game()
        game.players[0].weapon = Weapon("JAIL_875", "Staff of Trickery", 4, 1)
        game.step(Action("HERO_ATTACK", target_player=1))
        self.assertIsNone(game.players[0].weapon)
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        options = game.pending_choice["options"]
        self.assertTrue(all(card.definition.card_class == "DRUID" for card in options))
        self.assertTrue(all(
            card.cost == max(0, card.definition.cost - 4) for card in options
        ))

    def test_horn_of_plenty_discovers_discounted_nature_spell(self):
        game = self.game()
        horn = self.add_hand(game, "EDR_270")
        game.step(Action("PLAY", horn.entity_id))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        options = game.pending_choice["options"]
        self.assertTrue(options)
        self.assertTrue(all(
            card.definition.card_type == "SPELL"
            and card.definition.spell_school == "NATURE"
            and card.cost == max(0, card.definition.cost - 2)
            for card in options
        ))

    def test_secret_ingredient_choose_one_attack_or_druid_card(self):
        attack_game = self.game()
        ingredient = self.add_hand(attack_game, "JAIL_201")
        attack_game.step(Action("PLAY", ingredient.entity_id))
        self.assertEqual("RULE_CHOICE", attack_game.pending_choice["kind"])
        attack_game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(2, attack_game.players[0].hero_attack_bonus)

        card_game = self.game()
        ingredient = self.add_hand(card_game, "JAIL_201")
        card_game.step(Action("PLAY", ingredient.entity_id))
        card_game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual(1, len(card_game.players[0].hand))
        self.assertEqual("DRUID", card_game.players[0].hand[0].definition.card_class)

    def test_grove_shaper_summons_treant_that_copies_nature_spell(self):
        game = self.game()
        self.add_board(game, "EDR_271", 0)
        horn = self.add_hand(game, "EDR_270")
        game.step(Action("PLAY", horn.entity_id))
        treant = next(
            card for card in game.players[0].board if card.card_id == "EDR_271t"
        )
        self.assertEqual("EDR_270", treant.deathrattle_copy_card_id)
        game._damage_minion(0, treant, treant.health)
        game._resolve_deaths()
        self.assertTrue(any(
            card.card_id == "EDR_270" and card.created_by == "EDR_271t"
            for card in game.players[0].hand
        ))

    def test_lifebloom_heals_friendly_characters_and_summons_eight_costs(self):
        game = self.game()
        game.players[0].health = 20
        friendly = self.add_board(game, "CORE_LOOT_137", 0)
        friendly.damage = 3
        spell = self.add_hand(game, "MEND_042")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(28, game.players[0].health)
        self.assertEqual(0, friendly.damage)
        summoned = [card for card in game.players[0].board if card != friendly]
        self.assertEqual(2, len(summoned))
        self.assertTrue(all(card.definition.cost == 8 for card in summoned))

    def test_batch_draw_damage_and_choose_one_cards(self):
        game = self.game()
        dead = self.add_board(game, "CORE_CS2_231", 1)
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        sweep = self.add_hand(game, "CATA_526")
        game.step(Action("PLAY", sweep.entity_id))
        self.assertNotIn(dead, game.players[1].board)
        self.assertEqual(1, len(game.players[0].hand))

        wrath_game = self.game()
        target = self.add_board(wrath_game, "CORE_LOOT_137", 1)
        wrath = self.add_hand(wrath_game, "CORE_EX1_154")
        wrath_game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        wrath_game.step(Action("PLAY", wrath.entity_id, 1, target.entity_id))
        self.assertEqual(
            ["damage_3", "damage_1_draw"],
            [label for label, _ in wrath_game.pending_choice["options"]],
        )
        wrath_game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual(1, target.damage)

    def test_batch_conditional_and_costed_draw_cards(self):
        game = self.game()
        game.players[0].deck = [game._entity("Core_CS2_200", started_in_deck=True)]
        story = self.add_hand(game, "TLC_231")
        game.step(Action("PLAY", story.entity_id))
        drawn = game.players[0].hand[-1]
        self.assertEqual("Core_CS2_200", drawn.card_id)
        self.assertEqual(5, drawn.health_delta)
        self.assertEqual(5, game.players[0].armor)

        hybrid = self.add_hand(game, "TLC_236")
        game.players[0].deck = [
            game._entity("CORE_CS2_231", started_in_deck=True),
            game._entity("CORE_CS2_120", started_in_deck=True),
            game._entity("CORE_GVG_044", started_in_deck=True),
            game._entity("CORE_CS2_182", started_in_deck=True),
        ]
        game.step(Action("PLAY", hybrid.entity_id))
        self.assertEqual(4, len(game.players[0].hand))

    def test_batch_direct_damage_rules(self):
        game = self.game()
        game.players[0].health = 20
        target = self.add_board(game, "CORE_LOOT_137", 1)
        strike = self.add_hand(game, "RLK_024")
        game.step(Action("PLAY", strike.entity_id, 1, target.entity_id))
        self.assertEqual(6, target.damage)
        self.assertEqual(26, game.players[0].health)

        sweep = self.add_hand(game, "CATA_156")
        enemy = self.add_board(game, "CORE_CS2_231", 1)
        game.step(Action("PLAY", sweep.entity_id))
        self.assertEqual(26, game.players[1].health)
        self.assertEqual(4, enemy.damage)

    def test_living_roots_choose_one(self):
        damage_game = self.game()
        target = self.add_board(damage_game, "CORE_LOOT_137", 1)
        roots = self.add_hand(damage_game, "CORE_AT_037")
        damage_game.step(Action("PLAY", roots.entity_id, 1, target.entity_id))
        damage_game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(2, target.damage)

        summon_game = self.game()
        roots = self.add_hand(summon_game, "CORE_AT_037")
        summon_game.step(Action("PLAY", roots.entity_id))
        summon_game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual(2, len(summon_game.players[0].board))

    def test_frostbolt_and_blizzard_freeze_targets(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        frostbolt = self.add_hand(game, "CORE_CS2_024")
        game.step(Action("PLAY", frostbolt.entity_id, 1, target.entity_id))
        self.assertEqual(3, target.damage)
        self.assertEqual(game.turn, target.frozen_turn)

        blizzard = self.add_hand(game, "CORE_CS2_028")
        second = self.add_board(game, "CORE_CS2_231", 1)
        game.step(Action("PLAY", blizzard.entity_id))
        self.assertEqual(5, target.damage)
        self.assertEqual(2, second.damage)
        self.assertEqual(game.turn, target.frozen_turn)
        self.assertEqual(game.turn, second.frozen_turn)

    def test_frostwyrms_fury_damage_freeze_summon(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        other = self.add_board(game, "CORE_CS2_231", 1)
        fury = self.add_hand(game, "CORE_RLK_063")
        game.step(Action("PLAY", fury.entity_id, 1, target.entity_id))
        self.assertEqual(5, target.damage)
        self.assertEqual(game.turn, target.frozen_turn)
        self.assertEqual(game.turn, other.frozen_turn)
        self.assertTrue(any(card.card_id == "RLK_063t" for card in game.players[0].board))

    def test_wound_prey_damage_summon(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        prey = self.add_hand(game, "CORE_BAR_801")
        game.step(Action("PLAY", prey.entity_id, 1, target.entity_id))
        self.assertEqual(1, target.damage)
        self.assertTrue(any(card.card_id == "BAR_035t" for card in game.players[0].board))

    def test_infested_breath_damage_summon(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        breath = self.add_hand(game, "EDR_814")
        game.step(Action("PLAY", breath.entity_id, 1, target.entity_id))
        self.assertEqual(2, target.damage)
        self.assertTrue(any(card.card_id == "EDR_810t" for card in game.players[0].board))

    def test_sleet_storm_fixed_and_random_damage(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        storm = self.add_hand(game, "CATA_485")
        game.step(Action("PLAY", storm.entity_id))
        self.assertEqual(28, game.players[1].health)
        self.assertEqual(1, enemy.damage)

    def test_drink_blood_lifesteal_refresh(self):
        game = self.game()
        game.players[0].health = 20
        game.players[0].hero_power_used = True
        target = self.add_board(game, "CORE_LOOT_137", 1)
        drink = self.add_hand(game, "JAIL_441")
        game.step(Action("PLAY", drink.entity_id, 1, target.entity_id))
        self.assertEqual(3, target.damage)
        self.assertEqual(23, game.players[0].health)
        self.assertFalse(game.players[0].hero_power_used)

    def test_void_blast_generates_void_soul(self):
        game = self.game()
        target = self.add_board(game, "CORE_CS2_231", 1)
        blast = self.add_hand(game, "JAIL_891")
        game.step(Action("PLAY", blast.entity_id, 1, target.entity_id))
        self.assertFalse(any(card is target for card in game.players[1].board))
        self.assertTrue(any(card.card_id == "JAIL_732" for card in game.players[0].hand))

    def test_life_cycle_replaces_same_cost(self):
        game = self.game()
        target = self.add_board(game, "CORE_CS2_231", 1)
        cycle = self.add_hand(game, "TLC_235")
        game.step(Action("PLAY", cycle.entity_id, 1, target.entity_id))
        self.assertFalse(any(card is target for card in game.players[1].board))
        replacement = game.players[1].board[0]
        self.assertEqual(0, replacement.definition.cost)

    def test_frost_strike_rune_discover(self):
        game = self.game()
        target = self.add_board(game, "CORE_CS2_231", 1)
        strike = self.add_hand(game, "RLK_025")
        game.step(Action("PLAY", strike.entity_id, 1, target.entity_id))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertTrue(all(
            game.card_defs[cid].card_class == "DEATHKNIGHT"
            and game.card_defs[cid].rune_cost.get("frost", 0) > 0
            for cid in game.pending_choice["pool"]
        ))

    def test_static_shock_damage_attack(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        shock = self.add_hand(game, "TIME_218")
        game.step(Action("PLAY", shock.entity_id, 1, target.entity_id))
        self.assertEqual(1, target.damage)
        self.assertEqual(1, game.players[0].hero_attack_bonus)

    def test_spirit_bomb_self_damage(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        bomb = self.add_hand(game, "CORE_BOT_222")
        game.step(Action("PLAY", bomb.entity_id, 1, target.entity_id))
        self.assertEqual(4, target.damage)
        self.assertEqual(26, game.players[0].health)

    def test_cower_in_fear_beast_discount(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 1)
        fear = self.add_hand(game, "TLC_823")
        beast = self.add_hand(game, "EDR_810t")
        game.step(Action("PLAY", fear.entity_id, 1, target.entity_id))
        self.assertEqual(2, game.players[0].next_beast_cost_reduction)
        before = game.players[0].mana
        game.step(Action("PLAY", beast.entity_id))
        self.assertEqual(before - max(0, beast.definition.cost - 2), game.players[0].mana)
        self.assertEqual(0, game.players[0].next_beast_cost_reduction)

    def test_heartroot_stones_repeat(self):
        game = self.game()
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True) for _ in range(2)]
        stones = self.add_hand(game, "MEND_043")
        game.step(Action("PLAY", stones.entity_id))
        self.assertEqual(2, len(game.players[0].hand))
        self.assertEqual(6, game.players[0].armor)

    def test_fast_forward_draw_choose_discount(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("CORE_CS2_231", started_in_deck=True),
            game._entity("CORE_CS2_120", started_in_deck=True),
        ]
        fast = self.add_hand(game, "TIME_770")
        game.step(Action("PLAY", fast.entity_id))
        self.assertEqual("RULE_CHOICE", game.pending_choice["kind"])
        options = game.pending_choice["options"]
        game.step(Action("RULE_CHOICE_PICK", 0))
        discounted = next(card for card in game.players[0].hand if card.entity_id == options[0][1][0].entity_id)
        self.assertEqual(-2, discounted.cost_delta)

    def test_dark_bribe_draw_give(self):
        game = self.game()
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True) for _ in range(3)]
        bribe = self.add_hand(game, "JAIL_206")
        game.step(Action("PLAY", bribe.entity_id))
        self.assertEqual("RULE_CHOICE", game.pending_choice["kind"])
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(1, len(game.players[1].hand))
        self.assertEqual(2, len(game.players[0].hand))

    def test_arcane_flow_shatters_and_merges_at_hand_edges(self):
        game = self.game()
        game.players[0].hand.clear()
        game.players[0].deck = [game._entity("CATA_489", started_in_deck=True)]
        game._draw(game.players[0])
        self.assertEqual(["CATA_489t", "CATA_489t2"],
                         [card.card_id for card in game.players[0].hand])
        left, right = game.players[0].hand
        filler = game._entity("GAME_005")
        game.players[0].hand.insert(1, filler)
        game._normalize_shattered_hand(game.players[0])
        self.assertEqual(3, len(game.players[0].hand))
        game.players[0].hand.remove(filler)
        game._normalize_shattered_hand(game.players[0])
        self.assertEqual(["CATA_489"],
                         [card.card_id for card in game.players[0].hand])

    def test_arcane_flow_halves_and_merged_spell_have_correct_effects(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        game.players[1].health = 30
        left = self.add_hand(game, "CATA_489t")
        game.step(Action("PLAY", left.entity_id))
        self.assertEqual(26, game.players[1].health)

        right = self.add_hand(game, "CATA_489t2")
        game.step(Action("PLAY", right.entity_id))
        self.assertEqual(24, game.players[1].health)
        self.assertEqual(2, enemy.damage)

        merged = self.add_hand(game, "CATA_489")
        game.step(Action("PLAY", merged.entity_id))
        self.assertEqual(18, game.players[1].health)
        self.assertEqual(4, enemy.damage)

    def test_arcane_flow_hand_limit_keeps_left_piece_only(self):
        game = self.game()
        game.players[0].hand = [game._entity("GAME_005") for _ in range(9)]
        game._receive_drawn_card(game.players[0], game._entity("CATA_489"))
        self.assertEqual(10, len(game.players[0].hand))
        self.assertEqual("CATA_489t", game.players[0].hand[0].card_id)
        self.assertEqual(9, sum(card.card_id == "GAME_005" for card in game.players[0].hand))

    def test_arcane_flow_full_hand_burns_without_splitting(self):
        game = self.game()
        game.players[0].hand = [game._entity("GAME_005") for _ in range(10)]
        game._receive_drawn_card(game.players[0], game._entity("CATA_489"))
        self.assertEqual(10, len(game.players[0].hand))
        self.assertFalse(any(card.card_id.startswith("CATA_489t") for card in game.players[0].hand))

    def test_shatter_flight_maneuvers(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_LOOT_137", 0)
        spell = self.add_hand(game, "CATA_479")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, sum(card.card_id == "CATA_479t3" for card in game.players[0].board))
        self.assertEqual(1, friendly.attack_delta)
        self.assertTrue(friendly.divine_shield)

    def test_shatter_supply_run(self):
        game = self.game()
        held = self.add_hand(game, "CORE_LOOT_137")
        game.players[0].deck = [
            game._entity("CORE_LOOT_137", started_in_deck=True)
            for _ in range(3)
        ]
        spell = self.add_hand(game, "CATA_820")
        game.step(Action("PLAY", spell.entity_id))
        drawn = [card for card in game.players[0].hand if card.card_id == "CORE_LOOT_137"]
        self.assertEqual(4, len(drawn))
        self.assertTrue(all(card.attack_delta == 2 and card.health_delta == 2 for card in drawn))

    def test_shatter_wildwood_circle(self):
        game = self.game()
        friendly = self.add_board(game, "CORE_LOOT_137", 0)
        spell = self.add_hand(game, "CATA_134")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, sum(card.card_id == "CATA_134t3" for card in game.players[0].board))
        self.assertEqual("CATA_134t3", friendly.deathrattle_summon_card_id)
        friendly.damage = friendly.max_health
        game._resolve_deaths()
        self.assertEqual(3, sum(card.card_id == "CATA_134t3" for card in game.players[0].board))

    def test_shatter_schism(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 0)
        spell = self.add_hand(game, "CATA_306")
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertEqual(2, target.attack_delta)
        self.assertEqual(3, target.health_delta)
        self.assertTrue(target.elusive)
        copies = [card for card in game.players[0].board if card.entity_id != target.entity_id]
        self.assertEqual(1, len(copies))
        self.assertEqual(target.card_id, copies[0].card_id)
        self.assertEqual(target.attack, copies[0].attack)
        self.assertEqual(target.max_health, copies[0].max_health)

    def test_stolen_power_combined_shatter(self):
        game = self.game()
        game.players[0].card_class = "ROGUE"
        spell = self.add_hand(game, "CATA_202")
        game.step(Action("PLAY", spell.entity_id))
        generated = game.players[0].hand[-1]
        self.assertIn(generated.card_id, {"CATA_134", "CATA_306", "CATA_479", "CATA_489", "CATA_820"})
        self.assertTrue(generated.shatter_combined)

    def test_misplaced_pyromancer_shatter_trigger(self):
        game = self.game()
        pyromancer = self.add_board(game, "TIME_101", 0)
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        game._receive_drawn_card(game.players[0], game._entity("CATA_489"))
        self.assertEqual(2, enemy.damage)
        self.assertIn(pyromancer, game.players[0].board)

    def test_voltaic_burst(self):
        game = self.game()
        spell = self.add_hand(game, "CORE_BOT_451")
        game.step(Action("PLAY", spell.entity_id))
        sparks = [card for card in game.players[0].board if card.card_id == "BOT_102t"]
        self.assertEqual(2, len(sparks))
        self.assertTrue(all(card.rush for card in sparks))
        self.assertEqual(1, game.players[0].overload_next_turn)

    def test_silvermoon_portal(self):
        game = self.game()
        target = self.add_board(game, "CORE_LOOT_137", 0)
        spell = self.add_hand(game, "CORE_KAR_077")
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertEqual(2, target.attack_delta)
        self.assertEqual(2, target.health_delta)
        summoned = [card for card in game.players[0].board if card.entity_id != target.entity_id]
        self.assertEqual(1, len(summoned))
        self.assertEqual(2, summoned[0].definition.cost)

    def test_runed_orb(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "CORE_BAR_541")
        game.step(Action("PLAY", spell.entity_id, 1, enemy.entity_id))
        self.assertEqual(2, enemy.damage)
        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        options = game.pending_choice["options"]
        self.assertEqual(3, len(options))
        self.assertTrue(all(card.definition.card_type == "SPELL" for card in options))
        game.step(Action("DISCOVER_PICK", options[0].entity_id))
        self.assertEqual(1, len(game.players[0].hand))
        self.assertEqual("SPELL", game.players[0].hand[0].definition.card_type)

    def test_spectral_sight_outcast(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True)
            for _ in range(2)
        ]
        spell = self.add_hand(game, "CORE_BT_491")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, len(game.players[0].hand))

        game = self.game()
        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True)
            for _ in range(2)
        ]
        self.add_hand(game, "GAME_005")
        middle = self.add_hand(game, "CORE_BT_491")
        self.add_hand(game, "GAME_005")
        game.step(Action("PLAY", middle.entity_id))
        self.assertEqual(3, len(game.players[0].hand))

    def test_eye_beam_outcast_lifesteal(self):
        game = self.game()
        game.players[0].health = 20
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "CORE_BT_801")
        self.assertEqual(1, game._effective_cost(game.players[0], spell))
        game.step(Action("PLAY", spell.entity_id, 1, enemy.entity_id))
        self.assertEqual(3, enemy.damage)
        self.assertEqual(23, game.players[0].health)

    def test_deaths_advance(self):
        game = self.game()
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "CORE_CATA_009")
        game.step(Action("PLAY", spell.entity_id, 1, enemy.entity_id))
        self.assertGreaterEqual(enemy.frozen_turn, game.turn)
        self.assertIsNotNone(game.pending_choice)
        self.assertEqual("DISCOVER", game.pending_choice["kind"])

    def test_poison_breath(self):
        game = self.game()
        undead = self.add_board(game, "CAP_800", 0)
        spell = self.add_hand(game, "CORE_EDR_002")
        legal = game.legal_actions()
        self.assertIn(Action("PLAY", spell.entity_id, 0, undead.entity_id), legal)
        game.step(Action("PLAY", spell.entity_id, 0, undead.entity_id))
        self.assertTrue(undead.poisonous)

    def test_air_raid(self):
        game = self.game()
        spell = self.add_hand(game, "YOD_012")
        game.step(Action("PLAY", spell.entity_id))
        recruits = [card for card in game.players[0].board if card.card_id == "CS2_101t"]
        self.assertEqual(2, len(recruits))
        self.assertTrue(all(card.taunt for card in recruits))
        twin = next(card for card in game.players[0].hand if card.card_id == "YOD_012ts")
        game.step(Action("PLAY", twin.entity_id))
        self.assertEqual(4, sum(card.card_id == "CS2_101t" for card in game.players[0].board))

    def test_devouring_plague_random_lifesteal(self):
        game = self.game()
        game.players[0].health = 20
        first = self.add_board(game, "TLC_248", 1)
        second = self.add_board(game, "TLC_248", 1)
        spell = self.add_hand(game, "CORE_BAR_311")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(24, game.players[0].health)
        self.assertEqual(4, first.damage + second.damage)

    def test_counterspell(self):
        game = self.game()
        counter = self.add_hand(game, "CORE_EX1_287")
        game.step(Action("PLAY", counter.entity_id))
        self.assertEqual(["CORE_EX1_287"], [secret.card_id for secret in game.players[0].secrets])
        game.step(Action("END_TURN"))
        coin = game._entity("GAME_005")
        game.players[1].hand.append(coin)
        before = game.players[1].mana
        game.step(Action("PLAY", coin.entity_id))
        self.assertEqual([], game.players[0].secrets)
        self.assertEqual(before, game.players[1].mana)

    def test_ice_barrier(self):
        game = self.game()
        barrier = self.add_hand(game, "CORE_EX1_289")
        game.step(Action("PLAY", barrier.entity_id))
        game.step(Action("END_TURN"))
        game.players[1].hero_attack_bonus = 1
        game.step(Action("HERO_ATTACK", None, 0, None))
        self.assertEqual(29, game.players[0].health)
        self.assertEqual(8, game.players[0].armor)
        self.assertEqual([], game.players[0].secrets)

    def test_void_shard_lifesteal(self):
        game = self.game()
        game.players[0].health = 20
        shard = self.add_hand(game, "CORE_SW_442")
        game.step(Action("PLAY", shard.entity_id, 1, None))
        self.assertEqual(26, game.players[1].health)
        self.assertEqual(24, game.players[0].health)

    def test_initiation_summons_copy(self):
        game = self.game()
        target = self.add_board(game, "CAP_107t", 1)
        target.health_delta = -3
        spell = self.add_hand(game, "CORE_SCH_512")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertEqual(1, sum(m.card_id == "CAP_107t" for m in game.players[0].board))

    def test_healing_rain_random_split(self):
        game = self.game()
        game.players[0].health = 20
        ally = self.add_board(game, "CAP_107t", 0)
        ally.damage = 3
        rain = self.add_hand(game, "CORE_LOOT_373")
        game.step(Action("PLAY", rain.entity_id))
        self.assertGreaterEqual(game.players[0].health, 20)
        self.assertEqual(0, ally.damage)

    def test_wave_of_tar(self):
        game = self.game()
        enemy = self.add_board(game, "CAP_107t", 1)
        spell = self.add_hand(game, "TLC_439")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, enemy.damage)

    def test_imbue_threshold_cards(self):
        game = self.game()
        game.players[0].hero_power_imbues = 2
        picker = self.add_hand(game, "FIR_921")
        before = len(game.players[0].hand)
        game.step(Action("PLAY", picker.entity_id))
        self.assertEqual(before + 2 - 1, len(game.players[0].hand))

    def test_imbue_hero_power_druid(self):
        game = self.game()
        game.players[0].hero_power_id = "EDR_847p"
        game.players[0].mana = 2
        game.step(Action("HERO_POWER"))
        self.assertEqual(["EDR_847pt2"], [m.card_id for m in game.players[0].board])

    def test_imbue_progress_survives_temporary_hero_power(self):
        game = self.game()
        game.players[0].imbued_hero_power_id = "EDR_847p"
        game.players[0].hero_power_imbues = 2
        game.players[0].hero_power_id = "EDR_847p"
        game.step(Action("HERO_POWER"))
        self.assertEqual("EDR_847p", game.players[0].hero_power_id)
        self.assertEqual(2, game.players[0].hero_power_imbues)

    def test_imbue_hero_power_hunter(self):
        game = self.game()
        game.players[0].hero_power_id = "EDR_850p"
        beast = self.add_hand(game, "EDR_416t")
        before = beast.cost
        game.step(Action("HERO_POWER"))
        self.assertEqual(before - 1, beast.cost)
        self.assertEqual(1, beast.attack_delta)

    def test_imbue_hero_power_mage(self):
        game = self.game()
        game.players[0].hero_power_id = "END_000p"
        game.players[1].health = 30
        game.step(Action("HERO_POWER"))
        self.assertEqual(["CORE_CS2_231"], [m.card_id for m in game.players[0].board])
        self.assertEqual(29, game.players[1].health)

    def test_imbue_hero_power_shaman(self):
        game = self.game()
        game.players[0].hero_power_id = "EDR_448p"
        target = self.add_board(game, "CAP_107t", 0)
        game.step(Action("HERO_POWER"))
        self.assertNotEqual(target.entity_id, -1)
        self.assertEqual(1, len(game.players[0].board))
        self.assertLessEqual(game.players[0].board[0].cost, 0)

    def test_imbue_hero_power_rogue(self):
        game = self.game()
        game.players[0].card_class = "ROGUE"
        game.players[0].hero_power_id = "END_000p"
        before = len(game.players[0].hand)
        game.step(Action("HERO_POWER"))
        self.assertEqual(before + 1, len(game.players[0].hand))

    def test_imbue_hero_power_paladin(self):
        game = self.game()
        game.players[0].hero_power_id = "EDR_445p"
        before = len(game.players[0].deck)
        game.step(Action("HERO_POWER"))
        self.assertEqual(before + 2, len(game.players[0].deck))
        self.assertEqual(2, sum(c.card_id == "EDR_445pt3" for c in game.players[0].deck))

    def test_imbue_minion_batch(self):
        game = self.game()
        game.players[0].card_class = "PALADIN"
        drake = self.add_hand(game, "EDR_451")
        game.step(Action("PLAY", drake.entity_id))
        self.assertEqual("EDR_445p", game.players[0].hero_power_id)
        self.assertEqual(1, game.players[0].hero_power_imbues)

    def test_imbue_paladin_card_batch(self):
        game = self.game()
        game.players[0].card_class = "PALADIN"
        card = self.add_hand(game, "EDR_264")
        game.step(Action("PLAY", card.entity_id))
        self.assertEqual("EDR_445p", game.players[0].hero_power_id)
        self.assertTrue(game.players[0].board)
        self.assertTrue(game.players[0].board[0].taunt)

    def test_living_garden_imbue_discount(self):
        game = self.game()
        game.players[0].card_class = "SHAMAN"
        held = self.add_hand(game, "CAP_107t")
        garden = self.add_hand(game, "EDR_518")
        game.step(Action("PLAY", garden.entity_id))
        self.assertEqual("EDR_448p", game.players[0].hero_power_id)
        self.assertEqual(held.definition.cost - 1, held.cost)

    def test_wisprider_triggers_imbued_power(self):
        game = self.game()
        game.players[0].card_class = "MAGE"
        rider = self.add_hand(game, "EDR_519")
        game.step(Action("PLAY", rider.entity_id))
        self.assertEqual("EDR_851p", game.players[0].hero_power_id)
        self.assertTrue(game.players[0].board)
        self.assertEqual("CORE_CS2_231", game.players[0].board[-1].card_id)

    def test_neutral_imbue_uses_controller_class(self):
        game = self.game()
        game.players[0].card_class = "MAGE"
        guardian = self.add_hand(game, "EDR_800")
        game.step(Action("PLAY", guardian.entity_id))
        self.assertEqual("EDR_851p", game.players[0].hero_power_id)

    def test_neutral_imbue_weapon_uses_controller_class(self):
        game = self.game()
        game.players[0].card_class = "ROGUE"
        weapon = self.add_hand(game, "END_001")
        game.step(Action("PLAY", weapon.entity_id))
        self.assertEqual("END_000p", game.players[0].hero_power_id)

    def test_deathknight_imbue_first_undead_each_turn(self):
        game = self.game()
        game.players[0].card_class = "DEATHKNIGHT"
        game.players[0].hero_power_id = "END_003p"
        first = self.add_hand(game, "CORE_AT_003")
        second = self.add_hand(game, "CORE_AT_003")
        game.step(Action("PLAY", first.entity_id))
        game.step(Action("PLAY", second.entity_id))
        self.assertEqual(1, first.attack_delta)
        self.assertEqual(0, second.attack_delta)
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        third = self.add_hand(game, "CORE_AT_003")
        game.step(Action("PLAY", third.entity_id))
        self.assertEqual(1, third.attack_delta)

    def test_fleeing_treant_makes_next_power_free(self):
        game = self.game()
        game.players[0].card_class = "MAGE"
        game.players[0].mana = 5
        treant = self.add_hand(game, "EDR_500")
        game.step(Action("PLAY", treant.entity_id))
        self.assertEqual(0, game.players[0].hero_power_cost_override)
        game.players[0].hero_power_id = "END_000p"
        game.players[0].mana = 0
        game.step(Action("HERO_POWER"))
        self.assertIsNone(game.players[0].hero_power_cost_override)

    def test_eventuality_damages_and_imbues(self):
        game = self.game()
        game.players[0].card_class = "ROGUE"
        spell = self.add_hand(game, "END_000")
        game.players[0].mana = 5
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(28, game.players[1].health)
        self.assertEqual("END_000p", game.players[0].hero_power_id)


if __name__ == "__main__":
    unittest.main()
