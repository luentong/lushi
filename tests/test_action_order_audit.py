from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from hsa import DragonMirrorGame
from hsa.dragon_mirror import Action
from hsa.policy_value import HeuristicPolicyValueModel
from audit_action_order import fixed_order, inventory_signature
from replay_trace_state import replay_trace_state
from trace_search_match import compact_state
from audit_information_replanning import audit, finish_turn, crossfit_options


class ActionOrderAuditTests(unittest.TestCase):
    def test_crossfit_does_not_select_with_its_evaluation_samples(self):
        total, count, folds = crossfit_options([
            ({"continuation": "A"}, [1., -1.]),
            ({"continuation": "B"}, [-1., 1.]),
        ])
        self.assertEqual(-2., total)
        self.assertEqual(2, count)
        self.assertEqual(["A", "B"], [f["continuation"] for f in folds])
        self.assertEqual((0., 0, []), crossfit_options([({"continuation": "A"}, [1.])]))
        with self.assertRaises(ValueError):
            crossfit_options([({"continuation": "A"}, [1.]), ({"continuation": "B"}, [1., 2.])])

    def test_replanning_groups_public_reveals_not_sampled_enemy_hands(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 29)
        game.players[0].hand.clear()
        game.players[0].mana = 2
        game.players[0].hand.extend(game._entity(c) for c in ("CATA_556", "CAP_107"))
        before, rng = game.snapshot(), game.rng.getstate()
        rows = audit(game, HeuristicPolicyValueModel(), samples=16)
        cannon = next(r for r in rows if "PLAY Cannonmaster" in r["action"])
        carrier = next(r for r in rows if "PLAY Carrier Whelp" in r["action"])
        self.assertEqual(1, cannon["observation_groups"])
        self.assertEqual(16, cannon["crossfit_samples"])
        self.assertGreater(carrier["observation_groups"], 1)
        self.assertEqual(16, sum(carrier["conditional_best_action_counts"].values()))
        for row in rows:
            self.assertEqual(16, row["accepted_samples"] + row["rejected_samples"])
            self.assertEqual(row["accepted_samples"], sum(g["samples"] for g in row["groups"]))
            self.assertLessEqual(row["crossfit_samples"], row["accepted_samples"])
        self.assertEqual(before, game.snapshot())
        self.assertEqual(rng, game.rng.getstate())

    def test_recommendation_can_change_across_generated_public_outcomes(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 2026092607)
        game.players[0].hand.clear()
        game.players[0].mana = 4
        game.players[0].hand.extend(game._entity(c) for c in ("CATA_556", "CAP_107"))
        rows = audit(game, HeuristicPolicyValueModel(), samples=64, seed=914)
        carrier = next(r for r in rows if "PLAY Carrier Whelp" in r["action"])
        self.assertGreater(carrier["observation_groups"], 1)
        self.assertGreater(carrier["distinct_conditional_best_actions"], 1)
        self.assertTrue(carrier["outcome_sensitive_continuation"])
        self.assertEqual(64, sum(carrier["conditional_best_action_counts"].values()))

    def test_pending_choice_is_not_finished_by_assumed_selection(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 29)
        game.pending_choice = {"kind": "DISCOVER", "options": []}
        self.assertIsNone(finish_turn(game, game.current))
        self.assertIsNone(finish_turn(game, 1 - game.current))

    def test_paired_orders_preserve_chance_sample_without_mutating_root(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 29)
        game.players[0].hand.clear()
        game.players[0].mana = 2
        carrier, cannon = game._entity("CATA_556"), game._entity("CAP_107")
        game.players[0].hand.extend((carrier, cannon))
        before, rng = game.snapshot(), game.rng.getstate()
        a, b = Action("PLAY", carrier.entity_id), Action("PLAY", cannon.entity_id)
        model = HeuristicPolicyValueModel()
        ab, left = fixed_order(game.clone(), (a, b), model)
        ba, right = fixed_order(game.clone(), (b, a), model)
        self.assertTrue(ab["legal"] and ba["legal"])
        self.assertTrue(ab["steps"][0]["consumed_rng"])
        self.assertFalse(ba["steps"][0]["consumed_rng"])
        self.assertEqual(left.rng.getstate(), right.rng.getstate())
        self.assertEqual(inventory_signature(left), inventory_signature(right))
        self.assertEqual(before, game.snapshot())
        self.assertEqual(rng, game.rng.getstate())

    def test_unaffordable_second_action_is_not_silently_applied(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 29)
        game.players[0].hand.clear()
        game.players[0].mana = 1
        cards = [game._entity("CAP_107") for _ in range(2)]
        game.players[0].hand.extend(cards)
        result, _ = fixed_order(game, [Action("PLAY", c.entity_id) for c in cards], HeuristicPolicyValueModel())
        self.assertFalse(result["legal"])
        self.assertEqual(1, len(result["steps"]))

    def trace(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 29)
        payload = {"seed": 29, "initial_state": compact_state(game.snapshot()), "steps": []}
        for step in range(1, 4):
            action = Action("END_TURN")
            row = {"step": step, "state_before": compact_state(game.snapshot()),
                   "description": game.describe_action(action)}
            game.step(action)
            row["state_after"] = compact_state(game.snapshot())
            payload["steps"].append(row)
        return payload

    def replay(self, payload, step=3):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "trace.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            return replay_trace_state(path, step)

    def test_replays_and_matches_each_recorded_state(self):
        payload = self.trace()
        game = self.replay(payload)
        self.assertEqual(payload["steps"][2]["state_before"], compact_state(game.snapshot()))

    def test_rejects_initial_state_drift(self):
        payload = self.trace()
        payload["initial_state"]["players"][0]["health"] -= 1
        with self.assertRaisesRegex(RuntimeError, "Initial trace"):
            self.replay(payload)

    def test_rejects_step_state_drift(self):
        payload = self.trace()
        payload["steps"][0]["state_after"]["players"][0]["health"] -= 1
        with self.assertRaisesRegex(RuntimeError, "after step 1"):
            self.replay(payload)

    def test_rejects_missing_actions_and_invalid_step(self):
        payload = self.trace()
        payload["steps"][0]["description"] = "not a legal action"
        with self.assertRaisesRegex(RuntimeError, "matching legal action"):
            self.replay(payload)
        with self.assertRaises(ValueError):
            self.replay(payload, 0)


if __name__ == "__main__":
    unittest.main()
