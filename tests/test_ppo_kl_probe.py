import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from ppo_kl_probe import select_probe_rows, categorical_kl


class ProbeTests(unittest.TestCase):
    def test_game_balance_determinism_and_no_mutation(self):
        rows = [{'game_seed': seed, 'index': j} for seed, n in [(1, 1), (2, 100), (3, 3)] for j in range(n)]
        out = select_probe_rows(rows, 256, 7)
        self.assertEqual(len(out), 3)
        self.assertEqual({r['game_seed'] for r in out}, {1, 2, 3})
        self.assertEqual(out, select_probe_rows(rows, 256, 7))
        self.assertEqual(len(rows), 104)

    def test_exact_distribution_kl_and_padding(self):
        import torch
        old = torch.tensor([[.5, .5, 0.]]).clamp_min(1e-30).log()
        new = torch.tensor([[.8, .2, 0.]]).clamp_min(1e-30).log()
        self.assertAlmostEqual(float(categorical_kl(old, old)[0]), 0.)
        self.assertAlmostEqual(float(categorical_kl(old, new)[0]), .22314355, places=6)


if __name__ == '__main__':
    unittest.main()
