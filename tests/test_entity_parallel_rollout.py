import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from entity_parallel_rollout import collection_jobs, retry_job


class ParallelScheduleTests(unittest.TestCase):
    def test_external_mixture_balanced_by_learner_deck_and_seat(self):
        from collections import Counter, defaultdict
        args = SimpleNamespace(seed=42, games_per_round=128, deck_a=None, deck_b=None,
            heuristic_opponent_fraction=.25, search_opponent_fraction=.25)
        jobs = collection_jobs(args, 0, {"a": None, "b": None}, [("bootstrap", None)])
        self.assertEqual(jobs, collection_jobs(args, 0, {"a": None, "b": None}, [("bootstrap", None)]))
        groups = defaultdict(Counter)
        for job in jobs:
            groups[(job['deck_a'] if job['learner_seat'] == 0 else job['deck_b'],
                    job['learner_seat'])][job['opponent_version']] += 1
        for counts in groups.values():
            self.assertEqual({'bootstrap': 16, 'external:heuristic': 8, 'external:ismcts': 8}, dict(counts))

    def test_retry_preserves_deck_seat_opponent_and_has_disjoint_seed(self):
        args = SimpleNamespace(seed=42, games_per_round=16, deck_a=None, deck_b=None)
        jobs = collection_jobs(args, 0, {"a": None, "b": None}, [("bootstrap", None)])
        seeds = {job["seed"] for job in jobs}
        for job in jobs:
            retried = retry_job(job, len(jobs))
            self.assertNotIn(retried["seed"], seeds)
            self.assertEqual(1, retried["attempt"])
            for field in ("slot", "deck_a", "deck_b", "learner_seat", "opponent_version"):
                self.assertEqual(job[field], retried[field])


@unittest.skipUnless(importlib.util.find_spec("torch"), "torch not installed")
class ParallelCollectionTests(unittest.TestCase):
    def collect(self, workers, cap=160, external=None):
        import torch
        from hsa.entity_model import KIND_INDEX
        from benchmark_mcts import _decoded_decks
        from entity_parallel_rollout import collect_parallel_round

        class EndTurnPolicy(torch.nn.Module):
            card_ids = ()

            def forward(self, batch):
                logits = torch.where(batch["kind"] == KIND_INDEX["END_TURN"], 100., -100.)
                logits = logits.masked_fill(~batch["action_mask"], -1e9)
                return logits, torch.zeros(len(logits))

        torch.set_num_threads(1)
        config = ROOT / "config/decks_20260925_smoke8.json"
        decks = _decoded_decks(config)
        warrior = next(name for name, (_, cls) in decks.items() if cls == "WARRIOR")
        args = SimpleNamespace(seed=202701201001, games_per_round=2, deck_a=warrior,
            deck_b=warrior, cards=ROOT / "cards.251332.enUS.json", deck_config=config,
            max_actions=cap, rollout_workers=workers, worker_timeout=60,
            inference_batch_size=workers, advantage_mode="terminal", gae_lambda=.95)
        model = EndTurnPolicy().eval()
        args.heuristic_opponent_fraction = float(external == "heuristic")
        args.search_opponent_fraction = float(external == "ismcts")
        args.search_opponent_iterations = 4
        result = collect_parallel_round(model, [("bootstrap", {})], args, "cpu", 0, decks)
        return result, args.last_collection_metrics

    def test_external_opponents_only_record_learner_actions(self):
        for external in ("heuristic", "ismcts"):
            (rows, games, failures), _ = self.collect(2, cap=400, external=external)
            self.assertEqual([], failures)
            self.assertEqual(2, len(games))
            self.assertTrue(rows)
            by_seed = {g['seed']: g for g in games}
            for row in rows:
                game = by_seed[row['game_seed']]
                self.assertEqual(game['learner_seat'], row['actor'])
                self.assertEqual('external:' + external, row['opponent_version'])
                self.assertEqual(row['action_key'], game['action_trace'][row['trace_step']]['action'])

    def test_batched_collection_preserves_trace_seat_rewards_and_worker_independence(self):
        (rows1, games1, failed1), _ = self.collect(1)
        (rows2, games2, failed2), metrics = self.collect(2)
        self.assertEqual([], failed1)
        self.assertEqual([], failed2)
        self.assertEqual(games1, games2)
        self.assertEqual(rows1, rows2)
        self.assertEqual(2, len(games1))
        self.assertEqual(0, sum(g["invalid_actions"] for g in games1))
        self.assertEqual(2, metrics["completed_schedule_slots"])
        by_seed = {g["seed"]: g for g in games1}
        for row in rows1:
            game = by_seed[row["game_seed"]]
            trace = game["action_trace"][row["trace_step"]]
            self.assertEqual(game["learner_seat"], row["actor"])
            self.assertEqual(row["action_key"], trace["action"])
            expected = 0 if game["winner"] is None else 1 if game["winner"] == row["actor"] else -1
            self.assertEqual(expected, row["return"])
            self.assertEqual(expected, row["advantage"])
            self.assertTrue(row["terminated"])

    def test_truncations_preserve_failure_traces_and_never_become_draw_labels(self):
        (rows, games, failures), _ = self.collect(2, cap=1)
        self.assertEqual([], rows)
        self.assertEqual([], games)
        self.assertEqual(6, len(failures))
        self.assertEqual(6, len({f["seed"] for f in failures}))
        self.assertTrue(all("truncated" in f["error"] and len(f["actions"]) == 1 for f in failures))


if __name__ == "__main__":
    unittest.main()
