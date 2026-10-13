from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_entity_scale import training_command, disjoint_seed_ranges


class ScaleResumeTests(unittest.TestCase):
    def test_large_budget_has_no_train_development_confirmation_seed_overlap(self):
        self.assertTrue(disjoint_seed_ranges(202703010000, 32, 202801010000, 202901010000, 8, 2))
        self.assertFalse(disjoint_seed_ranges(202703010000, 32, 202704010000, 202705010000, 8, 2))
        self.assertFalse(disjoint_seed_ranges(0, 1, 200000, 200001, 8, 2))

    def test_resume_uses_latest_optimizer_checkpoint_and_original_opponent_anchor(self):
        args = SimpleNamespace(init_checkpoint=Path("anchor.pt"), device="npu:2",
            deck_config=Path("decks.json"), seed=202703010000, games_per_round=1024,
            workers=16, inference_batch_size=32, batch_size=32, epochs=2,
            learning_rate=1e-5, max_actions=400, opponent_pool_size=8)
        fresh = training_command(args, [], Path("round1.pt"))
        self.assertNotIn("--round-offset", fresh)
        self.assertEqual("minibatch", fresh[fresh.index("--kl-guard") + 1])
        args.kl_guard = "probe"
        probed = training_command(args, [], Path("probe.pt"))
        self.assertEqual("probe", probed[probed.index("--kl-guard") + 1])
        self.assertEqual("anchor.pt", fresh[fresh.index("--init-checkpoint") + 1])
        command = training_command(args, [Path("round1.pt"), Path("round2.pt")], Path("round3.pt"))
        self.assertEqual("round2.pt", command[command.index("--init-checkpoint") + 1])
        self.assertEqual("anchor.pt", command[command.index("--anchor-checkpoint") + 1])
        self.assertEqual("2", command[command.index("--round-offset") + 1])
        self.assertEqual(["round1.pt", "round2.pt"], command[command.index("--history-checkpoint") + 1:])
        self.assertEqual("1", command[command.index("--rounds") + 1])


if __name__ == "__main__":
    unittest.main()
