import gzip
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from compare_ppo_rollouts import compare


class ComparePpoRolloutsTests(unittest.TestCase):
    def test_only_credit_labels_may_differ(self):
        with tempfile.TemporaryDirectory() as directory:
            left = Path(directory) / "a.gz"
            right = Path(directory) / "b.gz"
            for path, advantage in ((left, 1.0), (right, -0.2)):
                with gzip.open(path, "wt", encoding="utf-8") as handle:
                    handle.write(json.dumps({"view": {"actions": [1, 2]}, "chosen": 1,
                                             "old_value": 0.1, "advantage": advantage}) + "\n")
            self.assertEqual(1, compare(left, right)["rows"])
            with gzip.open(right, "wt", encoding="utf-8") as handle:
                handle.write(json.dumps({"view": {"actions": [1, 2]}, "chosen": 0,
                                         "old_value": 0.1, "advantage": -0.2}) + "\n")
            with self.assertRaisesRegex(ValueError, "chosen"):
                compare(left, right)


if __name__ == "__main__":
    unittest.main()
