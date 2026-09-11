from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.rules import CardRule, Hook, RuleRegistry, RuleSource, build_rule_registry


class RuleRegistryTests(unittest.TestCase):
    def test_first_migration_has_machine_readable_provenance(self):
        rows = build_rule_registry().manifest()
        self.assertEqual(87, len(rows))
        by_id = {row["card_id"]: row for row in rows}
        self.assertEqual(["deathrattle"], by_id["CORE_EX1_110"]["hooks"])
        self.assertEqual(
            "upstream_adapted", by_id["CORE_EX1_110"]["source"]["kind"]
        )
        self.assertTrue(by_id["CORE_EX1_110"]["source"]["verification"])
        self.assertEqual(["hero_power"], by_id["EDR_449p"]["hooks"])
        self.assertEqual(
            "official_text_and_powerlog_verified",
            by_id["EDR_449p"]["source"]["kind"],
        )

    def test_duplicate_registration_is_rejected(self):
        rule = CardRule("TEST", {Hook.BATTLECRY: ()}, RuleSource("test", "test"))
        registry = RuleRegistry((rule,))
        with self.assertRaisesRegex(ValueError, "duplicate card rule"):
            registry.register(rule)


if __name__ == "__main__":
    unittest.main()
