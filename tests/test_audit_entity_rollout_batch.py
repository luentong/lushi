from pathlib import Path
import gzip
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from audit_entity_rollout_batch import (holm_adjust, load_decision_metadata, paired_sign_pvalue,
                                        screen_evidence, select_roots)


class AuditEntityRolloutBatchTests(unittest.TestCase):
    def test_stratified_root_selection_aligns_learner_steps(self):
        records = [
            {"seed": 11, "deck_a": "a", "deck_b": "b", "learner_seat": 0,
             "action_trace": [{"actor": 0, "action": ["END_TURN"]},
                              {"actor": 1, "action": ["END_TURN"]},
                              {"actor": 0, "action": ["PLAY"]}]},
            {"seed": 12, "deck_a": "a", "deck_b": "b", "learner_seat": 0,
             "action_trace": [{"actor": 0, "action": ["END_TURN"]},
                              {"actor": 0, "action": ["PLAY"]}]},
        ]
        decisions = {
            11: [{"actor": 0, "legal_actions": 3, "chosen_probability": 0.55},
                 {"actor": 0, "legal_actions": 4, "chosen_probability": 0.15}],
            12: [{"actor": 0, "legal_actions": 3, "chosen_probability": 0.48},
                 {"actor": 0, "legal_actions": 4, "chosen_probability": 0.08}],
        }
        roots = select_roots(records, decisions, max_root_actions=8, seed=1)
        self.assertEqual([2, 0], [row["step"] for row in roots])
        self.assertEqual(["low_chosen_probability", "middle_chosen_probability"],
                         [row["stratum"] for row in roots])
        with self.assertRaisesRegex(ValueError, "count mismatch"):
            select_roots(records, {**decisions, 11: decisions[11][:1]},
                         max_root_actions=8, seed=1)
        with self.assertRaisesRegex(ValueError, "action key mismatch"):
            bad = {**decisions, 11: [*decisions[11][:1],
                                     {**decisions[11][1], "trace_step": 2,
                                      "action_key": ["END_TURN"]}]}
            select_roots(records, bad, max_root_actions=8, seed=1)

    def test_exact_paired_sign_and_holm(self):
        self.assertAlmostEqual(2 / 256, paired_sign_pvalue(8, 0))
        self.assertEqual(1, paired_sign_pvalue(4, 4))
        comparisons = [{"sign_pvalue": 0.01}, {"sign_pvalue": 0.03},
                       {"sign_pvalue": 0.02}]
        holm_adjust(comparisons)
        self.assertEqual([0.03, 0.04, 0.04],
                         [round(row["holm_pvalue"], 2) for row in comparisons])

    def test_significant_worse_alternative_is_not_a_correction(self):
        evidence = screen_evidence([
            {"holm_pvalue": 0.01, "alternative_better": 1, "selected_better": 19},
            {"holm_pvalue": 0.02, "alternative_better": 17, "selected_better": 0},
            {"holm_pvalue": 1.0, "alternative_better": 2, "selected_better": 3},
        ])
        self.assertEqual(1, evidence["correction_candidates"])
        self.assertEqual(1, evidence["selected_action_supported_against_alternatives"])
        self.assertEqual(1, evidence["unresolved_comparisons"])

    def test_new_rollout_action_provenance_is_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "rollout.jsonl.gz"
            with gzip.open(path, "wt", encoding="utf-8") as handle:
                handle.write(json.dumps({"game_seed": 11, "actor": 0,
                                         "logp": -0.1, "view": {"actions": [{}, {}]},
                                         "trace_step": 0, "action_key": ["PLAY", 7, 1, 3]}) + "\n")
            rows = load_decision_metadata(path)
            record = {"seed": 11, "deck_a": "a", "deck_b": "b", "learner_seat": 0,
                      "action_trace": [{"actor": 0, "action": ["PLAY", 7, 1, 3]}]}
            self.assertEqual(1, len(select_roots([record], rows, max_root_actions=8, seed=1)))
            rows[11][0]["trace_step"] = 1
            with self.assertRaisesRegex(ValueError, "trace step mismatch"):
                select_roots([record], rows, max_root_actions=8, seed=1)


if __name__ == "__main__":
    unittest.main()
