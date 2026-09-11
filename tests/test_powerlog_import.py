from __future__ import annotations

import sys
import unittest
from enum import IntEnum
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.powerlog_import import json_value, normalize_packet_tree, public_entity_id


class ExampleTag(IntEnum):
    DAMAGE = 44


class FullEntity(SimpleNamespace):
    pass


class TagChange(SimpleNamespace):
    pass


class Block(SimpleNamespace):
    pass


class PowerLogImportTests(unittest.TestCase):
    def test_player_reference_is_reduced_to_public_entity_id(self):
        private = SimpleNamespace(
            name="Private#1234", entity_id=7, player_id=1
        )
        self.assertEqual(7, public_entity_id(private))
        self.assertNotIn("Private", str(public_entity_id(private)))

    def test_enums_are_serialized_by_stable_name(self):
        self.assertEqual("DAMAGE", json_value(ExampleTag.DAMAGE))

    def test_normalized_tree_maps_cards_without_player_names(self):
        reveal = FullEntity(
            entity=12, card_id="TEST_001", tags=[], packet_id=1, ts=None
        )
        change = TagChange(
            entity=12, tag=ExampleTag.DAMAGE, value=1,
            packet_id=3, ts=None,
        )
        block = Block(
            entity=12, target=0, type="TRIGGER", trigger_keyword=None,
            packet_id=2, ts=None, packets=[change],
        )
        tree = SimpleNamespace(packets=[reveal, block])
        payload = normalize_packet_tree(tree)
        self.assertEqual(["TEST_001"], payload["revealed_cards"])
        self.assertEqual("TEST_001", payload["blocks"][0]["source_card"])
        self.assertEqual("TEST_001", payload["blocks"][0]["effects"][0]["card_id"])
        self.assertNotIn("Private#1234", str(payload))


if __name__ == "__main__":
    unittest.main()
