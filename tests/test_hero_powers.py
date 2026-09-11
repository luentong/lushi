from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import Action, DragonMirrorGame, UnsupportedGeneratedCard


CARDS = ROOT / "cards.251332.enUS.json"


class BasicHeroPowerTests(unittest.TestCase):
    def game(self, card_class: str, seed: int = 19) -> DragonMirrorGame:
        game = DragonMirrorGame(
            CARDS, seed, player_classes=(card_class, "WARRIOR")
        )
        game.current = 0
        game.players[0].mana = 10
        game.players[0].hero_power_used = False
        game.players[0].board.clear()
        game.players[0].locations.clear()
        game.players[1].board.clear()
        return game

    def hero_power(self, game: DragonMirrorGame, **target) -> None:
        game.step(Action("HERO_POWER", **target))

    def test_warrior_and_hunter_hero_powers(self):
        warrior = self.game("WARRIOR")
        self.hero_power(warrior)
        self.assertEqual(2, warrior.players[0].armor)

        hunter = self.game("HUNTER")
        self.hero_power(hunter)
        self.assertEqual(28, hunter.players[1].health)

    def test_mage_and_priest_targeted_hero_powers(self):
        mage = self.game("MAGE")
        target = mage._entity("CAP_107t")
        target.summoned_turn = mage.turn - 1
        mage.players[1].board.append(target)
        self.hero_power(mage, target_player=1, target_entity=target.entity_id)
        self.assertNotIn(target, mage.players[1].board)

        priest = self.game("PRIEST")
        priest.players[1].health = 25
        self.hero_power(priest, target_player=1, target_entity=None)
        self.assertEqual(27, priest.players[1].health)

    def test_paladin_rogue_and_druid_hero_powers(self):
        paladin = self.game("PALADIN")
        self.hero_power(paladin)
        self.assertEqual("CS2_101t", paladin.players[0].board[0].card_id)

        rogue = self.game("ROGUE")
        self.hero_power(rogue)
        self.assertEqual(("CS2_082", 1, 2), (
            rogue.players[0].weapon.card_id,
            rogue.players[0].weapon.attack,
            rogue.players[0].weapon.durability,
        ))

        druid = self.game("DRUID")
        self.hero_power(druid)
        self.assertEqual(1, druid.players[0].attack)
        self.assertEqual(1, druid.players[0].armor)

    def test_shaman_does_not_repeat_basic_totems(self):
        game = self.game("SHAMAN")
        self.hero_power(game)
        first = game.players[0].board[0].card_id
        game.players[0].hero_power_used = False
        game.players[0].mana = 10
        self.hero_power(game)
        self.assertNotEqual(first, game.players[0].board[1].card_id)

    def test_warlock_and_demon_hunter_hero_powers(self):
        warlock = self.game("WARLOCK")
        hand_size = len(warlock.players[0].hand)
        self.hero_power(warlock)
        self.assertEqual(hand_size + 1, len(warlock.players[0].hand))
        self.assertEqual(28, warlock.players[0].health)

        demon_hunter = self.game("DEMONHUNTER")
        self.assertEqual(1, demon_hunter._hero_power_cost(demon_hunter.players[0]))
        self.hero_power(demon_hunter)
        self.assertEqual(1, demon_hunter.players[0].attack)

    def test_death_knight_ghoul_has_charge_and_dies_at_end_of_turn(self):
        game = self.game("DEATHKNIGHT")
        self.hero_power(game)
        ghoul = game.players[0].board[0]
        self.assertEqual("HERO_11bpt", ghoul.card_id)
        self.assertTrue(ghoul.charge)
        self.assertTrue(any(
            action.kind == "ATTACK" and action.source == ghoul.entity_id
            for action in game.legal_actions()
        ))
        game.step(Action("END_TURN"))
        self.assertNotIn(ghoul, game.players[0].board)

    def test_spell_damage_is_loaded_from_metadata(self):
        game = self.game("SHAMAN")
        totem = game._entity("CS2_052")
        game.players[0].board.append(totem)
        self.assertEqual(1, game._spell_damage(game.players[0]))

    def test_custom_decks_fail_closed_for_unimplemented_cards(self):
        with self.assertRaisesRegex(
            UnsupportedGeneratedCard, "without executable rules"
        ):
            DragonMirrorGame(
                CARDS,
                deck_counts=({"CATA_614": 30}, {"CATA_614": 30}),
            )


if __name__ == "__main__":
    unittest.main()
