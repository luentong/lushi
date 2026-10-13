from __future__ import annotations

import sys
import unittest
from enum import IntEnum
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.powerlog_import import (
    json_value, normalize_packet_tree, public_entity_id,
    record_explicit_block_card,
)
from hsa.incremental_powerlog import IncrementalPowerLogImporter


class ExampleTag(IntEnum):
    DAMAGE = 44


class FullEntity(SimpleNamespace):
    pass


class ShowEntity(SimpleNamespace):
    pass


class TagChange(SimpleNamespace):
    pass


class Block(SimpleNamespace):
    pass


class SubSpell(SimpleNamespace):
    pass


class Options(SimpleNamespace):
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

    def test_later_reveal_does_not_backfill_earlier_packet_identity(self):
        # hslog can reuse an entity object whose card_id was populated only
        # after parsing the whole file; that object is not an early reveal.
        entity = SimpleNamespace(entity_id=12, card_id="FUTURE_001")
        early = TagChange(entity=entity, tag=ExampleTag.DAMAGE, value=0,
                          packet_id=1, ts=None)
        in_block = TagChange(entity=entity, tag=ExampleTag.DAMAGE, value=1,
                             packet_id=3, ts=None)
        block = Block(entity=entity, target=0, type="TRIGGER",
                      trigger_keyword=None, packet_id=2, ts=None,
                      packets=[in_block])
        reveal = ShowEntity(entity=entity, card_id="FUTURE_001", tags=[],
                            packet_id=4, ts=None)
        late = TagChange(entity=entity, tag=ExampleTag.DAMAGE, value=2,
                         packet_id=5, ts=None)
        payload = normalize_packet_tree(
            SimpleNamespace(packets=[early, block, reveal, late]))
        self.assertNotIn("card_id", payload["preamble"][0])
        self.assertIsNone(payload["blocks"][0]["source_card"])
        self.assertNotIn("card_id", payload["blocks"][0]["effects"][0])
        self.assertEqual("FUTURE_001", payload["preamble"][1]["card_id"])
        self.assertEqual("FUTURE_001", payload["preamble"][2]["card_id"])

    def test_incremental_reparse_keeps_earlier_identity_hidden(self):
        entity = SimpleNamespace(entity_id=42, card_id="LATER_001")
        early = TagChange(entity=entity, tag=ExampleTag.DAMAGE, value=0,
                          packet_id=1, ts=None)
        action = Block(entity=entity, target=0, type="PLAY",
                       trigger_keyword=None, packet_id=2, ts=None, packets=[])
        tree = SimpleNamespace(packets=[early, action])
        importer = IncrementalPowerLogImporter.__new__(IncrementalPowerLogImporter)
        importer._parser = SimpleNamespace(games=[tree])
        first_payload = importer.payload()
        self.assertEqual("causal_reveal_only", first_payload["identity_timing"])
        first = first_payload["games"][0]
        self.assertIsNone(first["blocks"][0]["source_card"])
        tree.packets.append(ShowEntity(
            entity=entity, card_id="LATER_001", tags=[], packet_id=3, ts=None))
        second = importer.payload()["games"][0]
        self.assertIsNone(second["blocks"][0]["source_card"])
        self.assertNotIn("card_id", second["preamble"][0])
        self.assertEqual("LATER_001", second["preamble"][1]["card_id"])

    def test_nested_block_inside_non_block_container_is_retained(self):
        nested = Block(entity=7, target=0, type="TRIGGER",
                       trigger_keyword=None, packet_id=3, ts=None,
                       packets=[TagChange(entity=7, tag=ExampleTag.DAMAGE,
                                          value=1, packet_id=4, ts=None)])
        container = SubSpell(entity=7, packet_id=2, ts=None,
                             packets=[nested])
        outer = Block(entity=7, target=0, type="PLAY",
                      trigger_keyword=None, packet_id=1, ts=None,
                      packets=[container])
        payload = normalize_packet_tree(SimpleNamespace(packets=[outer]))
        self.assertEqual(2, payload["summary"]["packet_counts"]["Block"])
        self.assertEqual(["PLAY", "TRIGGER"],
                         [block["block_type"] for block in payload["blocks"]])
        self.assertEqual(1, len(payload["blocks"][1]["effects"]))

    def test_raw_block_card_hint_is_causal_and_ignores_hidden_opponent_card(self):
        hints = {}
        record_explicit_block_card(
            "D 18:37:01.9182795 GameState.DebugPrintPower() - "
            "BLOCK_START BlockType=PLAY Entity=[entityName=private id=103 "
            "zone=HAND cardId=JAIL_436t player=1] "
            "EffectCardId=none Target=0", hints)
        record_explicit_block_card(
            "D 18:37:02.0000001 GameState.DebugPrintPower() - "
            "BLOCK_START BlockType=PLAY Entity=[entityName=UNKNOWN ENTITY "
            "id=46 zone=HAND cardId= player=2] "
            "EffectCardId=none Target=[entityName=Hero id=9 "
            "cardId=HERO_10a player=1]", hints)
        self.assertEqual({("18:37:01.918279", "PLAY", 103): "JAIL_436t"}, hints)
        early = TagChange(entity=103, tag=ExampleTag.DAMAGE, value=0,
                          packet_id=1, ts=None)
        block = Block(entity=103, target=0, type="PLAY", packet_id=2,
                      ts="18:37:01.918279", packets=[])
        payload = normalize_packet_tree(
            SimpleNamespace(packets=[early, block]), hints)
        self.assertNotIn("card_id", payload["preamble"][0])
        self.assertEqual("JAIL_436t", payload["blocks"][0]["source_card"])
        self.assertNotIn("private", str(payload))

    def test_client_options_keep_ids_and_errors_without_private_names(self):
        private = SimpleNamespace(entity_id=12, name="Private#1234")
        option = SimpleNamespace(id=2, type="POWER", entity=private,
                                 error=None, error_param=None, options=[])
        packet = Options(id=8, ts=None, options=[option])
        payload = normalize_packet_tree(SimpleNamespace(packets=[packet]))
        row = payload["preamble"][0]
        self.assertEqual(8, row["id"])
        self.assertEqual({"id": 2, "type": "POWER", "entity": 12,
                          "error": None, "error_param": None, "options": []},
                         row["options"][0])
        self.assertNotIn("Private#1234", str(payload))


if __name__ == "__main__":
    unittest.main()
