"""Both exploration screens consume one shared, read-only rail projection."""
from copy import deepcopy
import unittest

import rail_reference_projection_model as shared
import routes7_comparison_projection as legacy
from dq32_macro_opportunities_model import opportunity_overview
from rail_gap_enrichment_model import load_gap_enrichment
from routes7_reference_model import load_route_references


class RailProjectionConsolidationTests(unittest.TestCase):
    def test_legacy_facade_points_to_exact_same_shared_logic(self):
        self.assertIs(legacy.decorate_comparison, shared.decorate_comparison)
        self.assertIs(legacy.format_minutes, shared.format_minutes)
        self.assertIs(legacy._cached_route_gaps, shared._cached_route_gaps)

    def test_local_unknown_and_historical_reference_semantics_preserved(self):
        rows={"rows":[
            {"base_id":"strasbourg","destination_id":"strasbourg",
             "evidence_status":"local","minimum_oneway_min":None,"source_url":None},
            {"base_id":"strasbourg","destination_id":"karlsruhe",
             "evidence_status":"not_researched","minimum_oneway_min":None,"source_url":None},
            {"base_id":"lille","destination_id":"brussels",
             "evidence_status":"historical_time","minimum_oneway_min":82,
             "source_url":"https://example.org/legacy"},
        ]}
        before=deepcopy(rows)
        references=load_route_references()
        gaps=load_gap_enrichment()
        result=shared.decorate_comparison(rows,references=references,gap_overlay=gaps)
        self.assertEqual(result["total"],3)
        self.assertEqual(result["local"],1)
        self.assertEqual(result["reference_only"],1)
        self.assertEqual(result["historical"],1)
        self.assertIsNone(result["cells"][("strasbourg","strasbourg")]["display_min"])
        self.assertFalse(result["cells"][("strasbourg","strasbourg")]["weekend_return_known"])
        self.assertEqual(result["cells"][("lille","brussels")]["display_min"],82)
        self.assertEqual(result["cells"][("strasbourg","karlsruhe")]["display_min"],48)
        self.assertEqual(rows,before)

    def test_dq32_and_legacy_facade_remain_consistent_for_new_gap(self):
        row=opportunity_overview("strasbourg")
        selected=next(x for x in row["destinations"]
                      if x["destination_id"]=="karlsruhe")
        self.assertEqual(selected["status"],"indicative_rail_reference_only")
        example=legacy.decorate_comparison({"rows":[{
            "base_id":"strasbourg","destination_id":"karlsruhe",
            "evidence_status":"not_researched",
            "minimum_oneway_min":None,"source_url":None,
        }]})["cells"][("strasbourg","karlsruhe")]
        self.assertEqual(selected["indicative_train_oneway_min"],example["display_min"])
        self.assertEqual(selected["indicative_train_label"],example["label"])
        self.assertFalse(row["official_plan_modified"])


if __name__ == "__main__":
    unittest.main()
