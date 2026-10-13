from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]

from audit_entity_rollout_root import public_root_state
from hsa.dragon_mirror import DragonMirrorGame


class PublicRootStateTests(unittest.TestCase):
    def test_opponent_hand_is_redacted(self):
        game = DragonMirrorGame(ROOT / "cards.251332.enUS.json", 1)
        game.current = 0
        game.players[0].hand = [game._entity("GAME_005")]
        game.players[1].hand = [game._entity("JAIL_891")]
        state = public_root_state(game)
        self.assertEqual("GAME_005", state["players"][0]["hand"][0]["card"])
        self.assertEqual(1, state["players"][1]["hand_count"])
        self.assertIsNone(state["players"][1]["hand"])


if __name__ == "__main__":
    unittest.main()
