"""DATA13 directional source integrity, precedence and full-coverage audit."""
import unittest
from copy import deepcopy

from data13_directed_connectivity_model import load_data13, validate_data13
from rail_reference_projection_model import decorate_comparison
from dq32_macro_opportunities_model import opportunity_overview
from tools.audit_data13_coverage import audit_coverage


class Data13DirectedRailCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload=load_data13()

    def test_sourced_records_do_not_claim_return_or_2027(self):
        rows=self.payload["records"]
        self.assertGreaterEqual(len(rows),30)
        self.assertEqual(len({(x["origin_id"],x["destination_id"]) for x in rows}),len(rows))
        self.assertEqual({x["reference_kind"] for x in rows},{"official_operator_minimum"})
        for row in rows:
            with self.subTest(origin=row["origin_id"],destination=row["destination_id"]):
                self.assertTrue(
                    row["source_url"].startswith((
                        "https://www.sncf-connect.com/train/trajet/",
                        "https://www.sncf-connect.com/train/horaires/",
                    )),
                    "Only canonical SNCF route and timetable URLs are accepted",
                )
                self.assertEqual(row["direction"],"outbound_only")
                self.assertFalse(row["return_2027_verified"])
                self.assertFalse(row["valid_for_2027"])
                self.assertTrue(1<=row["minimum_oneway_min"]<=1440)

    def test_forbidden_reverse_or_claim_and_duplicate_is_rejected(self):
        src={"schema_version":1,"scope":self.payload["scope"],
             "selection_policy":"fallback_after_historical_routes7_data9_data10_data11_data12",
             "checked_at":self.payload["checked_at"],"records":deepcopy(self.payload["records"])}
        for bad in ("future","reverse","duplicate","unknown_origin","bad_source","wrong_sncf_path"):
            with self.subTest(bad=bad):
                p=deepcopy(src)
                if bad=="future":p["records"][0]["valid_for_2027"]=True
                elif bad=="reverse":p["records"][0]["direction"]="both"
                elif bad=="duplicate":p["records"].append(deepcopy(p["records"][0]))
                elif bad=="unknown_origin":p["records"][0]["origin_id"]="invalid_city"
                elif bad=="wrong_sncf_path":p["records"][0]["source_url"]="https://www.sncf-connect.com/help/faq/rail/tickets"
                else:p["records"][0]["source_url"]="https://example.com/travel"
                with self.assertRaises(ValueError):validate_data13(p)

    def test_shared_projection_displays_only_sourced_fallback(self):
        r={"base_id":"haguenau","destination_id":"saverne",
           "evidence_status":"not_researched",
           "minimum_oneway_min":None,"source_url":None,"divergent_sources":False}
        result=decorate_comparison({"rows":[r]})
        cell=result["cells"][("haguenau","saverne")]
        self.assertEqual(cell["category"],"reference_only")
        self.assertTrue(cell["data13_connectivity_applied"])
        self.assertEqual(cell["display_min"],63)
        self.assertFalse(cell["valid_for_2027"])
        self.assertFalse(cell["weekend_return_known"])
        before={**r,"minimum_oneway_min":74,"evidence_status":"historical_time",
                "source_url":"https://www.sncf-connect.com/test/historical"}
        higher=decorate_comparison({"rows":[before]})["cells"][("haguenau","saverne")]
        self.assertEqual(higher["display_min"],74)
        self.assertFalse(higher["data13_connectivity_applied"])

    def test_dq32_is_read_only_and_evidence_reaches_front(self):
        overview=opportunity_overview("haguenau")
        match=next(x for x in overview["destinations"] if x["destination_id"]=="saverne")
        self.assertEqual(match["status"],"indicative_rail_reference_only")
        self.assertEqual(match["indicative_train_oneway_min"],63)
        self.assertEqual(match["indicative_source_dataset"],"data13_directed_connectivity_2026_11")
        self.assertTrue(match["indicative_source_url"].startswith("https://"))
        self.assertFalse(match["reachable_confirmed"])
        self.assertFalse(match["weekend_return_verified"])
        self.assertFalse(overview["official_plan_modified"])

    def test_exact_matrix_and_target_gap_are_audited(self):
        out=audit_coverage()
        self.assertEqual(out["eligible_pairs"],1350)
        self.assertEqual(out["previous_coverage"],227)
        self.assertGreater(out["new_displayed_data13"],0)
        self.assertEqual(out["historical_plus_indicative"]+out["unresearched"],1350)
        self.assertEqual(out["still_needed_for_50pct"],675-out["historical_plus_indicative"])
        self.assertEqual(len(out["per_base"]),30)
        self.assertEqual(sum(x["local"] for x in out["per_base"]),30)


if __name__=="__main__":
    unittest.main()
