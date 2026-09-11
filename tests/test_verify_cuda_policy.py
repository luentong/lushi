from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.lineage import ruleset_manifest


SCRIPT = ROOT / "scripts" / "verify_cuda_policy.py"
SPEC = importlib.util.spec_from_file_location("verify_cuda_policy", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class VerifyCudaPolicyTests(unittest.TestCase):
    def test_current_manifest_has_required_identity_fields(self):
        manifest = ruleset_manifest(ROOT)
        self.assertEqual("dragon-warrior-closed-v5", manifest["ruleset"])
        self.assertEqual(64, len(manifest["fingerprint_sha256"]))
        self.assertTrue(MODULE.ROOT.samefile(ROOT))


if __name__ == "__main__":
    unittest.main()
