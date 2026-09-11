from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import (
    ADDITIONAL_GENERATED_MINION_IDS,
    Action,
    BASIC_AUXILIARY_IDS,
    BONUS_EFFECTS,
    CardDef,
    DIRECT_IDS,
    DISCOVER_BANNED_IDS,
    DRAGON_IDS,
    DragonMirrorGame,
    EXECUTABLE_CARD_IDS,
    GENERATED_MINION_IDS,
    GENERATED_DRAGON_IDS,
    GENERATED_PIRATE_IDS,
    LOW_COST_DRAGON_IDS,
    Location,
    PIRATE_IDS,
    SUPPORTED_STADIUM_WEAPONS,
    SUPPORTED_ONE_COST_SUMMON_IDS,
    SUPPORTED_IDS,
    Weapon,
)


CARDS = ROOT / "cards.251332.enUS.json"


class DragonMirrorRulesTests(unittest.TestCase):
    def game(self, seed: int = 7) -> DragonMirrorGame:
        game = DragonMirrorGame(CARDS, seed)
        for player in game.players:
            player.hand.clear()
            player.board.clear()
            player.locations.clear()
            player.mana = 20
            player.max_mana = 10
            player.health = 30
            player.armor = 0
        return game

    def add_hand(self, game: DragonMirrorGame, card_id: str, player: int = 0):
        card = game._entity(card_id)
        game.players[player].hand.append(card)
        return card

    def add_board(self, game: DragonMirrorGame, card_id: str, player: int = 0):
        card = game._entity(card_id)
        card.summoned_turn = game.turn - 1
        game.players[player].board.append(card)
        return card

    def play(self, game: DragonMirrorGame, card, target_player=None, target_entity=None):
        game.step(Action("PLAY", card.entity_id, target_player, target_entity))

    def test_direct_and_generated_metadata_entities_are_loaded(self):
        game = self.game()
        self.assertEqual(EXECUTABLE_CARD_IDS | BASIC_AUXILIARY_IDS, set(game.card_defs))
        self.assertEqual(17, len(DIRECT_IDS))
        self.assertEqual(72, len(GENERATED_MINION_IDS))
        self.assertEqual(40, len(GENERATED_DRAGON_IDS))
        self.assertEqual(7, len(GENERATED_PIRATE_IDS))
        self.assertFalse(DRAGON_IDS & DISCOVER_BANNED_IDS)
        self.assertEqual((1, 3, ("TAUNT",)), (
            game.card_defs["CORE_CS2_065"].attack,
            game.card_defs["CORE_CS2_065"].health,
            game.card_defs["CORE_CS2_065"].mechanics,
        ))
        self.assertEqual("Purifying Vines", game.card_defs["TLC_813"].name)
        self.assertEqual("CORE_EX1_277", game.card_defs["CORE_EX1_277"].card_id)
        self.assertEqual("Arcane Missiles", game.card_defs["CORE_EX1_277"].name)

    def test_hogger_duplicates_warptooth_after_initial_draw(self):
        game = DragonMirrorGame(CARDS, 11)
        for index, player in enumerate(game.players):
            supported = [c for c in player.deck + player.hand if c.card_id in SUPPORTED_IDS]
            # Hogger adds one Warptooth to each 30-card list. The second
            # player additionally owns The Coin, which is now a first-class
            # supported metadata entity instead of an out-of-band CardDef.
            self.assertEqual(31 + index, len(supported), f"player {index}")
            self.assertEqual(2, sum(c.card_id == "JAIL_421" for c in supported))

    def test_manual_mulligan_is_an_explicit_two_player_phase(self):
        game = DragonMirrorGame(CARDS, 11, manual_mulligan=True)
        self.assertEqual(0, game.turn)
        self.assertEqual(0, game.current)
        self.assertEqual("MULLIGAN", game.pending_choice["kind"])
        self.assertEqual((3, 4), tuple(len(p.hand) for p in game.players))
        self.assertFalse(any(c.card_id == "GAME_005" for c in game.players[1].hand))

        rejected = game.players[0].hand[0]
        game.step(Action("MULLIGAN_TOGGLE", rejected.entity_id))
        self.assertTrue(game.snapshot()["pending_choice"]["options"][0]["replace"])
        game.step(Action("MULLIGAN_CONFIRM"))

        self.assertEqual(1, game.current)
        self.assertEqual("MULLIGAN", game.pending_choice["kind"])
        self.assertNotIn(rejected, game.players[0].hand)
        self.assertIn(rejected, game.players[0].deck)
        self.assertEqual(3, len(game.players[0].hand))

        game.step(Action("MULLIGAN_CONFIRM"))
        self.assertIsNone(game.pending_choice)
        self.assertEqual(1, game.turn)
        self.assertEqual(0, game.current)
        self.assertEqual((4, 5), tuple(len(p.hand) for p in game.players))
        self.assertEqual(
            1, sum(c.card_id == "GAME_005" for c in game.players[1].hand)
        )

    def test_mulligan_toggle_can_restore_keep_and_rejected_card_cannot_redraw(self):
        game = DragonMirrorGame(CARDS, 29, manual_mulligan=True)
        rejected = game.players[0].hand[0]
        game.step(Action("MULLIGAN_TOGGLE", rejected.entity_id))
        game.step(Action("MULLIGAN_TOGGLE", rejected.entity_id))
        self.assertEqual(set(), game.pending_choice["selected"])
        game.step(Action("MULLIGAN_TOGGLE", rejected.entity_id))
        game.step(Action("MULLIGAN_CONFIRM"))
        self.assertNotIn(rejected.entity_id, {card.entity_id for card in game.players[0].hand})
        self.assertIn(rejected.entity_id, {card.entity_id for card in game.players[0].deck})

    def test_manual_mulligan_policy_and_trace_are_seed_reproducible(self):
        results = []
        for _ in range(2):
            game = DragonMirrorGame(CARDS, 37, manual_mulligan=True)
            while game.pending_choice:
                game.step(game.choose_random_action())
            results.append(game.events)
        self.assertEqual(results[0], results[1])
        self.assertEqual(2, sum(e["kind"] == "mulligan_result" for e in results[0]))
        self.assertEqual(1, sum(e["kind"] == "coin_given" for e in results[0]))

    def test_search_clone_is_independent_and_shares_immutable_catalogues(self):
        game = DragonMirrorGame(CARDS, 41)
        child = game.clone()
        self.assertIs(game.card_defs, child.card_defs)
        self.assertIs(game.rule_registry, child.rule_registry)
        self.assertIsNot(game.players, child.players)
        self.assertEqual([], child.events)
        self.assertEqual(game.rng.getstate(), child.rng.getstate())

        original_health = game.players[0].health
        child.players[0].health -= 7
        child.players[0].hand.clear()
        self.assertEqual(original_health, game.players[0].health)
        self.assertNotEqual(len(game.players[0].hand), len(child.players[0].hand))

    def test_search_branch_applies_action_without_mutating_parent(self):
        game = DragonMirrorGame(CARDS, 43)
        action = game.legal_actions()[0]
        parent_state = game.snapshot()
        child = game.branch(action)
        self.assertEqual(parent_state, game.snapshot())
        self.assertNotEqual(parent_state, child.snapshot())
        self.assertEqual(0, game.invalid_actions)
        self.assertEqual(0, child.invalid_actions)

    def test_cloned_rng_produces_the_same_random_outcome(self):
        game = DragonMirrorGame(CARDS, 47)
        child = game.clone(include_history=True)
        action = game.choose_random_action()
        self.assertEqual(action, child.choose_random_action())
        game.step(action)
        child.step(action)
        self.assertEqual(game.snapshot(), child.snapshot())
        self.assertEqual(game.events, child.events)

    def test_player_observation_masks_only_opponent_private_hand(self):
        game = DragonMirrorGame(CARDS, 53)
        view = game.observation(0)
        self.assertTrue(view["players"][0]["hand"])
        self.assertIn("id", view["players"][0]["hand"][0])
        self.assertEqual(len(game.players[1].hand), len(view["players"][1]["hand"]))
        self.assertTrue(all(card["hidden"] for card in view["players"][1]["hand"]))
        self.assertFalse(any("id" in card for card in view["players"][1]["hand"]))

    def test_determinization_preserves_counts_public_coin_and_game_rng(self):
        game = DragonMirrorGame(CARDS, 59)
        before_rng = game.rng.getstate()
        combined = sorted(
            card.entity_id for card in game.players[1].hand + game.players[1].deck
        )
        sampled = game.determinize_hidden(0, seed=999)
        self.assertEqual(before_rng, game.rng.getstate())
        self.assertEqual(before_rng, sampled.rng.getstate())
        self.assertEqual(len(game.players[1].hand), len(sampled.players[1].hand))
        self.assertEqual(
            combined,
            sorted(card.entity_id for card in sampled.players[1].hand + sampled.players[1].deck),
        )
        self.assertTrue(any(card.card_id == "GAME_005" for card in sampled.players[1].hand))
        sampled.players[1].hand.clear()
        self.assertTrue(game.players[1].hand)

    def test_brood_keeper_and_mother_duck(self):
        game = self.game()
        keeper = self.add_hand(game, "EDR_457")
        self.add_hand(game, "CATA_556")
        self.play(game, keeper)
        self.assertEqual((2, 2), (game.players[0].weapon.attack, game.players[0].weapon.durability))

        duck = self.add_hand(game, "EDR_492")
        self.play(game, duck)
        ducklings = [m for m in game.players[0].board if m.card_id == "EDR_492t"]
        self.assertEqual(3, len(ducklings))
        self.assertTrue(all(m.rush for m in ducklings))

    def test_librarian_silences_buffs_and_keywords(self):
        game = self.game()
        target = self.add_board(game, "JAIL_421", 1)
        target.attack_delta = 4
        target.taunt = True
        librarian = self.add_hand(game, "CORE_SW_066")
        self.play(game, librarian, 1, target.entity_id)
        self.assertEqual(target.definition.attack, target.attack)
        self.assertFalse(target.taunt)
        self.assertTrue(target.silenced)

    def test_kindred_and_holding_dragon_cost_reductions(self):
        game = self.game()
        player = game.players[0]
        windpeak = self.add_hand(game, "TLC_600")
        slither = self.add_hand(game, "END_033")
        self.assertEqual(4, game._effective_cost(player, slither))
        player.played_races_last_turn.add("DRAGON")
        self.assertEqual(5, game._effective_cost(player, windpeak))

    def test_searing_fissure_and_volcano_fire_bonus(self):
        game = self.game(17)
        friendly = self.add_board(game, "CATA_556", 0)
        enemy = self.add_board(game, "JAIL_384", 1)
        fissure = self.add_hand(game, "CATA_582")
        self.play(game, fissure)
        self.assertEqual(1, friendly.damage)
        self.assertEqual(1, enemy.damage)
        self.assertEqual(3, game.players[0].hero_attack_bonus)
        volcano = self.add_hand(game, "CATA_584")
        self.play(game, volcano)
        location = game.players[0].locations[0]
        location.cooldown = 0
        before = game.players[1].health + enemy.health
        game.step(Action("LOCATION", location.entity_id))
        after = game.players[1].health + enemy.health
        self.assertEqual(6, before - after)

    def test_torch_requires_damage_and_returns_on_excess(self):
        game = self.game()
        target = self.add_board(game, "JAIL_384", 1)
        target.damage = 9
        torch = self.add_hand(game, "CATA_585")
        self.play(game, torch, 1, target.entity_id)
        self.assertIn(torch, game.players[0].hand)
        self.assertNotIn(target, game.players[1].board)

    def test_sanguine_depths_activates_after_cooldown(self):
        game = self.game()
        location_card = self.add_hand(game, "CORE_REV_990")
        target = self.add_board(game, "JAIL_384", 1)
        self.play(game, location_card)
        location = game.players[0].locations[0]
        self.assertEqual(1, location.cooldown)
        location.cooldown = 0
        game.step(Action("LOCATION", location.entity_id, 1, target.entity_id))
        self.assertEqual(1, target.damage)
        self.assertEqual(12, target.attack)
        self.assertEqual(2, location.durability)

    def test_four_distinct_friendly_characters_summon_warptooth(self):
        game = self.game()
        player = game.players[0]
        warptooth = self.add_hand(game, "JAIL_421")
        second = game._entity("JAIL_421")
        player.deck.append(second)
        victims = [self.add_board(game, "JAIL_384", 0) for _ in range(3)]
        game._damage_hero(player, 1)
        for victim in victims:
            game._damage_minion(0, victim, 1)
        self.assertNotIn(warptooth, player.hand)
        self.assertIn(warptooth, player.board)
        self.assertIn(second, player.board)

    def test_discover_cards_stay_inside_supported_closed_pool(self):
        game = self.game(23)
        darkrider = self.add_hand(game, "EDR_456")
        self.add_hand(game, "CATA_556")
        self.play(game, darkrider)
        choices = game.legal_actions()
        self.assertEqual(3, len(choices))
        self.assertEqual({"DISCOVER_PICK"}, {choice.kind for choice in choices})
        options = game.pending_choice["options"]
        self.assertEqual(3, len({card.card_id for card in options}))
        self.assertEqual(3, len({card.gifts[0] for card in options}))
        game.step(choices[0])
        pick = [event for event in game.events if event["kind"] == "discover_pick"][-1]
        self.assertIn(pick["card"], SUPPORTED_IDS)

        suffusion = self.add_hand(game, "FIR_939")
        self.play(game, suffusion, 1, None)
        self.assertEqual({"DISCOVER_PICK"}, {choice.kind for choice in game.legal_actions()})
        game.step(game.legal_actions()[0])
        pick = [event for event in game.events if event["kind"] == "discover_pick"][-1]
        self.assertTrue(pick["gifts"])

    def test_dark_gifts_respect_keyword_eligibility(self):
        game = self.game()
        hogger = game._entity("JAIL_384")
        self.assertTrue(hogger.taunt)
        self.assertNotIn("bundled_up", game._eligible_dark_gifts(hogger))
        prescient = game._entity("END_033")
        self.assertTrue(prescient.elusive)
        self.assertNotIn("well_rested", game._eligible_dark_gifts(prescient))
        warptooth = game._entity("JAIL_421")
        warptooth.charge = True
        self.assertNotIn("sleepwalker", game._eligible_dark_gifts(warptooth))

    def test_rewind_card_records_a_restorable_decision_point(self):
        game = self.game()
        announcer = self.add_hand(game, "TIME_034")
        self.play(game, announcer)
        event = next(e for e in game.events if e["kind"] == "rewind_offer")
        self.assertTrue(event["restorable"])
        self.assertEqual(
            {"REWIND_KEEP", "REWIND_RETRY"},
            {action.kind for action in game.legal_actions()},
        )
        game.step(Action("REWIND_RETRY"))
        decision = [e for e in game.events if e["kind"] == "rewind_pick"][-1]
        self.assertEqual("retry", decision["decision"])
        self.assertIsNone(game.pending_choice)
        for index, player in enumerate(game.players):
            self.assertIn(player.weapon.card_id, SUPPORTED_STADIUM_WEAPONS)
            _, attack, durability = SUPPORTED_STADIUM_WEAPONS[player.weapon.card_id]
            self.assertEqual(attack + (1 if index == 0 else 0), player.weapon.attack)
            self.assertEqual(durability + (1 if index == 0 else 0), player.weapon.durability)

    def test_rewind_restores_first_roll_side_effects_before_retry(self):
        game = self.game(19)
        damaged = self.add_board(game, "JAIL_421")
        damaged.damage = 2
        base_attack = damaged.attack
        base_health = damaged.max_health
        game.players[0].weapon = Weapon("JAIL_376", "Ball and Chain", 1, 2)
        announcer = self.add_hand(game, "TIME_034")
        self.play(game, announcer)
        self.assertEqual(base_attack + 1, damaged.attack)
        game.step(Action("REWIND_RETRY"))
        restored = next(m for m in game.players[0].board if m.entity_id == damaged.entity_id)
        self.assertEqual(base_attack + 1, restored.attack)
        self.assertEqual(base_health + 2, restored.max_health)

    def test_generated_weapon_passives_and_deathrattle(self):
        game = self.game(29)
        player = game.players[0]
        enemy = game.players[1]

        player.weapon = Weapon("CORE_BT_781", "Bulwark of Azzinoth", 1, 1)
        game._damage_hero(player, 20)
        self.assertEqual(30, player.health)
        self.assertIsNone(player.weapon)

        player.armor = 7
        player.weapon = Weapon("CORE_LOOT_044", "Bladed Gauntlet", 0, 2)
        self.assertEqual(7, player.attack)
        legal = game.legal_actions()
        self.assertFalse(any(a.kind == "HERO_ATTACK" and a.target_entity is None for a in legal))

        friendly = self.add_board(game, "JAIL_421", 0)
        hostile = self.add_board(game, "JAIL_421", 1)
        player.weapon = Weapon("TLC_478", "Axe of the Forefathers", 2, 2)
        game.step(Action("HERO_ATTACK", None, 1, hostile.entity_id))
        self.assertGreaterEqual(friendly.damage, 1)

        cannoneer_source = self.add_hand(game, "CAP_107")
        self.play(game, cannoneer_source)
        cannoneer = next(c for c in player.hand if c.card_id == "CAP_107t")
        player.hand.remove(cannoneer)
        cannoneer.summoned_turn = game.turn - 1
        player.board.append(cannoneer)
        player.hero_attacks_this_turn = 0
        player.weapon = Weapon("CAP_103", "Hand Cannon", 3, 2)
        before = enemy.health
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertLess(enemy.health, before - 2)

    def test_generated_weapon_lifesteal_draw_discard_and_face_restriction(self):
        game = self.game(31)
        player = game.players[0]
        enemy = game.players[1]
        player.health = 20
        player.weapon = Weapon("RLK_067", "Corrupted Ashbringer", 5, 2)
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertEqual(25, player.health)

        player.hero_attacks_this_turn = 0
        before_deck = len(player.deck)
        player.weapon = Weapon("EDR_253", "Ursine Maul", 4, 2)
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertEqual(before_deck - 1, len(player.deck))

        player.hand.clear()
        low = self.add_hand(game, "EDR_456")
        high = self.add_hand(game, "JAIL_384")
        player.hero_attacks_this_turn = 0
        player.weapon = Weapon("END_016", "Chronoclaws", 4, 3)
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertIn(low, player.hand)
        self.assertNotIn(high, player.hand)

        player.hero_attacks_this_turn = 0
        player.weapon = Weapon("END_012", "Hand of Infinity", 4, 2)
        self.assertFalse(any(
            action.kind == "HERO_ATTACK" and action.target_entity is None
            for action in game.legal_actions()
        ))

    def test_generated_weapon_summon_and_draw_deathrattles(self):
        game = self.game(37)
        player = game.players[0]
        before_deck = len(player.deck)
        player.weapon = Weapon("DINO_408", "Crystal Tusk", 2, 1)
        game._destroy_weapon(player)
        self.assertEqual(before_deck - 2, len(player.deck))

        player.weapon = Weapon("CORE_OG_031", "Hammer of Twilight", 4, 1)
        game._destroy_weapon(player)
        self.assertTrue(any(m.card_id == "OG_031a" for m in player.board))

        player.weapon = Weapon("JAIL_450", "Corpse Cannon", 1, 2)
        player.hero_attacks_this_turn = 0
        game.step(Action("HERO_ATTACK", None, 1, None))
        ghoul = next(m for m in player.board if m.card_id == "JAIL_450t")
        self.assertTrue(ghoul.charge)

        player.hero_attacks_this_turn = 0
        player.weapon = Weapon("TLC_833", "Insect Claw", 2, 2)
        game.step(Action("HERO_ATTACK", None, 1, None))
        grub = next(m for m in player.board if m.card_id == "TLC_833t")
        self.assertTrue(grub.rush)

    def test_card_provenance_and_smuggled_shovel(self):
        game = self.game(41)
        player = game.players[0]
        original = game._entity("CATA_582", started_in_deck=True)
        generated = game._entity("CATA_582", created_by="test_generator")
        player.deck.extend([original, generated])
        player.weapon = Weapon("JAIL_380", "Smuggled Shovel", 1, 1)
        game._destroy_weapon(player)
        self.assertIn(generated, player.hand)
        self.assertIn(original, player.deck)
        self.assertFalse(generated.started_in_deck)
        self.assertEqual("test_generator", generated.created_by)

    def test_frostmourne_records_and_resummons_killed_minions(self):
        game = self.game(43)
        player = game.players[0]
        victim = self.add_board(game, "EDR_456", 1)
        player.weapon = Weapon("CORE_RLK_086", "Frostmourne", 4, 1)
        game.step(Action("HERO_ATTACK", None, 1, victim.entity_id))
        self.assertNotIn(victim, game.players[1].board)
        revived = [m for m in player.board if m.card_id == victim.card_id]
        self.assertEqual(1, len(revived))
        self.assertEqual("CORE_RLK_086", revived[0].created_by)

    def test_dormant_sheep_and_class_filtered_weapon_buff(self):
        game = self.game(47)
        player = game.players[0]
        player.weapon = Weapon("EDR_416", "Shepherd's Crook", 3, 2)
        game.step(Action("HERO_ATTACK", None, 1, None))
        sheep = next(m for m in player.board if m.card_id == "EDR_416t")
        self.assertEqual(2, sheep.dormant_turns)
        self.assertFalse(any(a.source == sheep.entity_id for a in game.legal_actions()))
        game._start_turn(1)
        game._start_turn(0)
        self.assertEqual(1, sheep.dormant_turns)
        game._start_turn(1)
        game._start_turn(0)
        self.assertEqual(0, sheep.dormant_turns)

        paladin = game._instance_from_definition(
            CardDef("TEST_PALADIN", "Paladin minion", "MINION", 1, 1, 1, "", (), "PALADIN")
        )
        warrior = game._entity("EDR_456")
        player.board.extend([paladin, warrior])
        player.weapon = Weapon("JAIL_329", "Truth Seeker", 3, 2)
        player.hero_attacks_this_turn = 0
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertEqual((3, 3), (paladin.attack, paladin.max_health))
        self.assertEqual((1, 1), (warrior.attack, warrior.max_health))

    def test_defiled_spear_hits_a_different_enemy(self):
        game = self.game(53)
        player = game.players[0]
        first = self.add_board(game, "JAIL_421", 1)
        second = self.add_board(game, "JAIL_421", 1)
        player.weapon = Weapon("EDR_842", "Defiled Spear", 2, 3)
        game.step(Action("HERO_ATTACK", None, 1, first.entity_id))
        self.assertEqual(2, first.damage)
        # "Another random enemy" may be either the opposing hero or the
        # other minion, but it must never hit the original attack target.
        enemy = game.players[1]
        self.assertEqual(2, (30 - enemy.health) + second.damage)

    def test_generated_keyword_dragons_and_poisonous_combat(self):
        game = self.game(59)
        wyrm = game._entity("CORE_DRG_079", created_by="EDR_456")
        self.assertTrue(wyrm.rush)
        self.assertTrue(wyrm.divine_shield)
        self.assertTrue(wyrm.elusive)

        poisonous = self.add_board(game, "TIME_045")
        defender = self.add_board(game, "JAIL_421", 1)
        game.step(Action("ATTACK", poisonous.entity_id, 1, defender.entity_id))
        self.assertFalse(any(m.entity_id == defender.entity_id for m in game.players[1].board))
        reborn = [m for m in game.players[0].board if m.card_id == "TIME_045"]
        self.assertEqual(1, len(reborn))
        self.assertEqual(1, reborn[0].health)
        self.assertTrue(reborn[0].poisonous)

    def test_elusive_only_blocks_enemy_spell_and_hero_power_targeting(self):
        game = self.game(61)
        elusive = self.add_board(game, "CORE_NEW1_023", 1)
        friendly = self.add_board(game, "CORE_NEW1_023")
        spell = self.add_hand(game, "FIR_939")
        spell_targets = {
            (a.target_player, a.target_entity)
            for a in game.legal_actions()
            if a.kind == "PLAY" and a.source == spell.entity_id
        }
        self.assertNotIn((1, elusive.entity_id), spell_targets)
        self.assertIn((0, friendly.entity_id), spell_targets)

        battlecry = self.add_hand(game, "TLC_600")
        battlecry_targets = {
            (a.target_player, a.target_entity)
            for a in game.legal_actions()
            if a.kind == "PLAY" and a.source == battlecry.entity_id
        }
        self.assertIn((1, elusive.entity_id), battlecry_targets)

    def test_generated_dragon_battlecries_without_secondary_pools(self):
        game = self.game(67)
        player = game.players[0]
        self.add_hand(game, "CORE_NEW1_023")
        broodmother = self.add_hand(game, "CATA_111")
        player.mana = 7
        self.play(game, broodmother)
        self.assertEqual(6, player.mana)

        self.add_hand(game, "CORE_NEW1_023")
        self.add_hand(game, "CORE_LOOT_137")
        twilight = self.add_hand(game, "CORE_EX1_043")
        self.play(game, twilight)
        self.assertEqual(4, twilight.max_health)

        friendly = self.add_board(game, "CORE_LOOT_137")
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        primordial = self.add_hand(game, "CORE_UNG_848")
        player.mana = 20
        self.play(game, primordial)
        self.assertEqual(2, friendly.damage)
        self.assertEqual(2, enemy.damage)
        self.assertEqual(0, primordial.damage)

    def test_generated_dragon_stat_battlecries(self):
        game = self.game(71)
        damaged_friendly = self.add_board(game, "JAIL_421")
        damaged_enemy = self.add_board(game, "JAIL_421", 1)
        damaged_friendly.damage = 1
        damaged_enemy.damage = 2

        infinite = self.add_hand(game, "TIME_051")
        self.play(game, infinite)
        self.assertEqual(6, infinite.attack)

        bronze = self.add_hand(game, "TIME_720")
        self.play(game, bronze)
        self.assertEqual(6, bronze.max_health)

        heir = self.add_hand(game, "TIME_871")
        self.play(game, heir)
        self.assertEqual((6, 10), (heir.attack, heir.max_health))

    def test_dragon_turtle_and_end_turn_dragons(self):
        game = self.game(73)
        player = game.players[0]
        gifted = self.add_hand(game, "CORE_NEW1_023")
        gifted.gifts.append("sweet_dreams")
        turtle = self.add_hand(game, "FIR_956")
        self.play(game, turtle)
        self.assertEqual(6, player.armor)
        self.assertEqual(3, player.hero_attack_bonus)

        earthen = self.add_board(game, "CATA_999")
        peddler = self.add_board(game, "EDR_889")
        target = self.add_board(game, "CORE_NEW1_023")
        other_target = self.add_board(game, "CORE_LOOT_137")
        eligible_dragons = [
            m for m in player.board
            if m.entity_id != peddler.entity_id and m.has_race("DRAGON")
        ]
        before = {
            m.entity_id: (m.attack, m.max_health) for m in eligible_dragons
        }
        enemy_health = game.players[1].health
        game.step(Action("END_TURN"))
        self.assertEqual(enemy_health - 4, game.players[1].health)
        changed = [
            m for m in eligible_dragons
            if (m.attack, m.max_health)
            == (before[m.entity_id][0] + 1, before[m.entity_id][1] + 1)
        ]
        self.assertEqual(1, len(changed))
        self.assertEqual((1, 4), (peddler.attack, peddler.max_health))

    def test_death_batch_chillmaw_and_afflicted_devastator(self):
        game = self.game(79)
        player = game.players[0]
        self.add_hand(game, "CORE_NEW1_023")
        chillmaw = self.add_board(game, "CORE_AT_123")
        friendly = self.add_board(game, "CORE_LOOT_137")
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        chillmaw.damage = chillmaw.max_health
        game._resolve_deaths()
        self.assertEqual(3, friendly.damage)
        self.assertEqual(3, enemy.damage)

        friendly.damage = 0
        enemy.damage = 0
        afflicted = self.add_hand(game, "EDR_459")
        self.play(game, afflicted)
        self.assertEqual(3, friendly.damage)
        afflicted.damage = afflicted.max_health
        game._resolve_deaths()
        self.assertTrue(any(m.entity_id == friendly.entity_id for m in player.board))
        self.assertEqual(3, enemy.damage)

    def test_deathrattle_filtered_draws(self):
        game = self.game(83)
        player = game.players[0]
        player.deck = [
            game._instance_from_definition(
                CardDef("TEST_BIG_SPELL", "Big Spell", "SPELL", 6)
            ),
            game._entity("CORE_NEW1_023"),
            game._entity("CORE_LOOT_137"),
            game._entity("EDR_456"),
        ]
        trickster = self.add_board(game, "EDR_571")
        trickster.damage = trickster.max_health
        game._resolve_deaths()
        self.assertTrue(any(card.card_id == "TEST_BIG_SPELL" for card in player.hand))

        dreadwing = self.add_board(game, "EDR_572")
        dreadwing.damage = dreadwing.max_health
        game._resolve_deaths()
        dragons = [
            card for card in player.hand
            if card.card_id in {"CORE_NEW1_023", "CORE_LOOT_137"}
        ]
        self.assertEqual(2, len(dragons))
        self.assertTrue(all(card.cost_delta == -1 for card in dragons))
        self.assertTrue(any(card.card_id == "EDR_456" for card in player.deck))

    def test_generated_dragon_end_turn_summon_and_damage(self):
        game = self.game(89)
        player = game.players[0]
        keeper = self.add_board(game, "CATA_476")
        blackwing = self.add_board(game, "CORE_YOP_034")
        enemy = self.add_board(game, "JAIL_421", 1)
        game.step(Action("END_TURN"))
        tokens = [m for m in player.board if m.card_id == "CATA_476t"]
        self.assertEqual(1, len(tokens))
        self.assertEqual((6, 6), (tokens[0].attack, tokens[0].max_health))
        self.assertTrue(tokens[0].divine_shield)
        self.assertTrue(tokens[0].has_race("ELEMENTAL"))
        self.assertTrue(tokens[0].has_race("DRAGON"))
        self.assertFalse(any(m.entity_id == enemy.entity_id for m in game.players[1].board))
        self.assertIn(keeper, player.board)
        self.assertIn(blackwing, player.board)

    def test_great_dracorex_damages_other_enemy_minions(self):
        game = self.game(97)
        dracorex = self.add_board(game, "DINO_401")
        primary = self.add_board(game, "CORE_LOOT_137", 1)
        collateral = self.add_board(game, "CORE_NEW1_023", 1)
        game.step(Action("ATTACK", dracorex.entity_id, 1, primary.entity_id))
        self.assertEqual(5, primary.damage)
        self.assertFalse(any(
            m.entity_id == collateral.entity_id for m in game.players[1].board
        ))
        self.assertEqual(6, dracorex.damage)

    def test_briarspawn_attacks_and_sends_excess_to_hero(self):
        game = self.game(101)
        briar = self.add_board(game, "EDR_453")
        target = self.add_board(game, "JAIL_421", 1)
        game.step(Action("END_TURN"))
        self.assertFalse(any(
            m.entity_id == target.entity_id for m in game.players[1].board
        ))
        self.assertEqual(21, game.players[1].health)
        self.assertEqual(3, briar.damage)

    def test_epoch_only_destroys_minions_played_last_turn(self):
        game = self.game(103)
        previous = self.add_board(game, "CORE_LOOT_137", 1)
        previous.played_turn = game.turn - 1
        summoned = self.add_board(game, "CORE_NEW1_023", 1)
        summoned.played_turn = -1
        epoch = self.add_hand(game, "TIME_714")
        self.play(game, epoch)
        self.assertFalse(any(
            m.entity_id == previous.entity_id for m in game.players[1].board
        ))
        self.assertTrue(any(
            m.entity_id == summoned.entity_id for m in game.players[1].board
        ))
        self.assertEqual(game.turn, epoch.played_turn)

    def test_scaled_lancer_gives_all_enemy_minions_taunt(self):
        game = self.game(107)
        attacker = self.add_board(game, "CORE_NEW1_023")
        lancer = self.add_board(game, "CATA_898")
        enemy = self.add_board(game, "CORE_NEW1_023", 1)
        attacks = [
            action for action in game.legal_actions()
            if action.kind == "ATTACK" and action.source == attacker.entity_id
        ]
        self.assertEqual({enemy.entity_id}, {action.target_entity for action in attacks})
        lancer.silenced = True
        attacks = [
            action for action in game.legal_actions()
            if action.kind == "ATTACK" and action.source == attacker.entity_id
        ]
        self.assertIn(None, {action.target_entity for action in attacks})

    def test_damaged_time_twisted_seer_adds_spell_damage(self):
        game = self.game(109)
        seer = self.add_board(game, "END_022")
        seer.damage = 1
        target = self.add_board(game, "CORE_LOOT_137", 1)
        spell = self.add_hand(game, "FIR_939")
        self.play(game, spell, 1, target.entity_id)
        self.assertEqual(4, target.damage)
        self.assertEqual(2, game._spell_damage(game.players[0]))

    def test_ysera_weaponsmith_and_cloud_serpent(self):
        game = self.game(113)
        player = game.players[0]
        player.max_mana = 7
        player.mana = 20
        ysera = self.add_hand(game, "EDR_000")
        self.play(game, ysera)
        self.assertEqual(10, player.max_mana)
        self.assertEqual(14, player.mana)

        held_minion = self.add_hand(game, "CORE_NEW1_023")
        held_weapon = game._instance_from_definition(
            CardDef("TEST_WEAPON", "Test Weapon", "WEAPON", 2, 2, 2)
        )
        player.hand.append(held_weapon)
        weaponsmith = self.add_hand(game, "END_021")
        self.play(game, weaponsmith)
        self.assertEqual(5, held_minion.attack)
        self.assertEqual(4, held_weapon.attack)

        serpent = self.add_hand(game, "TLC_888")
        before_ids = {card.entity_id for card in player.hand}
        self.play(game, serpent)
        copies = [
            card for card in player.hand
            if card.entity_id not in before_ids and card.created_by == "TLC_888"
        ]
        self.assertEqual(1, len(copies))
        self.assertTrue(copies[0].has_race("DRAGON"))

    def test_crumblecrusher_and_omen_of_the_end(self):
        game = self.game(127)
        player = game.players[0]
        enemy = game.players[1]
        first = self.add_board(game, "CORE_LOOT_137", 1)
        second = self.add_board(game, "CORE_NEW1_023", 1)
        enemy.locations.append(Location(9999, "TEST_LOCATION", 2, 0))
        enemy.weapon = Weapon("TEST_WEAPON", "Test Weapon", 2, 2)
        crusher = self.add_hand(game, "END_034")
        self.play(game, crusher)
        survivors = {m.entity_id for m in enemy.board}
        self.assertEqual(1, len(survivors & {first.entity_id, second.entity_id}))
        self.assertFalse(enemy.locations)
        self.assertIsNone(enemy.weapon)

        player.deck.clear()
        enemy.deck = [game._entity("CORE_NEW1_023") for _ in range(6)]
        omen = self.add_hand(game, "END_035")
        self.play(game, omen)
        self.assertEqual(1, len(enemy.deck))

    def test_illusory_greenwing_tokens_summon_when_drawn_and_replace_draw(self):
        game = self.game(131)
        player = game.players[0]
        player.deck.clear()
        greenwing = self.add_board(game, "EDR_260")
        greenwing.damage = greenwing.max_health
        game._resolve_deaths()
        illusions = [card for card in player.deck if card.card_id == "EDR_260t"]
        self.assertEqual(2, len(illusions))
        self.assertTrue(all(card.summoned_when_drawn for card in illusions))

        replacement = game._entity("CORE_NEW1_023")
        drawn_illusion = illusions[0]
        player.deck = [replacement, drawn_illusion]
        game._draw(player)
        self.assertTrue(any(
            m.entity_id == drawn_illusion.entity_id for m in player.board
        ))
        self.assertTrue(any(
            card.entity_id == replacement.entity_id for card in player.hand
        ))

    def test_murozond_becomes_infinite_at_next_owner_turn(self):
        game = self.game(137)
        murozond = self.add_hand(game, "TIME_024")
        self.play(game, murozond)
        self.assertTrue(murozond.infinite_attack_next_turn)
        game.step(Action("END_TURN"))
        self.assertEqual(8, murozond.attack)
        game.step(Action("END_TURN"))
        self.assertEqual(2_147_483_647, murozond.attack)
        self.assertFalse(murozond.infinite_attack_next_turn)

    def test_timelord_dormant_accelerates_on_newest_expansion_cards(self):
        game = self.game(139)
        timelord = self.add_hand(game, "TIME_063")
        self.play(game, timelord)
        self.assertEqual(5, timelord.dormant_turns)
        newest = self.add_hand(game, "TIME_024")
        self.play(game, newest)
        self.assertEqual(4, timelord.dormant_turns)
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        self.assertEqual(3, timelord.dormant_turns)

    def test_stormdrake_kindred_grants_temporary_immune(self):
        game = self.game(149)
        player = game.players[0]
        player.played_races_last_turn = {"DRAGON"}
        stormdrake = self.add_hand(game, "TLC_243")
        self.play(game, stormdrake)
        self.assertTrue(stormdrake.immune)
        game._damage_minion(0, stormdrake, 99)
        self.assertEqual(0, stormdrake.damage)
        game.step(Action("END_TURN"))
        self.assertFalse(stormdrake.immune)

    def test_portal_vanguard_rewind_restores_the_first_draw(self):
        game = self.game(151)
        player = game.players[0]
        player.deck = [
            game._entity("CORE_NEW1_023"),
            game._entity("CORE_LOOT_137"),
        ]
        portal = self.add_hand(game, "TIME_003")
        self.play(game, portal)
        first = game.pending_choice["outcome"]
        first_drawn = next(
            card for card in player.hand if card.entity_id == first["entity"]
        )
        self.assertEqual(2, first_drawn.attack_delta)
        self.assertEqual(2, first_drawn.health_delta)

        game.step(Action("REWIND_RETRY"))
        player = game.players[0]
        drawn = [
            card for card in player.hand
            if card.card_id in {"CORE_NEW1_023", "CORE_LOOT_137"}
        ]
        self.assertEqual(1, len(drawn))
        self.assertEqual((2, 2), (drawn[0].attack_delta, drawn[0].health_delta))
        self.assertEqual(1, len(player.deck))

    def test_conflux_crasher_rewind_does_not_stack_first_roll(self):
        game = self.game(157)
        enemy = game.players[1]
        crasher = self.add_hand(game, "TIME_004")
        self.play(game, crasher)
        self.assertEqual(23, enemy.health)
        game.step(Action("REWIND_RETRY"))
        self.assertEqual(23, game.players[1].health)
        decision = [e for e in game.events if e["kind"] == "rewind_pick"][-1]
        self.assertEqual("conflux_crasher", decision["effect"])

    def test_chrono_daggers_rewind_does_not_stack_damage(self):
        game = self.game(158)
        daggers = self.add_hand(game, "TIME_001")
        self.play(game, daggers)
        self.assertEqual(24, game.players[1].health)
        self.assertEqual(3, len(game.pending_choice["outcome"]))
        game.step(Action("REWIND_RETRY"))
        self.assertEqual(24, game.players[1].health)
        self.assertEqual(3, len(game.events[-1]["outcome"]))

    def test_bygone_doomspeaker_rewind_discards_once_per_player(self):
        game = self.game(159)
        for owner in (0, 1):
            self.add_hand(game, "CORE_NEW1_023", owner)
            self.add_hand(game, "CORE_LOOT_137", owner)
        doomspeaker = self.add_hand(game, "TIME_008")
        self.play(game, doomspeaker)
        self.assertEqual((1, 1), tuple(len(p.hand) for p in game.players))
        game.step(Action("REWIND_RETRY"))
        self.assertEqual((1, 1), tuple(len(p.hand) for p in game.players))
        self.assertEqual("bygone_doomspeaker", game.events[-1]["effect"])

    def test_cease_to_exist_silences_then_destroys(self):
        game = self.game(160)
        target = self.add_board(game, "CORE_GVG_085", 1)
        target.attack_delta = 5
        target.reborn = True
        spell = self.add_hand(game, "TIME_433")
        self.play(game, spell)
        self.assertFalse(game.players[1].board)
        game.step(Action("REWIND_RETRY"))
        self.assertFalse(game.players[1].board)

    def test_aeon_rend_hits_two_distinct_random_enemies(self):
        game = self.game(161)
        self.add_board(game, "CORE_GVG_085", 1)
        self.add_board(game, "CORE_NEW1_023", 1)
        spell = self.add_hand(game, "TIME_441")
        self.play(game, spell)
        outcome = game.pending_choice["outcome"]
        self.assertEqual(2, len(outcome))
        self.assertEqual(2, len({(hit["player"], hit["entity"]) for hit in outcome}))

    def test_shadows_of_yesterday_rewind_replaces_four_shades(self):
        game = self.game(162)
        spell = self.add_hand(game, "TIME_610")
        self.play(game, spell)
        self.assertEqual(4, len(game.players[0].board))
        for result in game.pending_choice["outcome"]:
            self.assertEqual(2, len(set(result["effects"])))
            self.assertTrue(set(result["effects"]) <= set(BONUS_EFFECTS))
        game.step(Action("REWIND_RETRY"))
        self.assertEqual(4, len(game.players[0].board))
        self.assertTrue(all(m.card_id == "TIME_610t2" for m in game.players[0].board))

    def test_basic_stat_auras_stack_and_still_buff_a_silenced_recipient(self):
        game = self.game(164)
        raid_leader = self.add_board(game, "CORE_CS2_122")
        champion = self.add_board(game, "CORE_CS2_222")
        warleader = self.add_board(game, "CORE_EX1_507")
        murloc = self.add_board(game, "DINO_404")
        game._refresh_continuous(game.players[0])
        self.assertEqual((4, 1), (murloc.aura_attack_bonus, murloc.aura_health_bonus))
        murloc.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertEqual((4, 1), (murloc.aura_attack_bonus, murloc.aura_health_bonus))
        raid_leader.silenced = True
        champion.silenced = True
        warleader.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertEqual((0, 0), (murloc.aura_attack_bonus, murloc.aura_health_bonus))

    def test_dire_wolf_aura_tracks_board_adjacency(self):
        game = self.game(165)
        left = self.add_board(game, "CORE_NEW1_023")
        wolf = self.add_board(game, "CORE_EX1_162")
        right = self.add_board(game, "CORE_LOOT_137")
        game._refresh_continuous(game.players[0])
        self.assertEqual((1, 0, 1), tuple(
            minion.aura_attack_bonus for minion in (left, wolf, right)
        ))
        game.players[0].board.remove(left)
        game._refresh_continuous(game.players[0])
        self.assertEqual(1, right.aura_attack_bonus)

    def test_survivalist_immunity_requires_an_empty_friendly_board(self):
        game = self.game(166)
        survivalist = self.add_board(game, "CATA_613")
        game._refresh_continuous(game.players[0])
        self.assertTrue(survivalist.immune)
        other = self.add_board(game, "CORE_NEW1_023")
        game._refresh_continuous(game.players[0])
        self.assertFalse(survivalist.immune)
        other.dormant_turns = 2
        game._refresh_continuous(game.players[0])
        self.assertTrue(survivalist.immune)

    def test_kayn_allows_friendly_attacks_to_ignore_taunt(self):
        game = self.game(168)
        attacker = self.add_board(game, "CORE_NEW1_023")
        kayn = self.add_board(game, "CORE_BT_187")
        taunt = self.add_board(game, "JAIL_384", 1)
        plain = self.add_board(game, "CORE_NEW1_023", 1)
        legal = {action.key() for action in game.legal_actions()}
        self.assertIn(Action("ATTACK", attacker.entity_id, 1, None).key(), legal)
        self.assertIn(Action("ATTACK", attacker.entity_id, 1, plain.entity_id).key(), legal)
        kayn.silenced = True
        legal = {action.key() for action in game.legal_actions()}
        self.assertNotIn(Action("ATTACK", attacker.entity_id, 1, None).key(), legal)
        self.assertIn(Action("ATTACK", attacker.entity_id, 1, taunt.entity_id).key(), legal)

    def test_goldrinn_and_bralma_modify_friendly_tribe_damage(self):
        game = self.game(169)
        beast = self.add_board(game, "JAIL_202")
        self.add_board(game, "EDR_480")
        before = game.players[1].health
        game.step(Action("ATTACK", beast.entity_id, 1, None))
        self.assertEqual(before - 2, game.players[1].health)

        game = self.game(170)
        elemental = self.add_board(game, "FIR_919")
        self.add_board(game, "TLC_228")
        before = game.players[1].health
        game.step(Action("ATTACK", elemental.entity_id, 1, None))
        self.assertEqual(before - elemental.attack - 1, game.players[1].health)

    def test_arachnathid_grants_and_removes_friendly_poisonous(self):
        game = self.game(171)
        friend = self.add_board(game, "JAIL_384")
        aura = self.add_board(game, "JAIL_459")
        target = self.add_board(game, "CORE_LOOT_137", 1)
        game._refresh_continuous(game.players[0])
        self.assertTrue(friend.aura_poisonous)
        game.step(Action("ATTACK", friend.entity_id, 1, target.entity_id))
        self.assertNotIn(target, game.players[1].board)
        aura.silenced = True
        game._refresh_continuous(game.players[0])
        self.assertFalse(friend.aura_poisonous)

    def test_naralex_only_sets_the_first_dragon_each_turn_to_one(self):
        game = self.game(172)
        player = game.players[0]
        self.add_board(game, "EDR_844")
        first = self.add_hand(game, "CORE_LOOT_137")
        second = self.add_hand(game, "CORE_NEW1_023")
        self.assertEqual(1, game._effective_cost(player, first))
        self.play(game, first)
        self.assertEqual(second.cost, game._effective_cost(player, second))

    def test_azure_queen_discounts_arcane_spells_with_another_dragon(self):
        game = self.game(173)
        player = game.players[0]
        queen = self.add_board(game, "TIME_852")
        arcane = game._instance_from_definition(
            CardDef("TEST_ARCANE", "Arcane Test", "SPELL", 5, spell_school="ARCANE")
        )
        self.assertEqual(5, game._effective_cost(player, arcane))
        self.add_board(game, "CORE_NEW1_023")
        self.assertEqual(3, game._effective_cost(player, arcane))
        queen.silenced = True
        self.assertEqual(5, game._effective_cost(player, arcane))

    def test_falric_draws_a_corpse_spender_and_multiplies_corpses(self):
        game = self.game(174)
        player = game.players[0]
        spender = game._entity("TLC_436")
        player.deck = [game._entity("CORE_NEW1_023"), spender]
        falric = self.add_hand(game, "CORE_EDR_003")
        self.play(game, falric)
        self.assertIn(spender, player.hand)

        victim = self.add_board(game, "CORE_NEW1_023")
        victim.damage = victim.max_health
        before = player.corpses
        game._resolve_deaths()
        self.assertEqual(before + 2, player.corpses)

        second = self.add_board(game, "CORE_EDR_003")
        another = self.add_board(game, "CORE_NEW1_023")
        another.damage = another.max_health
        before = player.corpses
        game._resolve_deaths()
        self.assertEqual(before + 4, player.corpses)
        self.assertIn(second, player.board)

    def test_toreth_makes_minion_and_hero_shields_take_three_hits(self):
        game = self.game(175)
        player = game.players[0]
        shielded = self.add_board(game, "CORE_GVG_085")
        self.add_board(game, "EDR_258")
        player.hero_divine_shield = True
        game._refresh_continuous(player)
        self.assertEqual(3, shielded.divine_shield_hits)
        self.assertEqual(3, player.hero_divine_shield_hits)
        for expected in (2, 1):
            game._damage_minion(0, shielded, 99)
            game._damage_hero(player, 99)
            self.assertTrue(shielded.divine_shield)
            self.assertTrue(player.hero_divine_shield)
            self.assertEqual(expected, shielded.divine_shield_hits)
            self.assertEqual(expected, player.hero_divine_shield_hits)
        game._damage_minion(0, shielded, 99)
        game._damage_hero(player, 99)
        self.assertFalse(shielded.divine_shield)
        self.assertFalse(player.hero_divine_shield)
        self.assertEqual(30, player.health)

    def test_ido_spell_stays_available_only_while_ido_is_active(self):
        game = self.game(176)
        player = game.players[0]
        ido = self.add_board(game, "TLC_241")
        target = self.add_board(game, "CORE_NEW1_023")
        game._refresh_continuous(player)
        spell = next(card for card in player.hand if card.card_id == "TLC_241t")
        self.play(game, spell, 0, target.entity_id)
        self.assertEqual((2, 2), (target.attack_delta, target.health_delta))
        self.assertTrue(target.divine_shield)
        self.assertEqual(1, sum(card.card_id == "TLC_241t" for card in player.hand))
        ido.silenced = True
        game._refresh_continuous(player)
        self.assertFalse(any(card.card_id == "TLC_241t" for card in player.hand))

    def test_azshara_summons_herald_scaled_tentacles_and_grants_windfury(self):
        game = self.game(177)
        player = game.players[0]
        player.herald_count = 4
        existing = self.add_board(game, "CORE_NEW1_023")
        azshara = self.add_hand(game, "CATA_151")
        self.play(game, azshara)
        self.assertEqual(
            [existing.card_id, "CATA_151t", "CATA_151", "CATA_151t"],
            [minion.card_id for minion in player.board],
        )
        self.assertEqual(8, player.hero_attack_bonus)
        player.weapon = Weapon("TEST", "Test Weapon", 1, 2)
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertTrue(any(
            action.kind == "HERO_ATTACK" for action in game.legal_actions()
        ))
        azshara.silenced = True
        self.assertFalse(any(
            action.kind == "HERO_ATTACK" for action in game.legal_actions()
        ))

    def test_azshara_only_summons_appendages_that_fit(self):
        game = self.game(178)
        player = game.players[0]
        for _ in range(5):
            self.add_board(game, "CORE_NEW1_023")
        azshara = self.add_hand(game, "CATA_151")
        self.play(game, azshara)
        self.assertEqual(7, len(player.board))
        self.assertEqual(1, sum(m.card_id == "CATA_151t" for m in player.board))

    def test_warmaster_filters_both_decks_and_black_knight_destroys_taunt(self):
        game = self.game(179)
        for owner in game.players:
            owner.deck = [
                game._entity("CORE_NEW1_023"),
                game._entity("CORE_LOOT_137"),
            ]
        warmaster = self.add_hand(game, "CATA_720")
        self.play(game, warmaster)
        self.assertTrue(all(
            [card.card_id for card in owner.deck] == ["CORE_LOOT_137"]
            for owner in game.players
        ))

        taunt = self.add_board(game, "JAIL_384", 1)
        knight = self.add_hand(game, "CORE_EX1_002")
        self.play(game, knight, 1, taunt.entity_id)
        self.assertNotIn(taunt, game.players[1].board)

    def test_thalnos_spell_damage_draw_and_mukla_bananas(self):
        game = self.game(180)
        player = game.players[0]
        thalnos = self.add_board(game, "CORE_EX1_012")
        player.deck = [game._entity("CORE_NEW1_023")]
        self.assertEqual(1, game._spell_damage(player))
        thalnos.damage = thalnos.max_health
        game._resolve_deaths()
        self.assertEqual("CORE_NEW1_023", player.hand[-1].card_id)

        mukla = self.add_hand(game, "CORE_EX1_014")
        self.play(game, mukla)
        bananas = [card for card in game.players[1].hand if card.card_id == "EX1_014t"]
        self.assertEqual(2, len(bananas))
        target = self.add_board(game, "CORE_NEW1_023", 1)
        game.current = 1
        game.players[1].mana = 10
        self.play(game, bananas[0], 1, target.entity_id)
        self.assertEqual((1, 1), (target.attack_delta, target.health_delta))

    def test_cairne_taelan_and_tindral_deathrattles(self):
        game = self.game(181)
        player = game.players[0]
        cairne = self.add_board(game, "CORE_EX1_110")
        cairne.damage = cairne.max_health
        game._resolve_deaths()
        self.assertTrue(any(m.card_id == "EX1_110t" for m in player.board))

        player.deck = [
            game._entity("CORE_NEW1_023"),
            game._entity("CORE_LOOT_137"),
        ]
        taelan = self.add_board(game, "CS3_024")
        taelan.damage = taelan.max_health
        game._resolve_deaths()
        self.assertTrue(any(c.card_id == "CORE_LOOT_137" for c in player.hand))

        game = self.game(182)
        tindral = self.add_board(game, "FIR_958", 0)
        enemy_minion = self.add_board(game, "CORE_LOOT_137", 1)
        game.current = 1
        tindral.damage = tindral.max_health
        game._resolve_deaths()
        self.assertEqual(26, game.players[1].health)
        self.assertEqual(4, enemy_minion.damage)

    def test_runthak_attack_buffs_hand_and_krog_sets_enemy_stats(self):
        game = self.game(183)
        player = game.players[0]
        runthak = self.add_board(game, "CS3_025")
        held_minion = self.add_hand(game, "CORE_NEW1_023")
        self.add_hand(game, "TIME_001")
        game.step(Action("ATTACK", runthak.entity_id, 1, None))
        self.assertEqual((1, 1), (held_minion.attack_delta, held_minion.health_delta))

        krog = self.add_board(game, "TLC_480")
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        game._end_turn()
        self.assertEqual((1, 1), (enemy.attack, enemy.max_health))

    def test_scorching_ravager_heralds_scaling_rush_soldiers(self):
        game = self.game(163)
        player = game.players[0]
        soldiers = []
        for expected_power in (1, 1, 2, 2, 4):
            ravager = self.add_hand(game, "CATA_160")
            self.play(game, ravager)
            soldier = player.board[-1]
            soldiers.append(soldier)
            self.assertEqual("CATA_580t", soldier.card_id)
            self.assertEqual(expected_power, soldier.herald_power)
            self.assertEqual((2 * expected_power, expected_power),
                             (soldier.attack, soldier.max_health))
            self.assertTrue(soldier.rush)
            player.board.clear()
        self.assertEqual(5, player.herald_count)

        enemy = game.players[1]
        enemy.board.clear()
        enemy.health = 30
        soldiers[-1].damage = soldiers[-1].max_health
        player.board.append(soldiers[-1])
        game._resolve_deaths()
        self.assertEqual(22, enemy.health)

    def test_herald_advances_when_board_full_without_summoning(self):
        game = self.game(167)
        player = game.players[0]
        player.board = [game._entity("CORE_NEW1_023") for _ in range(6)]
        ravager = self.add_hand(game, "CATA_160")
        self.play(game, ravager)
        self.assertEqual(7, len(player.board))
        self.assertEqual(1, player.herald_count)
        self.assertFalse(any(m.card_id == "CATA_580t" for m in player.board))

    def test_ultraxion_heralds_and_discounts_every_deathwing(self):
        game = self.game(173)
        player = game.players[0]
        first = game._instance_from_definition(
            CardDef("TEST_DW_1", "Deathwing", "MINION", 10, 12, 12)
        )
        second = game._instance_from_definition(
            CardDef("TEST_DW_2", "Deathwing, Worldbreaker", "MINION", 10, 0, 0)
        )
        player.hand.append(first)
        player.deck.append(second)
        player.herald_count = 1
        ultraxion = self.add_hand(game, "CATA_497")
        self.play(game, ultraxion)
        self.assertEqual(2, player.herald_count)
        self.assertEqual((8, 8), (first.cost, second.cost))
        soldier = next(m for m in player.board if m.card_id == "CATA_580t")
        self.assertEqual(1, soldier.herald_power)

        player.board.clear()
        player.herald_count = 3
        ultraxion = self.add_hand(game, "CATA_497")
        self.play(game, ultraxion)
        self.assertEqual((4, 4), (first.cost, second.cost))
        soldier = next(m for m in player.board if m.card_id == "CATA_580t")
        self.assertEqual(2, soldier.herald_power)

    def test_ravaging_ghoul_damages_every_other_minion(self):
        game = self.game(179)
        friendly = self.add_board(game, "CORE_NEW1_023")
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        ghoul = self.add_hand(game, "CORE_OG_149")
        self.play(game, ghoul)
        self.assertEqual(1, friendly.damage)
        self.assertEqual(1, enemy.damage)
        self.assertEqual(0, ghoul.damage)

    def test_detonation_juggernaut_buffs_taunts_in_hand(self):
        game = self.game(181)
        taunt = self.add_hand(game, "CORE_LOOT_137")
        plain = self.add_hand(game, "CORE_NEW1_023")
        taunt_base = (taunt.attack, taunt.max_health)
        plain_base = (plain.attack, plain.max_health)
        juggernaut = self.add_hand(game, "CORE_WW_329")
        self.play(game, juggernaut)
        self.assertEqual(
            (taunt_base[0] + 2, taunt_base[1] + 2),
            (taunt.attack, taunt.max_health),
        )
        self.assertEqual(plain_base, (plain.attack, plain.max_health))

    def test_eggbasher_damages_and_buffs_a_minion(self):
        game = self.game(191)
        target = self.add_board(game, "CORE_LOOT_137", 1)
        base_attack = target.attack
        eggbasher = self.add_hand(game, "EDR_468")
        self.play(game, eggbasher, 1, target.entity_id)
        self.assertEqual(1, target.damage)
        self.assertEqual(base_attack + 4, target.attack)

    def test_endtime_survivor_checks_hero_damage_this_turn(self):
        game = self.game(193)
        player = game.players[0]
        game._damage_hero(player, 1)
        survivor = self.add_hand(game, "END_019")
        self.play(game, survivor)
        self.assertEqual((8, 9), (survivor.attack, survivor.max_health))

    def test_latorvian_armorer_only_gains_armor_on_lethal(self):
        game = self.game(197)
        player = game.players[0]
        target = self.add_board(game, "CORE_NEW1_023", 1)
        armorer = self.add_hand(game, "TLC_606")
        self.play(game, armorer, 1, target.entity_id)
        self.assertFalse(game.players[1].board)
        self.assertEqual(5, player.armor)

        target = self.add_board(game, "CORE_LOOT_137", 1)
        armorer = self.add_hand(game, "TLC_606")
        self.play(game, armorer, 1, target.entity_id)
        self.assertIn(target, game.players[1].board)
        self.assertEqual(5, player.armor)

    def test_enrage_attack_is_dynamic_and_silence_removes_it(self):
        game = self.game(199)
        grommash = self.add_board(game, "CORE_EX1_414")
        brave = self.add_board(game, "CORE_OG_218", 1)
        self.assertEqual((4, 2), (grommash.attack, brave.attack))
        game._damage_minion(0, grommash, 1)
        game._damage_minion(1, brave, 1)
        self.assertEqual((10, 5), (grommash.attack, brave.attack))
        grommash.silenced = True
        brave.silenced = True
        self.assertEqual((4, 2), (grommash.attack, brave.attack))

    def test_frothing_berserkers_gain_attack_for_every_damage_event(self):
        game = self.game(211)
        first = self.add_board(game, "CORE_EX1_604")
        second = self.add_board(game, "CORE_EX1_604", 1)
        shielded = self.add_board(game, "CATA_476", 1)
        shielded.divine_shield = True
        victim = self.add_board(game, "CORE_LOOT_137", 1)
        game._damage_minion(1, shielded, 1)
        self.assertEqual((2, 2), (first.attack, second.attack))
        game._damage_minion(1, victim, 1)
        self.assertEqual((3, 3), (first.attack, second.attack))

    def test_tortolla_and_rioter_damage_survival_triggers(self):
        game = self.game(223)
        player = game.players[0]
        tortolla = self.add_board(game, "EDR_471")
        rioter = self.add_board(game, "JAIL_029")
        base_attack = tortolla.attack
        game._damage_minion(0, tortolla, 2)
        self.assertEqual(1, player.armor)
        # +1 from Tortolla itself and +1 because it survived beside Rioter.
        self.assertEqual(base_attack + 2, tortolla.attack)

        doomed = game._instance_from_definition(
            CardDef("TEST_1_HP", "One Health", "MINION", 1, 1, 1)
        )
        doomed.summoned_turn = game.turn - 1
        player.board.append(doomed)
        game._damage_minion(0, doomed, 1)
        self.assertEqual(1, doomed.attack)
        game._resolve_deaths()
        self.assertNotIn(doomed, player.board)
        self.assertIn(rioter, player.board)

    def test_stonecarver_buffs_another_damaged_friendly_minion(self):
        game = self.game(227)
        player = game.players[0]
        stonecarver = self.add_board(game, "TLC_623")
        damaged = self.add_board(game, "CORE_LOOT_137")
        untouched = self.add_board(game, "CORE_NEW1_023")
        damaged.damage = 1
        damaged_base = (damaged.attack, damaged.max_health)
        untouched_base = (untouched.attack, untouched.max_health)
        game.step(Action("END_TURN"))
        self.assertEqual(
            (damaged_base[0] + 2, damaged_base[1] + 2),
            (damaged.attack, damaged.max_health),
        )
        self.assertEqual(untouched_base, (untouched.attack, untouched.max_health))
        self.assertIn(stonecarver, player.board)

    def test_blastpowder_engineer_buffs_friendly_pirate_damage(self):
        game = self.game(229)
        engineer = self.add_board(game, "CAP_104")
        pirate = game._instance_from_definition(
            CardDef("TEST_PIRATE", "Test Pirate", "MINION", 1, 2, 2,
                    "PIRATE", (), "WARRIOR", ("PIRATE",))
        )
        pirate.summoned_turn = game.turn - 1
        game.players[0].board.append(pirate)
        enemy_health = game.players[1].health
        game.step(Action("ATTACK", pirate.entity_id, 1, None))
        self.assertEqual(enemy_health - 3, game.players[1].health)
        self.assertIn(engineer, game.players[0].board)

    def test_captain_crowley_summons_cannoneers_and_adds_shots(self):
        game = self.game(233)
        player = game.players[0]
        captain = self.add_hand(game, "CAP_106")
        self.play(game, captain)
        cannoneers = [m for m in player.board if m.card_id == "CAP_107t"]
        self.assertEqual(2, len(cannoneers))
        enemy_health = game.players[1].health
        game.step(Action("END_TURN"))
        self.assertEqual(enemy_health - 4, game.players[1].health)
        self.assertEqual(
            4, sum(event["kind"] == "cannoneer_shot" for event in game.events)
        )

    def test_crowley_adds_shots_when_hand_cannon_triggers_cannoneers(self):
        game = self.game(234)
        player = game.players[0]
        self.add_board(game, "CAP_106")
        self.add_board(game, "CAP_107t")
        self.add_board(game, "CAP_107t")
        player.weapon = Weapon("CAP_103", "Hand Cannon", 3, 2)
        enemy_health = game.players[1].health

        game.step(Action("HERO_ATTACK", None, 1, None))

        self.assertEqual(enemy_health - 7, game.players[1].health)
        shots = [
            event for event in game.events
            if event["kind"] == "cannoneer_shot"
        ]
        self.assertEqual(4, len(shots))
        self.assertTrue(all(event["reason"] == "hero_attack" for event in shots))

    def test_cannoneer_attack_and_end_turn_shot_are_separate_actions(self):
        game = self.game(235)
        cannoneer = self.add_board(game, "CAP_107t")
        enemy_health = game.players[1].health

        attack = Action("ATTACK", cannoneer.entity_id, 1, None)
        self.assertIn(attack, game.legal_actions())
        game.step(attack)
        self.assertEqual(enemy_health - 1, game.players[1].health)
        self.assertEqual(1, cannoneer.attacks_this_turn)
        self.assertFalse(any(
            event["kind"] == "cannoneer_shot" for event in game.events
        ))

        game.step(Action("END_TURN"))
        self.assertEqual(enemy_health - 2, game.players[1].health)
        shots = [
            event for event in game.events
            if event["kind"] == "cannoneer_shot"
        ]
        self.assertEqual(1, len(shots))
        self.assertIsNone(shots[0]["target_entity"])

    def test_random_enemy_pool_includes_stealth_but_targeting_does_not(self):
        game = self.game(237)
        stealth = self.add_board(game, "CORE_EX1_010", 1)
        stealth.stealth = True

        target = (1, stealth.entity_id)
        self.assertIn(target, game._random_enemy_characters(0))
        self.assertNotIn(target, game._enemy_characters(0))

    def test_destructive_blaze_survival_and_deathrattle(self):
        game = self.game(239)
        player = game.players[0]
        blaze = self.add_board(game, "CATA_586")
        game._damage_minion(0, blaze, 1)
        copies = [m for m in player.board if m.card_id == "CATA_586"]
        self.assertEqual(2, len(copies))
        self.assertEqual(0, copies[-1].damage)

        game.players[1].board.clear()
        enemy_health = game.players[1].health
        blaze.damage = blaze.max_health
        game._resolve_deaths()
        self.assertEqual(enemy_health - 2, game.players[1].health)

    def test_envoy_of_the_end_uses_shared_herald_tracker(self):
        game = self.game(241)
        player = game.players[0]
        player.herald_count = 2
        envoy = self.add_hand(game, "CATA_722")
        self.play(game, envoy)
        soldier = next(m for m in player.board if m.card_id == "CATA_580t")
        self.assertEqual(2, soldier.herald_power)
        self.assertFalse(soldier.rush)
        self.assertEqual(3, player.herald_count)

    def test_warmaul_challenger_battles_until_one_dies(self):
        game = self.game(251)
        enemy = self.add_board(game, "CORE_LOOT_137", 1)
        challenger = self.add_hand(game, "CORE_BT_120")
        self.play(game, challenger, 1, enemy.entity_id)
        self.assertNotIn(challenger, game.players[0].board)
        self.assertIn(enemy, game.players[1].board)
        self.assertGreater(enemy.damage, 0)

    def test_hookfist_triggers_after_hero_attack(self):
        game = self.game(257)
        player = game.players[0]
        hookfist = self.add_board(game, "CORE_NX2_028")
        player.deck = [game._entity("CORE_NEW1_023")]
        player.weapon = Weapon("TEST_WEAPON", "Test Weapon", 1, 2)
        hand_before = len(player.hand)
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertEqual(4, player.armor)
        self.assertEqual(hand_before + 1, len(player.hand))
        self.assertIn(hookfist, player.board)

    def test_ragnaros_summons_scaled_hands_and_triggers_deathrattles(self):
        game = self.game(263)
        player = game.players[0]
        player.herald_count = 2
        ragnaros = self.add_hand(game, "CATA_150")
        self.play(game, ragnaros)
        hands = [m for m in player.board if m.card_id == "CATA_150t"]
        self.assertEqual(2, len(hands))
        self.assertTrue(all((m.attack, m.max_health) == (4, 2) for m in hands))
        enemy_health = game.players[1].health
        game.step(Action("END_TURN"))
        self.assertEqual(enemy_health - 8, game.players[1].health)

    def test_barricade_basher_reacts_to_each_armor_gain(self):
        game = self.game(269)
        player = game.players[0]
        basher = self.add_board(game, "DINO_400")
        enemy = self.add_board(game, "CORE_NEW1_023", 1)
        base_stats = (basher.attack, basher.max_health)
        game._gain_armor(player, 2)
        self.assertEqual(2, player.armor)
        self.assertEqual(
            (base_stats[0] + 2, base_stats[1] + 2),
            (basher.attack, basher.max_health),
        )
        self.assertNotIn(enemy, game.players[1].board)

    def test_rampaging_hound_forces_all_enemy_minions_to_attack(self):
        game = self.game(271)
        first = self.add_board(game, "CORE_NEW1_023", 1)
        second = self.add_board(game, "CORE_NEW1_023", 1)
        hound = self.add_hand(game, "JAIL_435")
        self.play(game, hound)
        self.assertNotIn(first, game.players[1].board)
        self.assertNotIn(second, game.players[1].board)
        self.assertIn(hound, game.players[0].board)
        self.assertEqual(6, hound.damage)

    def test_disguised_watchman_can_be_played_on_enemy_side(self):
        game = self.game(277)
        enemy = self.add_board(game, "CORE_NEW1_023", 1)
        watchman = self.add_hand(game, "JAIL_455")
        self.play(game, watchman, 1, None)
        self.assertIn(watchman, game.players[1].board)
        self.assertNotIn(enemy, game.players[1].board)
        self.assertNotIn(watchman, game.players[0].board)

    def test_nablya_copies_damaged_minions_with_rush(self):
        game = self.game(281)
        player = game.players[0]
        damaged = self.add_board(game, "CORE_LOOT_137")
        damaged.attack_delta = 2
        damaged.damage = 3
        untouched = self.add_board(game, "CORE_NEW1_023")
        nablya = self.add_hand(game, "TLC_624")
        self.play(game, nablya)
        copies = [
            m for m in player.board
            if m.created_by == "TLC_624"
        ]
        self.assertEqual(1, len(copies))
        self.assertEqual(damaged.attack, copies[0].attack)
        self.assertEqual(damaged.max_health, copies[0].health)
        self.assertEqual(0, copies[0].damage)
        self.assertTrue(copies[0].rush)
        self.assertIn(untouched, player.board)

    def test_scrappy_defender_attack_tracks_deck_threshold(self):
        game = self.game(283)
        player = game.players[0]
        player.deck = [game._entity("CORE_NEW1_023") for _ in range(25)]
        scrappy = self.add_board(game, "JAIL_311")
        game.legal_actions()
        self.assertEqual(7, scrappy.attack)
        game._draw(player)
        self.assertEqual(2, scrappy.attack)
        scrappy.silenced = True
        player.deck.append(game._entity("CORE_NEW1_023"))
        game._refresh_scrappy(player)
        self.assertEqual(2, scrappy.attack)

    def test_keeper_of_flame_buffs_then_destroys_after_three_future_turns(self):
        game = self.game(293)
        player = game.players[0]
        doomed = self.add_hand(game, "CORE_NEW1_023")
        safe_spell = self.add_hand(game, "FIR_939")
        base_stats = (doomed.attack, doomed.max_health)
        keeper = self.add_hand(game, "FIR_928")
        self.play(game, keeper)
        self.assertEqual(
            (base_stats[0] + 3, base_stats[1] + 3),
            (doomed.attack, doomed.max_health),
        )
        self.assertEqual(3, doomed.burning_turns)
        self.assertEqual(0, safe_spell.burning_turns)

        for _ in range(6):
            game.step(Action("END_TURN"))
        self.assertIn(doomed, player.hand)
        self.assertEqual(1, doomed.burning_turns)
        game.step(Action("END_TURN"))
        self.assertNotIn(doomed, player.hand)

    def test_sky_raider_uses_the_complete_pirate_pool(self):
        game = self.game(307)
        raider = self.add_hand(game, "CORE_DRG_024")
        self.play(game, raider)
        generated = [
            card for card in game.players[0].hand
            if card.created_by == "CORE_DRG_024"
        ]
        self.assertEqual(1, len(generated))
        self.assertIn(generated[0].card_id, PIRATE_IDS)

    def test_bloodsail_raider_and_dread_corsair_use_weapon_attack(self):
        game = self.game(311)
        player = game.players[0]
        game._equip_weapon(player, Weapon("TEST", "Test", 3, 2))
        corsair = self.add_hand(game, "CORE_NEW1_022")
        self.assertEqual(1, game._effective_cost(player, corsair))
        raider = self.add_hand(game, "CORE_NEW1_018")
        self.play(game, raider)
        self.assertEqual(5, raider.attack)

    def test_southsea_captain_aura_updates_and_can_cause_death(self):
        game = self.game(313)
        player = game.players[0]
        pirate = self.add_board(game, "CORE_DRG_024")
        captain = self.add_board(game, "CORE_NEW1_027")
        game._refresh_continuous(player)
        self.assertEqual((2, 3), (pirate.attack, pirate.max_health))
        self.assertEqual((3, 3), (captain.attack, captain.max_health))
        pirate.damage = 2
        captain.damage = captain.max_health
        game._resolve_deaths()
        self.assertNotIn(captain, player.board)
        self.assertNotIn(pirate, player.board)

    def test_small_time_buccaneer_tracks_weapon_presence(self):
        game = self.game(317)
        player = game.players[0]
        buccaneer = self.add_board(game, "CORE_WON_351")
        game._refresh_continuous(player)
        self.assertEqual(1, buccaneer.attack)
        game._equip_weapon(player, Weapon("TEST", "Test", 1, 2))
        self.assertEqual(3, buccaneer.attack)
        game._destroy_weapon(player)
        self.assertEqual(1, buccaneer.attack)

    def test_fogsail_freebooter_has_conditional_battlecry_target(self):
        game = self.game(319)
        enemy = game.players[1]
        freebooter = self.add_hand(game, "CS3_022")
        self.assertIn(Action("PLAY", freebooter.entity_id), game.legal_actions())
        game.players[0].weapon = Weapon("TEST", "Test", 1, 2)
        self.assertNotIn(Action("PLAY", freebooter.entity_id), game.legal_actions())
        self.assertIn(
            Action("PLAY", freebooter.entity_id, 1, None), game.legal_actions()
        )
        self.play(game, freebooter, 1, None)
        self.assertEqual(28, enemy.health)

    def test_time_skipper_triggers_for_each_side_on_every_end_turn(self):
        game = self.game(323)
        self.add_board(game, "TIME_054", 0)
        self.add_board(game, "TIME_054", 1)
        game.step(Action("END_TURN"))
        coins = [card for card in game.players[0].hand if card.card_id == "GAME_005"]
        self.assertEqual(2, len(coins))
        self.assertTrue(all(card.created_by == "TIME_054" for card in coins))

    def test_commander_geddon_replaces_turn_draw_with_deck_choice(self):
        game = self.game(331)
        player = game.players[0]
        geddon = self.add_hand(game, "CATA_591")
        self.play(game, geddon)
        self.assertTrue(player.geddon_draw)

        player.hand.clear()
        player.deck = [
            game._entity("CORE_NEW1_023"),
            game._entity("CORE_DRG_024"),
            game._entity("CORE_NEW1_018"),
            game._entity("CORE_NEW1_022"),
        ]
        game._start_turn(0)
        self.assertEqual("GEDDON_DRAW", game.pending_choice["kind"])
        self.assertEqual(3, len(game.pending_choice["options"]))
        self.assertEqual(1, len(player.deck))
        picked = game.pending_choice["options"][0]
        original_cost = picked.cost
        game.step(Action("DISCOVER_PICK", picked.entity_id))
        self.assertIn(picked, player.hand)
        self.assertEqual(max(0, original_cost - 3), picked.cost)
        self.assertEqual(1, len(player.deck))
        event = next(e for e in reversed(game.events) if e["kind"] == "geddon_pick")
        self.assertEqual(2, len(event["destroyed"]))

    def test_ysondre_death_count_scales_its_deathrattle(self):
        game = self.game(337)
        player = game.players[0]
        first = self.add_board(game, "EDR_465")
        first.damage = first.max_health
        game._resolve_deaths()
        first_wave = [m for m in player.board if m.created_by == "EDR_465"]
        self.assertEqual(1, player.ysondre_deaths)
        self.assertEqual(1, len(first_wave))
        self.assertTrue(first_wave[0].has_race("DRAGON"))

        player.board.clear()
        second = self.add_board(game, "EDR_465")
        second.damage = second.max_health
        game._resolve_deaths()
        second_wave = [m for m in player.board if m.created_by == "EDR_465"]
        self.assertEqual(2, player.ysondre_deaths)
        self.assertEqual(2, len(second_wave))
        self.assertTrue(all(m.card_id in DRAGON_IDS for m in second_wave))

    def test_one_cost_stealth_and_spell_damage(self):
        game = self.game(347)
        infiltrator = self.add_board(game, "CORE_EX1_010", 1)
        zapper = self.add_board(game, "CS3_007", 0)
        self.assertNotIn((1, infiltrator.entity_id), game._enemy_characters(0))
        self.assertEqual(1, game._spell_damage(game.players[0]))

        attacker = self.add_board(game, "CORE_BT_701", 0)
        game.step(Action("ATTACK", attacker.entity_id, 1, None))
        self.assertFalse(attacker.stealth)

    def test_one_cost_hero_auras_and_attack_trigger(self):
        game = self.game(349)
        player = game.players[0]
        spider = self.add_board(game, "JAIL_202")
        battlefiend = self.add_board(game, "CORE_BT_351")
        fletcher = self.add_board(game, "TIME_606")
        game._equip_weapon(player, Weapon("TEST", "Test", 1, 2))
        game._refresh_continuous(player)
        self.assertEqual(2, player.attack)
        self.assertEqual(0, game._hero_power_cost(player))
        game.step(Action("HERO_POWER"))
        self.assertEqual(20, player.mana)
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertEqual(2, battlefiend.attack)
        self.assertIn(spider, player.board)
        self.assertIn(fletcher, player.board)

    def test_one_cost_end_turn_and_played_deathrattle_triggers(self):
        game = self.game(353)
        player = game.players[0]
        mosquito = self.add_board(game, "EDR_816")
        caretaker = self.add_board(game, "EDR_971")
        overseer = self.add_board(game, "JAIL_880")
        player.health = 20
        game.players[1].health = 21
        dryad = self.add_hand(game, "EDR_485")
        self.play(game, dryad)
        self.assertTrue(dryad.rush)
        game.step(Action("END_TURN"))
        self.assertEqual(3, caretaker.attack)
        self.assertEqual(2, overseer.attack)
        self.assertEqual((23, 24), (player.health, game.players[1].health))
        self.assertIn(mosquito, player.board)

    def test_one_cost_simple_deathrattles(self):
        game = self.game(359)
        player = game.players[0]
        opponent = game.players[1]
        opponent.deck = [game._entity("CORE_NEW1_023") for _ in range(2)]
        operator = self.add_board(game, "CAP_004")
        operator.damage = operator.max_health
        game._resolve_deaths()
        self.assertEqual(2, len(opponent.hand))

        recipient = self.add_board(game, "CORE_NEW1_023")
        servant = self.add_board(game, "CORE_YOD_026")
        servant.damage = servant.max_health
        game._resolve_deaths()
        self.assertEqual(5, recipient.attack)

        player.deck = [game._entity("EDR_465")]
        dryad = self.add_board(game, "EDR_485")
        dryad.damage = dryad.max_health
        game._resolve_deaths()
        self.assertTrue(any(card.card_id == "EDR_465" for card in player.hand))

        before = opponent.health + sum(m.health for m in opponent.board)
        cinder = self.add_board(game, "TLC_249")
        cinder.damage = cinder.max_health
        game._resolve_deaths()
        after = opponent.health + sum(m.health for m in opponent.board)
        self.assertEqual(2, before - after)

    def test_one_cost_contextual_support_has_expected_size(self):
        self.assertEqual(60, len(SUPPORTED_ONE_COST_SUMMON_IDS))

    def test_crystalspine_cub_triggers_when_last_mana_is_spent(self):
        game = self.game(367)
        player = game.players[0]
        cub = self.add_board(game, "CATA_130")
        player.mana = 1
        card = self.add_hand(game, "CORE_DRG_024")
        self.play(game, card)
        self.assertEqual((2, 2), (cub.attack, cub.max_health))

    def test_twilight_egg_upgrades_only_its_whelp(self):
        game = self.game(373)
        egg = self.add_board(game, "CATA_210")
        game._start_turn(0)
        self.assertEqual((0, 2), (egg.attack, egg.max_health))
        self.assertEqual(1, egg.twilight_whelp_bonus)
        egg.damage = egg.max_health
        game._resolve_deaths()
        whelp = next(m for m in game.players[0].board if m.card_id == "CATA_210t")
        self.assertEqual((3, 2), (whelp.attack, whelp.max_health))

    def test_violet_spellwing_adds_playable_arcane_missiles(self):
        game = self.game(379)
        spellwing = self.add_board(game, "CORE_DRG_107")
        spellwing.damage = spellwing.max_health
        game._resolve_deaths()
        missiles = next(c for c in game.players[0].hand if c.card_id == "CORE_EX1_277")
        self.play(game, missiles)
        self.assertEqual(27, game.players[1].health)

    def test_squirrel_and_blight_cast_when_drawn(self):
        game = self.game(383)
        player = game.players[0]
        squirrel = self.add_board(game, "CORE_SW_439")
        squirrel.damage = squirrel.max_health
        game._resolve_deaths()
        acorn = next(c for c in player.deck if c.card_id == "CORE_SW_439t")
        normal = game._entity("CORE_DRG_024")
        player.deck = [normal, acorn]
        game._draw(player)
        self.assertTrue(any(m.card_id == "CORE_SW_439t" for m in player.board))
        self.assertIn(normal, player.hand)

        doctor = self.add_board(game, "JAIL_442")
        doctor.damage = doctor.max_health
        game._resolve_deaths()
        blight = next(c for c in player.deck if c.card_id == "JAIL_442t")
        replacement = game._entity("CORE_DRG_024")
        player.deck = [replacement, blight]
        health = player.health
        game._draw(player)
        self.assertEqual(health - 2, player.health)
        self.assertIn(replacement, player.hand)

    def test_condition_dormant_one_drops_awaken(self):
        game = self.game(389)
        player = game.players[0]
        sprite = self.add_board(game, "EDR_469")
        self.assertGreater(sprite.dormant_turns, 0)
        game.step(Action("HERO_POWER"))
        self.assertEqual(0, sprite.dormant_turns)

        player.board.clear()
        worm = self.add_board(game, "MEND_040")
        for _ in range(6):
            self.add_board(game, "CORE_DRG_024")
        game._refresh_continuous(player)
        self.assertEqual(0, worm.dormant_turns)

    def test_one_cost_tribe_triggers_use_play_and_summon_semantics(self):
        game = self.game(397)
        tidecaller = self.add_board(game, "CORE_EX1_509")
        murmy = self.add_hand(game, "CORE_ULD_723")
        self.play(game, murmy)
        self.assertEqual(2, tidecaller.attack)

        vapor = self.add_board(game, "CORE_WC_042")
        elemental = self.add_hand(game, "CORE_UNG_809")
        self.play(game, elemental)
        self.assertEqual(2, vapor.attack)

    def test_glade_ecologist_generates_and_casts_purifying_vines(self):
        game = self.game(401)
        friendly = self.add_board(game, "CORE_DRG_024", 0)
        enemy = self.add_board(game, "CORE_DRG_024", 1)
        ecologist = self.add_board(game, "TLC_820", 0)
        ecologist.damage = ecologist.max_health
        game._resolve_deaths()
        vines = next(c for c in game.players[0].hand if c.card_id == "TLC_813")

        game.step(Action("PLAY", vines.entity_id, 0, friendly.entity_id))
        self.assertEqual(4, friendly.max_health)

        second = game._entity("TLC_820")
        game._summon(game.players[0], second)
        second.damage = second.max_health
        game._resolve_deaths()
        vines = next(c for c in game.players[0].hand if c.card_id == "TLC_813")
        game.step(Action("PLAY", vines.entity_id, 1, enemy.entity_id))
        self.assertNotIn(enemy, game.players[1].board)

    def test_dreambound_raptor_grants_distinct_bonus_effects_after_play(self):
        game = self.game(409)
        first = self.add_board(game, "EDR_849", 0)
        second = self.add_board(game, "EDR_849", 0)
        played = self.add_hand(game, "CORE_DRG_024", 0)
        self.play(game, played)

        granted = {
            effect for effect in (
                "divine_shield", "elusive", "lifesteal", "poisonous",
                "reborn", "rush", "taunt", "windfury",
            )
            if getattr(played, effect)
        }
        self.assertEqual(2, len(granted))
        self.assertFalse(any(getattr(first, effect) for effect in granted))
        self.assertFalse(any(getattr(second, effect) for effect in granted))
        events = [e for e in game.events if e["kind"] == "bonus_effect"]
        self.assertEqual(2, len(events))

    def test_stardust_scythe_generates_first_three_void_soul_tiers(self):
        game = self.game(419)
        player = game.players[0]
        player.weapon = Weapon("JAIL_730", "Stardust Scythe", 3, 3)

        expected_costs = (1, 2, 3)
        for expected_cost in expected_costs:
            player.hero_attacks_this_turn = 0
            game.step(Action("HERO_ATTACK", None, 1, None))
            soul = next(c for c in player.hand if c.card_id == "JAIL_732")
            self.assertEqual(expected_cost, soul.void_soul_cost)
            game.step(Action("PLAY", soul.entity_id))
            summoned = [
                minion for minion in player.board
                if minion.created_by == "JAIL_732"
            ][-1]
            self.assertEqual(expected_cost, summoned.cost)

        self.assertEqual(4, player.void_soul_level)
        self.assertIsNone(player.weapon)

    def test_imp_gang_stooge_puts_two_grandmother_imps_on_deck_bottom(self):
        game = self.game(421)
        player = game.players[0]
        existing_bottom = player.deck[0]
        stooge = self.add_board(game, "JAIL_399", 0)
        stooge.damage = stooge.max_health
        game._resolve_deaths()

        bottom = player.deck[:2]
        self.assertTrue(all(card.card_id == "JAIL_399t1" for card in bottom))
        self.assertTrue(all(card.taunt and card.lifesteal for card in bottom))
        self.assertIs(existing_bottom, player.deck[2])

    def test_void_soul_four_and_five_cost_tiers_are_playable(self):
        game = self.game(423)
        player = game.players[0]
        for tier in (4, 5):
            player.void_soul_level = tier
            game._after_hero_attack(
                player, Weapon("JAIL_730", "Stardust Scythe", 3, 3),
                (1, None), 3,
            )
            soul = next(c for c in player.hand if c.card_id == "JAIL_732")
            game.step(Action("PLAY", soul.entity_id))
            summoned = [
                minion for minion in player.board
                if minion.created_by == "JAIL_732"
            ][-1]
            self.assertEqual(tier, summoned.cost)

    def test_eredar_deceptor_summons_a_rush_demon_after_draw(self):
        game = self.game(427)
        player = game.players[0]
        deceptor = self.add_board(game, "CORE_TTN_843", 0)
        drawn = game._entity("CORE_DRG_024")
        player.deck = [drawn]
        game._draw(player)
        token = next(m for m in player.board if m.created_by == deceptor.card_id)
        self.assertEqual((1, 1), (token.attack, token.max_health))
        self.assertTrue(token.rush)

    def test_wrathspike_brute_retaliates_only_if_it_survives_attack(self):
        game = self.game(431)
        player = game.players[0]
        enemy = game.players[1]
        attacker = self.add_board(game, "CORE_DRG_024", 0)
        attacker.summoned_turn = game.turn - 1
        brute = self.add_board(game, "CORE_BT_510", 1)
        bystander = self.add_board(game, "CORE_DRG_024", 0)
        health = player.health
        game.step(Action("ATTACK", attacker.entity_id, 1, brute.entity_id))
        self.assertEqual(health - 1, player.health)
        self.assertEqual(1, bystander.damage)

        lethal = self.add_board(game, "CORE_EX1_414", 0)
        lethal.attack_delta += 20
        lethal.summoned_turn = game.turn - 1
        enemy_brute = self.add_board(game, "CORE_BT_510", 1)
        health = player.health
        game.step(Action("ATTACK", lethal.entity_id, 1, enemy_brute.entity_id))
        self.assertEqual(health, player.health)

    def test_ravenous_felhunter_resurrects_two_low_cost_deathrattles(self):
        game = self.game(433)
        player = game.players[0]
        spellwing = self.add_board(game, "CORE_DRG_107", 0)
        spellwing.damage = spellwing.max_health
        game._resolve_deaths()
        felhunter = self.add_board(game, "EDR_891", 0)
        felhunter.damage = felhunter.max_health
        game._resolve_deaths()
        restored = [m for m in player.board if m.created_by == "EDR_891"]
        self.assertEqual(2, len(restored))
        self.assertTrue(all(m.card_id == "CORE_DRG_107" for m in restored))

    def test_void_soul_six_and_seven_cost_tiers_are_playable(self):
        game = self.game(439)
        player = game.players[0]
        for tier in (6, 7):
            player.void_soul_level = tier
            game._after_hero_attack(
                player, Weapon("JAIL_730", "Stardust Scythe", 3, 3),
                (1, None), 3,
            )
            soul = next(c for c in player.hand if c.card_id == "JAIL_732")
            game.step(Action("PLAY", soul.entity_id))
            summoned = [
                minion for minion in player.board
                if minion.created_by == "JAIL_732"
            ][-1]
            self.assertEqual(tier, summoned.cost)

    def test_six_cost_demon_deathrattles_damage_correct_sides(self):
        game = self.game(443)
        friendly = self.add_board(game, "CORE_DRG_024", 0)
        enemy = self.add_board(game, "CORE_DRG_024", 1)
        sewer_imp = self.add_board(game, "JAIL_007", 0)
        sewer_imp.damage = sewer_imp.max_health
        game._resolve_deaths()
        self.assertEqual(28, game.players[1].health)
        self.assertNotIn(enemy, game.players[1].board)
        self.assertEqual(0, friendly.damage)

        impfernal = self.add_board(game, "JAIL_398", 0)
        impfernal.damage = impfernal.max_health
        game._resolve_deaths()
        self.assertEqual((27, 25), (game.players[0].health, game.players[1].health))
        self.assertNotIn(friendly, game.players[0].board)

    def test_seven_cost_demon_end_turn_triggers(self):
        game = self.game(449)
        priestess = self.add_board(game, "CORE_BT_493", 0)
        game.step(Action("END_TURN"))
        self.assertEqual(24, game.players[1].health)
        self.assertIn(priestess, game.players[0].board)

        game = self.game(451)
        terror = self.add_board(game, "CORE_TTN_866", 0)
        enemy = self.add_board(game, "CORE_DRG_024", 1)
        game.step(Action("END_TURN"))
        self.assertNotIn(enemy, game.players[1].board)
        self.assertIn(terror, game.players[0].board)

    def test_ferocious_felbat_resurrects_two_high_cost_deathrattles(self):
        game = self.game(457)
        player = game.players[0]
        sewer_imp = self.add_board(game, "JAIL_007", 0)
        sewer_imp.damage = sewer_imp.max_health
        game._resolve_deaths()
        felbat = self.add_board(game, "EDR_892", 0)
        felbat.damage = felbat.max_health
        game._resolve_deaths()
        restored = [m for m in player.board if m.created_by == "EDR_892"]
        self.assertEqual(2, len(restored))
        self.assertTrue(all(m.card_id == "JAIL_007" for m in restored))

    def test_void_soul_eight_through_ten_cost_tiers_are_playable_and_cap(self):
        game = self.game(461)
        player = game.players[0]
        for tier in (8, 9, 10):
            player.void_soul_level = tier
            game._after_hero_attack(
                player, Weapon("JAIL_730", "Stardust Scythe", 3, 3),
                (1, None), 3,
            )
            soul = next(c for c in player.hand if c.card_id == "JAIL_732")
            game.step(Action("PLAY", soul.entity_id))
            summoned = [
                minion for minion in player.board
                if minion.created_by == "JAIL_732"
            ][-1]
            self.assertEqual(tier, summoned.cost)
        self.assertEqual(10, player.void_soul_level)

    def test_eight_cost_demon_rules(self):
        game = self.game(463)
        player = game.players[0]
        forgefiend = self.add_board(game, "CORE_SW_068", 0)
        forgefiend.damage = forgefiend.max_health
        game._resolve_deaths()
        self.assertEqual(8, player.armor)

        asphyxiodon = self.add_board(game, "DINO_132", 0)
        victim = self.add_board(game, "CORE_DRG_024", 1)
        game.step(Action("END_TURN"))
        self.assertNotIn(victim, game.players[1].board)
        self.assertIn(asphyxiodon, player.board)

    def test_illidari_inquisitor_follows_hero_attack(self):
        game = self.game(467)
        player = game.players[0]
        inquisitor = self.add_board(game, "CS3_020", 0)
        player.weapon = Weapon("TEST", "Test", 1, 2)
        before = game.players[1].health
        game.step(Action("HERO_ATTACK", None, 1, None))
        self.assertEqual(before - 1 - inquisitor.attack, game.players[1].health)
        self.assertEqual(1, inquisitor.attacks_this_turn)

    def test_tichondrius_immunity_and_nathrezim_cost_aura(self):
        game = self.game(479)
        player = game.players[0]
        tichondrius = self.add_board(game, "CORE_CATA_001", 0)
        game._damage_hero(player, 20)
        self.assertEqual(30, player.health)
        tichondrius.silenced = True
        game._damage_hero(player, 2)
        self.assertEqual(28, player.health)

        nathrezim = self.add_board(game, "JAIL_890", 0)
        held = self.add_hand(game, "CORE_DRG_024", 1)
        self.assertEqual(3, game._effective_cost(game.players[1], held))
        nathrezim.silenced = True
        self.assertEqual(1, game._effective_cost(game.players[1], held))

    def test_voidlord_omen_and_moragg_deathrattles(self):
        game = self.game(487)
        player = game.players[0]
        voidlord = self.add_board(game, "CORE_LOOT_368", 0)
        voidlord.damage = voidlord.max_health
        game._resolve_deaths()
        walkers = [m for m in player.board if m.created_by == "CORE_LOOT_368"]
        self.assertEqual(3, len(walkers))
        self.assertTrue(all(m.taunt for m in walkers))

        player.board.clear()
        omen = self.add_board(game, "EDR_421", 0)
        omen.summoned_turn = game.turn - 1
        game.step(Action("ATTACK", omen.entity_id, 1, None))
        self.assertEqual(2, omen.omen_damage)
        omen.damage = omen.max_health
        before = game.players[1].health
        game._resolve_deaths()
        self.assertEqual(before - 2, game.players[1].health)

        player.board.clear()
        player.deck = [game._entity("EDR_456")]
        moragg = self.add_board(game, "JAIL_906", 0)
        moragg.damage = moragg.max_health
        game._resolve_deaths()
        demon = next(m for m in player.board if m.card_id == "EDR_456")
        self.assertTrue(demon.summon_moragg_on_death)
        demon.damage = demon.max_health
        game._resolve_deaths()
        self.assertTrue(any(m.card_id == "JAIL_906" for m in player.board))

    def test_declarative_deathrattle_preserves_moragg_return_marker(self):
        game = self.game(488)
        player = game.players[0]
        forgefiend = self.add_board(game, "CORE_SW_068", 0)
        forgefiend.summon_moragg_on_death = True
        forgefiend.damage = forgefiend.max_health
        game._resolve_deaths()
        self.assertEqual(8, player.armor)
        returned = [
            minion for minion in player.board
            if minion.card_id == "JAIL_906"
            and minion.created_by == "CORE_SW_068"
        ]
        self.assertEqual(1, len(returned))

    def test_hook_carrier_and_cannonmaster_generation(self):
        game = self.game()
        initial_entities = {card.entity_id for card in game.players[0].hand}
        carrier = self.add_hand(game, "CATA_556")
        initial_entities.add(carrier.entity_id)
        self.play(game, carrier)
        generated_dragons = [
            card for card in game.players[0].hand
            if card.entity_id not in initial_entities
        ]
        self.assertEqual(1, len(generated_dragons))
        self.assertIn(generated_dragons[0].card_id, LOW_COST_DRAGON_IDS)
        self.assertLessEqual(generated_dragons[0].definition.cost, 3)
        self.assertEqual("CATA_556", generated_dragons[0].created_by)
        hook = self.add_hand(game, "CAP_105")
        self.play(game, hook)
        self.assertEqual({"DISCOVER_PICK"}, {choice.kind for choice in game.legal_actions()})
        offered = {option.card_id for option in game.pending_choice["options"]}
        self.assertTrue(offered.issubset(PIRATE_IDS))
        self.assertEqual(min(3, len(PIRATE_IDS)), len(offered))
        first_choice = game.legal_actions()[0]
        selected_pirate = next(
            option.card_id for option in game.pending_choice["options"]
            if option.entity_id == first_choice.source
        )
        self.assertEqual(0, sum(m.card_id == "CAP_107t" for m in game.players[0].board))
        game.step(first_choice)
        self.assertEqual(2, sum(m.card_id == "CAP_107t" for m in game.players[0].board))
        self.assertTrue(any(c.card_id == selected_pirate for c in game.players[0].hand))

    def test_tiny_pal_frost_ammunition_freezes_two_other_enemies(self):
        game = self.game()
        player, enemy = game.players
        player.weapon = Weapon(
            "JAIL_458", "Tiny Pal", 2, 3, ammunition=1
        )
        enemy.weapon = Weapon("TEST", "Test Weapon", 1, 2)
        attacked = game._instance_from_definition(
            CardDef("TEST_TARGET", "Target", "MINION", 1, 0, 5)
        )
        other = game._instance_from_definition(
            CardDef("TEST_OTHER", "Other", "MINION", 1, 1, 5)
        )
        attacked.summoned_turn = other.summoned_turn = game.turn - 1
        enemy.board.extend([attacked, other])

        game.step(Action("HERO_ATTACK", None, 1, attacked.entity_id))

        self.assertGreaterEqual(enemy.frozen_turn, 0)
        self.assertGreaterEqual(other.frozen_turn, 0)
        self.assertLess(attacked.frozen_turn, 0)
        self.assertEqual("AMMUNITION", game.pending_choice["kind"])
        self.assertEqual([2, 3, 4], game.pending_choice["options"])
        game.step(Action("AMMUNITION_PICK", 2))
        self.assertEqual(2, player.weapon.ammunition)
        game.step(Action("END_TURN"))
        kinds = {action.kind for action in game.legal_actions()}
        self.assertNotIn("HERO_ATTACK", kinds)
        self.assertFalse(any(
            action.kind == "ATTACK" and action.source == other.entity_id
            for action in game.legal_actions()
        ))
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        self.assertLess(enemy.frozen_turn, 0)
        self.assertLess(other.frozen_turn, 0)

    def test_tiny_pal_fire_ammunition_damages_all_enemies(self):
        game = self.game()
        player, enemy = game.players
        player.weapon = Weapon(
            "JAIL_458", "Tiny Pal", 2, 3, ammunition=2
        )
        survivor = game._instance_from_definition(
            CardDef("TEST_SURVIVOR", "Survivor", "MINION", 1, 1, 2)
        )
        casualty = game._instance_from_definition(
            CardDef("TEST_CASUALTY", "Casualty", "MINION", 1, 1, 1)
        )
        enemy.board.extend([survivor, casualty])

        game.step(Action("HERO_ATTACK", None, 1, None))

        self.assertEqual(27, enemy.health)
        self.assertEqual(1, survivor.health)
        self.assertNotIn(casualty, enemy.board)
        self.assertEqual([1, 3, 4], game.pending_choice["options"])
        self.assertEqual(
            [Action("AMMUNITION_PICK", 1), Action("AMMUNITION_PICK", 3),
             Action("AMMUNITION_PICK", 4)],
            game.legal_actions(),
        )

    def test_first_tortotem_dependency_tranche_loads_special_states(self):
        game = self.game()
        self.assertGreaterEqual(len(ADDITIONAL_GENERATED_MINION_IDS), 6)
        self.assertTrue(ADDITIONAL_GENERATED_MINION_IDS <= set(game.card_defs))
        patriarch = game._entity("TIME_046")
        specter = game._entity("JAIL_942")
        self.assertEqual(3, patriarch.dormant_turns)
        self.assertTrue(patriarch.taunt)
        self.assertTrue(specter.taunt)
        self.assertTrue(specter.cant_attack)
        specter.summoned_turn = game.turn - 1
        game.players[0].board.append(specter)
        self.assertFalse(any(
            action.kind == "ATTACK" and action.source == specter.entity_id
            for action in game.legal_actions()
        ))

    def test_chillfallen_baron_draws_on_battlecry_and_deathrattle(self):
        game = self.game()
        player = game.players[0]
        player.deck = [game._entity("TIME_053"), game._entity("DINO_404")]
        baron = game._entity("RLK_708")
        player.hand.append(baron)

        game.step(Action("PLAY", baron.entity_id))
        self.assertEqual(1, len(player.deck))
        baron.damage = baron.max_health
        game._resolve_deaths()
        self.assertEqual(0, len(player.deck))

    def test_cinderfin_deathrattle_and_firegill_kindred(self):
        game = self.game()
        player = game.players[0]
        cinderfin = game._entity("TLC_225")
        cinderfin.summoned_turn = game.turn - 1
        player.board.append(cinderfin)
        cinderfin.damage = cinderfin.max_health
        game._resolve_deaths()
        token = next(m for m in player.board if m.card_id == "TLC_249")
        self.assertEqual("TLC_225", token.created_by)

        recipient = game._instance_from_definition(
            CardDef("TEST_RECIPIENT", "Recipient", "MINION", 1, 1, 1)
        )
        recipient.summoned_turn = game.turn
        player.board.append(recipient)
        player.played_races_last_turn = {"ELEMENTAL"}
        firegill = game._entity("DINO_404")
        player.hand.append(firegill)
        game.step(Action("PLAY", firegill.entity_id))
        self.assertTrue(recipient.rush)

    def test_sinful_steed_reborn_keeps_enchantments_and_full_health(self):
        game = self.game()
        steed = game._entity("CAP_800")
        steed.attack_delta = 2
        steed.health_delta = 3
        steed.summoned_turn = game.turn - 1
        game.players[0].board.append(steed)
        steed.damage = steed.max_health

        game._resolve_deaths()

        reborn = next(m for m in game.players[0].board if m.card_id == "CAP_800")
        self.assertEqual(steed.attack, reborn.attack)
        self.assertEqual(reborn.max_health, reborn.health)
        self.assertFalse(reborn.reborn)

    def test_chromatic_broodmother_refreshes_mana_after_attack(self):
        game = self.game()
        player = game.players[0]
        broodmother = game._entity("CATA_469")
        broodmother.summoned_turn = game.turn - 1
        player.board.append(broodmother)
        player.mana = 0
        player.max_mana = 10

        game.step(Action("ATTACK", broodmother.entity_id, 1, None))

        self.assertEqual(broodmother.attack, player.mana)

    def test_porcupine_and_bonechill_deathrattle_damage(self):
        game = self.game()
        enemy = game.players[1]
        enemy.board.extend([
            game._instance_from_definition(
                CardDef("TEST_A", "A", "MINION", 1, 0, 20)
            ),
            game._instance_from_definition(
                CardDef("TEST_B", "B", "MINION", 1, 0, 20)
            ),
        ])
        porcupine = game._entity("CORE_BT_201")
        game.players[0].board.append(porcupine)
        before = enemy.health + sum(m.health for m in enemy.board)
        porcupine.damage = porcupine.max_health
        game._resolve_deaths()
        after = enemy.health + sum(m.health for m in enemy.board)
        self.assertEqual(porcupine.attack, before - after)

        bonechill = game._entity("TLC_401")
        game.players[0].board.append(bonechill)
        before = enemy.health + sum(m.health for m in enemy.board)
        bonechill.damage = bonechill.max_health
        game._resolve_deaths()
        after = enemy.health + sum(m.health for m in enemy.board)
        self.assertEqual(18, before - after)

    def test_chillspine_freezes_on_kindred_and_magma_grows_on_fire_spell(self):
        game = self.game()
        player, enemy = game.players
        targets = [
            game._instance_from_definition(
                CardDef(f"TEST_{i}", f"Target {i}", "MINION", 1, 1, 5)
            )
            for i in range(3)
        ]
        enemy.board.extend(targets)
        player.played_races_last_turn = {"BEAST"}
        chillspine = game._entity("DINO_413")
        player.hand.append(chillspine)
        game.step(Action("PLAY", chillspine.entity_id))
        frozen = [m for m in targets if m.frozen_turn >= 0]
        self.assertEqual(2, len(frozen))
        self.assertTrue(all(m.health == 3 for m in frozen))

        magma = game._entity("TLC_224")
        magma.summoned_turn = game.turn - 1
        player.board.append(magma)
        spell = game._entity("CATA_582")
        player.hand.append(spell)
        before = (magma.attack, magma.max_health)
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(
            (before[0] + spell.cost, before[1] + spell.cost),
            (magma.attack, magma.max_health),
        )

    def test_techysaurus_and_everburning_phoenix_cost_trackers(self):
        game = self.game()
        player = game.players[0]
        player.generated_cards_played = 3
        player.cards_played_this_turn = 2
        techysaurus = game._entity("DINO_409")
        phoenix = game._entity("FIR_919")
        self.assertEqual(4, game._effective_cost(player, techysaurus))
        self.assertEqual(2, game._effective_cost(player, phoenix))

        phoenix.summoned_turn = game.turn - 1
        player.board.append(phoenix)
        phoenix.damage = phoenix.max_health
        game._resolve_deaths()
        self.assertEqual(1, player.pending_phoenixes)
        game.step(Action("END_TURN"))
        returned = next(card for card in player.hand if card.card_id == "FIR_919")
        self.assertEqual("FIR_919", returned.created_by)
        self.assertEqual(0, player.pending_phoenixes)

    def test_magma_hound_only_triggers_after_surviving_minion_attack(self):
        game = self.game()
        player, enemy = game.players
        hound = game._entity("FIR_953")
        hound.summoned_turn = game.turn - 1
        player.board.append(hound)
        defender = game._instance_from_definition(
            CardDef("TEST_DEFENDER", "Defender", "MINION", 1, 0, 10)
        )
        enemy.board.append(defender)
        before = enemy.health + defender.health
        game.step(Action("ATTACK", hound.entity_id, 1, defender.entity_id))
        after = enemy.health + max(0, defender.health)
        self.assertEqual(hound.attack * 2, before - after)

    def test_tyrannogill_summons_three_individually_gifted_murlocs(self):
        game = self.game()
        tyrannogill = game._entity("TLC_240")
        game.players[0].board.append(tyrannogill)
        tyrannogill.damage = tyrannogill.max_health
        game._resolve_deaths()
        spawns = [m for m in game.players[0].board if m.created_by == "TLC_240"]
        self.assertEqual(3, len(spawns))
        self.assertTrue(all(m.has_race("MURLOC") for m in spawns))
        self.assertTrue(all(any(getattr(m, effect) for effect in (
            "divine_shield", "elusive", "lifesteal", "poisonous", "reborn",
            "rush", "taunt", "windfury",
        )) for m in spawns))

    def test_dread_raptor_kindred_draws_and_zeroes_low_cost_deathrattle(self):
        game = self.game()
        player = game.players[0]
        player.played_races_last_turn = {"BEAST"}
        player.deck = [game._entity("TLC_249")]
        raptor = game._entity("TLC_432")
        player.hand.append(raptor)
        game.step(Action("PLAY", raptor.entity_id))
        drawn = next(card for card in player.hand if card.card_id == "TLC_249")
        self.assertEqual(0, game._effective_cost(player, drawn))

    def test_slagclaw_kindred_triggers_all_cinder_deathrattles(self):
        game = self.game()
        player, enemy = game.players
        existing = game._entity("TLC_249")
        existing.summoned_turn = game.turn - 1
        player.board.append(existing)
        player.played_races_last_turn = {"DRAGON"}
        slagclaw = game._entity("TLC_482")
        player.hand.append(slagclaw)
        before = enemy.health
        game.step(Action("PLAY", slagclaw.entity_id))
        self.assertEqual(3, sum(m.card_id == "TLC_249" for m in player.board))
        self.assertEqual(before - 6, enemy.health)

    def test_fire_plume_phoenix_has_explicit_battlecry_target(self):
        game = self.game()
        phoenix = game._entity("CORE_UNG_084")
        game.players[0].hand.append(phoenix)
        self.assertIn(
            Action("PLAY", phoenix.entity_id, 1, None), game.legal_actions()
        )
        game.step(Action("PLAY", phoenix.entity_id, 1, None))
        self.assertEqual(27, game.players[1].health)

    def test_windpeak_wyrm_battlecry_and_coin_spell_rules(self):
        game = self.game()
        player = game.players[0]
        player.mana = 20
        wyrm = game._entity("TLC_600")
        player.hand.append(wyrm)
        game.step(Action("PLAY", wyrm.entity_id, 1, None))
        self.assertEqual(25, game.players[1].health)
        self.assertEqual(5, player.armor)

        coin = game._instance_from_definition(
            CardDef("GAME_005", "The Coin", "SPELL", 0)
        )
        player.hand.append(coin)
        before = player.mana
        game.step(Action("PLAY", coin.entity_id))
        self.assertEqual(before + 1, player.mana)

    def test_mirrex_tracks_last_opponent_minion_as_three_four_copy(self):
        game = self.game()
        tracker = game._entity("DINO_407")
        game.players[1].hand.append(tracker)
        played = game._entity("CATA_556")
        game.players[0].hand.append(played)
        game.step(Action("PLAY", played.entity_id))
        self.assertTrue(tracker.mirrex_tracker)
        self.assertEqual("CATA_556", tracker.card_id)
        self.assertEqual((3, 4), (tracker.attack, tracker.max_health))

    def test_hooktail_chest_fills_original_players_hand_with_coins(self):
        game = self.game()
        hooktail = game._entity("TIME_713")
        game.players[0].hand.append(hooktail)
        game.step(Action("PLAY", hooktail.entity_id))
        chest = next(m for m in game.players[1].board if m.card_id == "TIME_713t")
        self.assertEqual(8, chest.health)
        chest.damage = chest.max_health
        game._resolve_deaths()
        self.assertEqual(10, len(game.players[0].hand))
        self.assertTrue(all(c.card_id == "GAME_005" for c in game.players[0].hand))

    def test_torga_draws_kindred_and_matching_activator(self):
        game = self.game()
        player = game.players[0]
        player.deck = [
            game._entity("TIME_053"),
            game._entity("CATA_556"),
            game._entity("TLC_600"),
        ]
        torga = game._entity("TLC_102")
        player.hand.append(torga)
        game.step(Action("PLAY", torga.entity_id))
        self.assertEqual(
            {"TLC_600", "CATA_556"}, {card.card_id for card in player.hand}
        )

    def test_volcanic_thrasher_draws_fire_spell_with_kindred_bonus(self):
        game = self.game()
        player = game.players[0]
        player.played_races_last_turn = {"ELEMENTAL"}
        player.deck = [game._entity("CATA_582")]
        thrasher = game._entity("TLC_223")
        player.hand.append(thrasher)
        game.step(Action("PLAY", thrasher.entity_id))
        spell = next(card for card in player.hand if card.card_id == "CATA_582")
        self.assertEqual(2, spell.spell_damage_bonus)
        target = game._instance_from_definition(
            CardDef("TEST_TARGET", "Target", "MINION", 1, 0, 10)
        )
        game.players[1].board.append(target)
        game.step(Action("PLAY", spell.entity_id))
        self.assertEqual(3, target.damage)

    def test_prepare_spends_remaining_mana_and_locks_card_until_later_turn(self):
        game = self.game()
        player = game.players[0]
        securitybot = game._entity("JAIL_457")
        player.hand.append(securitybot)
        player.mana = 3
        game.step(Action("PREPARE", securitybot.entity_id))
        self.assertEqual(0, player.mana)
        self.assertEqual(0, game._effective_cost(player, securitybot))
        self.assertFalse(any(
            action.kind == "PLAY" and action.source == securitybot.entity_id
            for action in game.legal_actions()
        ))
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        self.assertTrue(any(
            action.kind == "PLAY" and action.source == securitybot.entity_id
            for action in game.legal_actions()
        ))

    def test_hijacked_securitybot_buffs_other_friendly_minions(self):
        game = self.game()
        player = game.players[0]
        other = game._instance_from_definition(
            CardDef("TEST_OTHER", "Other", "MINION", 1, 2, 2)
        )
        player.board.append(other)
        securitybot = game._entity("JAIL_457")
        player.hand.append(securitybot)
        game.step(Action("PLAY", securitybot.entity_id))
        self.assertEqual((3, 3), (other.attack, other.max_health))
        self.assertEqual((3, 3), (securitybot.attack, securitybot.max_health))

    def test_remnant_costs_less_per_death_this_turn_and_draws_two(self):
        game = self.game()
        player = game.players[0]
        victims = [
            game._instance_from_definition(
                CardDef(f"TEST_{i}", f"Victim {i}", "MINION", 1, 1, 1)
            )
            for i in range(2)
        ]
        player.board.extend(victims)
        for victim in victims:
            victim.damage = victim.max_health
        game._resolve_deaths()
        self.assertEqual(2, game.minions_died_this_turn)
        player.deck = [game._entity("TIME_053"), game._entity("DINO_404")]
        remnant = game._entity("END_004")
        player.hand.append(remnant)
        self.assertEqual(5, game._effective_cost(player, remnant))
        game.step(Action("PLAY", remnant.entity_id))
        self.assertEqual(0, len(player.deck))

    def test_diabolus_rex_kindred_hits_distinct_board_edges(self):
        game = self.game()
        player, enemy = game.players
        rex = game._entity("DINO_138")
        player.played_races_last_turn = {rex.definition.races[0]}
        targets = [
            game._instance_from_definition(
                CardDef(f"TEST_{i}", f"Target {i}", "MINION", 1, 0, 10)
            )
            for i in range(3)
        ]
        enemy.board.extend(targets)
        player.hand.append(rex)
        game.step(Action("PLAY", rex.entity_id))
        self.assertEqual([4, 10, 4], [target.health for target in targets])

    def test_friendly_death_creates_corpse_and_arms_hollow_direhorn(self):
        game = self.game()
        player = game.players[0]
        player.corpses = 2
        direhorn = game._entity("DINO_416")
        victim = game._instance_from_definition(
            CardDef("TEST_VICTIM", "Victim", "MINION", 1, 1, 1)
        )
        player.board.extend([direhorn, victim])
        victim.damage = victim.max_health
        game._resolve_deaths()
        self.assertTrue(direhorn.reborn)
        self.assertEqual(0, player.corpses)

    def test_reanimated_pterrordax_spends_corpses_instead_of_mana(self):
        game = self.game()
        player = game.players[0]
        player.corpses = 5
        player.mana = 0
        pterrordax = game._entity("TLC_436")
        player.hand.append(pterrordax)
        self.assertIn(Action("PLAY", pterrordax.entity_id), game.legal_actions())
        game.step(Action("PLAY", pterrordax.entity_id))
        self.assertEqual(0, player.corpses)
        self.assertEqual(0, player.mana)
        self.assertIn(pterrordax, player.board)

    def test_volcoross_offers_affordable_corpse_amounts(self):
        game = self.game()
        player = game.players[0]
        player.corpses = 25
        volcoross = game._entity("FIR_951")
        player.hand.append(volcoross)
        game.step(Action("PLAY", volcoross.entity_id))
        self.assertEqual(
            [Action("CORPSE_SPEND", 10), Action("CORPSE_SPEND", 20)],
            game.legal_actions(),
        )
        before = (volcoross.attack, volcoross.max_health)
        game.step(Action("CORPSE_SPEND", 20))
        self.assertEqual(5, player.corpses)
        self.assertEqual(
            (before[0] + 20, before[1] + 20),
            (volcoross.attack, volcoross.max_health),
        )

    def test_hideous_husk_summons_leeches_that_steal_health(self):
        game = self.game()
        player, enemy = game.players
        target = game._instance_from_definition(
            CardDef("TEST_TARGET", "Target", "MINION", 1, 1, 4)
        )
        enemy.board.append(target)
        husk = game._entity("EDR_810")
        player.hand.append(husk)
        game.step(Action("PLAY", husk.entity_id))
        self.assertEqual(2, sum(m.card_id == "EDR_810t" for m in player.board))
        game.step(Action("END_TURN"))
        self.assertNotIn(target, enemy.board)
        self.assertEqual((34, 34), (player.health, player.max_health))

    def test_magmaw_refills_appendages_and_body_buffs_a_friend(self):
        game = self.game()
        player = game.players[0]
        magmaw = game._entity("CATA_550")
        player.hand.append(magmaw)
        game.step(Action("PLAY", magmaw.entity_id))
        bodies = [m for m in player.board if m.card_id == "CATA_550t"]
        self.assertEqual(6, len(bodies))
        self.assertEqual(93, player.pending_magmaw_bodies)
        attack_before = sum(m.attack for m in player.board)
        bodies[0].damage = bodies[0].max_health
        game._resolve_deaths()
        self.assertEqual(6, sum(m.card_id == "CATA_550t" for m in player.board))
        self.assertEqual(92, player.pending_magmaw_bodies)
        self.assertEqual(attack_before + 2, sum(m.attack for m in player.board))

    def test_nythendra_splits_and_reforms_from_surviving_beetles(self):
        game = self.game()
        player = game.players[0]
        nythendra = game._entity("EDR_818")
        player.board.append(nythendra)
        nythendra.damage = nythendra.max_health
        game._resolve_deaths()
        beetles = [m for m in player.board if m.card_id == "EDR_818t"]
        self.assertEqual(7, len(beetles))
        for beetle in beetles[:3]:
            beetle.damage = beetle.max_health
        game._resolve_deaths()
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        reformed = next(m for m in player.board if m.card_id == "EDR_818")
        self.assertEqual((4, 4), (reformed.attack, reformed.max_health))
        self.assertTrue(reformed.taunt)
        self.assertFalse(any(m.card_id == "EDR_818t" for m in player.board))

    def test_haywire_hornswog_tracks_lifetime_overload(self):
        game = self.game()
        player = game.players[0]
        hornswog = game._entity("END_030")
        player.hand.append(hornswog)
        game._overload(player, 2)
        game._overload(player, 1)
        self.assertEqual(3, game._effective_cost(player, hornswog))
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        self.assertEqual(3, player.locked_mana)
        self.assertEqual(player.max_mana - 3, player.mana)
        self.assertEqual(3, game._effective_cost(player, hornswog))

    def test_blackwing_experiment_preserves_attack_as_spell_damage(self):
        game = self.game()
        player, enemy = game.players
        experiment = game._entity("CATA_464")
        experiment.attack_delta += 2
        player.board.append(experiment)
        experiment.damage = experiment.max_health
        game._resolve_deaths()
        breath = next(card for card in player.hand if card.card_id == "CATA_464t")
        self.assertEqual(5, breath.dynamic_spell_damage)
        self.assertIn(Action("PLAY", breath.entity_id, 1, None), game.legal_actions())
        game.step(Action("PLAY", breath.entity_id, 1, None))
        self.assertEqual(25, enemy.health)

    def test_basic_demon_battlecries_self_damage_freeze_and_discard(self):
        game = self.game()
        player = game.players[0]
        flame_imp = game._entity("CORE_EX1_319")
        frost_imp = game._entity("CATA_612")
        homunculus = game._entity("CORE_LOOT_013")
        player.hand.extend([flame_imp, frost_imp, homunculus])
        game.step(Action("PLAY", flame_imp.entity_id))
        game.step(Action("PLAY", frost_imp.entity_id))
        game.step(Action("PLAY", homunculus.entity_id))
        self.assertEqual(25, player.health)
        self.assertEqual(game.turn, frost_imp.frozen_turn)

        doomguard = game._entity("CORE_EX1_310")
        filler = [game._entity("TIME_053"), game._entity("DINO_404")]
        player.hand[:] = [doomguard, *filler]
        game.step(Action("PLAY", doomguard.entity_id))
        self.assertEqual([], player.hand)

    def test_agent_and_occultist_use_explicit_hand_targets(self):
        game = self.game()
        player = game.players[0]
        target = game._entity("TIME_053")
        agent = game._entity("CATA_200")
        player.hand.extend([target, agent])
        game.step(Action("PLAY", agent.entity_id, 0, target.entity_id))
        self.assertEqual("GAME_005", target.card_id)

        discard_target = game._entity("DINO_404")
        occultist = game._entity("CATA_490")
        player.hand.extend([discard_target, occultist])
        game.step(Action("PLAY", occultist.entity_id, 0, discard_target.entity_id))
        self.assertNotIn(discard_target, player.hand)

    def test_satyr_copies_lowest_and_assailant_shuffles_shared_card(self):
        game = self.game()
        player, enemy = game.players
        cheap = game._entity("TIME_053")
        expensive = game._entity("EDR_421")
        enemy.hand.extend([cheap, expensive])
        satyr = game._entity("EDR_521")
        player.hand.append(satyr)
        game.step(Action("PLAY", satyr.entity_id))
        self.assertTrue(any(c.card_id == cheap.card_id for c in player.hand))

        shared = game._entity("DINO_404")
        enemy_shared = game._entity("DINO_404")
        assailant = game._entity("EDR_524")
        player.hand.extend([shared, assailant])
        enemy.hand.append(enemy_shared)
        before_deck = len(enemy.deck)
        before_shared = [
            card.entity_id for card in enemy.hand
            if card.card_id in {held.card_id for held in player.hand}
        ]
        game.step(Action("PLAY", assailant.entity_id))
        after_hand = {card.entity_id for card in enemy.hand}
        self.assertEqual(1, sum(entity not in after_hand for entity in before_shared))
        self.assertEqual(before_deck + 1, len(enemy.deck))

    def test_riftcleaver_and_tichondrius_demon_discount(self):
        game = self.game()
        player, enemy = game.players
        target = game._instance_from_definition(
            CardDef("TEST_TARGET", "Target", "MINION", 1, 1, 6)
        )
        enemy.board.append(target)
        riftcleaver = game._entity("CORE_ULD_165")
        player.hand.append(riftcleaver)
        game.step(Action("PLAY", riftcleaver.entity_id, 1, target.entity_id))
        self.assertNotIn(target, enemy.board)
        self.assertEqual(24, player.health)

        tichondrius = game._entity("CORE_CATA_001")
        demon = game._entity("EDR_486")
        player.hand.extend([tichondrius, demon])
        game.step(Action("PLAY", tichondrius.entity_id))
        self.assertEqual(0, game._effective_cost(player, demon))
        game.step(Action("PLAY", demon.entity_id))
        self.assertFalse(player.next_demon_free)

    def test_bloodthistle_illusionist_marks_one_secret_copy_fake(self):
        game = self.game()
        player = game.players[0]
        illusionist = game._entity("EDR_780")
        player.hand.append(illusionist)
        game.step(Action("PLAY", illusionist.entity_id))
        pair = [m for m in player.board if m.card_id == "EDR_780"]
        self.assertEqual(2, len(pair))
        self.assertEqual(1, sum(m.illusion_fake for m in pair))
        fake = next(m for m in pair if m.illusion_fake)
        game._damage_minion(player.index, fake, 1)
        game._resolve_deaths()
        self.assertNotIn(fake, player.board)

    def test_xavius_discovers_an_existing_deck_minion_with_dark_gift(self):
        game = self.game()
        player = game.players[0]
        player.deck = [
            game._entity("TIME_053", started_in_deck=True),
            game._entity("DINO_404", started_in_deck=True),
            game._entity("EDR_486", started_in_deck=True),
        ]
        xavius = game._entity("EDR_856")
        player.hand.append(xavius)
        game.step(Action("PLAY", xavius.entity_id))
        actions = game.legal_actions()
        self.assertEqual(3, len(actions))
        option = next(
            card for card in game.pending_choice["options"]
            if "sweet_dreams" not in card.gifts
        )
        before = len(player.deck)
        game.step(Action("DISCOVER_PICK", option.entity_id))
        self.assertEqual(before - 1, len(player.deck))
        picked = next(card for card in player.hand if card.entity_id == option.entity_id)
        self.assertTrue(picked.gifts)
        self.assertTrue(picked.started_in_deck)

    def test_alarashi_transforms_only_hand_minions_and_keeps_stats_and_cost(self):
        game = self.game()
        player = game.players[0]
        minion = game._entity("TIME_053")
        minion.attack_delta += 3
        minion.health_delta += 2
        minion.cost_delta -= 1
        spell = game._entity("CATA_582")
        alarashi = game._entity("EDR_493")
        player.hand.extend([minion, spell, alarashi])
        expected = (minion.entity_id, minion.cost, minion.attack, minion.max_health)
        game.step(Action("PLAY", alarashi.entity_id))
        transformed = next(c for c in player.hand if c.entity_id == expected[0])
        self.assertTrue(transformed.has_race("DEMON"))
        self.assertEqual(expected, (
            transformed.entity_id, transformed.cost,
            transformed.attack, transformed.max_health,
        ))
        self.assertIn(spell, player.hand)

    def test_shadowflame_stalker_discovers_two_identical_gifted_demons(self):
        game = self.game()
        player = game.players[0]
        stalker = game._entity("FIR_924")
        player.hand.append(stalker)
        game.step(Action("PLAY", stalker.entity_id))
        option = game.pending_choice["options"][0]
        option_id = option.card_id
        gifts = list(option.gifts)
        game.step(Action("DISCOVER_PICK", option.entity_id))
        copies = [
            card for card in player.hand + player.deck
            if card.card_id == option_id and card.created_by == "FIR_924"
        ]
        self.assertEqual(2, len(copies))
        self.assertTrue(all(card.gifts == gifts for card in copies))

    def test_annoyotron_micro_machine_and_dragonbane_basics(self):
        game = self.game()
        player, enemy = game.players
        annoy = game._entity("CORE_GVG_085")
        self.assertTrue(annoy.taunt and annoy.divine_shield)
        micro = game._entity("CORE_GVG_103")
        dragonbane = game._entity("CORE_DRG_256")
        player.board.extend([micro, dragonbane])
        before = micro.attack
        game.step(Action("HERO_POWER"))
        self.assertEqual(25, enemy.health)
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        self.assertEqual(before + 2, micro.attack)

    def test_curator_draws_one_of_each_tribe(self):
        game = self.game()
        player = game.players[0]
        player.deck = [
            game._instance_from_definition(
                CardDef("TEST_BEAST", "Beast", "MINION", 1, 1, 1, "BEAST")
            ),
            game._instance_from_definition(
                CardDef("TEST_DRAGON", "Dragon", "MINION", 1, 1, 1, "DRAGON")
            ),
            game._instance_from_definition(
                CardDef("TEST_MURLOC", "Murloc", "MINION", 1, 1, 1, "MURLOC")
            ),
        ]
        curator = game._entity("CORE_KAR_061")
        player.hand.append(curator)
        game.step(Action("PLAY", curator.entity_id))
        self.assertEqual(3, len(player.hand))
        self.assertEqual(0, len(player.deck))

    def test_steamcleaner_pickpocket_and_ratcatcher_deck_rules(self):
        game = self.game()
        player, enemy = game.players
        original = game._entity("TIME_053", started_in_deck=True)
        generated = game._entity("DINO_404", created_by="TEST")
        enemy_generated = game._entity("DINO_404", created_by="TEST")
        player.deck = [original, generated]
        enemy.deck = [enemy_generated]
        cleaner = game._entity("CORE_REV_946")
        player.hand.append(cleaner)
        game.step(Action("PLAY", cleaner.entity_id))
        self.assertEqual([original], player.deck)
        self.assertEqual([], enemy.deck)

        player.deck = [game._entity("TIME_053") for _ in range(25)]
        picker = game._entity("JAIL_456")
        player.hand.append(picker)
        game.step(Action("PLAY", picker.entity_id))
        self.assertEqual(24, len(player.deck))

        player.deck = [game._entity("CATA_582"), game._entity("TIME_053")]
        rat = game._entity("JAIL_882")
        player.hand.append(rat)
        game.step(Action("PLAY", rat.entity_id))
        self.assertEqual(2, sum(c.definition.card_type == "SPELL" for c in player.deck))
        rat.damage = rat.max_health
        before = len(player.hand)
        game._resolve_deaths()
        self.assertEqual(before + 1, len(player.hand))

    def test_alarmomatic_swaps_with_opponent_hand_minion(self):
        game = self.game()
        player, enemy = game.players
        alarm = game._entity("JAIL_502")
        incoming = game._entity("DINO_404")
        player.board.append(alarm)
        player.deck.clear()
        enemy.deck.clear()
        enemy.hand[:] = [incoming]
        game.step(Action("END_TURN"))
        game.step(Action("END_TURN"))
        self.assertIn(incoming, player.board)
        self.assertIn(alarm, enemy.hand)

    def test_hardlight_pmm_clockwork_and_quantum_states(self):
        game = self.game()
        player = game.players[0]
        player.health = 20
        protector = game._entity("TIME_015")
        player.hand.append(protector)
        game.step(Action("PLAY", protector.entity_id))
        self.assertEqual(23, player.health)
        game._damage_hero(player, 9)
        self.assertEqual(23, player.health)
        self.assertFalse(player.hero_divine_shield)

        target = game._instance_from_definition(
            CardDef("TEST_TARGET", "Target", "MINION", 1, 2, 3)
        )
        player.board.append(target)
        pmm = game._entity("TIME_043")
        player.hand.append(pmm)
        game.step(Action("PLAY", pmm.entity_id, 0, target.entity_id))
        self.assertEqual((8, 8), (target.attack, target.max_health))
        self.assertFalse(any(
            action.kind == "ATTACK" and action.source == target.entity_id
            and action.target_entity is None
            for action in game.legal_actions()
        ))

        player.turns_taken = 4
        rager = game._entity("TIME_048")
        player.hand.append(rager)
        game.step(Action("PLAY", rager.entity_id))
        self.assertEqual(rager.definition.health + 4, rager.max_health)
        quantum = game._entity("TIME_060")
        player.board.append(quantum)
        game._damage_minion(player.index, quantum, 2)
        self.assertEqual(4, quantum.damage)

    def test_tankgineer_and_timebomb_deathrattles(self):
        game = self.game()
        player, enemy = game.players
        tankgineer = game._entity("TIME_017")
        timebomb = game._entity("TIME_603")
        victim = game._instance_from_definition(
            CardDef("TEST_VICTIM", "Victim", "MINION", 1, 9, 9)
        )
        player.board.extend([tankgineer, timebomb])
        enemy.board.append(victim)
        tankgineer.damage = tankgineer.max_health
        timebomb.damage = timebomb.max_health
        game._resolve_deaths()
        tank = next(m for m in player.board if m.card_id == "TIME_017t")
        self.assertEqual((7, 7), (tank.attack, tank.max_health))
        self.assertTrue(tank.divine_shield)
        self.assertNotIn(victim, enemy.board)

    def test_finja_summons_two_murlocs_after_attack_kill(self):
        game = self.game()
        player, enemy = game.players
        finja = self.add_board(game, "CORE_CFM_344")
        victim = game._instance_from_definition(
            CardDef("TEST_VICTIM", "Victim", "MINION", 1, 1, 2)
        )
        enemy.board.append(victim)
        murlocs = [game._entity("DINO_404"), game._entity("CORE_EX1_507")]
        non_murloc = game._entity("TIME_053")
        player.deck[:] = [*murlocs, non_murloc]

        game.step(Action("ATTACK", finja.entity_id, 1, victim.entity_id))

        self.assertNotIn(victim, enemy.board)
        self.assertTrue(all(murloc in player.board for murloc in murlocs))
        self.assertEqual([non_murloc], player.deck)
        trigger = next(e for e in game.events if e["kind"] == "finja_trigger")
        self.assertCountEqual([m.entity_id for m in murlocs], trigger["summoned"])

    def test_lorewalker_copies_cast_spell_even_if_spell_damages_it(self):
        game = self.game()
        cho = self.add_board(game, "CORE_EX1_100", 1)
        spell = self.add_hand(game, "CATA_582")

        self.play(game, spell)

        copies = [c for c in game.players[1].hand if c.card_id == spell.card_id]
        self.assertEqual(1, len(copies))
        self.assertEqual(cho.card_id, copies[0].created_by)

    def test_keymaster_copies_opponent_draw_at_cost_one(self):
        game = self.game()
        keymaster = self.add_board(game, "CORE_SCH_717", 1)
        drawn = game._entity("CORE_LOOT_137")
        game.players[0].deck[:] = [drawn]

        game._draw(game.players[0])

        copied = game.players[1].hand[-1]
        self.assertEqual(drawn.card_id, copied.card_id)
        self.assertEqual(1, game._effective_cost(game.players[1], copied))
        self.assertEqual(keymaster.card_id, copied.created_by)

    def test_warden_maiev_buffs_later_minions_but_not_herself(self):
        game = self.game()
        maiev = self.add_hand(game, "JAIL_850")
        self.play(game, maiev)
        self.assertEqual((1, 3, 0), (maiev.attack, maiev.max_health, maiev.dormant_turns))

        minion = self.add_hand(game, "TIME_053")
        expected = (minion.attack + 3, minion.max_health + 3)
        self.play(game, minion)
        self.assertEqual((*expected, 1), (
            minion.attack, minion.max_health, minion.dormant_turns,
        ))

    def test_togwaggle_redistributes_combined_hands_preserving_sizes(self):
        game = self.game(31)
        player, enemy = game.players
        first = [game._entity("TIME_053"), game._entity("DINO_404")]
        second = [
            game._entity("CORE_LOOT_137"), game._entity("CATA_582"),
            game._entity("CORE_EX1_507"),
        ]
        togwaggle = game._entity("JAIL_852")
        player.hand[:] = [togwaggle, *first]
        enemy.hand[:] = second
        original_ids = {c.entity_id for c in first + second}

        self.play(game, togwaggle)

        self.assertEqual((2, 3), (len(player.hand), len(enemy.hand)))
        self.assertEqual(
            original_ids,
            {c.entity_id for c in player.hand + enemy.hand},
        )

    def test_city_chief_esho_buffs_other_minions_wherever_they_are(self):
        game = self.game()
        player = game.players[0]
        board_minion = self.add_board(game, "CORE_NEW1_023")
        hand_minion = game._entity("DINO_404")
        deck_minions = [
            game._entity("CORE_LOOT_137"), game._entity("CORE_NEW1_023"),
        ]
        player.deck[:] = deck_minions
        esho = game._entity("TLC_110")
        player.hand[:] = [esho, hand_minion]
        before = {
            held.entity_id: (held.attack, held.max_health)
            for held in [board_minion, hand_minion, *deck_minions]
        }

        self.play(game, esho)

        self.assertEqual((5, 7), (esho.attack, esho.max_health))
        for held in [board_minion, hand_minion, *deck_minions]:
            self.assertEqual(
                (before[held.entity_id][0] + 2, before[held.entity_id][1] + 2),
                (held.attack, held.max_health),
            )

    def test_genn_transforms_reversibly_and_upgrades_warrior_hero_power(self):
        game = self.game()
        player = game.players[0]
        genn = game._entity("CATA_615")
        even = game._entity("CATA_582")
        odd = game._entity("CATA_585")
        player.hand[:] = [genn, even]

        game.legal_actions()
        self.assertEqual("CATA_615t", genn.card_id)
        self.assertEqual((6, 5), (genn.attack, genn.max_health))

        player.hand.append(odd)
        game.legal_actions()
        self.assertEqual("CATA_615", genn.card_id)
        self.assertEqual((5, 4), (genn.attack, genn.max_health))

        player.hand.remove(odd)
        self.play(game, genn)
        self.assertEqual((1, 4), (
            game._hero_power_cost(player), player.hero_power_armor,
        ))
        before = player.armor
        game.step(Action("HERO_POWER"))
        self.assertEqual(before + 4, player.armor)

    def test_khelos_egg_hatches_after_five_deaths(self):
        game = self.game()
        player = game.players[0]
        egg = game._entity("DINO_410")
        player.board.append(egg)
        expected_stages = [
            "DINO_410t2", "DINO_410t3", "DINO_410t4", "DINO_410t5",
            "DINO_410t",
        ]
        for expected in expected_stages:
            current = player.board[0]
            current.damage = current.max_health
            game._resolve_deaths()
            self.assertEqual(expected, player.board[0].card_id)
        khelos = player.board[0]
        self.assertEqual((20, 20), (khelos.attack, khelos.max_health))
        self.assertTrue(khelos.taunt)

    def test_fixed_seed_mirror_is_reproducible_and_legal(self):
        first = DragonMirrorGame(CARDS, 202609080001).run_random()
        second = DragonMirrorGame(CARDS, 202609080001).run_random()
        self.assertEqual(first, second)
        self.assertTrue(first["finished"])
        self.assertEqual(0, first["invalid_actions"])


if __name__ == "__main__":
    unittest.main()
