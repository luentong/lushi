import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from screen_entity_external_opponents import unknown_card_entities


class ScreenTests(unittest.TestCase):
    def test_synthetic_hero_power_is_not_missing_card(self):
        view = {'entities': [{'card_id': c} for c in [None, 'CLASS_POWER:WARRIOR', 'known', 'new_card']]}
        self.assertEqual(1, unknown_card_entities(view, {'known'}))


if __name__ == '__main__':
    unittest.main()
