from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

SPEC = importlib.util.spec_from_file_location(
    "audit_standard_rules", ROOT / "scripts" / "audit_standard_rules.py"
)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class StandardRuleCoverageTests(unittest.TestCase):
    def test_metadata_only_cards_are_never_reported_as_playable(self):
        self.assertEqual(
            "not_implemented",
            MODULE.implementation_status("CATA_614", set()),
        )

    def test_supported_legacy_and_declarative_are_distinguished(self):
        self.assertEqual(
            "legacy_compatibility",
            MODULE.implementation_status("CAP_107t", set()),
        )
        self.assertEqual(
            "declarative",
            MODULE.implementation_status("CAP_107t", {"CAP_107t"}),
        )


if __name__ == "__main__":
    unittest.main()
