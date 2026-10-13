import sys
from pathlib import Path
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from audit_ppo_progress import summarize_round


class ProgressTests(unittest.TestCase):
    def test_rejected_minibatch_is_not_counted_as_update(self):
        row = dict(approx_kl=.01, entropy=1., value_loss=.5, update_applied=True)
        report = {'history': [{'round': 1, 'rows': 65, 'kl_early_stopped': True,
                  'updates': [row, dict(row, approx_kl=.04, update_applied=False)],
                  'opponent_versions': {'bootstrap': 2}}]}
        out = summarize_round(report, 32, 2)
        self.assertEqual(out['planned_updates'], 6)
        self.assertEqual(out['applied_updates'], 1)
        self.assertAlmostEqual(out['update_fraction'], 1/6)
        self.assertEqual(out['trigger_kl'], .04)


if __name__ == '__main__':
    unittest.main()
