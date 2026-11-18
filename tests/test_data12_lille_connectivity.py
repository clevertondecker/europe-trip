"""DATA12: source constraints, fallback order and DQ3.2 Lille integration."""
import unittest
from copy import deepcopy
from data12_lille_connectivity_model import (
    load_lille_connectivity,validate_lille_connectivity,
)
from dq32_macro_opportunities_model import opportunity_overview
from rail_reference_projection_model import decorate_comparison


class LilleCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_lille_connectivity()

    def test_records_are_sourced_oneway_and_not_fabricated_2027(self):
        records=self.data["records"]
        self.assertEqual(len(records),26)
        self.assertEqual(len({r["destination_id"] for r in records}),26)
        for r in records:
            self.assertEqual(r["origin_id"],"lille")
            self.assertEqual(r["direction"],"outbound_only")
            self.assertFalse(r["valid_for_2027"])
            self.assertFalse(r["return_2027_verified"])
            self.assertTrue(r["source_url"].startswith("https://"))
            self.assertGreater(r["minimum_oneway_min"],0)

    def test_bad_origin_and_future_claim_are_rejected(self):
        original={
            "schema_version":1,"scope":self.data["scope"],
            "selection_policy":"fallback_after_historical_routes7_data9_data10_data11",
            "checked_at":self.data["checked_at"],
            "records":deepcopy(self.data["records"]),
        }
        wrong=deepcopy(original)
        wrong["records"][0]["origin_id"]="mulhouse"
        with self.assertRaises(ValueError):
            validate_lille_connectivity(wrong)
        wrong=deepcopy(original)
        wrong["records"][0]["return_2027_verified"]=True
        with self.assertRaises(ValueError):
            validate_lille_connectivity(wrong)

    def test_projection_only_fills_missing_and_keeps_oneway(self):
        pair={
            "base_id":"lille","destination_id":"strasbourg",
            "evidence_status":"not_researched",
            "minimum_oneway_min":None,"source_url":None,"divergent_sources":False
        }
        cell=decorate_comparison({"rows":[pair]})["cells"][("lille","strasbourg")]
        self.assertEqual(cell["category"],"reference_only")
        self.assertEqual(cell["display_min"],183)
        self.assertTrue(cell["lille_connectivity_applied"])
        self.assertFalse(cell["valid_for_2027"])
        existing=deepcopy(pair)
        existing.update(evidence_status="historical_time",
                        minimum_oneway_min=188,
                        source_url="https://example.org/historical")
        result=decorate_comparison({"rows":[existing]})["cells"][("lille","strasbourg")]
        self.assertEqual(result["display_min"],188)
        self.assertFalse(result["lille_connectivity_applied"])

    def test_lille_screen_has_more_research_to_compare(self):
        view=opportunity_overview("lille")
        self.assertEqual(view["registry_destinations"],46)
        self.assertGreaterEqual(view["rail_reference_total_count"],28)
        cities={row["destination_id"]:row for row in view["destinations"]}
        for dest in ("strasbourg","reims","saverne","colmar",
                     "metz","nancy","thionville","rotterdam","ghent","offenburg","freiburg"):
            with self.subTest(dest=dest):
                row=cities[dest]
                self.assertNotEqual(row["status"],"unresearched_from_base")
                self.assertIsNotNone(
                    row["minimum_train_oneway_min"] or
                    row["indicative_train_oneway_min"])
                self.assertFalse(row["weekend_return_verified"])
        self.assertTrue(view["unresearched_destinations"])
        self.assertFalse(view["official_plan_modified"])


if __name__=="__main__":
    unittest.main()
