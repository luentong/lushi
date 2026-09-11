from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import Action, DragonMirrorGame, Location, Weapon


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
        self.assertEqual((1, 1), (location.durability, location.cooldown))
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


if __name__ == "__main__":
    unittest.main()
