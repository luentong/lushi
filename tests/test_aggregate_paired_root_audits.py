from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from aggregate_paired_root_audits import aggregate, _sign_test_two_sided


class AggregatePairedAuditTests(unittest.TestCase):
    def audit(self, path, seed, baseline, alternative):
        obj = {
            "schema": "paired-root-outcome-audit-v1", "trace": "trace.json",
            "step": 2, "actor": 0, "recorded_action": "end",
            "continuation_policy": "entity-greedy", "checkpoint": "model.pt",
            "max_actions": 240, "seed": seed,
            "results": [
                {"action_key": ["END_TURN"], "description": "end",
                 "outcomes": [{"replicate": i, "status": s}
                              for i, s in enumerate(baseline)]},
                {"action_key": ["PLAY", 1], "description": "play",
                 "outcomes": [{"replicate": i, "status": s}
                              for i, s in enumerate(alternative)]},
            ],
        }
        path.write_text(json.dumps(obj), encoding="utf-8")

    def test_aggregate_keeps_paired_seeds(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.json", Path(folder) / "b.json"
            self.audit(a, 10, ["losses", "wins"], ["wins", "wins"])
            self.audit(b, 12, ["losses", "wins"], ["wins", "losses"])
            result = aggregate([a, b])
            self.assertEqual(4, result["seed_count"])
            row = result["results"][1]
            self.assertEqual((2, 1, 1),
                             (row["alternative_better"], row["recorded_better"],
                              row["tied"]))
            self.assertEqual(1.0, row["paired_sign_p_two_sided"])

    def test_rejects_overlapping_seeds(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.json", Path(folder) / "b.json"
            self.audit(a, 10, ["wins"], ["wins"])
            self.audit(b, 10, ["wins"], ["wins"])
            with self.assertRaisesRegex(ValueError, "duplicate continuation seed"):
                aggregate([a, b])

    def test_sign_test(self):
        self.assertAlmostEqual(0.0654296875, _sign_test_two_sided(9, 2))
        self.assertIsNone(_sign_test_two_sided(0, 0))


if __name__ == "__main__":
    unittest.main()
