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
        self.assertTrue({x["reference_kind"] for x in rows}.issubset({
            "official_operator_minimum", "secondary_route_minimum"}))
        self.assertIn("official_operator_minimum", {x["reference_kind"] for x in rows})
        for row in rows:
            with self.subTest(origin=row["origin_id"],destination=row["destination_id"]):
                if row["reference_kind"] == "official_operator_minimum":
                    self.assertTrue(row["source_url"].startswith((
                        "https://www.sncf-connect.com/train/trajet/",
                        "https://www.sncf-connect.com/train/horaires/",
                    )))
                    self.assertEqual(row["confidence"], "medium")
                else:
                    self.assertTrue(row["source_url"].startswith(
                        "https://www.thetrainline.com/en/train-times/"))
                    self.assertEqual(row["confidence"], "low")
                self.assertEqual(row["direction"],"outbound_only")
                self.assertFalse(row["return_2027_verified"])
                self.assertFalse(row["valid_for_2027"])
                self.assertTrue(1<=row["minimum_oneway_min"]<=1440)

    def test_forbidden_reverse_or_claim_and_duplicate_is_rejected(self):
        src={"schema_version":1,"scope":self.payload["scope"],
             "selection_policy":"fallback_after_historical_routes7_data9_data10_data11_data12",
             "checked_at":self.payload["checked_at"],"records":deepcopy(self.payload["records"])}
        for bad in ("future","reverse","duplicate","unknown_origin","bad_source","wrong_sncf_path","wrong_trainline_path","wrong_trainline_confidence"):
            with self.subTest(bad=bad):
                p=deepcopy(src)
                if bad=="future":p["records"][0]["valid_for_2027"]=True
                elif bad=="reverse":p["records"][0]["direction"]="both"
                elif bad=="duplicate":p["records"].append(deepcopy(p["records"][0]))
                elif bad=="unknown_origin":p["records"][0]["origin_id"]="invalid_city"
                elif bad=="wrong_sncf_path":p["records"][0]["source_url"]="https://www.sncf-connect.com/help/faq/rail/tickets"
                elif bad=="wrong_trainline_path":
                    p["records"][0]["reference_kind"]="secondary_route_minimum"
                    p["records"][0]["confidence"]="low"
                    p["records"][0]["source_url"]="https://www.thetrainline.com/en/help/contact"
                elif bad=="wrong_trainline_confidence":
                    p["records"][0]["reference_kind"]="secondary_route_minimum"
                    p["records"][0]["source_url"]="https://www.thetrainline.com/en/train-times/arlon-to-metz"
                else:p["records"][0]["source_url"]="https://example.com/travel"
                with self.assertRaises(ValueError):validate_data13(p)

    def test_shared_projection_displays_only_sourced_fallback(self):
        r={"base_id":"arlon","destination_id":"strasbourg",
           "evidence_status":"not_researched",
           "minimum_oneway_min":None,"source_url":None,"divergent_sources":False}
        result=decorate_comparison({"rows":[r]})
        cell=result["cells"][("arlon","strasbourg")]
        self.assertEqual(cell["category"],"reference_only")
        self.assertTrue(cell["data13_connectivity_applied"])
        self.assertEqual(cell["display_min"],141)
        self.assertFalse(cell["valid_for_2027"])
        self.assertFalse(cell["weekend_return_known"])
        before={**r,"minimum_oneway_min":74,"evidence_status":"historical_time",
                "source_url":"https://www.sncf-connect.com/test/historical"}
        higher=decorate_comparison({"rows":[before]})["cells"][("arlon","strasbourg")]
        self.assertEqual(higher["display_min"],74)
        self.assertFalse(higher["data13_connectivity_applied"])

    def test_secondary_source_is_not_mislabeled_as_operator(self):
        row={"base_id":"arlon","destination_id":"strasbourg",
             "evidence_status":"not_researched",
             "minimum_oneway_min":None,"source_url":None,
             "divergent_sources":False}
        cell=decorate_comparison({"rows":[row]})["cells"][("arlon","strasbourg")]
        self.assertEqual(cell["category"], "reference_only")
        self.assertTrue(cell["data13_connectivity_applied"])
        self.assertEqual(cell["source_kind"], "secondary_route_minimum")
        self.assertEqual(cell["confidence"], "low")
        self.assertIn("referência secundária", cell["label"])
        self.assertNotIn("operadora", cell["label"])

    def test_dq32_is_read_only_and_evidence_reaches_front(self):
        overview=opportunity_overview("arlon")
        match=next(x for x in overview["destinations"] if x["destination_id"]=="strasbourg")
        self.assertEqual(match["status"],"indicative_rail_reference_only")
        self.assertEqual(match["indicative_train_oneway_min"],141)
        self.assertEqual(match["indicative_source_dataset"],"data13_directed_connectivity_2026_11")
        self.assertTrue(match["indicative_source_url"].startswith("https://"))
        self.assertFalse(match["reachable_confirmed"])
        self.assertFalse(match["weekend_return_verified"])
        self.assertFalse(overview["official_plan_modified"])

    def test_data15_batches_reach_actual_discovery_projection(self):
        # Validate the *displayed* matrix, not merely new dataset row counts.
        checked=(
            ("belfort","lille",298),
            ("reims","lausanne",382),
            ("belfort","reims",235),
            ("reims","lyon",204),
            ("haguenau","mulhouse",94),
            ("haguenau","belfort",121),
            ("belfort","saint_louis",54),
            ("belfort","selestat",70),
            ("belfort","beaune",105),
            ("belfort","haguenau",146),
            ("reims","mulhouse",158),
            ("reims","metz",68),
            ("reims","besancon",289),
            ("reims","beaune",225),
            ("reims","arras",137),
            ("reims","saint_louis",204),
            ("belfort","besancon",70),
            ("saverne","saint_louis",104),
        )
        for origin,destination,minimum in checked:
            with self.subTest(pair=(origin,destination)):
                view=opportunity_overview(origin)
                row=next(x for x in view["destinations"]
                         if x["destination_id"]==destination)
                self.assertEqual(row["indicative_train_oneway_min"],minimum)
                self.assertEqual(row["indicative_source_dataset"],
                                 "data13_directed_connectivity_2026_11")
                self.assertFalse(row["weekend_return_verified"])
                self.assertFalse(row["reachable_confirmed"])
        audit=audit_coverage()
        self.assertEqual(audit["historical_plus_indicative"],544)
        self.assertEqual(audit["unresearched"],806)

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
