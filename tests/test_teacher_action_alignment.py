import sys
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa import DragonMirrorGame, InformationSetMCTSPolicy
from hsa.encoding import encode_decision
from generate_policy_value_data import validate_teacher_alignment
from generate_policy_value_data import independent_conditional_targets
from types import SimpleNamespace


class TeacherActionAlignmentTests(unittest.TestCase):
    def game(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 3)
        for player in game.players:
            player.hand.clear()
            player.board.clear()
        player = game.players[game.current]
        player.mana = player.max_mana = 6
        player.hand = [game._entity("EDR_463"), game._entity("EDR_463")]
        return game

    def test_optional_no_target_twilight_is_not_duplicated(self):
        game = self.game()
        actions = game.legal_actions()
        self.assertEqual(len(actions), len({a.key() for a in actions}))
        plays = [a for a in actions if a.kind == "PLAY"]
        self.assertEqual(2, len(plays))  # Two card instances, not two identical options.
        self.assertNotEqual(plays[0].source, plays[1].source)
        self.assertTrue(all(a.target_player is None and a.target_entity is None for a in plays))

    def test_search_encoder_and_export_share_concrete_action_order(self):
        game = self.game()
        decision = encode_decision(game)
        policy = InformationSetMCTSPolicy(samples=1, iterations_per_sample=4, rollout_depth=0, seed=7)
        policy.choose(game)
        validate_teacher_alignment(decision.action_keys, policy.last_search)
        self.assertEqual(len(decision.actions), len(policy.last_search["root_policy"]))

    def test_single_action_path_also_records_identity(self):
        game = self.game()
        game.players[game.current].mana = 0
        decision = encode_decision(game)
        policy = InformationSetMCTSPolicy(samples=1, iterations_per_sample=1, rollout_depth=0)
        policy.choose(game)
        validate_teacher_alignment(decision.action_keys, policy.last_search)

    def test_same_length_but_reordered_labels_are_rejected(self):
        keys = (("END_TURN", -1, -1, -1), ("HERO_POWER", -1, -1, -1))
        search = {"root_action_keys": keys[::-1], "root_policy": [0.5, 0.5]}
        with self.assertRaisesRegex(ValueError, "keys differ"):
            validate_teacher_alignment(keys, search)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_teacher_alignment((keys[0], keys[0]), search)
        with self.assertRaisesRegex(ValueError, "length mismatch"):
            validate_teacher_alignment(keys, {"root_action_keys": keys, "root_policy": [1]})

    def test_independently_researched_branch_exports_aligned_observation(self):
        game = self.game()
        policy = SimpleNamespace(conditional_training_states=[{
            "game": game, "root_action": "generated_card", "trigger_depth": 2,
            "observation_visits": 4, "policy_visits": 4}])
        args = SimpleNamespace(export_observer_view=True, conditional_training_max_branches=1,
                               conditional_training_repeats=2, conditional_training_iterations=4,
                               rollout_depth=0, search_seed=7, policy_target_source="visits")
        rows = independent_conditional_targets(policy, game.current, args, 101, 4,
                                               known_deck={"EDR_463": 2})
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual(len(row["policy_target"]), len(row["observer_view"]["actions"]))
        self.assertEqual(len(row["action_keys"]), len(row["policy_target"]))
        self.assertTrue(row["observer_view"]["known_deck_provided"])


if __name__ == "__main__":
    unittest.main()
