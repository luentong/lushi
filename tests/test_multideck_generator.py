import unittest

from scripts.generate_multideck_policy_value_data import (
    _record_failed_future,
    allocate_counts,
)


class MultiDeckGeneratorTests(unittest.TestCase):
    def test_sparse_equal_weight_allocation_is_seeded_and_not_prefix_biased(self):
        weights = [1.0] * 127
        first = allocate_counts(weights, 2048, 0, tie_break_seed=20260929)
        repeated = allocate_counts(weights, 2048, 0, tie_break_seed=20260929)
        different = allocate_counts(weights, 2048, 0, tie_break_seed=20260930)

        self.assertEqual(first, repeated)
        self.assertNotEqual(first, different)
        self.assertEqual(2048, sum(first))
        self.assertTrue(all(count >= 0 for count in first))
        self.assertGreater(sum(first[32:]), 0)
        self.assertGreater(sum(first[64:]), 0)
        self.assertGreater(sum(first[96:]), 0)

    def test_failed_future_updates_manifest_index_not_pending_position(self):
        records = [{"status": "not_sampled"} for _ in range(20)]
        future = object()
        failed_index = _record_failed_future(
            records, {future: 17}, future, RuntimeError("child failed")
        )

        self.assertEqual(17, failed_index)
        self.assertEqual("failed", records[17]["status"])
        self.assertEqual("child failed", records[17]["error"])
        self.assertEqual("not_sampled", records[0]["status"])


if __name__ == "__main__":
    unittest.main()
