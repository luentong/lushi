from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from hsa.standard_catalog import CARDS_BUILD, StandardCatalog


class StandardCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = StandardCatalog.load(ROOT / "cards.251332.enUS.json")

    def test_pinned_build_inventory_is_stable(self):
        self.assertEqual(251332, CARDS_BUILD)
        self.assertEqual(2161, len(self.catalog))
        self.assertEqual(1166, len(self.catalog.collectible()))
        self.assertEqual(995, len(self.catalog.generated_entities()))

    def test_inventory_covers_all_playable_card_types(self):
        by_type = Counter(card.card_type for card in self.catalog.collectible())
        self.assertEqual(718, by_type["MINION"])
        self.assertEqual(392, by_type["SPELL"])
        self.assertEqual(35, by_type["WEAPON"])
        self.assertEqual(19, by_type["LOCATION"])
        self.assertEqual(2, by_type["HERO"])

    def test_multiclass_cards_use_classes_field(self):
        card = self.catalog["END_001"]
        self.assertFalse(card.card_class)
        self.assertGreater(len(card.classes), 1)
        for card_class in card.classes:
            self.assertTrue(self.catalog.eligible_for_class(card.card_id, card_class))

    def test_cannoneer_metadata_preserves_trigger_without_attack_confusion(self):
        card = self.catalog["CAP_107t"]
        self.assertEqual("MINION", card.card_type)
        self.assertEqual((1, 1), (card.attack, card.health))
        self.assertIn("At the end of your turn", card.text)


if __name__ == "__main__":
    unittest.main()
