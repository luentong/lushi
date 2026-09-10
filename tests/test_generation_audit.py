from __future__ import annotations

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.dragon_mirror import (
    ADDITIONAL_GENERATED_MINION_IDS,
    ADDITIONAL_PLAYABLE_CARD_IDS,
    ADDITIONAL_PLAYABLE_MINION_IDS,
    BLOCKED_GENERATOR_IDS,
    DISCOVER_BANNED_IDS,
    PIRATE_IDS,
    SUPPORTED_ONE_COST_SUMMON_IDS,
    SUPPORTED_DEMON_PLAY_IDS,
    SUPPORTED_STADIUM_WEAPONS,
    SUPPORTED_VOID_SOUL_DEMON_IDS,
    WARRIOR_MINION_IDS,
)
from hsa.generation_audit import (
    PRIORITY_CLOSURE_BACKLOG,
    WEAPON_CLOSURE_BACKLOG,
    build_audit,
)


class GenerationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary, cls.details = build_audit(ROOT / "cards.251332.enUS.json")

    def ids(self, pool: str) -> set[str]:
        return {row["card_id"] for row in self.details if row["pool"] == pool}

    def test_direct_generators_are_in_their_expected_full_pools(self):
        self.assertIn("TLC_600", self.ids("dragon"))
        self.assertIn("EDR_456", self.ids("warrior_minion"))
        self.assertIn("CAP_107", self.ids("pirate"))

    def test_pool_audit_is_nonempty_and_partitioned(self):
        for pool in (
            "dragon", "warrior_minion", "pirate", "weapon",
            "one_cost_minion",
            "tortotem_multi_type_minion",
            "demon_play", "mech_play", "five_cost_minion_play",
            "two_cost_minion_play", "four_cost_minion_play",
            "legendary_minion_play",
            "rewind_card_play", "aura_card_play",
            "void_soul_demon_1", "void_soul_demon_2", "void_soul_demon_3",
            "void_soul_demon_4", "void_soul_demon_5",
            "void_soul_demon_6", "void_soul_demon_7",
            "void_soul_demon_8", "void_soul_demon_9", "void_soul_demon_10",
        ):
            row = self.summary["summary"][pool]
            self.assertGreater(row["candidate_count"], 0)
            self.assertEqual(
                row["candidate_count"],
                row["direct_supported"] + row["generated_supported"]
                + row["metadata_only"] + row["needs_rule"],
            )

    def test_standard_weapon_pool_exposes_remaining_rule_backlog(self):
        weapon = self.summary["summary"]["weapon"]
        self.assertEqual(
            set(SUPPORTED_STADIUM_WEAPONS),
            self.ids("weapon") & set(SUPPORTED_STADIUM_WEAPONS),
        )
        rows = {
            row["card_id"]: row for row in self.details if row["pool"] == "weapon"
        }
        for card_id, (name, attack, durability) in SUPPORTED_STADIUM_WEAPONS.items():
            self.assertEqual(name, rows[card_id]["name"])
            self.assertEqual(attack, rows[card_id]["attack"])
            self.assertEqual(durability, rows[card_id]["health_or_durability"])
        self.assertEqual(35, weapon["candidate_count"])
        self.assertEqual(len(SUPPORTED_STADIUM_WEAPONS), weapon["generated_supported"])
        self.assertEqual(35 - len(SUPPORTED_STADIUM_WEAPONS), weapon["unimplemented"])

    def test_warrior_minion_pool_excludes_other_class_cards(self):
        for row in self.details:
            if row["pool"] == "warrior_minion":
                self.assertIn("WARRIOR", row["card_class"].split(","))

    def test_runtime_warrior_discover_pool_matches_supported_audit_rows(self):
        expected = {
            row["card_id"] for row in self.details
            if row["pool"] == "warrior_minion"
            and row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertEqual(expected, WARRIOR_MINION_IDS)

    def test_runtime_pirate_pool_matches_supported_audit_rows(self):
        expected = {
            row["card_id"] for row in self.details
            if row["pool"] == "pirate"
            and row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertEqual(expected, PIRATE_IDS)

    def test_one_cost_summon_pool_is_contextual_and_audited(self):
        rows = [row for row in self.details if row["pool"] == "one_cost_minion"]
        supported = {
            row["card_id"] for row in rows
            if row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertEqual(65, len(rows))
        self.assertEqual(SUPPORTED_ONE_COST_SUMMON_IDS, supported)
        self.assertNotIn("TIME_872", WARRIOR_MINION_IDS)

    def test_tortotem_dependency_pool_is_explicit_and_incremental(self):
        rows = [
            row for row in self.details
            if row["pool"] == "tortotem_multi_type_minion"
        ]
        self.assertEqual(55, len(rows))
        supported = {
            row["card_id"] for row in rows
            if row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertTrue(ADDITIONAL_GENERATED_MINION_IDS <= supported)
        blocked = {
            row["card_id"] for row in rows if row["status"] == "needs_rule"
        }
        self.assertTrue(BLOCKED_GENERATOR_IDS <= blocked)
        self.assertFalse(BLOCKED_GENERATOR_IDS & supported)

    def test_fixed_deck_generation_bans_are_excluded(self):
        discovered = {
            row["card_id"] for row in self.details
            if row["pool"] in {"dragon", "warrior_minion", "pirate"}
        }
        self.assertFalse(discovered & DISCOVER_BANNED_IDS)

    def test_all_void_soul_demon_tiers_are_closed(self):
        rows = [
            row for row in self.details
            if row["pool"].startswith("void_soul_demon_")
        ]
        supported = {
            row["card_id"] for row in rows
            if row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertEqual(38, len(rows))
        self.assertEqual(SUPPORTED_VOID_SOUL_DEMON_IDS, supported)
        self.assertFalse(any(row["status"] == "needs_rule" for row in rows))

    def test_demon_play_pool_is_stricter_than_summon_pool(self):
        rows = [row for row in self.details if row["pool"] == "demon_play"]
        supported = {
            row["card_id"] for row in rows
            if row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertEqual(38, len(rows))
        self.assertEqual(SUPPORTED_DEMON_PLAY_IDS, supported)
        self.assertEqual(2, sum(row["status"] == "needs_rule" for row in rows))

    def test_mech_play_pool_includes_every_newly_playable_mech(self):
        mech_ids = self.ids("mech_play")
        supported = {
            row["card_id"] for row in self.details
            if row["pool"] == "mech_play"
            and row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertTrue((ADDITIONAL_PLAYABLE_MINION_IDS & mech_ids) <= supported)

    def test_closed_rewind_tranche_is_audited_as_supported(self):
        rows = [row for row in self.details if row["pool"] == "rewind_card_play"]
        supported = {
            row["card_id"] for row in rows
            if row["status"] in {"direct_supported", "generated_supported"}
        }
        self.assertEqual(18, len(rows))
        self.assertTrue(ADDITIONAL_PLAYABLE_CARD_IDS <= supported)
        self.assertEqual(8, len(supported))

    def test_closed_aura_tranche_is_audited_as_supported(self):
        aura_ids = self.ids("aura_card_play")
        supported = {
            row["card_id"] for row in self.details
            if row["pool"] == "aura_card_play"
            and row["status"] in {"direct_supported", "generated_supported"}
        }
        promoted = {
            "CATA_151", "CATA_613", "CORE_BT_187", "CORE_CATA_001", "CORE_CS2_122",
            "CORE_CS2_222", "CORE_EDR_003", "CORE_EX1_162",
            "CORE_EX1_507", "EDR_258", "EDR_480", "EDR_844", "JAIL_202",
            "JAIL_459", "JAIL_890", "TIME_606", "TIME_852", "TLC_228",
            "TLC_241",
        }
        self.assertTrue(promoted <= ADDITIONAL_PLAYABLE_MINION_IDS)
        self.assertTrue((promoted & aura_ids) <= supported)
        self.assertEqual(24, len(supported))

    def test_closed_legendary_tranche_is_audited_as_supported(self):
        rows = [
            row for row in self.details
            if row["pool"] == "legendary_minion_play"
        ]
        supported = {
            row["card_id"] for row in rows
            if row["status"] in {"direct_supported", "generated_supported"}
        }
        tranche = {
            "CATA_720", "CORE_EX1_002", "CORE_EX1_012", "CORE_EX1_014",
            "CORE_EX1_110", "CS3_024", "CS3_025", "FIR_958", "TLC_480",
            "CORE_CFM_344", "CORE_EX1_100", "CORE_SCH_717", "JAIL_850",
            "JAIL_852", "TLC_110",
            "CATA_615", "DINO_410",
        }
        self.assertTrue(tranche <= ADDITIONAL_PLAYABLE_MINION_IDS)
        self.assertTrue(tranche <= supported)
        self.assertEqual(35, len(supported))

    def test_remaining_weapon_backlog_explains_transitive_closure(self):
        rows = {
            row["card_id"]: row
            for row in self.details
            if row["pool"] == "weapon" and row["status"] == "needs_rule"
        }
        self.assertEqual(set(rows), set(WEAPON_CLOSURE_BACKLOG))
        exported = {
            row["card_id"]: row
            for row in self.summary["weapon_closure_backlog"]
        }
        self.assertEqual(set(rows), set(exported))
        for card_id, row in exported.items():
            self.assertEqual(rows[card_id]["name"], row["name"])
            self.assertTrue(row["mechanic"])
            self.assertTrue(row["transitive_dependencies"])

    def test_priority_backlog_exactly_tracks_the_five_plus_one_plus_three_gap(self):
        missing = {
            row["card_id"]: row
            for row in self.details
            if row["pool"] in {"dragon", "warrior_minion", "weapon"}
            and row["status"] == "needs_rule"
        }
        self.assertEqual(set(missing), set(PRIORITY_CLOSURE_BACKLOG))
        exported = {
            row["card_id"]: row
            for row in self.summary["priority_closure_backlog"]
        }
        self.assertEqual(set(missing), set(exported))
        for card_id, row in exported.items():
            self.assertEqual(missing[card_id]["pool"], row["pool"])
            self.assertEqual(missing[card_id]["name"], row["name"])
            self.assertTrue(row["mechanic"])
            self.assertTrue(row["transitive_dependencies"])


if __name__ == "__main__":
    unittest.main()
