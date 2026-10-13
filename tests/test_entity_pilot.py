import sys
from collections import Counter
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from run_entity_pilot import jobs_for, validated_reused_jobs


class EntityPilotTests(unittest.TestCase):
    def test_reused_schedule_must_be_complete_and_identical(self):
        schedule = jobs_for(["warrior", "druid"], 1, 100)
        jobs = [dict(index=i, deck_a=a, deck_b=b, seed=s, exit_code=0)
                for i, a, b, s in schedule]
        self.assertEqual(jobs, validated_reused_jobs({"jobs": jobs}, schedule))
        for bad in (jobs[:-1], jobs + [jobs[0]],
                    [dict(jobs[0], seed=999), *jobs[1:]],
                    [dict(jobs[0], exit_code=1), *jobs[1:]]):
            with self.assertRaises(ValueError):
                validated_reused_jobs({"jobs": bad}, schedule)

    def test_all_ordered_matchups_and_seeds_are_balanced(self):
        jobs = jobs_for(["warrior", "druid"], 8, 202609291000)
        self.assertEqual(32, len(jobs))
        self.assertEqual(32, len({row[3] for row in jobs}))
        self.assertEqual({("warrior", "warrior"): 8, ("warrior", "druid"): 8,
                          ("druid", "warrior"): 8, ("druid", "druid"): 8},
                         Counter((row[1], row[2]) for row in jobs))


if __name__ == "__main__":
    unittest.main()
