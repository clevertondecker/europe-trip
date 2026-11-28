"""Pilot discoveries must never become selected destinations automatically."""
import copy
import json
import tempfile
from pathlib import Path
import unittest

from tools.regional_opportunity_research_model import (
    load_regional_opportunities, opportunity_projection, DATA,
)


class RegionalOpportunityTests(unittest.TestCase):
    def test_four_source_backed_candidates_and_separate_basket(self):
        out = opportunity_projection()
        rows = out["regional_discovery_proposals"]
        self.assertEqual(len(rows), 4)
        self.assertLessEqual(len({x["corridor"] for x in rows}), 2)
        self.assertEqual({x["proposed_destination_id"] for x in rows},
                         {"maastricht", "leuven", "eguisheim", "riquewihr"})
        self.assertFalse(out["wishlist_mutated"])
        self.assertFalse(out["comparison_basket_mutated"])
        self.assertEqual(out["viable_weekend_claims"], 0)
        self.assertTrue(all(x["historical_train_time_min"] is None for x in rows))

    def test_identity_and_source_are_required(self):
        baseline = json.loads(DATA.read_text(encoding="utf-8"))
        mutations = []
        duplicate = copy.deepcopy(baseline)
        duplicate["proposals"][1]["proposed_destination_id"] = "maastricht"
        mutations.append(duplicate)
        existing = copy.deepcopy(baseline)
        existing["proposals"][0]["proposed_destination_id"] = "basel"
        mutations.append(existing)
        insecure = copy.deepcopy(baseline)
        insecure["proposals"][0]["source_url"] = "http://example.com"
        mutations.append(insecure)
        false_promise = copy.deepcopy(baseline)
        false_promise["proposals"][0]["weekend_return_verified"] = True
        mutations.append(false_promise)
        too_many = copy.deepcopy(baseline)
        too_many["proposals"].extend(copy.deepcopy(baseline["proposals"]))
        mutations.append(too_many)
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "test.json"
            for case in mutations:
                path.write_text(json.dumps(case), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_regional_opportunities(path)


if __name__ == "__main__":
    unittest.main()
