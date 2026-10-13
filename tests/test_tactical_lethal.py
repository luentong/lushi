from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from audit_search_tactics import make_case
from hsa.mcts import InformationSetMCTSPolicy
from hsa.policy_value import PolicyValueOutput
from hsa.tactical_lethal import find_face_attack_lethal, find_same_turn_lethal
from hsa.dragon_mirror import CardDef, Location, Weapon
from hsa.rules import CardRule, RuleRegistry, RuleSource, Hook, DamageEnemyHero


class EndOnly:
    def predict(self, game, actions):
        weights = tuple(float(a.kind == "END_TURN") for a in actions)
        total = sum(weights) or len(actions)
        return PolicyValueOutput(tuple(w / total for w in weights), .999)


class TacticalLethalTests(unittest.TestCase):
    def test_two_step_witness_executes_and_does_not_mutate_root(self):
        game, _, _ = make_case("reserve_mana_for_lethal")
        before = game.snapshot()
        witness = find_same_turn_lethal(game)
        self.assertIsNotNone(witness)
        self.assertEqual(2, len(witness.actions))
        branch = game.clone(record_events=False)
        for action in witness.actions:
            self.assertIn(action, branch.legal_actions())
            branch.step(action)
        self.assertTrue(branch.finished)
        self.assertEqual(0, branch.winner)
        self.assertEqual(before, game.snapshot())

    def test_terminal_sequence_overrides_wrong_end_prior(self):
        for name in ("reserve_mana_for_lethal", "after_generation_lethal"):
            game, expected, _ = make_case(name)
            policy = InformationSetMCTSPolicy(samples=1, iterations_per_sample=8,
                                             policy_value_model=EndOnly())
            self.assertTrue(expected(policy.choose(game)))
            self.assertEqual("bounded_same_turn_terminal", policy.last_search["selection_source"])
            self.assertEqual(1., sum(policy.last_search["root_policy"]))

    def test_unknown_secrets_and_spell_on_board_are_not_terminal_proofs(self):
        game, _, _ = make_case("after_generation_lethal")
        game.players[1].secrets.append(game._entity("CORE_EX1_287"))
        self.assertIsNone(find_same_turn_lethal(game))
        game.players[1].secrets.clear()
        game.players[1].board.append(game._entity("CATA_556"))
        self.assertIsNone(find_same_turn_lethal(game))

    def test_public_face_attack_witness_uses_each_attacker_only_when_legal(self):
        game, _, _ = make_case("immediate_lethal")
        game.players[1].health = 6
        first = game.players[0].board[0]
        first.windfury = True
        witness = find_same_turn_lethal(game)
        self.assertEqual(2, len(witness.actions))
        first.attacks_this_turn = 1
        self.assertIsNone(find_same_turn_lethal(game))
        first.attacks_this_turn = 0
        guard = game._entity("CATA_556")
        guard.taunt = True
        game.players[1].board.append(guard)
        self.assertIsNone(find_same_turn_lethal(game))

    def test_face_attack_precheck_handles_board_weapon_and_location(self):
        game, expected, _ = make_case("immediate_lethal")
        game.players[0].weapon = Weapon("TEST_WEAPON", "Test Weapon", 1, 2)
        game.players[0].locations.append(Location(7001, "TEST_LOCATION", 2, cooldown=0))
        enemy_body = game._entity("CAP_107")
        enemy_body.summoned_turn = game.turn - 2
        game.players[1].board.append(enemy_body)

        # The old shared deterministic-tactics scope deliberately refused this
        # root because it contained a weapon/location. Face-attack lethality
        # remains provable by the engine even with those unrelated objects.
        self.assertIsNone(find_same_turn_lethal(game))
        witness = find_face_attack_lethal(game)
        self.assertIsNotNone(witness)
        branch = game.clone(record_events=False)
        for action in witness.actions:
            self.assertIn(action, branch.legal_actions())
            branch.step(action)
        self.assertTrue(branch.finished)
        self.assertEqual(0, branch.winner)
        game.players[1].hero_immune = True
        self.assertIsNone(find_face_attack_lethal(game))
        game.players[1].hero_immune = False
        game.players[1].secrets.append(game._entity("CORE_EX1_287"))
        self.assertIsNone(find_face_attack_lethal(game))
        game.players[1].secrets.clear()

        policy = InformationSetMCTSPolicy(
            samples=1, iterations_per_sample=8, policy_value_model=EndOnly(),
        )
        action = policy.choose(game)
        self.assertTrue(expected(action))
        self.assertEqual("bounded_face_attack_terminal", policy.last_search["selection_source"])

    def test_face_attack_search_reaches_seven_attacker_lethal_with_small_node_budget(self):
        game, _, _ = make_case("immediate_lethal")
        for _ in range(6):
            attacker = game._entity("CAP_107")
            attacker.summoned_turn = game.turn - 2
            game.players[0].board.append(attacker)
        game.players[1].health = sum(card.attack for card in game.players[0].board)
        witness = find_face_attack_lethal(game, max_nodes=64)
        self.assertIsNotNone(witness)
        self.assertEqual(7, len(witness.actions))

    def test_random_generation_is_not_a_deterministic_witness(self):
        game, _, _ = make_case("information_before_commitment")
        self.assertIsNone(find_same_turn_lethal(game))

    def test_no_hardcoded_card_identity_and_hero_immunity_respected(self):
        game, _, _ = make_case("after_generation_lethal")
        card_id = "TEST_PRIMITIVE_LETHAL"
        game.card_defs = {**game.card_defs, card_id: CardDef(card_id, "Test damage", "SPELL", 1)}
        game.executable_card_ids = game.executable_card_ids | {card_id}
        game.rule_registry = RuleRegistry((*game.rule_registry.all_rules(),
            CardRule(card_id, {Hook.SPELL: (DamageEnemyHero(7),)},
                     RuleSource("test", "test", card_id, "test", ()))))
        game.players[0].hand = [game._entity(card_id)]
        self.assertIsNotNone(find_same_turn_lethal(game))
        game.players[1].hero_immune = True
        self.assertIsNone(find_same_turn_lethal(game))

    def test_depth_bound_is_inconclusive_and_hidden_order_does_not_matter(self):
        game, _, _ = make_case("reserve_mana_for_lethal")
        self.assertIsNone(find_same_turn_lethal(game, max_depth=1))
        first = find_same_turn_lethal(game)
        game.players[0].deck.reverse()
        game.players[1].deck.reverse()
        game.rng.seed(999)
        self.assertEqual(first.actions, find_same_turn_lethal(game).actions)


if __name__ == "__main__":
    unittest.main()
