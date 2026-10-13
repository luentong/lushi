import copy
import gzip
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from train_entity_selfplay import (terminal_return, load_observer_records, weight_games,
                                  aggregate_metrics, bootstrap_gate, selection_score,
                                  rollout_schedule, rollout_opponent_schedule,
                                  weight_ppo_games, retain_opponent_pool, report_argument,
                                  assign_ppo_advantages, constrain_mulligan_actions)
from generate_policy_value_data import neural_teacher_kwargs


class EntityTrainingContracts(unittest.TestCase):
    def test_mulligan_behavior_does_not_retoggle_selected_cards(self):
        from types import SimpleNamespace
        from hsa.dragon_mirror import Action
        game = SimpleNamespace(pending_choice={"kind": "MULLIGAN", "selected": {11}})
        actions = [Action("MULLIGAN_TOGGLE", 11), Action("MULLIGAN_TOGGLE", 12),
                   Action("MULLIGAN_CONFIRM")]
        filtered = constrain_mulligan_actions(game, actions)
        self.assertEqual([("MULLIGAN_TOGGLE", 12, -1, -1),
                          ("MULLIGAN_CONFIRM", -1, -1, -1)],
                         [action.key() for action in filtered])

    def test_rollouts_balance_both_matchups_and_learner_seats(self):
        from collections import Counter
        jobs = rollout_schedule(["warrior", "druid"], 32, 4)
        self.assertEqual(8, len(set(jobs)))
        self.assertEqual({4}, set(Counter(jobs).values()))
        self.assertEqual(jobs, rollout_schedule(["warrior", "druid"], 32, 4))
        self.assertEqual({("warrior", "druid", 0), ("warrior", "druid", 1)},
                         set(rollout_schedule(["warrior", "druid"], 4, 4, "warrior", "druid")))

    def test_each_complete_opponent_cycle_uses_every_historical_version(self):
        from collections import Counter
        ids = ["bootstrap", "round1", "round2"]
        schedule = rollout_opponent_schedule(ids, 12, 19)
        self.assertEqual({4}, set(Counter(schedule).values()))
        self.assertEqual(schedule, rollout_opponent_schedule(ids, 12, 19))
        with self.assertRaises(ValueError):
            rollout_opponent_schedule(["bootstrap", "bootstrap"], 2, 19)

    def test_each_learner_deck_sees_balanced_historical_versions(self):
        from collections import Counter
        decks = ["a", "b", "a", "a", "b", "b", "a", "b"]
        versions = rollout_opponent_schedule(["bootstrap", "round1"], len(decks), 7, decks)
        for deck in ("a", "b"):
            self.assertEqual({"bootstrap": 2, "round1": 2},
                             dict(Counter(v for d, v in zip(decks, versions) if d == deck)))
        with self.assertRaises(ValueError):
            rollout_opponent_schedule(["bootstrap"], 2, 7, ["a"])

    def test_anchor_remains_in_full_historical_pool(self):
        pool = [("bootstrap", 0)] + [(f"round{i}", i) for i in range(1, 7)]
        self.assertEqual(["bootstrap", "round4", "round5", "round6"],
                         [name for name, _ in retain_opponent_pool(pool, 4)])
        self.assertEqual(["bootstrap"], [name for name, _ in retain_opponent_pool(pool, 1)])
        self.assertEqual(["bootstrap", "round1"],
                         [name for name, _ in retain_opponent_pool(pool[:2], 4)])

    def test_repeated_checkpoint_paths_are_json_reportable(self):
        self.assertEqual(["a.pt", "b.pt"],
                         report_argument([Path("a.pt"), Path("b.pt")]))

    def test_partial_multideck_cycle_covers_every_deck_in_both_positions(self):
        from collections import Counter
        decks = [f"deck{i}" for i in range(8)]
        jobs = rollout_schedule(decks, 16, 23)
        self.assertEqual({2}, set(Counter(a for a, _, _ in jobs).values()))
        self.assertEqual({2}, set(Counter(b for _, b, _ in jobs).values()))
        self.assertEqual({0, 1}, {seat for _, _, seat in jobs})
        complete = rollout_schedule(decks, 128, 23)
        self.assertEqual(128, len(set(complete)))

    def test_long_and_short_games_have_equal_total_weight(self):
        rows = [{"seed": 1}] + [{"seed": 2} for _ in range(9)]
        weight_games(rows)
        self.assertAlmostEqual(5, rows[0]["weight"])
        self.assertAlmostEqual(5, sum(r["weight"] for r in rows[1:]))

    def test_ppo_trajectories_weight_each_completed_game_equally(self):
        rows = [{"game_seed": 1}] + [{"game_seed": 2} for _ in range(9)]
        weight_ppo_games(rows)
        self.assertAlmostEqual(5, rows[0]["weight"])
        self.assertAlmostEqual(5, sum(row["weight"] for row in rows[1:]))

    def test_gae_can_credit_a_good_move_in_a_lost_game(self):
        episode = [{"actor": 0, "old_value": -0.8},
                   {"actor": 0, "old_value": 0.3},
                   {"actor": 0, "old_value": -0.9}]
        assign_ppo_advantages(episode, -1, mode="gae", gae_lambda=0.5)
        self.assertAlmostEqual(0.475, episode[0]["advantage"])
        self.assertAlmostEqual(-1.25, episode[1]["advantage"])
        self.assertAlmostEqual(-0.1, episode[2]["advantage"])
        self.assertEqual([-1] * 3, [row["return"] for row in episode])
        self.assertTrue(all(row["terminated"] and not row["truncated"] for row in episode))

    def test_terminal_credit_retains_previous_behavior(self):
        episode = [{"actor": 1, "old_value": -0.3},
                   {"actor": 1, "old_value": 0.4}]
        assign_ppo_advantages(episode, 1)
        self.assertEqual([1.3, 0.6], [row["advantage"] for row in episode])
        assign_ppo_advantages(episode, 1, mode="gae", gae_lambda=1)
        self.assertAlmostEqual(1.3, episode[0]["advantage"])
        self.assertAlmostEqual(0.6, episode[1]["advantage"])
        with self.assertRaises(ValueError):
            assign_ppo_advantages(episode, 1, mode="gae", gae_lambda=1.1)
        with self.assertRaises(ValueError):
            assign_ppo_advantages(episode + [{"actor": 0, "old_value": 0}], 1)

    def test_partial_batch_is_weighted_by_actual_row_count(self):
        self.assertAlmostEqual(1 / 9, aggregate_metrics([
            {"rows": 8, "value_brier": 0}, {"rows": 1, "value_brier": 1}])["value_brier"])
        with self.assertRaises(ValueError):
            aggregate_metrics([{"value_brier": 0.1}])

    def test_overfit_value_or_worse_policy_blocks_automatic_ppo(self):
        initial = {"policy_ce": 1.5, "value_brier": 0.25}
        for candidate in ({"policy_ce": 1.4, "value_brier": 0.51},
                          {"policy_ce": 1.6, "value_brier": 0.20},
                          {"policy_ce": float("nan"), "value_brier": 0.20}):
            self.assertFalse(bootstrap_gate(candidate, initial, 0.25)["passed"])
        candidate = {"policy_ce": 1.4, "value_brier": 0.23}
        self.assertTrue(bootstrap_gate(candidate, initial, 0.25)["passed"])
        self.assertFalse(bootstrap_gate(candidate, initial, 0.20)["passed"])
        self.assertAlmostEqual(1.4 + 2 * 0.23, selection_score(candidate, 0.5))

    def test_returns_use_actor_not_action_parity(self):
        actors = [0, 0, 0, 1, 1, 0]
        self.assertEqual([1, 1, 1, -1, -1, 1],
                         [terminal_return(0, a, terminated=True) for a in actors])

    def test_draw_and_truncation_differ(self):
        self.assertEqual(0, terminal_return(None, 0, terminated=True))
        with self.assertRaises(ValueError):
            terminal_return(None, 0, terminated=False)
        with self.assertRaises(ValueError):
            terminal_return(7, 0, terminated=True)

    def test_legacy_rows_cannot_be_fabricated_into_entity_views(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.jsonl.gz"
            with gzip.open(path, "wt") as handle:
                handle.write(json.dumps({"record_type": "decision", "value_target": 1}) + "\n")
            with self.assertRaisesRegex(ValueError, "missing observer_view"):
                load_observer_records([path], 10, 1)

    def test_no_checkpoint_keeps_legacy_generator_unchanged(self):
        from types import SimpleNamespace
        self.assertEqual({}, neural_teacher_kwargs(SimpleNamespace()))


@unittest.skipUnless(importlib.util.find_spec("torch"), "torch not installed")
class PPOLossTests(unittest.TestCase):
    def test_bootstrap_selects_initialization_and_stops_when_updates_do_not_improve(self):
        import torch
        from unittest.mock import patch
        from hsa import DragonMirrorGame
        from hsa.observer_view import observer_view
        from train_entity_selfplay import main
        torch.set_num_threads(1)
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 12)
        view = observer_view(game, actions=game.legal_actions())
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory) / "teacher.jsonl.gz"
            output = Path(directory) / "model.pt"
            with gzip.open(data, "wt") as handle:
                for seed, value in ((1, 1), (2, -1), (5, 1), (10, -1)):
                    handle.write(json.dumps({"record_type": "decision", "game_seed": seed,
                                             "observer_view": view, "value_target": value,
                                             "policy_target": [1 / len(view["actions"])] * len(view["actions"])}) + "\n")
            args = ["train_entity_selfplay.py", "--mode", "bootstrap", "--data", str(data),
                    "--output", str(output), "--d-model", "16", "--layers", "1", "--heads", "2",
                    "--epochs", "3", "--early-stopping-patience", "1", "--learning-rate", "0",
                    "--reset-value-head", "--batch-size", "2"]
            with patch.object(sys, "argv", args):
                self.assertEqual(0, main())
            report = json.loads(output.with_suffix(".report.json").read_text())
            self.assertEqual("complete", report["status"])
            self.assertTrue(report["early_stopped"])
            self.assertEqual(1, len(report["history"]))
            self.assertEqual(0, report["selection"]["epoch"])
            self.assertEqual("neutral_untrained", report["selected_value_status"])
            self.assertTrue(report["bootstrap_gate"]["passed"])
            self.assertTrue(Path(report["selection"]["path"]).is_file())

    def test_neutral_critic_reset_does_not_change_policy(self):
        import torch
        from hsa import DragonMirrorGame
        from hsa.observer_view import observer_view
        from hsa.entity_model import EntityPolicyValueNet, collate_views
        from train_entity_selfplay import reset_value_prediction
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 12)
        model = EntityPolicyValueNet(sorted(game.card_defs), 32, 1, 4).eval()
        batch = collate_views([observer_view(game, actions=game.legal_actions())], model.card_ids)
        with torch.no_grad():
            before, _ = model(batch)
            reset_value_prediction(model)
            after, values = model(batch)
        self.assertTrue(torch.equal(before, after))
        self.assertTrue(torch.equal(values, torch.zeros_like(values)))

    def test_unchanged_policy_has_zero_kl_and_finite_gradients(self):
        import torch
        from hsa import DragonMirrorGame
        from hsa.observer_view import observer_view
        from hsa.entity_model import EntityPolicyValueNet, collate_views
        from train_entity_selfplay import ppo_loss
        torch.set_num_threads(1)
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 12)
        view = observer_view(game, actions=game.legal_actions())
        model = EntityPolicyValueNet(sorted(game.card_defs), 32, 1, 4).eval()
        with torch.no_grad():
            logits, _ = model(collate_views([view], model.card_ids))
        row = {"view": view, "chosen": 0, "logp": float(logits.log_softmax(-1)[0, 0]),
               "return": 1.0, "advantage": 0.75}
        loss, metrics = ppo_loss(model, [row], "cpu")
        self.assertAlmostEqual(0, metrics["approx_kl"], places=6)
        loss.backward()
        self.assertTrue(all(p.grad is None or torch.isfinite(p.grad).all() for p in model.parameters()))

    def test_positive_advantage_increases_selected_action_probability(self):
        import torch
        from train_entity_selfplay import ppo_loss

        class TinyPolicy(torch.nn.Module):
            card_ids = ()

            def __init__(self):
                super().__init__()
                self.logits = torch.nn.Parameter(torch.tensor([0.0, 0.0]))

            def forward(self, batch):
                count = batch["cards"].shape[0]
                return self.logits.expand(count, -1), self.logits[:1].sum().detach().expand(count) * 0

        from hsa import DragonMirrorGame
        from hsa.observer_view import observer_view
        from hsa.dragon_mirror import Action
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 12)
        view = observer_view(game, actions=[Action("END_TURN"), Action("HERO_POWER")])
        model = TinyPolicy()
        row = {"view": view, "chosen": 1, "logp": -0.6931471805599453,
               "return": 1.0, "advantage": 1.0}
        optimizer = torch.optim.SGD(model.parameters(), lr=0.1)
        loss, _ = ppo_loss(model, [row], "cpu")
        loss.backward(); optimizer.step()
        self.assertGreater(float(model.logits.softmax(-1)[1].detach()), 0.5)

    def test_ppo_game_weights_affect_policy_gradient(self):
        import torch
        from hsa import DragonMirrorGame
        from hsa.dragon_mirror import Action
        from hsa.observer_view import observer_view
        from train_entity_selfplay import ppo_loss

        class TinyPolicy(torch.nn.Module):
            card_ids = ()

            def __init__(self):
                super().__init__()
                self.logits = torch.nn.Parameter(torch.zeros(2))

            def forward(self, batch):
                count = batch["cards"].shape[0]
                return self.logits.expand(count, -1), self.logits[:1].sum().expand(count) * 0

        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 12)
        view = observer_view(game, actions=[Action("END_TURN"), Action("HERO_POWER")])
        model = TinyPolicy()
        rows = [{"view": view, "chosen": choice, "logp": -0.6931471805599453,
                 "return": 0.0, "advantage": 1.0, "weight": weight}
                for choice, weight in ((0, 1.5), (1, 0.5))]
        loss, _ = ppo_loss(model, rows, "cpu")
        loss.backward()
        self.assertLess(float(model.logits.grad[0]), 0)
        self.assertGreater(float(model.logits.grad[1]), 0)


if __name__ == "__main__":
    unittest.main()
