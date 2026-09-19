from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import (
    Action, DragonMirrorGame, HERALD_COLLECTIBLE_IDS, Location, LOST_CITY_QUEST_IDS,
    LOST_CITY_QUEST_REWARDS, STANDARD_VANILLA_IDS, Weapon,
)
from hsa.rules import ENGINE_OWNED_AUXILIARY_IDS


CARDS = ROOT / "cards.251332.enUS.json"


class FirstStandardCardBatchTests(unittest.TestCase):
    def test_all_current_standard_herald_cards_are_executable(self):
        game = self.game()
        self.assertTrue(HERALD_COLLECTIBLE_IDS <= game.executable_card_ids)

    def test_all_standard_prepare_cards_are_executable(self):
        prepare_ids = {
            "CAP_407", "JAIL_321", "JAIL_326", "JAIL_395", "JAIL_407",
            "JAIL_435", "JAIL_444", "JAIL_453", "JAIL_457", "JAIL_718",
            "JAIL_721", "JAIL_735", "JAIL_890", "JAIL_906", "JAIL_909",
            "JAIL_912", "JAIL_913", "JAIL_998",
        }
        game = self.game()
        self.assertTrue(prepare_ids <= game.executable_card_ids)

    def test_kindred_and_map_rule_cards_are_executable(self):
        rule_ids = {
            "TLC_226", "TLC_251", "TLC_366", "TLC_428", "TLC_429",
            "TLC_435", "TLC_440", "TLC_442", "TLC_447", "TLC_454",
            "TLC_464", "TLC_519", "TLC_815", "TLC_816", "TLC_824",
            "TLC_900", "TLC_903",
        }
        game = self.game()
        self.assertTrue(rule_ids <= game.executable_card_ids)

    def test_standard_location_batch_is_executable(self):
        game = self.game()
        self.assertTrue({"CATA_161", "CATA_301", "CATA_477", "CATA_527", "EDR_454", "EDR_520", "JAIL_877", "JAIL_887", "JAIL_987", "MEND_044", "TIME_044", "TIME_436", "TIME_446", "TIME_810", "TLC_449"}
                        <= game.executable_card_ids)

    def test_standard_choose_one_batch_is_executable(self):
        game = self.game()
        self.assertTrue({"CATA_569", "CATA_724", "CORE_AT_052", "CORE_EX1_250", "CORE_OG_044", "Core_LOE_115", "CORE_ONY_018", "CORE_TSC_650", "CS3_007", "EDR_233", "EDR_257", "EDR_263", "EDR_490", "EDR_525", "EDR_570", "EDR_843", "EDR_872", "END_010", "END_028", "JAIL_380", "TIME_601", "TLC_227"}
                        <= game.executable_card_ids)

    def test_boomkin_choose_one_deals_damage_or_heals(self):
        game = self.game()
        game.players[0].health = 20
        minion = self.add_hand(game, "CORE_ONY_018")
        game.step(Action("PLAY", minion.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual(26, game.players[1].health)

    def test_flipper_friends_choose_one_summons_orca_or_otters(self):
        game = self.game()
        spell = self.add_hand(game, "CORE_TSC_650")
        game.step(Action("PLAY", spell.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual(6, len(game.players[0].board))
        self.assertTrue(all(m.card_id == "TSC_650t4" for m in game.players[0].board))

    def test_raven_idol_choose_one_offers_type_discover(self):
        game = self.game()
        spell = self.add_hand(game, "Core_LOE_115")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(["discover_minion", "discover_spell"],
                         game.snapshot()["pending_choice"]["options"])
        game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertTrue(all(option.definition.card_type == "SPELL"
                            for option in game.pending_choice["options"]))

    def test_spark_of_life_choose_one_class_discover(self):
        game = self.game()
        spell = self.add_hand(game, "EDR_872")
        game.step(Action("PLAY", spell.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertTrue(all(option.definition.card_class == "MAGE"
                            or "MAGE" in getattr(option.definition, "classes", ())
                            for option in game.pending_choice["options"]))

    def test_reforestation_choose_one_draw_type(self):
        game = self.game()
        game.players[0].deck = [game._entity("CORE_CS2_023"), game._entity("CORE_EX1_005")]
        spell = self.add_hand(game, "EDR_843")
        game.step(Action("PLAY", spell.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual("CORE_EX1_005", game.players[0].hand[-1].card_id)

    def test_reforestation_upgrades_after_three_turns_held(self):
        game = self.game()
        spell = self.add_hand(game, "EDR_843")
        for _ in range(3):
            game._start_turn(0)
        self.assertEqual("EDR_843t1", spell.card_id)

    def test_twilight_timereaver_choose_one_sets_other_minion_stat(self):
        game = self.game()
        source = self.add_hand(game, "END_010")
        other = self.add_board(game, "CORE_EX1_005", 0)
        game.step(Action("PLAY", source.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(1, other.attack)

    def test_barbed_thorn_choose_one_grants_hero_poisonous(self):
        game = self.game()
        thorn = self.add_hand(game, "EDR_525")
        game.step(Action("PLAY", thorn.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(game.turn, game.players[0].hero_poisonous_until_turn)

    def test_fandral_combines_choose_one_effects(self):
        game = self.game()
        fandral = self.add_board(game, "CORE_OG_044", 0)
        self.assertEqual("CORE_OG_044", fandral.card_id)
        game.players[0].health = 20
        boomkin = self.add_hand(game, "CORE_ONY_018")
        game.step(Action("PLAY", boomkin.entity_id))
        self.assertIsNone(game.pending_choice)
        self.assertEqual(28, game.players[0].health)
        self.assertEqual(26, game.players[1].health)

    def test_getaway_hogdriver_draw_two_minions_and_gains_charge(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("CORE_EX1_005"), game._entity("CORE_CS2_172")
        ]
        driver = self.add_hand(game, "JAIL_462")
        game.step(Action("PLAY", driver.entity_id))
        self.assertTrue(driver.charge)
        self.assertEqual(2, len(game.players[0].hand))

    def test_arrow_retriever_draws_until_three_cards(self):
        game = self.game()
        game.players[0].deck = [game._entity("CORE_EX1_005") for _ in range(4)]
        retriever = self.add_hand(game, "TIME_601")
        game.step(Action("PLAY", retriever.entity_id))
        self.assertEqual(3, len(game.players[0].hand))

    def test_overload_minions_lock_next_turn_mana(self):
        game = self.game()
        totem = self.add_hand(game, "CORE_AT_052")
        game.step(Action("PLAY", totem.entity_id))
        self.assertEqual(1, game.players[0].overload_next_turn)
        elemental = self.add_hand(game, "CORE_EX1_250")
        game.step(Action("PLAY", elemental.entity_id))
        self.assertEqual(3, game.players[0].overload_next_turn)

    def test_for_all_time_destroys_only_attack_four_or_less(self):
        game = self.game()
        low = self.add_board(game, "CORE_EX1_005", 0)
        high = self.add_board(game, "CORE_EX1_005", 1, attack=5)
        spell = self.add_hand(game, "END_028")
        game.step(Action("PLAY", spell.entity_id))
        self.assertNotIn(low, game.players[0].board)
        self.assertIn(high, game.players[1].board)
        self.assertEqual(2, game.players[0].overload_next_turn)

    def test_novice_zapper_overloads_after_play(self):
        game = self.game()
        zapper = self.add_hand(game, "CS3_007")
        game.step(Action("PLAY", zapper.entity_id))
        self.assertEqual(1, game.players[0].overload_next_turn)

    def test_overload_hardcoded_cards_are_registered_for_audit(self):
        game = self.game()
        self.assertIn("JAIL_452", game.executable_card_ids)
        self.assertIn("TIME_014", game.executable_card_ids)
        self.assertIsNotNone(game.rule_registry.get("JAIL_452"))
        self.assertIsNotNone(game.rule_registry.get("TIME_014"))

    def test_smuggled_shovel_draws_only_generated_spell(self):
        game = self.game()
        generated = game._entity("CORE_CS2_013", started_in_deck=False)
        original = game._entity("CORE_CS2_013", started_in_deck=True)
        game.players[0].deck = [original, generated]
        shovel = self.add_board(game, "JAIL_380", 0)
        game._deathrattle(game.players[0], shovel)
        self.assertEqual(1, len(game.players[0].hand))
        self.assertEqual("CORE_CS2_013", game.players[0].hand[0].card_id)
        self.assertEqual(1, len(game.players[0].deck))

    def test_scaled_lancer_aura_adds_enemy_taunt_and_clears_on_silence(self):
        game = self.game()
        aura = self.add_board(game, "CATA_898", 0)
        enemy = self.add_board(game, "CORE_EX1_005", 1)
        self.assertTrue(game._has_taunt(1, enemy))
        aura.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertFalse(game._has_taunt(1, enemy))

    def test_raid_leader_aura_buffs_other_minions_only(self):
        game = self.game()
        leader = self.add_board(game, "CORE_CS2_122", 0)
        other = self.add_board(game, "CORE_EX1_005", 0)
        game._refresh_continuous(game.players[0])
        base = other.definition.attack
        self.assertEqual(base + 1, other.attack)
        self.assertEqual(leader.definition.attack, leader.attack)

    def test_continuous_aura_cards_are_registered_for_audit(self):
        game = self.game()
        for card_id in (
            "CATA_898", "CATA_613", "TLC_228", "CORE_WON_351", "JAIL_202",
            "EDR_480", "TTN_844", "CATA_130", "CAP_104", "CORE_BT_187",
            "CORE_CATA_001", "CORE_EDR_003", "EDR_810", "JAIL_890", "TIME_606",
        ):
            self.assertIsNotNone(game.rule_registry.get(card_id))

    def test_murloc_warleader_aura_buffs_other_murlocs_only(self):
        game = self.game()
        leader = self.add_board(game, "CORE_EX1_507", 0)
        other = self.add_board(game, "CORE_EX1_507", 0)
        game._refresh_continuous(game.players[0])
        self.assertEqual(leader.definition.attack, leader.attack)
        self.assertEqual(other.definition.attack + 2, other.attack)
        leader.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertEqual(other.definition.attack, other.attack)

    def test_dire_wolf_aura_is_position_limited(self):
        game = self.game()
        left = self.add_board(game, "CORE_EX1_005", 0)
        wolf = self.add_board(game, "CORE_EX1_162", 0)
        right = self.add_board(game, "CORE_EX1_005", 0)
        far = self.add_board(game, "CORE_EX1_005", 0)
        game._refresh_continuous(game.players[0])
        self.assertEqual(left.definition.attack + 1, left.attack)
        self.assertEqual(right.definition.attack + 1, right.attack)
        self.assertEqual(far.definition.attack, far.attack)
        wolf.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertEqual(left.definition.attack, left.attack)
        self.assertEqual(right.definition.attack, right.attack)

    def test_arachnathid_aura_grants_poisonous_and_clears(self):
        game = self.game()
        aura = self.add_board(game, "JAIL_459", 0)
        target = self.add_board(game, "CORE_EX1_005", 0)
        game._refresh_continuous(game.players[0])
        self.assertTrue(aura.aura_poisonous)
        self.assertTrue(target.aura_poisonous)
        aura.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertFalse(target.aura_poisonous)

    def test_toreth_aura_expands_divine_shield(self):
        game = self.game()
        self.add_board(game, "EDR_258", 0)
        shielded = self.add_board(game, "CORE_EX1_008", 0)
        game._refresh_continuous(game.players[0])
        self.assertTrue(shielded.divine_shield)
        self.assertEqual(3, shielded.divine_shield_hits)

    def test_ido_spell_lifecycle(self):
        game = self.game()
        ido = self.add_board(game, "TLC_241", 0)
        game._refresh_continuous(game.players[0])
        self.assertEqual(1, sum(card.card_id == "TLC_241t" for card in game.players[0].hand))
        ido.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertFalse(any(card.card_id == "TLC_241t" for card in game.players[0].hand))

    def test_naralex_first_dragon_discount(self):
        game = self.game()
        game.players[0].board = [self.add_board(game, "EDR_844", 0)]
        dragon = game._entity("CORE_EX1_284")
        game.players[0].hand = [dragon]
        game._refresh_continuous(game.players[0])
        self.assertEqual(1, game._effective_cost(game.players[0], dragon))
        game.players[0].dragons_played_this_turn = 1
        self.assertGreater(game._effective_cost(game.players[0], dragon), 1)

    def test_blastpowder_engineer_adds_pirate_damage_only_on_own_turn(self):
        game = self.game()
        self.add_board(game, "CAP_104", 0)
        pirate = self.add_board(game, "CORE_NEW1_027", 0)
        self.assertEqual(2, game._modified_damage(1, pirate))
        game.current = 1
        self.assertEqual(1, game._modified_damage(1, pirate))

    def test_quel_dorei_fletcher_hero_power_threshold(self):
        game = self.game()
        game.players[0].hand = [game._entity("CORE_CS2_023") for _ in range(3)]
        self.add_board(game, "TIME_606", 0)
        self.assertEqual(0, game._hero_power_cost(game.players[0]))
        game.players[0].hand.append(game._entity("CORE_CS2_023"))
        self.assertGreater(game._hero_power_cost(game.players[0]), 0)

    def test_tichondrius_hero_immunity_clears_on_silence(self):
        game = self.game()
        demonlord = self.add_board(game, "CORE_CATA_001", 0)
        game._damage_hero(game.players[0], 5)
        self.assertEqual(30, game.players[0].health)
        demonlord.silenced = True
        game._damage_hero(game.players[0], 5)
        self.assertEqual(25, game.players[0].health)

    def test_falric_doubles_corpses_from_friendly_deaths(self):
        game = self.game()
        self.add_board(game, "CORE_EDR_003", 0)
        victim = self.add_board(game, "CORE_EX1_005", 0)
        victim.health = 0
        game._resolve_deaths()
        self.assertEqual(2, game.players[0].corpses)

    def test_captive_nathrezim_global_cost_aura_affects_both_hands(self):
        game = self.game()
        self.add_board(game, "JAIL_890", 0)
        own = game._entity("CORE_EX1_005")
        enemy = game._entity("CORE_EX1_005")
        game.players[0].hand = [own]
        game.players[1].hand = [enemy]
        self.assertEqual(4, game._effective_cost(game.players[0], own))
        self.assertEqual(4, game._effective_cost(game.players[1], enemy))
        game.players[0].board[0].silenced = True
        self.assertEqual(2, game._effective_cost(game.players[0], own))

    def test_captain_crowley_summons_cannoneers_and_adds_shots(self):
        game = self.game()
        captain = self.add_hand(game, "CAP_106")
        game.step(Action("PLAY", captain.entity_id))
        cannoneers = [m for m in game.players[0].board if m.card_id == "CAP_107t"]
        self.assertEqual(2, len(cannoneers))
        self.assertEqual(1, sum(m.card_id == "CAP_106" for m in game.players[0].board))

    def test_si7_slayer_buffs_stealthed_attacker(self):
        game = self.game()
        self.add_board(game, "CAP_000", 0)
        attacker = self.add_board(game, "CORE_EX1_005", 0)
        attacker.stealth = True
        base_attack = attacker.attack
        game._after_minion_attack(0, attacker, was_stealthed=True)
        self.assertEqual(base_attack + 2, attacker.attack)
        self.assertEqual(attacker.definition.health + 2, attacker.max_health)

    def test_si7_supplier_draws_after_attack(self):
        game = self.game()
        supplier = self.add_board(game, "CAP_003", 0)
        supplier.stealth = True
        game.players[0].deck = [game._entity("AT_001")]
        game._after_minion_attack(0, supplier, was_stealthed=True)
        self.assertEqual(1, len(game.players[0].hand))

    def test_mathias_shaw_discounts_after_stealth_attack(self):
        game = self.game()
        self.add_board(game, "CAP_005", 0)
        attacker = self.add_board(game, "CORE_EX1_005", 0)
        attacker.stealth = True
        held = game._entity("CORE_CS2_023")
        game.players[0].hand = [held]
        game._after_minion_attack(0, attacker, was_stealthed=True)
        self.assertEqual(held.definition.cost - 3, held.cost)

    def test_king_maluk_discards_hand_for_infinite_banana(self):
        game = self.game()
        king = self.add_hand(game, "TIME_042")
        game.players[0].hand.append(game._entity("CORE_CS2_023"))
        game.step(Action("PLAY", king.entity_id))
        self.assertEqual(["TIME_042t"], [card.card_id for card in game.players[0].hand])
        target = self.add_board(game, "CORE_EX1_005", 0)
        banana = game.players[0].hand[0]
        game.step(Action("PLAY", banana.entity_id, target_player=0, target_entity=target.entity_id))
        self.assertEqual(1, target.attack - target.definition.attack)
        self.assertEqual(1, sum(card.card_id == "TIME_042t" for card in game.players[0].hand))

    def test_chronochiller_skips_start_turn_draw(self):
        game = self.game()
        self.add_board(game, "TIME_617", 0)
        game.players[0].deck = [game._entity("CORE_CS2_023", started_in_deck=True)]
        game._start_turn(0)
        self.assertEqual(1, len(game.players[0].deck))
        self.assertTrue(any(event["kind"] == "chronochiller_skip_draw" for event in game.events))

    def test_sheltered_survivor_shuffles_selected_hand_card(self):
        game = self.game()
        survivor = self.add_hand(game, "CATA_721")
        chosen = game._entity("CORE_CS2_023")
        game.players[0].hand.append(chosen)
        game.step(Action("PLAY", survivor.entity_id))
        self.assertEqual("HAND_DISCARD", game.pending_choice["kind"])
        game.step(Action("DISCARD_PICK", chosen.entity_id))
        self.assertEqual(1, len(game.players[0].hand))
        self.assertEqual("CORE_CS2_023", game.players[0].hand[0].card_id)
        self.assertEqual(0, len(game.players[0].deck))

    def test_asphyxiate_destroys_highest_attack_enemy(self):
        game = self.game()
        low = self.add_board(game, "CORE_EX1_005", 1)
        high = self.add_board(game, "CORE_EX1_005", 1)
        low.attack_delta = 1
        high.attack_delta = 5
        spell = self.add_hand(game, "CORE_RLK_087")
        game.step(Action("PLAY", spell.entity_id))
        self.assertIn(low, game.players[1].board)
        self.assertNotIn(high, game.players[1].board)

    def test_nascent_bolt_draws_two_if_survives(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        game.players[1].board[0].health_delta = 10
        game.players[0].deck = [game._entity("CORE_CS2_023") for _ in range(2)]
        spell = self.add_hand(game, "TIME_216")
        game.step(Action("PLAY", spell.entity_id, target_player=1, target_entity=target.entity_id))
        self.assertEqual(2, len(game.players[0].hand))

    def test_living_flame_draws_fire_spell(self):
        game = self.game()
        game.players[0].deck = [game._entity("AT_001")]
        flame = self.add_board(game, "FIR_929", 0)
        flame.health = 0
        game._resolve_deaths()
        self.assertEqual(1, len(game.players[0].hand))

    def test_temporal_construct_draws_excess(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        target.health_delta = -4
        game.players[0].deck = [game._entity("CORE_CS2_023")]
        construct = self.add_hand(game, "TIME_858")
        game.step(Action("PLAY", construct.entity_id, target_player=1, target_entity=target.entity_id))
        self.assertEqual(1, len(game.players[0].hand))

    def test_disciple_of_the_dove_draws_and_buffs_hand_minions(self):
        game = self.game()
        game.players[0].deck = [game._entity("CORE_EX1_005")]
        existing = game._entity("CORE_EX1_005")
        game.players[0].hand.append(existing)
        disciple = self.add_hand(game, "TIME_037")
        game.step(Action("PLAY", disciple.entity_id))
        self.assertEqual(2, len(game.players[0].hand))
        self.assertTrue(all(card.health_delta == 2 for card in game.players[0].hand))

    def test_emerald_bounty_locks_drawn_cards(self):
        game = self.game()
        game.players[0].deck = [game._entity("CORE_CS2_023") for _ in range(2)]
        spell = self.add_hand(game, "EDR_234")
        game.step(Action("PLAY", spell.entity_id))
        self.assertTrue(all(card.playable_after_turn == game.turn + 2 for card in game.players[0].hand))

    def test_precursory_strike_conditional_minion_draw(self):
        game = self.game()
        held = game._entity("CORE_EX1_005")
        held.cost_delta = 4
        game.players[0].hand.append(held)
        game.players[0].deck = [game._entity("CORE_EX1_005")]
        spell = self.add_hand(game, "TIME_750")
        game.step(Action("PLAY", spell.entity_id, target_player=1, target_entity=None))
        self.assertTrue(any(card.definition.card_type == "MINION" for card in game.players[0].hand))

    def test_muradins_last_stand_scales_with_attacks(self):
        game = self.game()
        game.players[0].hero_attacks_this_game = 3
        game.players[0].deck = [game._entity("CORE_CS2_023") for _ in range(2)]
        spell = self.add_hand(game, "CATA_568")
        self.assertEqual(6, game._effective_cost(game.players[0], spell))
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, len(game.players[0].hand))

    def test_morchok_draws_with_excess_discount(self):
        game = self.game()
        game.players[0].deck = [game._entity("CORE_CS2_023")]
        card = self.add_hand(game, "CATA_570")
        game.step(Action("PLAY", card.entity_id))
        self.assertEqual(1, len(game.players[0].hand))

    def test_primordial_overseer_nature_condition(self):
        game = self.game()
        nature = game._entity("AT_037")
        game.players[0].hand.append(nature)
        game.players[0].deck = [game._entity("CORE_CS2_023")]
        overseer = self.add_hand(game, "TIME_213")
        game.step(Action("PLAY", overseer.entity_id))
        self.assertEqual(1, overseer.attack_delta)
        self.assertEqual(2, len(game.players[0].hand))

    def test_for_glory_costs_less_per_enemy_minion(self):
        game = self.game()
        self.add_board(game, "CORE_EX1_005", 1)
        self.add_board(game, "CORE_EX1_005", 1)
        spell = self.add_hand(game, "TIME_715")
        self.assertEqual(3, game._effective_cost(game.players[0], spell))

    def test_eternal_toil_draws_if_target_survives(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        game.players[0].deck = [game._entity("CORE_CS2_023")]
        spell = self.add_hand(game, "END_020")
        game.step(Action("PLAY", spell.entity_id,
                         target_player=1, target_entity=target.entity_id))
        self.assertEqual(1, len(game.players[0].hand))
        self.assertIn(target, game.players[1].board)

    def test_felrattler_deathrattle_damages_enemy_minions(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        rattler = self.add_board(game, "CORE_WC_701", 0)
        rattler.damage = rattler.max_health
        game._resolve_deaths()
        self.assertEqual(1, target.damage)

    def test_rafaam_ladder_draws_different_costs(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("CORE_CS2_023"),
            game._entity("CORE_EX1_005"),
            game._entity("CORE_CS2_024"),
        ]
        game.players[0].deck[0].definition = game.card_defs["CORE_CS2_023"]
        spell = self.add_hand(game, "TIME_031")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(3, len(game.players[0].hand))
        self.assertEqual(3, len({card.definition.cost for card in game.players[0].hand}))

    def test_chronogor_draws_highest_and_gives_lowest(self):
        game = self.game()
        deck = [
            game._entity("CORE_CS2_023"),
            game._entity("CORE_EX1_005"),
            game._entity("CORE_CS2_029"),
            game._entity("CORE_CS2_062"),
        ]
        game.players[0].deck = deck
        construct = self.add_hand(game, "TIME_032")
        game.step(Action("PLAY", construct.entity_id))
        self.assertEqual(2, len(game.players[0].hand))
        self.assertEqual(2, len(game.players[1].hand))

    def test_liferender_requires_hero_health_change(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        target.health_delta = 10
        liferender = self.add_hand(game, "TIME_614")
        game.players[0].hero_health_changed_this_turn = True
        game.step(Action("PLAY", liferender.entity_id,
                         target_player=1, target_entity=target.entity_id))
        self.assertEqual(6, target.health)

    def test_gnome_muncher_attacks_lowest_health_enemy(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        target.damage = target.max_health - 1
        muncher = self.add_hand(game, "RLK_720")
        game.step(Action("PLAY", muncher.entity_id))
        game.step(Action("END_TURN"))
        self.assertNotIn(target, game.players[1].board)

    def test_sigil_of_cinder_triggers_next_turn(self):
        game = self.game()
        spell = self.add_hand(game, "FIR_902")
        game.step(Action("PLAY", spell.entity_id))
        before = game.players[1].health
        game._start_turn(0)
        self.assertLess(game.players[1].health, before)

    def test_tower_of_ghouls_summons_after_damage(self):
        game = self.game()
        tower = self.add_board(game, "JAIL_440", 0)
        game._damage_minion(0, tower, 1)
        self.assertEqual(2, sum(card.card_id == "JAIL_450t" for card in game.players[0].board))

    def test_tower_of_ghouls_triggers_before_lethal_death_processing(self):
        game = self.game()
        tower = self.add_board(game, "JAIL_440", 0)
        game._damage_minion(0, tower, tower.health)
        self.assertEqual(2, sum(card.card_id == "JAIL_450t" for card in game.players[0].board))
        game._resolve_deaths()
        self.assertEqual(2, sum(card.card_id == "JAIL_450t" for card in game.players[0].board))

    def test_gorishi_wasp_generates_stinger_after_damage(self):
        game = self.game()
        wasp = self.add_board(game, "TLC_630", 0)
        game._damage_minion(0, wasp, 1)
        self.assertTrue(any(card.card_id == "TLC_630t" for card in game.players[0].hand))

    def test_gorishi_wasp_generates_stinger_before_lethal_death_processing(self):
        game = self.game()
        wasp = self.add_board(game, "TLC_630", 0)
        game._damage_minion(0, wasp, wasp.health)
        self.assertTrue(any(card.card_id == "TLC_630t" for card in game.players[0].hand))


    def test_sleep_paralysis_choose_one_summons_two_nonattacking_demons(self):
        game = self.game()
        spell = self.add_hand(game, "EDR_490")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(["summon_night_terrors", "destroy_enemy_minion"],
                         game.snapshot()["pending_choice"]["options"])
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(2, len(game.players[0].board))
        self.assertTrue(all(m.card_id == "EDR_490t" and m.cant_attack
                            for m in game.players[0].board))

    def test_ominous_nightmares_buffs_only_damaged_minion(self):
        game = self.game()
        target = self.add_board(game, "CORE_CS2_172", 0)
        target.damage = 1
        spell = self.add_hand(game, "EDR_570")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(["damage_all_minions", "buff_damaged_minion"],
                         game.snapshot()["pending_choice"]["options"])
        game.step(Action("RULE_CHOICE_PICK", 1, 0, target.entity_id))
        self.assertEqual(2, target.attack_delta)
        self.assertEqual(2, target.health_delta)

    def test_chef_nethrek_is_executable(self):
        game = self.game()
        self.assertIn("JAIL_860", game.executable_card_ids)

    def test_irida_sinseeker_is_executable(self):
        game = self.game()
        self.assertIn("JAIL_719", game.executable_card_ids)

    def test_blood_doctor_thalena_is_executable(self):
        game = self.game()
        self.assertIn("JAIL_446", game.executable_card_ids)

    def test_mugzee_is_executable(self):
        game = self.game()
        self.assertIn("JAIL_800", game.executable_card_ids)

    def test_aya_is_executable(self):
        game = self.game()
        self.assertIn("JAIL_504", game.executable_card_ids)

    def test_rulebreaker_cards_are_executable(self):
        game = self.game()
        self.assertTrue({"JAIL_397", "JAIL_319"} <= game.executable_card_ids)

    def test_r4t4tcher_is_executable(self):
        game = self.game()
        self.assertIn("JAIL_882", game.executable_card_ids)

    def test_king_of_the_underbelly_is_executable(self):
        game = self.game()
        self.assertIn("JAIL_831", game.executable_card_ids)

    def test_holmes_investigation_is_an_explicit_hand_guess(self):
        game = self.game()
        holmes = self.add_hand(game, "JAIL_851")
        opponent_card = game._entity("CORE_CS2_013")
        game.players[1].hand.append(opponent_card)

        game.step(Action("PLAY", holmes.entity_id))

        self.assertEqual("RULE_CHOICE", game.pending_choice["kind"])
        self.assertEqual(1, len(game.pending_choice["options"]))
        pending = game.snapshot()["pending_choice"]
        self.assertEqual("JAIL_851", pending["source_card"])
        self.assertEqual(
            [{"entity": opponent_card.entity_id, "card_id": "CORE_CS2_013"}],
            pending["option_metadata"],
        )
        self.assertEqual(
            [Action("RULE_CHOICE_PICK", 0).key()],
            [action.key() for action in game.legal_actions()],
        )
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual("CORE_CS2_013", game.players[0].holmes_target_card_id)

    def test_elise_navigator_location_choices(self):
        game = self.game()
        by_cost = {}
        for card_id, definition in game.card_defs.items():
            if definition.card_type and definition.cost not in by_cost:
                by_cost[definition.cost] = card_id
        game.players[0].deck = [
            game._entity(by_cost[cost], started_in_deck=True)
            for cost in range(10) if cost in by_cost
        ]
        elise = self.add_hand(game, "TLC_100")
        game.step(Action("PLAY", elise.entity_id))
        self.assertEqual("ELISE_COST", game.pending_choice["stage"])
        game.step(Action("RULE_CHOICE_PICK", 1))
        self.assertEqual("ELISE_EFFECTS", game.pending_choice["stage"])
        game.step(Action("RULE_CHOICE_PICK", 0))
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertIsNone(game.pending_choice)
        self.assertEqual(1, len(game.players[0].locations))
        self.assertEqual(5, game.players[0].locations[0].custom_tier)
        self.assertEqual(2, len(game.players[0].locations[0].custom_effects))

    def test_elise_one_cost_excludes_radiant_crystals_and_activates(self):
        game = self.game()
        by_cost = {}
        for card_id, definition in game.card_defs.items():
            if definition.card_type and definition.cost not in by_cost:
                by_cost[definition.cost] = card_id
        game.players[0].deck = [
            game._entity(by_cost[cost], started_in_deck=True)
            for cost in range(10) if cost in by_cost
        ]
        elise = self.add_hand(game, "TLC_100")
        game.step(Action("PLAY", elise.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 0))
        labels = [label for label, _ in game.pending_choice["options"]]
        self.assertNotIn("Radiant Crystals", labels)
        game.step(Action("RULE_CHOICE_PICK", 0))
        game.step(Action("RULE_CHOICE_PICK", 0))
        location = game.players[0].locations[0]
        location.cooldown = 0
        game.players[1].health = 30
        game.step(Action("LOCATION", location.entity_id))
        self.assertEqual(30, game.players[1].health)
        location.cooldown = 0
        game.step(Action("LOCATION", location.entity_id))
        self.assertEqual(29, game.players[1].health)

    def test_bashana_carves_nature_spells(self):
        game = self.game()
        bashana = self.add_hand(game, "MEND_046")
        game.step(Action("PLAY", bashana.entity_id))
        tokens = [card for card in game.players[0].board if card.card_id == "MEND_046t"]
        self.assertEqual(3, len(tokens))
        self.assertTrue(all(token.embedded_spell_id for token in tokens))
        total = sum(
            game.card_defs[token.embedded_spell_id].cost for token in tokens
        )
        self.assertEqual(12, total)
        carve = next(
            event for event in reversed(game.events)
            if event["kind"] == "bashana_runetotem"
        )
        self.assertEqual(12, carve["total_cost"])
        self.assertTrue(carve["exact_total"])

    def test_vigilant_sentry_no_neutral_summons_two(self):
        game = self.game()
        game.players[0].deck = [game._entity("JAIL_035", started_in_deck=True)]
        sentry = self.add_hand(game, "JAIL_035")
        game.step(Action("PLAY", sentry.entity_id))
        self.assertEqual(3, sum(
            minion.card_id == "JAIL_035" for minion in game.players[0].board
        ))

    def test_scarlet_bruiser_no_neutral_adds_discounted_paladin_card(self):
        game = self.game()
        game.players[0].deck = [game._entity("JAIL_035", started_in_deck=True)]
        bruiser = self.add_board(game, "JAIL_328")
        game._damage_minion(0, bruiser, bruiser.health)
        game._resolve_deaths()
        generated = [
            card for card in game.players[0].hand
            if card.created_by == "JAIL_328"
        ]
        self.assertEqual(1, len(generated))
        self.assertEqual("PALADIN", generated[0].definition.card_class)
        self.assertEqual(-2, generated[0].cost_delta)

    def game(self, **kwargs) -> DragonMirrorGame:
        game = DragonMirrorGame(CARDS, 29, **kwargs)
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

    def test_standard_batch_50_registry_and_smoke(self):
        batch = {
            "RLK_067", "CORE_BT_921", "EDR_272", "CATA_558", "CORE_CS2_179",
            "CORE_DRG_079", "CORE_EX1_010", "CORE_EX1_028", "CORE_GIL_558",
            "CORE_GVG_085", "CORE_LOOT_137", "CORE_NEW1_023", "CORE_ULD_723",
            "CS3_038", "Core_CS2_200", "EDR_486", "EDR_598", "TIME_045",
            "TIME_053", "TIME_056", "TLC_248", "CORE_ICC_038", "CORE_BT_701",
            "CORE_EX1_082", "CORE_ULD_271", "CORE_EX1_058", "CORE_EX1_103",
            "CORE_EX1_506", "CORE_LOOT_413", "CORE_REV_308", "CORE_SW_088",
            "CORE_CS2_042", "CORE_EX1_134", "CORE_GVG_059", "CORE_EX1_362",
            "CORE_CFM_753", "CORE_TSC_076", "CORE_UNG_952", "CORE_GVG_061",
            "CORE_BAR_310", "CORE_EX1_198", "CORE_ICC_214", "CORE_NEW1_031",
            "CORE_OG_211", "CORE_AV_337", "CORE_RLK_062", "CORE_ULD_178",
            "CORE_WON_141", "CORE_LOOT_309", "CORE_RLK_657",
        }
        game = self.game()
        self.assertEqual(50, len(batch))
        self.assertTrue(batch <= game.executable_card_ids)
        self.assertTrue(batch <= {rule.card_id for rule in game.rule_registry.all_rules()})
        # Metadata keywords are initialized even when the rule body is empty.
        evasive = game._entity("CORE_DRG_079")
        self.assertTrue(evasive.rush and evasive.divine_shield and evasive.elusive)

        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        bomber = self.add_hand(game, "CORE_EX1_082")
        game.step(Action("PLAY", bomber.entity_id))
        self.assertTrue(any(e["kind"] == "random_other_character_damage" for e in game.events))

        target = self.add_board(game, "CORE_LOOT_137", 1)
        natalie = self.add_hand(game, "CORE_EX1_198")
        game.step(Action("PLAY", natalie.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)

        companion = self.add_hand(game, "CORE_NEW1_031")
        game.step(Action("PLAY", companion.entity_id))
        self.assertTrue(any(minion.card_id in {"NEW1_032", "NEW1_033", "NEW1_034"}
                            for minion in game.players[0].board))

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
        enemy = self.add_board(game, "CATA_565", 1)
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
        enemy = self.add_board(game, "TLC_248", 1, attack=0)
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

    def test_herald_source_cards_and_ritual_tokens(self):
        for card_id in ("CATA_525", "CATA_565", "CATA_580", "CATA_780"):
            game = self.game()
            card = self.add_hand(game, card_id)
            game.step(Action("PLAY", card.entity_id))
            self.assertEqual(1, game.players[0].herald_count, card_id)
            self.assertTrue(any(m.card_id == "CATA_580t" for m in game.players[0].board), card_id)

        game = self.game()
        ritual = self.add_hand(game, "CATA_561")
        game.step(Action("PLAY", ritual.entity_id))
        self.assertEqual(1, game.players[0].herald_count)
        self.assertEqual(2, sum(m.card_id == "CATA_561t" for m in game.players[0].board))
        self.assertTrue(all(m.rush for m in game.players[0].board if m.card_id == "CATA_561t"))

    def test_herald_derived_charged_hand_aura_and_sinestra_wing(self):
        game = self.game()
        left = self.add_board(game, "CATA_565", 0)
        hand = game._entity("CATA_153t")
        hand.herald_power = 2
        hand.summoned_turn = game.turn
        game._summon(game.players[0], hand)
        self.assertEqual(2, left.aura_attack_bonus)

        game = self.game()
        wing = game._entity("CATA_154t")
        wing.summoned_turn = game.turn
        game._summon(game.players[0], wing)
        generated = next(card for card in game.players[0].hand if card.created_by == "CATA_154t")
        self.assertIn(generated.definition.card_class, {
            "DEMONHUNTER", "DRUID", "HUNTER", "MAGE", "PALADIN", "PRIEST",
            "ROGUE", "SHAMAN", "WARLOCK", "WARRIOR", "DEATHKNIGHT",
        })
        self.assertNotEqual(generated.definition.card_class, game.players[0].card_class)

    def test_herald_chogall_soldier_destroys_right_and_grows(self):
        game = self.game()
        game.players[0].herald_count = 2
        soldier = game._entity("CATA_725t")
        soldier.summoned_turn = game.turn - 1
        game._summon(game.players[0], soldier)
        right = self.add_board(game, "CATA_565", 0)
        before = soldier.attack
        game._end_turn()
        self.assertNotIn(right, game.players[0].board)
        self.assertEqual(before + 2, soldier.attack)

        game = self.game()
        soldier = game._entity("CATA_725t")
        soldier.summoned_turn = game.turn - 1
        game._summon(game.players[0], soldier)
        dormant = self.add_board(game, "CATA_565", 0)
        dormant.dormant_turns = 2
        game._end_turn()
        self.assertIn(dormant, game.players[0].board)

    def test_herald_soldier_azshara_and_alakir_variants(self):
        game = self.game()
        game.players[0].herald_count = 3
        soldier = game._entity("CATA_525t")
        soldier.summoned_turn = game.turn
        game._summon(game.players[0], soldier)
        self.assertEqual(2, game.players[0].hero_attack_bonus)

        game = self.game()
        neighbor = self.add_board(game, "CATA_565", 0)
        soldier = game._entity("CATA_565t")
        soldier.herald_power = 4
        soldier.summoned_turn = game.turn
        game._summon(game.players[0], soldier)
        self.assertEqual(4, neighbor.aura_attack_bonus)

        game = self.game()
        game.players[0].herald_count = 1
        neighbor = self.add_board(game, "CATA_565", 0)
        charged = game._entity("CATA_153t")
        charged.summoned_turn = game.turn
        game._summon(game.players[0], charged)
        self.assertEqual(1, neighbor.aura_attack_bonus)
        herald = self.add_hand(game, "CATA_160")
        game.step(Action("PLAY", herald.entity_id))
        self.assertEqual(1, neighbor.aura_attack_bonus)

    def test_herald_soldier_onyxia_variant_generates_health_cost_card(self):
        game = self.game()
        game.players[0].herald_count = 1
        soldier = game._entity("CATA_780t")
        soldier.summoned_turn = game.turn
        game._summon(game.players[0], soldier)
        generated = [card for card in game.players[0].hand if card.created_by == "CATA_780t"]
        self.assertEqual(1, len(generated))
        self.assertEqual(game.turn, generated[0].costs_health_expiry_turn)

        game = self.game()
        game.players[0].herald_count = 1
        wing = game._entity("CATA_154t")
        wing.summoned_turn = game.turn
        game._summon(game.players[0], wing)
        generated = next(card for card in game.players[0].hand if card.created_by == "CATA_154t")
        first_cost = generated.cost
        herald = self.add_hand(game, "CATA_160")
        game.step(Action("PLAY", herald.entity_id))
        self.assertEqual(first_cost, generated.cost)

    def test_alakir_colossal_and_cost_matching_minions(self):
        game = self.game()
        alakir = self.add_hand(game, "CATA_153")
        game.step(Action("PLAY", alakir.entity_id))
        self.assertEqual(2, sum(m.card_id == "CATA_153t" for m in game.players[0].board))
        generated = [card for card in game.players[0].hand if card.created_by == "CATA_153"]
        self.assertEqual(2, len(generated))
        self.assertTrue(all(card.cost == 1 for card in generated))

    def test_sinestra_colossal_doubles_other_class_spells(self):
        game = self.game()
        sinestra = self.add_hand(game, "CATA_154")
        game.step(Action("PLAY", sinestra.entity_id))
        spell = self.add_hand(game, "CATA_530")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, game.players[0].herald_count)
        self.assertEqual(2, sum(m.card_id == "CATA_154t" for m in game.players[0].board))

    def test_vulcanos_colossal_and_end_turn_damage(self):
        game = self.game()
        vulcanos = self.add_hand(game, "CATA_488")
        game.step(Action("PLAY", vulcanos.entity_id))
        self.assertEqual(2, sum(m.card_id == "CATA_488t" for m in game.players[0].board))
        enemy = self.add_board(game, "CATA_565", 1)
        before = enemy.health
        game._end_turn()
        self.assertEqual(before - 3, enemy.health)
        self.assertEqual(8, vulcanos.health)

        plume = next(m for m in game.players[0].board if m.card_id == "CATA_488t")
        game._damage_minion(0, plume, 1)
        generated = [card for card in game.players[0].hand if card.created_by == "CATA_488t"]
        self.assertEqual(3, len(generated))
        self.assertTrue(all(card.definition.spell_school == "FIRE" for card in generated))
        self.assertTrue(all(card.cost <= 0 for card in generated))

    def test_black_blood_colossal_bodies(self):
        game = self.game()
        black_blood = self.add_hand(game, "CATA_300")
        game.step(Action("PLAY", black_blood.entity_id))
        bodies = [m for m in game.players[0].board if m.card_id.startswith("CATA_300t")]
        self.assertEqual(3, len(bodies))
        enemy = self.add_board(game, "CATA_565", 1)
        black_blood.damage = 2
        heal = self.add_hand(game, "CORE_AT_055")
        game.step(Action("PLAY", heal.entity_id, 0, black_blood.entity_id))
        self.assertLess(enemy.health, enemy.max_health)

    def test_chromatus_heads_remove_keywords(self):
        game = self.game()
        chromatus = self.add_hand(game, "CATA_432")
        game.step(Action("PLAY", chromatus.entity_id))
        heads = [m for m in game.players[0].board if m.card_id.startswith("CATA_432t")]
        self.assertEqual(4, len(heads))
        self.assertTrue(chromatus.taunt and chromatus.lifesteal and chromatus.elusive)
        head = next(m for m in heads if m.card_id == "CATA_432t1")
        head.damage = head.max_health
        game._resolve_deaths()
        self.assertFalse(chromatus.taunt)

    def test_chogall_colossal_arms(self):
        game = self.game()
        chogall = self.add_hand(game, "CATA_726")
        game.step(Action("PLAY", chogall.entity_id))
        arms = [m for m in game.players[0].board if m.card_id in {"CATA_726t", "CATA_726t1"}]
        self.assertEqual(2, len(arms))
        enemy_minion = game._entity("CATA_565")
        game.players[1].deck.append(enemy_minion)
        before = len(game.players[1].deck)
        game._end_turn()
        self.assertEqual(before - 1, len(game.players[1].deck))

    def test_supreme_dinomancy_buffs_all_beast_zones(self):
        game = self.game()
        hand_beast = self.add_hand(game, "CATA_565")
        deck_beast = game._entity("CATA_565")
        game.players[0].deck.append(deck_beast)
        board_beast = self.add_board(game, "CATA_565", 0)
        before = [(card.attack, card.max_health) for card in (hand_beast, deck_beast, board_beast)]
        spell = self.add_hand(game, "TLC_828")
        game.step(Action("PLAY", spell.entity_id))
        after = [(card.attack, card.max_health) for card in (hand_beast, deck_beast, board_beast)]
        self.assertEqual([(a + 2, h + 2) for a, h in before], after)

    def test_story_of_amara_sets_hero_health(self):
        game = self.game()
        game.players[0].health = 12
        spell = self.add_hand(game, "TLC_835")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual((40, 40), (game.players[0].health, game.players[0].max_health))

    def test_fumigate_hits_same_race(self):
        game = self.game()
        target = self.add_board(game, "CATA_565", 1)
        same_race = self.add_board(game, "CATA_565", 1)
        other = self.add_board(game, "CORE_CS2_065", 1)
        spell = self.add_hand(game, "TLC_901")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertEqual((3, 3), (target.damage, same_race.damage))
        self.assertEqual(0, other.damage)

    def test_judgment_sets_all_minion_stats(self):
        game = self.game()
        source = self.add_board(game, "CATA_565", 0)
        other = self.add_board(game, "CORE_CS2_065", 0)
        spell = self.add_hand(game, "JAIL_326")
        game.step(Action("PREPARE", spell.entity_id))
        game.step(Action("PLAY", spell.entity_id, 0, source.entity_id))
        self.assertEqual((source.attack, source.max_health), (other.attack, other.max_health))

    def test_hold_them_off_buffs_lifesteal(self):
        game = self.game()
        target = self.add_board(game, "CATA_565", 0)
        spell = self.add_hand(game, "JAIL_913")
        game.step(Action("PREPARE", spell.entity_id))
        game.step(Action("PLAY", spell.entity_id, 0, target.entity_id))
        self.assertTrue(target.lifesteal)
        self.assertEqual(5, target.attack_delta)

    def test_prepare_discounts_jailbird_in_hand(self):
        game = self.game()
        prepared = self.add_hand(game, "JAIL_326")
        jailbird = self.add_hand(game, "JAIL_453")
        before = jailbird.cost
        game.step(Action("PREPARE", prepared.entity_id))
        self.assertLess(jailbird.cost, before)

    def test_sawbones_destroys_other_minions_and_refreshes(self):
        game = self.game()
        other = self.add_board(game, "CATA_565", 0)
        sawbones = self.add_hand(game, "JAIL_444")
        game.step(Action("PREPARE", sawbones.entity_id))
        game.step(Action("PLAY", sawbones.entity_id))
        self.assertNotIn(other, game.players[0].board)
        self.assertGreaterEqual(game.players[0].mana, 1)

    def test_sewer_swimmer_triggers_friendly_deathrattle(self):
        game = self.game()
        game.players[0].health = 20
        target = self.add_board(game, "JAIL_912", 0)
        swimmer = self.add_hand(game, "JAIL_395")
        game.step(Action("PREPARE", swimmer.entity_id))
        game.step(Action("PLAY", swimmer.entity_id, 0, target.entity_id))
        self.assertEqual(26, game.players[0].health)

    def test_tras_tath_gains_summoned_demon_stats(self):
        game = self.game()
        parasite = self.add_hand(game, "JAIL_721")
        game.step(Action("PREPARE", parasite.entity_id))
        game.step(Action("PLAY", parasite.entity_id))
        before = (parasite.attack, parasite.max_health)
        demon = game._entity("CORE_CS2_065")
        demon.summoned_turn = game.turn
        game._summon(game.players[0], demon)
        self.assertEqual(
            (before[0] + demon.attack, before[1] + demon.max_health),
            (parasite.attack, parasite.max_health),
        )

    def test_black_market_auctioneer_draws_after_spell(self):
        game = self.game()
        auctioneer = self.add_hand(game, "JAIL_718")
        game.step(Action("PREPARE", auctioneer.entity_id))
        game.step(Action("PLAY", auctioneer.entity_id))
        spell = self.add_hand(game, "CORE_CS2_023")
        hand_before = len(game.players[0].hand) - 1
        game.step(Action("PLAY", spell.entity_id))
        self.assertGreaterEqual(len(game.players[0].hand), hand_before)

    def test_vanessa_generates_discounted_battlecry_minion(self):
        game = self.game()
        vanessa = self.add_hand(game, "JAIL_407")
        game.step(Action("PREPARE", vanessa.entity_id))
        game.step(Action("PLAY", vanessa.entity_id))
        spell = self.add_hand(game, "CORE_CS2_023")
        game.step(Action("PLAY", spell.entity_id))
        generated = [card for card in game.players[0].hand if card.created_by == "JAIL_407"]
        self.assertEqual(1, len(generated))
        self.assertIn("BATTLECRY", generated[0].definition.mechanics)
        self.assertLessEqual(generated[0].cost, generated[0].definition.cost - 2)

    def test_tricksy_improviser_prepared_secrets(self):
        game = self.game()
        prior_spell = self.add_hand(game, "CORE_EX1_289")
        game.step(Action("PLAY", prior_spell.entity_id))
        improvisor = self.add_hand(game, "JAIL_321")
        game.step(Action("PREPARE", improvisor.entity_id))
        game.step(Action("PLAY", improvisor.entity_id))
        self.assertGreaterEqual(len(game.players[0].secrets), 2)

    def test_defias_wannabe_prepare_combo(self):
        game = self.game()
        coin = self.add_hand(game, "JAIL_COIN1")
        game.step(Action("PLAY", coin.entity_id))
        wannabe = self.add_hand(game, "JAIL_909")
        game.step(Action("PREPARE", wannabe.entity_id))
        before = (wannabe.attack, wannabe.max_health)
        game.step(Action("PLAY", wannabe.entity_id))
        self.assertEqual((before[0] + 1, before[1] + 1), (wannabe.attack, wannabe.max_health))

    def test_code_violet_repeats_after_three_other_spells(self):
        game = self.game()
        game.players[0].max_mana = game.players[0].mana = 10
        for _ in range(3):
            coin = self.add_hand(game, "JAIL_COIN1")
            game.step(Action("PLAY", coin.entity_id))
        spell = self.add_hand(game, "JAIL_735")
        game.step(Action("PREPARE", spell.entity_id))
        game.step(Action("PLAY", spell.entity_id))
        summoned = [m for m in game.players[0].board if m.created_by == "JAIL_735"]
        self.assertEqual(2, len(summoned))

    def test_wanted_poster_grants_prepare(self):
        game = self.game()
        poster = self.add_hand(game, "CAP_407")
        game.step(Action("PLAY", poster.entity_id))
        self.assertIsNotNone(game.pending_choice)
        option = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", option.entity_id))
        granted = next(card for card in game.players[0].hand if card.entity_id == option.entity_id)
        self.assertTrue(granted.prepare_granted)
        self.assertTrue(any(action.kind == "PREPARE" and action.source == granted.entity_id
                            for action in game.legal_actions()))

    def test_experimental_animation_heralds_and_damages_enemy_minions(self):
        game = self.game()
        enemy = self.add_board(game, "TLC_248", 1)
        spell = self.add_hand(game, "CATA_156")
        before = enemy.health
        hero_before = game.players[1].health
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(1, game.players[0].herald_count)
        self.assertEqual(before - 4, enemy.health)
        self.assertEqual(hero_before, game.players[1].health)

    def test_fel_infusion_herald_and_hero_lifesteal(self):
        game = self.game()
        game.players[0].health = 20
        spell = self.add_hand(game, "CATA_530")
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(1, game.players[0].herald_count)
        self.assertEqual(game.turn, game.players[0].hero_lifesteal_turn)
        game.players[0].hero_attack_bonus = 1
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertGreater(game.players[0].health, 20)

        game = self.game()
        game.players[0].health = 20
        spell = self.add_hand(game, "CATA_530")
        enemy = self.add_board(game, "CATA_565", 1)
        game.step(Action("PLAY", spell.entity_id))
        game.players[0].hero_attack_bonus = 1
        game.step(Action("HERO_ATTACK", None, 1, enemy.entity_id))
        self.assertGreater(game.players[0].health, 20)

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

    def test_scramble_for_gear_gains_armor_and_shuffles_cast_when_drawn_gear(self):
        game = self.game()
        spell = self.add_hand(game, "JAIL_386")
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, game.players[0].armor)
        gear = [card for card in game.players[0].deck if card.card_id == "JAIL_386t"]
        self.assertEqual(5, len(gear))
        self.assertTrue(all(card.casts_when_drawn_armor == 2 for card in gear))
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)] + gear[:1]
        before = game.players[0].armor
        game._draw(game.players[0])
        self.assertEqual(before + 2, game.players[0].armor)

    def test_spire_security_reveals_and_splits_damage(self):
        game = self.game()
        game.players[0].deck = [game._entity("CORE_CFM_604", started_in_deck=True)]
        enemies = [self.add_board(game, "CORE_LOOT_137", 1) for _ in range(3)]
        security = self.add_hand(game, "JAIL_379")
        game.step(Action("PLAY", security.entity_id))
        self.assertEqual(5, sum(minion.damage for minion in enemies))
        reveal = next(event for event in reversed(game.events)
                      if event["kind"] == "reveal_spell")
        self.assertEqual("CORE_CFM_604", reveal["card"])
        self.assertTrue(reveal["triggered"])

    def test_overheal_core_minions(self):
        game = self.game()
        player = game.players[0]
        source = game._entity("CORE_CFM_604")
        champion = self.add_board(game, "CORE_AT_011")
        geode = self.add_board(game, "CORE_CFM_606")
        clergy = self.add_board(game, "CORE_CS3_014")
        player.deck = [game._entity("GAME_005", started_in_deck=True)]
        player.hand.clear()
        game._apply_heal(player, player, 3, source=source)
        self.assertEqual(2, champion.attack_delta)
        self.assertTrue(any(m.created_by == "CORE_CFM_606" for m in player.board))
        self.assertEqual(1, len(player.hand))

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

    def test_bitterbloom_knight_uses_controller_class(self):
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

    def test_drakeadon_mongrel_summons_random_four_cost(self):
        game = self.game()
        drakeadon = self.add_board(game, "CATA_723", 0)
        game._damage_minion(0, drakeadon, drakeadon.health)
        game._resolve_deaths()
        summoned = [
            minion for minion in game.players[0].board
            if minion.created_by == "CATA_723"
        ]
        self.assertEqual(2, len(summoned))
        self.assertTrue(all(minion.definition.cost == 4 for minion in summoned))

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

    def test_tyrax_deathrattle_opens_terrors_grave(self):
        game = self.game()
        tyrax = self.add_board(game, "TLC_433t", 0)
        tyrax.damage = tyrax.max_health
        game._resolve_deaths()
        self.assertFalse(game.players[0].board)
        self.assertEqual(1, len(game.players[0].locations))
        self.assertEqual("TLC_433t2", game.players[0].locations[0].card_id)

    def test_terrors_grave_deals_four_and_resummons_tyrax(self):
        game = self.game()
        location_card = game._entity("TLC_433t2")
        location = Location(location_card.entity_id, location_card.card_id,
                            1, 0)
        game.players[0].locations.append(location)
        target = self.add_board(game, "CORE_LOOT_137", 1)
        game._use_location(Action("LOCATION", location.entity_id, 1, target.entity_id))
        self.assertEqual(4, target.damage)
        self.assertNotIn(location, game.players[0].locations)
        self.assertTrue(any(card.card_id == "TLC_433t" for card in game.players[0].board))

    def test_ashalon_adapts_twice_and_persists_on_played_minions(self):
        game = self.game()
        ashalon = self.add_hand(game, "TLC_229t14")
        game.step(Action("PLAY", ashalon.entity_id))
        self.assertEqual("ASHALON_ADAPT", game.pending_choice["kind"])
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual("ASHALON_ADAPT", game.pending_choice["kind"])
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertEqual(2, len(game.players[0].ashalon_adaptations))
        minion = self.add_hand(game, "CORE_LOOT_137")
        game.step(Action("PLAY", minion.entity_id))
        self.assertGreaterEqual(minion.attack, minion.definition.attack)
        self.assertGreaterEqual(minion.max_health, minion.definition.health)

    def test_reach_equilibrium_combines_soletos_halves(self):
        game = self.game()
        game.players[0].active_quests["TLC_817"] = {
            "progress": 0, "turns": 0, "flags": set(), "holy": 4, "shadow": 4,
        }
        game._complete_lost_city_quest(game.players[0], "TLC_817")
        self.assertEqual(["TLC_817t5"], [c.card_id for c in game.players[0].hand])
        combined = game.players[0].hand[0]
        game.step(Action("PLAY", combined.entity_id))
        self.assertEqual(2, sum(c.card_id == "TLC_817t5" for c in game.players[0].board))

    def test_generated_soletos_half_combine_outside_quest_reward(self):
        game = self.game()
        game._add_generated(game.players[0], game._entity("TLC_817t3"))
        game._add_generated(game.players[0], game._entity("TLC_817t4"))
        self.assertEqual(["TLC_817t5"], [c.card_id for c in game.players[0].hand])

    def test_underfel_rift_is_once_per_turn(self):
        game = self.game()
        first = self.add_hand(game, "TLC_446t")
        second = self.add_hand(game, "TLC_446t")
        game.step(Action("PLAY", first.entity_id))
        self.assertFalse(any(a.kind == "PLAY" and a.source == second.entity_id
                             for a in game.legal_actions()))

    def test_origin_stone_plays_unchosen_discover_options_and_loses_durability(self):
        game = self.game()
        game.players[0].weapon = Weapon("TLC_460t", "The Origin Stone", 0, 4)
        game._offer_discover(
            game.players[0],
            ["CORE_AT_055", "CORE_LOOT_137", "CORE_CS2_023"],
            dark_gift=False, source_card_id="TEST_DISCOVER",
        )
        chosen = next(
            option for option in game.pending_choice["options"]
            if option.card_id == "CORE_AT_055"
        )
        game.step(Action("DISCOVER_PICK", chosen.entity_id))
        self.assertEqual(5, game.players[0].weapon.durability)
        self.assertTrue(any(card.card_id == "CORE_LOOT_137" for card in game.players[0].board))
        self.assertEqual(2, game.players[0].cards_played_this_turn)

    def test_origin_stone_reward_can_be_equipped_from_quest(self):
        game = self.game()
        game.players[0].active_quests["TLC_460"] = {
            "progress": 8, "turns": 0, "flags": set(),
        }
        game._complete_lost_city_quest(game.players[0], "TLC_460")
        reward = next(card for card in game.players[0].hand if card.card_id == "TLC_460t")
        game.step(Action("PLAY", reward.entity_id))
        self.assertEqual("TLC_460t", game.players[0].weapon.card_id)
        self.assertEqual(8, game.players[0].weapon.durability)

    def test_ashalon_plants_adaptation_summons_two_plants(self):
        game = self.game()
        game.players[0].ashalon_adaptations = ["plants"]
        minion = self.add_hand(game, "CORE_LOOT_137")
        game.step(Action("PLAY", minion.entity_id))
        self.assertEqual(2, sum(card.card_id == "UNG_999t2t1" for card in game.players[0].board))

    def test_forbidden_sequence_counts_discover_only_after_pick(self):
        game = self.game()
        game.players[0].active_quests["TLC_460"] = {
            "progress": 0, "turns": 0, "flags": set(),
        }
        game._offer_discover(
            game.players[0], ["CORE_AT_055", "CORE_CS2_023", "CORE_LOOT_137"],
            dark_gift=False, source_card_id="TEST_DISCOVER",
        )
        self.assertEqual(0, game.players[0].active_quests["TLC_460"]["progress"])
        game.step(Action("DISCOVER_PICK", game.pending_choice["options"][0].entity_id))
        self.assertEqual(1, game.players[0].active_quests["TLC_460"]["progress"])

    def test_new_lost_city_state_is_visible_in_snapshot(self):
        game = self.game()
        game.players[0].underfel_rift_used_turn = 7
        game.players[0].ashalon_adaptations = ["taunt", "plants"]
        state = game.snapshot()["players"][0]
        self.assertEqual(7, state["underfel_rift_used_turn"])
        self.assertEqual(["taunt", "plants"], state["ashalon_adaptations"])

    def test_weapon_play_uses_printed_health_as_durability(self):
        game = self.game()
        weapon = self.add_hand(game, "TLC_239t")
        game.step(Action("PLAY", weapon.entity_id))
        self.assertEqual(5, game.players[0].weapon.durability)

    def test_fallen_hero_increases_mage_hero_power_damage(self):
        game = self.game()
        game.players[0].card_class = "MAGE"
        self.add_board(game, "CORE_AT_003", 0)
        game.players[0].mana = 2
        game.step(Action("HERO_POWER", target_player=1, target_entity=None))
        self.assertEqual(28, game.players[1].health)

    def test_all_current_class_legendary_quests_are_registered(self):
        expected = {
            "END_017",
            "TLC_229", "TLC_239", "TLC_426", "TLC_433", "TLC_446",
            "TLC_460", "TLC_513", "TLC_602", "TLC_631", "TLC_817", "TLC_830",
        }
        self.assertEqual(expected, set(LOST_CITY_QUEST_IDS))
        self.assertTrue(
            expected - {"TLC_239", "TLC_426", "TLC_817"}
            <= set(LOST_CITY_QUEST_REWARDS)
        )

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
        self.assertEqual(3, target.damage)

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

    def test_dk_rune_trigger_cards_are_executable(self):
        game = self.game()
        self.assertTrue({"CORE_RLK_083", "CORE_RLK_116", "RLK_223",
                         "TIME_611", "TIME_612", "TIME_613"}
                        | {"TIME_617", "CORE_RLK_706", "JAIL_443",
                           "JAIL_445", "JAIL_454", "TIME_615"}
                        <= game.executable_card_ids)

    def test_death_knight_rune_configuration_is_inferred_and_exposed(self):
        game = self.game(
            deck_counts=({"RLK_024": 30}, {"RLK_024": 30}),
            player_classes=("DEATHKNIGHT", "DEATHKNIGHT"),
        )
        self.assertEqual({"blood": 1, "frost": 0, "unholy": 0},
                         game.players[0].rune_counts)
        self.assertEqual(game.players[0].rune_counts,
                         game.snapshot()["players"][0]["rune_counts"])

    def test_death_knight_rune_configuration_rejects_wrong_color(self):
        with self.assertRaises(ValueError):
            self.game(
                deck_counts=({"RLK_024": 30}, {"RLK_024": 30}),
                player_classes=("DEATHKNIGHT", "DEATHKNIGHT"),
                rune_configs=(
                    {"blood": 0, "frost": 1, "unholy": 0},
                    {"blood": 1, "frost": 0, "unholy": 0},
                ),
            )

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

    def test_outcast_remaining_standard_cards(self):
        # Crimson Sigil Runner only draws when it is played from a hand edge.
        game = self.game()
        game.players[0].deck = [game._entity("GAME_005", started_in_deck=True)]
        runner = self.add_hand(game, "CORE_BT_480")
        game.step(Action("PLAY", runner.entity_id))
        self.assertEqual(1, len(game.players[0].hand))

        # Flash Flood repeats and recomputes the two board edges for Outcast.
        game = self.game()
        left = self.add_board(game, "CORE_LOOT_137", 1)
        right = self.add_board(game, "CORE_LOOT_137", 1)
        left.health_delta += 10
        right.health_delta += 10
        flood = self.add_hand(game, "CATA_533")
        self.add_hand(game, "GAME_005")
        self.add_hand(game, "GAME_005")
        game.step(Action("PLAY", flood.entity_id))
        self.assertEqual(10, left.damage)
        self.assertEqual(10, right.damage)

        # Horn of Feasting gives all three Raptors temporary attack immunity.
        game = self.game()
        horn = self.add_hand(game, "DINO_136")
        game.step(Action("PLAY", horn.entity_id))
        self.assertEqual(3, len(game.players[0].board))
        self.assertTrue(all(m.immune_while_attacking for m in game.players[0].board))
        self.assertTrue(all(not m.immune for m in game.players[0].board))

        # Bygone Echoes spends corpses and Outcast adds the third summon.
        game = self.game()
        game.players[0].corpses = 4
        echoes = self.add_hand(game, "END_005")
        game.step(Action("PLAY", echoes.entity_id))
        self.assertEqual(0, game.players[0].corpses)
        self.assertEqual(3, len(game.players[0].board))

        # Doomsday Prepper protects the hero only when played from an edge.
        game = self.game()
        prepper = self.add_hand(game, "TIME_021")
        game.step(Action("PLAY", prepper.entity_id))
        game._damage_hero(game.players[0], 5)
        self.assertEqual(30, game.players[0].health)

    def test_corpse_core_cards(self):
        game = self.game()
        game.players[0].corpses = 4
        tomb = self.add_hand(game, "CORE_RLK_118")
        game.step(Action("PLAY", tomb.entity_id))
        self.assertEqual(0, game.players[0].corpses)
        self.assertEqual(2, len(game.players[0].board))
        self.assertTrue(all(m.taunt and m.reborn for m in game.players[0].board))

        game = self.game()
        game.players[0].corpses = 1
        bagger = self.add_hand(game, "RLK_503")
        game.step(Action("PLAY", bagger.entity_id))
        self.assertEqual(2, game.players[0].corpses)

        game = self.game()
        game.players[0].corpses = 8
        chow = self.add_hand(game, "CATA_465")
        game.step(Action("PLAY", chow.entity_id))
        self.assertEqual(0, game.players[0].corpses)
        self.assertTrue(all(m.rush for m in game.players[0].board))

    def test_corpse_discover_and_hero_rebirth_boundaries(self):
        game = self.game()
        game.players[0].corpses = 5
        clone = self.add_hand(game, "JAIL_451")
        game.step(Action("PLAY", clone.entity_id))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        choice = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", choice.entity_id))
        self.assertEqual(0, game.players[0].corpses)
        self.assertEqual(1, len(game.players[0].board))
        self.assertEqual(choice.card_id, game.players[0].board[0].card_id)

        game = self.game()
        game.players[0].corpses = 5
        paleomancy = self.add_hand(game, "TLC_434")
        game.step(Action("PLAY", paleomancy.entity_id))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        game.step(Action("DISCOVER_PICK", game.pending_choice["options"][0].entity_id))
        self.assertEqual(0, game.players[0].corpses)
        self.assertGreaterEqual(len(game.players[0].hand), 1)

        game = self.game()
        game.players[0].corpses = 7
        husk = self.add_hand(game, "TIME_618")
        game.step(Action("PLAY", husk.entity_id))
        game._damage_hero(game.players[0], 99)
        self.assertEqual(7, game.players[0].health)
        self.assertEqual(0, game.players[0].corpses)
        self.assertFalse(game.players[0].corpse_rebirth_pending)

        game = self.game()
        flower = self.add_board(game, "EDR_815", 0)
        game.players[0].corpses = 2
        target = game._entity("CORE_LOOT_137")
        target.summoned_turn = game.turn
        game._summon(game.players[1], target)
        self.assertEqual(3, target.damage)
        self.assertEqual(0, game.players[0].corpses)

    def test_standard_hero_cards(self):
        game = self.game()
        jaraxxus = self.add_hand(game, "CORE_EX1_323")
        game.step(Action("PLAY", jaraxxus.entity_id))
        self.assertEqual("EX1_tk33", game.players[0].hero_power_id)
        self.assertIsNotNone(game.players[0].weapon)
        self.assertEqual("EX1_323w", game.players[0].weapon.card_id)
        game.step(Action("HERO_POWER"))
        self.assertEqual(1, sum(m.card_id == "EX1_tk34" for m in game.players[0].board))

    def test_tradeable_standard_cards(self):
        game = self.game()
        game.players[0].deck = [
            game._entity("GAME_005", started_in_deck=True),
            game._entity("GAME_005", started_in_deck=True),
        ]
        trade = self.add_hand(game, "CORE_SW_429")
        game.step(Action("TRADE", trade.entity_id))
        self.assertEqual(1, len(game.players[0].hand))

        game = self.game()
        game.players[0].mana = 20
        large = self.add_board(game, "CORE_LOOT_137", 1, attack=6)
        hunter = self.add_hand(game, "CORE_EX1_005")
        game.step(Action("PLAY", hunter.entity_id, 1, large.entity_id))
        self.assertNotIn(large, game.players[1].board)

        game = self.game()
        location_card = game._entity("CORE_REV_023")
        game.players[0].hand.append(location_card)
        location = Location(game.next_entity_id, "CORE_REV_990", 3, cooldown=0)
        game.next_entity_id += 1
        game.players[1].locations.append(location)
        game.step(Action("PLAY", location_card.entity_id, 1, location.entity_id))
        self.assertFalse(game.players[1].locations)

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

    def test_dual_class_imbue_weapon_selects_deathknight_power(self):
        game = self.game()
        game.players[0].card_class = "DEATHKNIGHT"
        weapon = self.add_hand(game, "END_001")
        game.step(Action("PLAY", weapon.entity_id))
        self.assertEqual("END_003p", game.players[0].hero_power_id)

    def test_all_imbue_metadata_cards_have_registered_rules(self):
        game = self.game()
        import json
        with CARDS.open(encoding="utf-8") as handle:
            cards = json.load(handle)
        imbue_ids = {
            card["id"] for card in cards
            if "IMBUE" in card.get("referencedTags", [])
        }
        self.assertTrue(imbue_ids)
        self.assertTrue(all(card_id in game.rule_registry for card_id in imbue_ids))

    def test_dark_gift_discover_tranches(self):
        for card_id in ("EDR_102", "FIR_900"):
            game = self.game()
            card = self.add_hand(game, card_id)
            game.step(Action("PLAY", card.entity_id))
            self.assertEqual("DISCOVER", game.pending_choice["kind"])
            self.assertTrue(all(c.gifts for c in game.pending_choice["options"]))

        game = self.game()
        game.players[0].corpses = 2
        rite = self.add_hand(game, "EDR_811")
        game.step(Action("PLAY", rite.entity_id))
        self.assertEqual(0, game.players[0].corpses)
        self.assertTrue(game.pending_choice["options"])

    def test_frostburn_matriarch_dark_gift_condition(self):
        game = self.game()
        held = self.add_hand(game, "EDR_810t")
        held.gifts.append("bundled_up")
        matriarch = self.add_hand(game, "FIR_901")
        game.step(Action("PLAY", matriarch.entity_id))
        self.assertEqual(2, sum(m.card_id == "FIR_901t" for m in game.players[0].board))

    def test_overgrown_horror_discounts_dark_gifts(self):
        game = self.game()
        held = self.add_hand(game, "EDR_810t")
        held.gifts.append("bundled_up")
        horror = self.add_hand(game, "EDR_654")
        game.step(Action("PLAY", horror.entity_id))
        self.assertEqual(max(0, held.definition.cost - 2), held.cost)

    def test_cindersword_buffs_with_dark_gift(self):
        game = self.game()
        held = self.add_hand(game, "EDR_810t")
        held.gifts.append("bundled_up")
        sword = self.add_hand(game, "FIR_922")
        game.step(Action("PLAY", sword.entity_id))
        self.assertEqual(4, game.players[0].weapon.attack)

    def test_wallow_copies_dark_gifts(self):
        game = self.game()
        wallow = self.add_hand(game, "EDR_487")
        target = self.add_board(game, "CORE_NEW1_023", 0)
        game._apply_dark_gift(target, "bundled_up")
        self.assertIn("bundled_up", wallow.gifts)
        target2 = self.add_board(game, "EDR_810t", 0)
        game._apply_dark_gift(target2, "sweet_dreams")
        self.assertIn("sweet_dreams", wallow.gifts)
        hidden_target = self.add_hand(game, "EDR_810t")
        game._apply_dark_gift(hidden_target, "well_rested")
        self.assertIn("well_rested", wallow.gifts)

    def test_unrestricted_dark_gift_can_stack(self):
        game = self.game()
        # Sweet Dreams is universally eligible and changes max health.
        target = self.add_board(game, "CORE_NEW1_023", 0)
        game._apply_dark_gift(target, "sweet_dreams")
        first_health = target.max_health
        game._apply_dark_gift(target, "sweet_dreams")
        self.assertEqual(first_health + 5, target.max_health)
        self.assertEqual(2, target.gifts.count("sweet_dreams"))

    def test_wallow_self_gift_is_copied_and_stacks(self):
        game = self.game()
        wallow = self.add_hand(game, "EDR_487")
        game._apply_dark_gift(wallow, "sweet_dreams")
        self.assertEqual(2, wallow.gifts.count("sweet_dreams"))
        self.assertEqual(10, wallow.health_delta)

    def test_played_wallow_does_not_receive_future_gifts(self):
        game = self.game()
        wallow = self.add_board(game, "EDR_487", 0)
        target = self.add_board(game, "CORE_NEW1_023", 0)
        game._apply_dark_gift(target, "sweet_dreams")
        self.assertEqual([], wallow.gifts)

    def test_persisting_horror_reborns_full_health_with_gifts(self):
        game = self.game()
        target = self.add_board(game, "EDR_810t", 0)
        game._apply_dark_gift(target, "persisting_horror")
        game._apply_dark_gift(target, "sweet_dreams")
        game._damage_minion(0, target, target.health)
        game._resolve_deaths()
        reborn = next(card for card in game.players[0].board if card.card_id == "EDR_810t")
        self.assertEqual(reborn.max_health, reborn.health)
        self.assertIn("persisting_horror", reborn.gifts)
        self.assertIn("sweet_dreams", reborn.gifts)

    def test_raptor_herald_dark_gift_discover(self):
        game = self.game()
        herald = self.add_hand(game, "CORE_EDR_004")
        game.step(Action("PLAY", herald.entity_id))
        self.assertTrue(game.pending_choice["options"])
        self.assertTrue(all(c.has_race("BEAST") and c.gifts for c in game.pending_choice["options"]))

    def test_rude_awakening_repeats_battlecry_only(self):
        game = self.game()
        game.players[0].card_class = "MAGE"
        rider = self.add_hand(game, "EDR_871")
        game._apply_dark_gift(rider, "rude_awakening")
        game.step(Action("PLAY", rider.entity_id))
        self.assertEqual(2, sum(c.card_id == "CORE_CS2_231" for c in game.players[0].hand))
        self.assertEqual(1, sum(m.card_id == "EDR_871" for m in game.players[0].board))

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

    def test_hamuul_start_of_game_and_spell_threshold(self):
        game = self.game()
        game.players[0].card_class = "DRUID"
        hamuul = self.add_hand(game, "EDR_845")
        game.players[0].deck = [
            game._entity("CORE_LOOT_373", started_in_deck=True)
            for _ in range(3)
        ]
        game._start_of_game()
        self.assertTrue(game.players[0].hamuul_active)
        self.assertEqual("EDR_847p", game.players[0].hero_power_id)
        for _ in range(3):
            spell = self.add_hand(game, "CORE_LOOT_373")
            game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(2, game.players[0].hero_power_imbues)

    def test_malorne_discovers_legendary_and_discount(self):
        game = self.game()
        game.players[0].hero_power_imbues = 4
        malorne = self.add_hand(game, "EDR_888")
        game.step(Action("PLAY", malorne.entity_id))
        self.assertIsNotNone(game.pending_choice)
        option = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", option.entity_id))
        self.assertTrue(any(c.card_id == option.card_id and c.cost == 1 for c in game.players[0].hand))

    def test_class_imbue_cards_use_their_controller_class(self):
        hunter = self.game()
        hunter.players[0].card_class = "HUNTER"
        beast = hunter._entity("EDR_810t")
        hunter.players[0].deck = [beast]
        houndmaster = self.add_hand(hunter, "EDR_226")
        hunter.step(Action("PLAY", houndmaster.entity_id))
        self.assertEqual("EDR_850p", hunter.players[0].hero_power_id)

        shaman = self.game()
        shaman.players[0].card_class = "SHAMAN"
        shaman.players[0].health = 20
        aspect = self.add_hand(shaman, "EDR_231")
        shaman.step(Action("PLAY", aspect.entity_id, 0, None))
        self.assertEqual("EDR_448p", shaman.players[0].hero_power_id)


class SecondStandardCardBatchTests(unittest.TestCase):
    """Smoke/regression coverage for the 50-card 50B tranche."""

    BATCH = {
        "CORE_RLK_121", "CORE_EX1_007", "EDR_253", "EDR_256", "CORE_TRL_240",
        "CORE_NEW1_020", "CORE_NEW1_021", "EDR_110", "TLC_633", "CORE_KAR_057",
        "EDR_255", "FIR_961", "JAIL_118", "TIME_018", "TIME_019", "CAP_803",
        "CATA_304", "FIR_777", "TIME_427", "TIME_431", "TIME_855", "END_014",
        "TIME_600", "EDR_941", "EDR_874", "TLC_220", "END_023", "CATA_209",
        "CORE_BAR_878", "JAIL_461", "CORE_RLK_706", "EDR_842", "FIR_904",
        "CATA_552", "EDR_262", "MEND_302", "TIME_856", "TLC_365", "TLC_605",
        "TLC_621", "TLC_829", "TLC_987", "CATA_494", "JAIL_803", "END_026",
        "EDR_979", "EDR_540", "JAIL_503", "TLC_466", "JAIL_719",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 31)
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

    def add_hand(self, game, card_id):
        card = game._entity(card_id)
        game.players[0].hand.append(card)
        return card

    def add_board(self, game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_after_spell_and_after_attack_windows(self):
        game = self.game()
        self.add_board(game, "CORE_NEW1_020")
        spell = self.add_hand(game, "CORE_AT_055")
        enemy = self.add_board(game, "CORE_EX1_005", 1)
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertGreater(enemy.damage, 0)

        game = self.game()
        game.players[0].weapon = Weapon("EDR_253", "Ursine Maul", 2, 2)
        game.players[0].deck = [game._entity("CORE_AT_055")]
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertTrue(game.players[0].hand)

    def test_start_turn_doomsayer_and_acolyte_death(self):
        game = self.game()
        self.add_board(game, "CORE_NEW1_021")
        self.add_board(game, "CORE_EX1_005", 1)
        game._start_turn(0)
        self.assertFalse(game.players[1].board)

        game = self.game()
        self.add_board(game, "CORE_RLK_121")
        undead = self.add_board(game, "CAP_800")
        game.players[0].deck = [game._entity("CORE_AT_055")]
        game._damage_minion(0, undead, 99)
        game._resolve_deaths()
        self.assertTrue(any(event["kind"] == "acolyte_of_death_draw" for event in game.events))

    def test_targeted_spell_smoke(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        spell = self.add_hand(game, "EDR_262")
        game.step(Action("PLAY", spell.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        self.assertTrue(any(m.card_id == "DRG_217t" for m in game.players[0].board))

    def test_tar_tyrant_attack_bonus_tracks_opponent_turn(self):
        game = self.game()
        tar = self.add_board(game, "TLC_605", 0)
        self.assertEqual(1, tar.attack)
        game._start_turn(1)
        self.assertEqual(7, tar.attack)
        game._start_turn(0)
        self.assertEqual(1, tar.attack)
        tar.silenced = True
        self.assertEqual(1, tar.attack)

    def test_maloriak_and_story_of_lakkari_cross_turn_hooks(self):
        game = self.game()
        maloriak = self.add_board(game, "CATA_494")
        discarded = game._entity("CORE_EX1_005")
        game._dispatch_after_discard(game.players[0], discarded)
        self.assertTrue(any(m.card_id == discarded.card_id for m in game.players[0].board))
        self.assertIn(maloriak, game.players[0].board)

        game = self.game()
        story = self.add_hand(game, "TLC_466")
        game.step(Action("PLAY", story.entity_id))
        self.assertEqual(3, game.players[0].lakkari_turns)
        game._end_turn()
        self.assertEqual(2, game.players[0].lakkari_turns)
        self.assertEqual(7, sum(m.card_id == "Story_09_Imp" for m in game.players[0].board))


class ThirdStandardCardBatchTests(unittest.TestCase):
    """Regression coverage for the independent 50-card 50C tranche."""

    BATCH = {
        "TLC_817", "CATA_139", "TLC_513", "TLC_446", "TLC_433", "TLC_460",
        "TLC_239", "TLC_229", "TLC_631", "TLC_830", "TLC_602", "JAIL_450",
        "TLC_426", "JAIL_430", "TLC_833", "JAIL_458", "EDR_847",
        "CORE_RLK_086", "CORE_LOOT_044", "TLC_478", "TLC_107", "JAIL_730",
        "JAIL_376", "JAIL_329", "FIR_907", "END_016", "DINO_408",
        "CORE_OG_031", "CORE_DAL_720", "CORE_BT_781", "CATA_472", "CATA_467",
        "CAP_103", "CORE_DMF_067", "CORE_DRG_403", "CORE_EX1_059",
        "CORE_GIL_534", "CORE_GIL_623", "CORE_KAR_062", "CORE_SCH_713",
        "CORE_UNG_928", "EDR_254", "EDR_470", "EDR_861", "END_008",
        "TLC_101", "TLC_468", "TIME_443", "END_031", "TLC_242",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 37)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.deck.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    @staticmethod
    def add_board(game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_cost_windows_and_hero_power_triggers(self):
        game = self.game()
        game.players[0].card_class = "WARRIOR"
        game.players[0].mana = 2
        game.players[0].max_mana = 5
        sentinel = self.add_board(game, "EDR_470")
        self.add_board(game, "END_008")
        game.step(Action("HERO_POWER"))
        self.assertEqual(2, sentinel.health_delta)
        self.assertEqual(2, game.players[0].mana)

        game = self.game()
        saboteur = self.add_hand(game, "CORE_DRG_403")
        game.step(Action("PLAY", saboteur.entity_id))
        game._start_turn(1)
        self.assertEqual(4, game._hero_power_cost(game.players[1]))
        game.step(Action("HERO_POWER"))
        self.assertEqual(0, game.players[1].hero_power_cost_surcharge)

        game = self.game()
        neophyte = self.add_hand(game, "CORE_SCH_713")
        game.step(Action("PLAY", neophyte.entity_id))
        game._start_turn(1)
        spell = self.add_hand(game, "CORE_AT_055", 1)
        self.assertEqual(spell.cost + 1, game._effective_cost(game.players[1], spell))

    def test_blob_hounds_and_conditional_attack(self):
        game = self.game()
        blob = self.add_board(game, "TLC_468")
        game._damage_minion(0, blob, blob.health)
        game._resolve_deaths()
        self.assertEqual(
            {"TLC_468t1", "TLC_468t2"},
            {minion.card_id for minion in game.players[0].board},
        )

        game = self.game()
        hounds = self.add_hand(game, "TIME_443")
        game.step(Action("PLAY", hounds.entity_id))
        self.assertEqual(2, sum(
            minion.card_id in {"TIME_443t", "TIME_443t2"}
            for minion in game.players[0].board
        ))
        self.assertLess(game.players[1].health, 30)

        game = self.game()
        creeper = self.add_board(game, "CORE_UNG_928")
        self.assertEqual(creeper.definition.attack, creeper.attack)
        game._start_turn(1)
        self.assertEqual(creeper.definition.attack + 2, creeper.attack)
        game._start_turn(0)
        self.assertEqual(creeper.definition.attack, creeper.attack)

    def test_swap_discover_and_choice_rules(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005", 1)
        target.attack_delta = 2
        target.health_delta = 5
        before_attack, before_health = target.attack, target.max_health
        alchemist = self.add_hand(game, "CORE_EX1_059")
        game.step(Action("PLAY", alchemist.entity_id, 1, target.entity_id))
        self.assertEqual(before_health, target.attack)
        self.assertEqual(before_attack, target.max_health)

        game = self.game()
        self.add_hand(game, "CATA_111")
        historian = self.add_hand(game, "CORE_KAR_062")
        game.step(Action("PLAY", historian.entity_id))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertTrue(all(option.has_race("DRAGON") for option in game.pending_choice["options"]))

        game = self.game()
        stegodon = self.add_hand(game, "TLC_242")
        game.step(Action("PLAY", stegodon.entity_id))
        game.step(Action("RULE_CHOICE_PICK", 2))
        stegodon = next(m for m in game.players[0].board if m.entity_id == stegodon.entity_id)
        self.assertEqual(1, stegodon.attack_delta)
        self.assertEqual(1, stegodon.health_delta)


class FourthStandardCardBatchTests(unittest.TestCase):
    """Regression coverage for the fourth independent Standard card tranche."""

    BATCH = {
        "CATA_140", "CATA_190h", "DINO_435", "END_015", "JAIL_200", "TLC_825",
        "CORE_BOT_576", "CORE_BT_321", "CORE_BT_416", "CORE_CATA_002",
        "CORE_CATA_004", "CORE_CFM_781", "CORE_CFM_790", "CORE_DMF_511",
        "CORE_EDR_001", "CORE_EX1_131", "CORE_EX1_383", "CORE_EX1_559",
        "CORE_GIL_531", "CORE_ICC_210", "CORE_ICC_407", "CORE_LOE_039",
        "CORE_ONY_022", "CORE_SCH_181", "CORE_TID_931", "CORE_TRL_111",
        "CORE_TRL_900", "CORE_ULD_280", "CORE_WON_096", "Core_UNG_072",
        "DINO_130", "DINO_131", "DINO_403", "DINO_405", "DINO_412",
        "DINO_422", "DINO_433", "DINO_434", "EDR_001", "EDR_060", "EDR_105",
        "EDR_230", "EDR_252", "EDR_273", "EDR_481", "EDR_531", "EDR_848",
        "EDR_890", "EDR_942", "EDR_978",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 41)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.deck.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    @staticmethod
    def add_board(game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_cost_reductions_and_generated_cards(self):
        game = self.game()
        felscreamer = self.add_hand(game, "CORE_BT_416")
        game.step(Action("PLAY", felscreamer.entity_id))
        demon = self.add_hand(game, "CORE_CS2_065")
        self.assertEqual(max(0, demon.cost - 2), game._effective_cost(game.players[0], demon))
        game.step(Action("PLAY", demon.entity_id))
        self.assertEqual(0, game.players[0].next_demon_cost_reduction)

        game = self.game()
        self.add_hand(game, "GAME_005")
        game.step(Action("PLAY", game.players[0].hand[0].entity_id))
        foxy = self.add_hand(game, "CORE_DMF_511")
        game.step(Action("PLAY", foxy.entity_id))
        defias = self.add_hand(game, "CORE_EX1_131")
        self.assertEqual(0, game._effective_cost(game.players[0], defias))
        game.step(Action("PLAY", defias.entity_id))
        self.assertTrue(any(minion.card_id == "EX1_131t" for minion in game.players[0].board))

        game = self.game()
        dryad = self.add_hand(game, "EDR_001")
        game.step(Action("PLAY", dryad.entity_id))
        self.assertEqual(1, len(game.players[0].hand))
        self.assertTrue(game.players[0].hand[0].card_id.startswith("DREAM_"))

    def test_deathrattle_and_delayed_windows(self):
        game = self.game()
        rat = self.add_hand(game, "CORE_CFM_790")
        self.add_hand(game, "CORE_EX1_005", player=1)
        game.step(Action("PLAY", rat.entity_id))
        self.assertEqual(1, len(game.players[1].board))

        game = self.game()
        egg = self.add_board(game, "DINO_130")
        game._damage_minion(0, egg, egg.health)
        game._resolve_deaths()
        self.assertTrue(any(minion.card_id == "DINO_130t" for minion in game.players[0].board))

        game = self.game()
        target = self.add_board(game, "CORE_EX1_005")
        ceremony = self.add_hand(game, "DINO_405")
        game.step(Action("PLAY", ceremony.entity_id))
        game._start_turn(1)
        game._start_turn(0)
        game._end_turn()
        self.assertEqual(2, target.attack_delta)
        self.assertEqual(2, target.health_delta)

        game = self.game()
        strider = self.add_board(game, "EDR_978")
        game._damage_minion(0, strider, strider.health)
        game._resolve_deaths()
        self.assertEqual("EDR_978", game.players[0].deck[0].card_id)
        self.assertEqual(1, game.players[0].deck[0].cost)


class FifthStandardCardBatchTests(unittest.TestCase):
    """Regression coverage for the Time Travel 50E Standard tranche."""

    BATCH = {
        "TIME_006", "TIME_016", "TIME_025", "TIME_026", "TIME_027",
        "TIME_028", "TIME_029", "TIME_036", "TIME_040", "TIME_047",
        "TIME_049", "TIME_050", "TIME_052", "TIME_055", "TIME_057",
        "TIME_061", "TIME_062", "TIME_100", "TIME_102", "TIME_212",
        "TIME_214", "TIME_215", "TIME_217", "TIME_428", "TIME_429",
        "TIME_434", "TIME_435", "TIME_444", "TIME_447", "TIME_448",
        "TIME_449", "TIME_616", "TIME_620", "TIME_700", "TIME_703",
        "TIME_704", "TIME_705", "TIME_707", "TIME_710", "TIME_711",
        "TIME_712", "TIME_716", "TIME_730", "TIME_857", "TIME_859",
        "TIME_860", "TIME_861", "TIME_870", "TIME_872", "TIME_873",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 43)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.deck.clear()
            player.secrets.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    @staticmethod
    def add_board(game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_shreds_and_time_summons(self):
        game = self.game()
        hopper = self.add_hand(game, "TIME_025")
        game.step(Action("PLAY", hopper.entity_id))
        self.assertEqual(2, sum(card.card_id == "TIME_025t" for card in game.players[0].deck))
        replacement = game._entity("CORE_AT_055")
        game.players[0].deck.append(replacement)
        shred = next(card for card in game.players[0].deck if card.card_id == "TIME_025t")
        game.players[0].deck.remove(shred)
        game.players[0].deck.append(shred)
        game._draw(game.players[0])
        self.assertEqual(27, game.players[0].health)
        self.assertIn(replacement, game.players[0].hand)

        game = self.game()
        self.add_hand(game, "CATA_111")
        dimension = self.add_hand(game, "TIME_006")
        game.step(Action("PLAY", dimension.entity_id))
        self.assertEqual(2, sum(card.card_id == "TIME_006t1" for card in game.players[0].board))

    def test_past_discover_and_time_state(self):
        game = self.game()
        neon = self.add_hand(game, "TIME_016")
        game.step(Action("PLAY", neon.entity_id))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        option = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", option.entity_id))
        selected = next(card for card in game.players[0].hand if card.entity_id == option.entity_id)
        self.assertEqual(option.definition.attack + 5, selected.attack)
        self.assertEqual(option.definition.health + 5, selected.max_health)

        game = self.game()
        alter = self.add_hand(game, "TIME_857")
        game.step(Action("PLAY", alter.entity_id))
        option = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", option.entity_id))
        selected = next(card for card in game.players[0].hand if card.entity_id == option.entity_id)
        self.assertEqual(max(0, option.definition.cost - 2), selected.cost)
        self.assertEqual("DISCOVER", game.pending_choice["kind"])

        game = self.game()
        aura = self.add_hand(game, "TIME_700")
        game.step(Action("PLAY", aura.entity_id))
        game._end_turn()
        self.assertEqual(2, game.players[0].chronological_aura_turns[0])
        self.assertTrue(any(card.card_id == "TIME_700t" for card in game.players[0].board))

        game = self.game()
        coyote = self.add_hand(game, "TIME_047")
        game._damage_hero(game.players[1], 1)
        game._damage_hero(game.players[1], 1)
        self.assertEqual(max(0, coyote.cost - 2), game._effective_cost(game.players[0], coyote))


class SixthStandardCardBatchTests(unittest.TestCase):
    """Regression coverage for Cataclysm/Mending tranche 50F."""

    BATCH = {
        "CATA_132", "CATA_136", "CATA_180", "CATA_186", "CATA_208", "CATA_216",
        "CATA_305", "CATA_452", "CATA_458", "CATA_471", "CATA_473", "CATA_474",
        "CATA_475", "CATA_478", "CATA_483", "CATA_487", "CATA_493", "CATA_498",
        "CATA_499", "CATA_528", "CATA_529", "CATA_551", "CATA_553", "CATA_560",
        "CATA_564", "CATA_566", "CATA_567", "CATA_610", "CATA_614", "CATA_616",
        "CATA_697", "CATA_699", "CATA_786", "CATA_897", "CATA_978", "CATA_979",
        "MEND_041", "MEND_045", "MEND_300", "MEND_301", "MEND_303", "MEND_304",
        "MEND_305", "MEND_800", "MEND_801", "MEND_802", "MEND_803", "MEND_804",
        "MEND_805", "MEND_900",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 47)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.deck.clear()
            player.secrets.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    @staticmethod
    def add_board(game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_cataclysm_persistent_state_and_tokens(self):
        game = self.game()
        broodwatcher = self.add_hand(game, "CATA_132")
        broodwatcher.mana_spent_while_held = 8
        game.step(Action("PLAY", broodwatcher.entity_id))
        self.assertEqual(2, sum(card.card_id == "CATA_132t" for card in game.players[0].board))

        game = self.game()
        left = self.add_hand(game, "CORE_EX1_005")
        sabotage = self.add_hand(game, "CATA_186t")
        self.add_hand(game, "CORE_CS2_029")
        self.assertEqual(left.cost + 1, game._effective_cost(game.players[0], left))
        self.assertEqual(sabotage.cost, game._effective_cost(game.players[0], sabotage))

        game = self.game()
        spell = self.add_hand(game, "CORE_CS2_029")
        game.players[0].deck.append(game._entity("CORE_CS2_029"))
        kalec = self.add_hand(game, "CATA_458")
        game.step(Action("PLAY", kalec.entity_id))
        self.assertEqual(1, spell.spell_damage_bonus)
        self.assertEqual(1, game.players[0].deck[0].spell_damage_bonus)

        game = self.game()
        sigil = self.add_hand(game, "CATA_528")
        game.step(Action("PLAY", sigil.entity_id))
        game._start_turn(1)
        game._start_turn(0)
        self.assertTrue(any(card.card_id == "CATA_528t" for card in game.players[0].board))

        game = self.game()
        transformed = self.add_hand(game, "CATA_551")
        dragon = self.add_hand(game, "CATA_132")
        game.step(Action("PLAY", dragon.entity_id))
        self.assertEqual("CATA_551t", transformed.card_id)

    def test_animal_companion_and_recruit_package(self):
        game = self.game()
        game.players[0].deck.append(game._entity("CORE_EX1_005"))
        tame = self.add_hand(game, "MEND_300")
        game.step(Action("PLAY", tame.entity_id))
        self.assertEqual(1, game.players[0].animal_companion_cost_increase)
        self.assertEqual(1, len(game.players[0].hand))

        game = self.game()
        spiritspeaker = self.add_hand(game, "MEND_301")
        game.step(Action("PLAY", spiritspeaker.entity_id))
        self.assertEqual("RULE_CHOICE", game.pending_choice["kind"])
        game.step(Action("RULE_CHOICE_PICK", 0))
        self.assertTrue(any(card.card_id == "NEW1_032" for card in game.players[0].board))

        game = self.game()
        spell = self.add_hand(game, "MEND_802")
        game.step(Action("PLAY", spell.entity_id))
        recruits = [card for card in game.players[0].board if card.card_id == "CS2_101t"]
        self.assertEqual(2, len(recruits))
        self.assertTrue(all(card.divine_shield for card in recruits))

        game = self.game()
        blade = self.add_hand(game, "MEND_803")
        game.step(Action("PLAY", blade.entity_id))
        teamwork = self.add_hand(game, "MEND_900")
        game.step(Action("PLAY", teamwork.entity_id))
        recruits = [card for card in game.players[0].board if card.card_id == "CS2_101t"]
        self.assertEqual(4, len(recruits))
        self.assertTrue(all(card.attack >= 2 and card.max_health >= 2 for card in recruits))

        game = self.game()
        dead = self.add_board(game, "CORE_EX1_005")
        game._damage_minion(0, dead, dead.health)
        game._resolve_deaths()
        charity = self.add_hand(game, "MEND_805")
        game.step(Action("PLAY", charity.entity_id))
        copied = game.players[0].hand[-1]
        self.assertEqual("CORE_EX1_005", copied.card_id)
        self.assertEqual(7, copied.attack)
        self.assertEqual(5, copied.max_health)


class SeventhStandardCardBatchTests(unittest.TestCase):
    """Regression coverage for the 50G combat/stateful standard tranche."""

    BATCH = {
        "CAP_006", "CAP_101", "CAP_400", "CAP_802", "CAP_804", "CAP_805",
        "CAP_806", "CATA_480", "CATA_563", "CORE_AT_062", "CORE_BAR_313",
        "CORE_BOT_256", "CORE_ETC_111", "CORE_ETC_523", "CORE_SCH_605",
        "CORE_SW_047", "CORE_WON_350", "DINO_137", "DINO_402", "DINO_415",
        "DINO_424", "DINO_426", "DINO_427", "DINO_428", "DINO_429",
        "DINO_430", "EDR_014", "EDR_460", "EDR_461", "EDR_464", "EDR_472",
        "EDR_477", "EDR_482", "EDR_483", "EDR_484", "EDR_495", "EDR_530",
        "EDR_853", "END_002", "END_006", "END_009", "END_012", "END_013",
        "END_018", "END_029", "END_032", "FIR_778", "FIR_913", "FIR_955",
        "FIR_960",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 53)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.deck.clear()
            player.secrets.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    @staticmethod
    def add_board(game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_masks_and_druid_state_rules(self):
        game = self.game()
        target = self.add_board(game, "CORE_EX1_005")
        mask = self.add_hand(game, "DINO_402")
        game.step(Action("PLAY", mask.entity_id, 0, target.entity_id))
        self.assertEqual(7, len(game.players[0].board))
        self.assertTrue(all(card.attack == 1 and card.max_health == 1
                            for card in game.players[0].board))

        game = self.game()
        story = self.add_hand(game, "DINO_415")
        game.step(Action("PLAY", story.entity_id))
        self.assertEqual("DISCOVER", game.pending_choice["kind"])
        self.assertTrue(all(option.cost >= 5 and "DEATHRATTLE" in option.definition.mechanics
                            for option in game.pending_choice["options"]))
        option = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", option.entity_id))
        self.assertTrue(any(card.card_id == option.card_id for card in game.players[0].board))

        game = self.game()
        tyrande = self.add_hand(game, "EDR_464")
        game.step(Action("PLAY", tyrande.entity_id))
        self.assertEqual(3, game.players[0].spells_cast_twice_remaining)
        spell = self.add_hand(game, "CAP_006")
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertEqual(2, game.players[0].spells_cast_twice_remaining)
        self.assertEqual(28, game.players[1].health)

        game = self.game()
        taka = self.add_hand(game, "DINO_430")
        game.step(Action("PLAY", taka.entity_id))
        option = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", option.entity_id))
        taka_on_board = next(card for card in game.players[0].board if card.card_id == "DINO_430")
        self.assertEqual(option.attack, taka_on_board.attack)
        self.assertEqual(option.max_health, taka_on_board.max_health)
        self.assertEqual(option.card_id, taka_on_board.deathrattle_summon_card_id)
        self.assertEqual(1, len(game.players[0].board))

    def test_resurrect_transform_and_cost_rules(self):
        game = self.game()
        conspirator = self.add_board(game, "CAP_400")
        game._damage_minion(0, conspirator, conspirator.health)
        game._resolve_deaths()
        self.assertEqual(2, sum(card.card_id == "CAP_400t2t" for card in game.players[1].deck))
        game._draw(game.players[1])
        self.assertTrue(any(card.card_id == "CAP_400t2t" for card in game.players[0].board))

        game = self.game()
        target = self.add_board(game, "CORE_EX1_005")
        specialist = self.add_hand(game, "CAP_804")
        game.step(Action("PLAY", specialist.entity_id, 0, target.entity_id))
        self.assertTrue(target.reborn)
        specialist = self.add_hand(game, "CAP_804")
        game.step(Action("PLAY", specialist.entity_id, 0, target.entity_id))
        self.assertEqual(2, sum(card.card_id == target.card_id for card in game.players[0].board))

        game = self.game()
        game.players[0].health = 10
        apple = self.add_hand(game, "EDR_482")
        game.step(Action("PLAY", apple.entity_id))
        self.assertEqual(22, game.players[0].health)
        self.assertEqual(2, len(game.players[0].delayed_self_damage))

        game = self.game()
        game.players[0].health = 20
        game.players[0].mana = 0
        game.players[0].restored_health_this_turn = 1
        knight = self.add_hand(game, "CORE_ETC_523")
        game.step(Action("PLAY", knight.entity_id))
        self.assertEqual(17, game.players[0].health)
        self.assertEqual(0, game.players[0].mana)

    def test_deathrattle_and_copy_rules(self):
        game = self.game()
        held = self.add_hand(game, "CAP_006")
        acolyte = self.add_hand(game, "END_018")
        game.step(Action("PLAY", acolyte.entity_id))
        self.assertGreater(held.cost, 1_000_000)
        acolyte_on_board = next(card for card in game.players[0].board if card.card_id == "END_018")
        game._damage_minion(0, acolyte_on_board, acolyte_on_board.health)
        game._resolve_deaths()
        self.assertEqual(1, held.cost)

        game = self.game()
        held = self.add_hand(game, "CORE_EX1_005")
        ford = self.add_board(game, "CORE_SW_047")
        game._damage_minion(0, ford, 1)
        self.assertEqual(held.definition.attack + 5, held.attack)
        self.assertEqual(held.definition.health + 5, held.max_health)

        game = self.game()
        flytrap = self.add_board(game, "EDR_484")
        victim = self.add_board(game, "CORE_EX1_005", player=1)
        game._damage_minion(1, victim, victim.health)
        game._resolve_deaths()
        self.assertEqual(flytrap.definition.attack + victim.attack, flytrap.attack)


class EighthStandardCardBatchTests(unittest.TestCase):
    """Regression coverage for 50H deck/secret/upgrade card mechanics."""

    BATCH = {
        "CAP_401", "CAP_402", "CAP_403", "CAP_406", "CORE_AV_107",
        "CORE_CATA_006", "CORE_GIL_577", "CORE_TRL_345", "CORE_ULD_152",
        "EDR_455", "FIR_911", "FIR_914", "FIR_916", "FIR_918", "FIR_927",
        "FIR_940", "FIR_952", "JAIL_030", "JAIL_123", "JAIL_125", "JAIL_204",
        "JAIL_225", "JAIL_312", "JAIL_327", "JAIL_387", "JAIL_436", "JAIL_447",
        "JAIL_448", "JAIL_474", "JAIL_507", "JAIL_515", "JAIL_516", "JAIL_706",
        "JAIL_733", "JAIL_734", "JAIL_805", "JAIL_806", "JAIL_876", "JAIL_878",
        "JAIL_879", "JAIL_881", "JAIL_883", "JAIL_940", "JAIL_974", "JAIL_986",
        "TLC_234", "TLC_237", "TLC_244", "TLC_245", "TLC_256",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 59)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.deck.clear()
            player.secrets.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    @staticmethod
    def add_board(game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_deck_secret_and_discover_rules(self):
        game = self.game()
        ordinary = self.add_hand(game, "CORE_EX1_005")
        evidence = self.add_hand(game, "CAP_402")
        game.step(Action("PLAY", evidence.entity_id))
        self.assertEqual(1, sum(card.card_id == "CAP_400t2t" for card in game.players[1].deck))
        self.assertEqual("CAP_402", ordinary.temporary_play_effect)

        game = self.game()
        spell = self.add_hand(game, "CORE_CS2_029", player=0)
        plate = self.add_hand(game, "CORE_ULD_152", player=1)
        target = self.add_board(game, "CORE_EX1_005", player=0)
        game.current = 1
        game.step(Action("PLAY", plate.entity_id))
        game.current = 0
        game.step(Action("PLAY", spell.entity_id, 1, None))
        self.assertNotIn(target, game.players[0].board)

        game = self.game()
        glacial = self.add_hand(game, "CORE_AV_107")
        game.step(Action("PLAY", glacial.entity_id))
        option = game.pending_choice["options"][0]
        game.step(Action("DISCOVER_PICK", option.entity_id))
        selected = next(card for card in game.players[0].board if card.card_id == option.card_id)
        self.assertEqual(game.turn, selected.frozen_turn)

    def test_damage_deathrattle_and_hand_rules(self):
        game = self.game()
        victim = self.add_board(game, "CORE_EX1_005", player=1)
        nab = self.add_hand(game, "JAIL_225")
        game.step(Action("PLAY", nab.entity_id, 1, victim.entity_id))
        copied = game.players[0].deck[-1]
        self.assertEqual("CORE_EX1_005", copied.card_id)
        self.assertEqual(2, copied.cost)

        game = self.game()
        target = self.add_board(game, "CORE_EX1_005")
        dig = self.add_hand(game, "JAIL_876")
        game.step(Action("PLAY", dig.entity_id, 0, target.entity_id))
        self.assertEqual(4, target.deathrattle_summon_random_cost)
        self.assertEqual(2, target.deathrattle_summon_token_count)

        game = self.game()
        bite = self.add_hand(game, "JAIL_436")
        game.step(Action("PLAY", bite.entity_id))
        self.assertEqual(1, game.players[0].hero_attack_bonus)
        self.assertEqual(1, game.players[0].armor)
        self.assertTrue(any(card.card_id == "JAIL_436t" for card in game.players[0].hand))

        game = self.game()
        card = self.add_hand(game, "FIR_911")
        game._start_turn(0)
        self.assertEqual(1, card.smoldering_stage)
        game._start_turn(1)
        game._start_turn(0)
        self.assertNotIn(card, game.players[0].hand)


class NinthStandardCardBatchTests(unittest.TestCase):
    """Regression coverage for the Lost City 50I standard-card tranche."""

    BATCH = {
        "CORE_BAR_812", "DINO_414", "TLC_106", "TLC_109", "TLC_230", "TLC_232", "TLC_233",
        "TLC_247", "TLC_250", "TLC_252", "TLC_254", "TLC_257", "TLC_334",
        "TLC_364", "TLC_427", "TLC_430", "TLC_438", "TLC_441", "TLC_443",
        "TLC_444", "TLC_450", "TLC_452", "TLC_462", "TLC_465", "TLC_467",
        "TLC_469", "TLC_477", "TLC_479", "TLC_483", "TLC_516", "TLC_517",
        "TLC_518", "TLC_520", "TLC_521", "TLC_601", "TLC_620", "TLC_622",
        "TLC_810", "TLC_811", "TLC_814", "TLC_818", "TLC_819", "TLC_821",
        "TLC_822", "TLC_826", "TLC_827", "TLC_831", "TLC_836", "TLC_840",
        "TLC_841",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 61)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.deck.clear()
            player.secrets.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    @staticmethod
    def add_board(game, card_id, player=0):
        card = game._entity(card_id)
        card.summoned_turn = -1
        game._summon(game.players[player], card)
        return card

    def test_batch_has_exactly_fifty_registered_cards(self):
        game = self.game()
        self.assertEqual(50, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {rule.card_id for rule in game.rule_registry.all_rules()})

    def test_delayed_deck_and_cost_rules(self):
        game = self.game()
        flock = self.add_hand(game, "TLC_232")
        game.step(Action("PLAY", flock.entity_id))
        self.assertEqual([], game.players[0].board)
        game._start_turn(1)
        game._start_turn(0)
        self.assertEqual(3, sum(card.card_id == "TLC_237t" for card in game.players[0].board))

        game = self.game()
        loh = self.add_hand(game, "TLC_257")
        game.step(Action("PLAY", loh.entity_id))
        minion = self.add_hand(game, "CORE_EX1_005")
        self.assertEqual(5, game._effective_cost(game.players[0], minion))

        game = self.game()
        raptors = self.add_hand(game, "TLC_826")
        game.step(Action("PLAY", raptors.entity_id))
        self.assertEqual(10, sum(card.card_id == "TLC_826t" for card in game.players[0].deck))
        raptor = next(card for card in game.players[0].deck if card.card_id == "TLC_826t")
        game.players[0].deck.remove(raptor)
        game._receive_drawn_card(game.players[0], raptor)
        self.assertTrue(any(card.card_id == "TLC_826t" for card in game.players[0].board))

    def test_persistent_combat_and_hand_state_rules(self):
        game = self.game()
        ally = self.add_hand(game, "CORE_BAR_812", player=1)
        game.current = 1
        game.step(Action("PLAY", ally.entity_id))
        defender = self.add_board(game, "CORE_EX1_005", player=1)
        attacker = self.add_board(game, "CORE_EX1_005", player=0)
        game.current = 0
        game.step(Action("ATTACK", attacker.entity_id, 1, defender.entity_id))
        self.assertTrue(any(card.card_id == "CORE_CS2_033" for card in game.players[1].board))

        game = self.game()
        defenses = self.add_hand(game, "TLC_622")
        game.step(Action("PLAY", defenses.entity_id))
        security = next(card for card in game.players[0].board if card.card_id == "TLC_622t")
        before = security.attack
        game._damage_minion(0, security, 1)
        self.assertEqual(before + 1, security.attack)

        game = self.game()
        attacker = self.add_board(game, "CORE_EX1_005")
        archaios = self.add_board(game, "TLC_811")
        attacker.health_delta += 4
        game._after_minion_attack(0, attacker)
        self.assertEqual(archaios.max_health, attacker.max_health)

        game = self.game()
        original = self.add_hand(game, "CORE_EX1_005")
        toru = self.add_hand(game, "TLC_841")
        game.step(Action("PLAY", toru.entity_id))
        jar = next(card for card in game.players[0].hand if card.entity_id == original.entity_id)
        self.assertEqual("TLC_841t", jar.card_id)
        game._summon(game.players[0], jar)
        game._damage_minion(0, jar, jar.health)
        game._resolve_deaths()
        self.assertTrue(any(card.card_id == "CORE_EX1_005" for card in game.players[0].board))


class FinalStandardClosureTests(unittest.TestCase):
    """The final collectible Standard closure is declarative and executable."""

    BATCH = {
        "CAP_405", "CATA_213", "CATA_307", "CATA_470", "CATA_621",
        "CORE_CFM_670", "CORE_DAL_575", "CORE_WON_145", "EDR_031",
        "EDR_209", "EDR_232", "EDR_238", "EDR_259", "EDR_261",
        "EDR_430", "EDR_489", "EDR_491", "EDR_494", "EDR_517",
        "EDR_522", "EDR_526", "EDR_527", "EDR_781", "EDR_812",
        "EDR_819", "EDR_873", "EDR_895", "JAIL_101", "JAIL_122",
        "JAIL_205", "JAIL_303", "JAIL_313", "JAIL_315", "JAIL_330",
        "JAIL_434", "JAIL_470", "JAIL_500", "JAIL_802", "JAIL_861",
        "MEND_100", "MEND_307", "MEND_505", "TIME_030", "TIME_041",
        "TIME_064", "TIME_103", "TIME_706", "TTN_851",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 113)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.deck.clear()
            player.locations.clear()
            player.secrets.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = player.max_health = 30
            player.armor = 0
        return game

    @staticmethod
    def add_hand(game, card_id, player=0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    def test_final_48_registry_and_smoke(self):
        game = self.game()
        self.assertEqual(48, len(self.BATCH))
        self.assertTrue(self.BATCH <= game.executable_card_ids)
        self.assertTrue(self.BATCH <= {
            rule.card_id for rule in game.rule_registry.all_rules()
        })

    def test_final_48_stateful_effects(self):
        game = self.game()
        alex = self.add_hand(game, "CATA_307")
        game.step(Action("PLAY", alex.entity_id))
        self.assertEqual(15, game.players[0].health)
        game._apply_heal(game.players[0], game.players[0], 15)
        self.assertEqual(15, game.players[1].health)

        game = self.game()
        agamaggan = self.add_hand(game, "EDR_489")
        game.step(Action("PLAY", agamaggan.entity_id))
        coin = self.add_hand(game, "CORE_CS2_023")
        before = game.players[1].health
        game.step(Action("PLAY", coin.entity_id))
        self.assertEqual(before - 3, game.players[1].health)

        game = self.game()
        aura = self.add_hand(game, "TTN_851")
        game.step(Action("PLAY", aura.entity_id))
        spell = self.add_hand(game, "GAME_005")
        # The generic duration spans the opponent's next two own turns; the
        # present global turn is deliberately not charged.
        self.assertEqual(0, game._effective_cost(game.players[0], spell))

        game = self.game()
        source = self.add_hand(game, "TIME_706")
        game.players[0].starting_hand_snapshot = [game._entity("GAME_005")]
        original = self.add_hand(game, "CORE_CS2_023")
        game.step(Action("PLAY", source.entity_id))
        self.assertTrue(all(card.card_id == "GAME_005" for card in game.players[0].hand))
        game._end_turn()
        self.assertIn(original, game.players[0].hand)


class AuxiliaryEntityCoverageTests(unittest.TestCase):
    """Regression coverage for non-collectible current-Standard entities."""

    COINS = {
        "CATA_COIN1", "CATA_COIN2", "CATA_COIN3", "CATA_COIN4", "CATA_COIN5", "CATA_COIN6",
        "DINO_COIN1", "DINO_COIN2", "EDR_COIN1", "EDR_COIN2", "TLC_COIN2",
        "TIME_COIN1", "TIME_COIN2", "TIME_COIN3", "TIME_COIN4", "TIME_EVENT_COIN",
        "JAIL_COIN2", "JAIL_COIN3", "JAIL_EVENT_COIN",
    }

    def game(self):
        game = DragonMirrorGame(CARDS, 31337)
        game.current = 0
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.deck.clear()
            player.locations.clear()
            player.secrets.clear()
            player.mana = 0
            player.max_mana = 10
        return game

    def test_every_coin_variant_grants_temporary_mana(self):
        self.assertEqual(19, len(self.COINS))
        for card_id in self.COINS:
            with self.subTest(card_id=card_id):
                game = self.game()
                coin = game._entity(card_id)
                game.players[0].hand.append(coin)
                game.step(Action("PLAY", coin.entity_id))
                self.assertEqual(1, game.players[0].mana)

    def test_engine_owned_auxiliaries_are_executable(self):
        game = self.game()
        self.assertTrue(ENGINE_OWNED_AUXILIARY_IDS <= game.executable_card_ids)
        self.assertTrue(ENGINE_OWNED_AUXILIARY_IDS <= set(game.card_defs))

    def test_generated_leyline_options_and_scout_token(self):
        game = self.game()
        discount = game._entity("MEND_505t2")
        game.players[0].hand.append(discount)
        leyline = game._entity("MEND_500")
        game.players[0].hand.append(leyline)
        before = game._effective_cost(game.players[0], leyline)
        game.step(Action("PLAY", discount.entity_id))
        self.assertEqual(before - 2, game._effective_cost(game.players[0], leyline))

        game = self.game()
        target = game._entity("CORE_CS2_231")
        target.summoned_turn = -1
        game._summon(game.players[1], target)
        scout = game._entity("CATA_552t")
        game.players[0].mana = 20
        game.players[0].hand.append(scout)
        game.step(Action("PLAY", scout.entity_id, 1, target.entity_id))
        self.assertLess(target.health, target.max_health)


if __name__ == "__main__":
    unittest.main()
