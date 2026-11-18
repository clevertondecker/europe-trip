"""DATA 10 — research provenance and conservative shared projection regressions."""
from copy import deepcopy
import json
import unittest

from data10_connectivity_model import DATA,load_connectivity_references,validate_connectivity_dataset
from rail_reference_projection_model import decorate_comparison
from dq32_macro_opportunities_model import opportunity_overview
from rail_gap_coverage_audit_model import build_rail_coverage_inventory


class Data10ConnectivityTests(unittest.TestCase):
    def test_all_registered_bases_and_additive_sourced_times(self):
        data=load_connectivity_references()
        self.assertEqual(len(data["records"]),99)
        self.assertEqual(len(data["by_pair"]),99)
        self.assertEqual(len({r["origin_id"] for r in data["records"]}),30)
        self.assertFalse(data["mutates_catalog"])
        self.assertEqual(data["verified_2027_services"],0)
        for r in data["records"]:
            self.assertGreater(r["minimum_oneway_min"],0)
            self.assertTrue(r["source_url"].startswith("https://"))
            self.assertFalse(r["valid_for_2027"])
            self.assertFalse(r["return_2027_verified"])

    def test_bad_provenance_local_duplicates_and_invented_2027_rejected(self):
        original=json.loads(DATA.read_text(encoding="utf-8"))
        before=deepcopy(original)
        variants=[
            ("minimum_oneway_min",0),
            ("minimum_oneway_min",True),
            ("minimum_oneway_min",1.5),
            ("source_url","https://untrusted.invalid/timetable"),
            ("source_url","http://www.sncf-connect.com/timetable"),
            ("source_checked_at","2027-01-01"),
            ("confidence","high"),
            ("reference_kind","unknown_kind"),
            ("valid_for_2027",True),
            ("return_2027_verified",True),
            ("direction","round_trip"),
            ("origin_id","invalid_base_id"),
            ("destination_id","invalid_destination_id"),
            ("destination_id",original["records"][0]["origin_id"]),
            ("origin_station_id","fabricated_hbf"),
        ]
        for key,value in variants:
            with self.subTest(key=key,value=value),self.assertRaises(ValueError):
                m=deepcopy(original)
                m["records"][0][key]=value
                validate_connectivity_dataset(m)
        repeated=deepcopy(original)
        repeated["records"].append(deepcopy(repeated["records"][0]))
        with self.assertRaises(ValueError):
            validate_connectivity_dataset(repeated)
        self.assertEqual(original,before)

    def test_known_old_rail_and_data9_win_over_data10(self):
        rows={"rows":[
            {"base_id":"lille","destination_id":"brussels",
             "evidence_status":"historical_time","minimum_oneway_min":82,
             "source_url":"https://example.org/old"},
            {"base_id":"mulhouse","destination_id":"aachen",
             "evidence_status":"not_researched","minimum_oneway_min":None,
             "source_url":None},
            {"base_id":"mulhouse","destination_id":"mulhouse",
             "evidence_status":"local","minimum_oneway_min":None,"source_url":None}
        ]}
        before=deepcopy(rows)
        result=decorate_comparison(rows)
        self.assertEqual(result["cells"][("lille","brussels")]["category"],"historical")
        self.assertFalse(result["cells"][("lille","brussels")]["connectivity_applied"])
        self.assertTrue(result["cells"][("mulhouse","aachen")]["gap_applied"])
        self.assertFalse(result["cells"][("mulhouse","aachen")]["connectivity_applied"])
        self.assertEqual(result["cells"][("mulhouse","mulhouse")]["category"],"local")
        self.assertIsNone(result["cells"][("mulhouse","mulhouse")]["display_min"])
        self.assertFalse(result["cells"][("mulhouse","mulhouse")]["connectivity_applied"])
        self.assertEqual(rows,before)

    def test_data10_directed_reference_never_proves_reverse(self):
        pair={"minimum_oneway_min":71,"source_url":"https://www.thetrainline.com/en/stations/kehl",
              "source_checked_at":"2026-11-18","confidence":"low",
              "reference_kind":"secondary_station_top_routes"}
        doc={"rows":[
            {"base_id":"unknown_origin","destination_id":"unknown_destination",
             "evidence_status":"not_researched","minimum_oneway_min":None,
             "source_url":None},
            {"base_id":"unknown_destination","destination_id":"unknown_origin",
             "evidence_status":"not_researched","minimum_oneway_min":None,
             "source_url":None},
        ]}
        result=decorate_comparison(doc,connectivity_overlay={
            "by_pair":{("unknown_origin","unknown_destination"):pair}})
        outbound=result["cells"][("unknown_origin","unknown_destination")]
        reverse=result["cells"][("unknown_destination","unknown_origin")]
        self.assertEqual(outbound["category"],"reference_only")
        self.assertTrue(outbound["connectivity_applied"])
        self.assertEqual(outbound["display_min"],71)
        self.assertFalse(outbound["valid_for_2027"])
        self.assertFalse(outbound["weekend_return_known"])
        self.assertEqual(reverse["category"],"no_time")
        self.assertIsNone(reverse["display_min"])

    def test_dq32_and_comparison_share_new_reference(self):
        for base,dest in (("mulhouse","dijon"),("strasbourg","kehl"),
                          ("arlon","luxembourg_city"),("trier","cologne")):
            with self.subTest(base=base,dest=dest):
                view=opportunity_overview(base)
                entry=next(x for x in view["destinations"] if x["destination_id"]==dest)
                cell=decorate_comparison({"rows":[{
                    "base_id":base,"destination_id":dest,"evidence_status":"not_researched",
                    "minimum_oneway_min":None,"source_url":None,
                }]})["cells"][(base,dest)]
                if entry["status"]=="indicative_rail_reference_only":
                    self.assertEqual(entry["indicative_train_oneway_min"],cell["display_min"])
                    self.assertEqual(entry["indicative_train_label"],cell["label"])
                    self.assertTrue(entry["indicative_source_url"].startswith("https://"))
                else:
                    # Previously indexed historical observations still take precedence.
                    self.assertEqual(entry["status"],"historical_train_time_only")
                    self.assertIsNotNone(entry["minimum_train_oneway_min"])
                self.assertFalse(entry["reachable_confirmed"])
                self.assertFalse(entry["weekend_return_verified"])

    def test_all_thirty_bases_improve_evidence_only_coverage(self):
        snapshot=build_rail_coverage_inventory()
        self.assertEqual((snapshot["base_count"],snapshot["destination_count"]),(30,46))
        self.assertEqual(snapshot["total_pairs"],1380)
        self.assertEqual(snapshot["local_pairs"],30)
        self.assertEqual(snapshot["historical_pairs"],54)
        self.assertGreater(snapshot["indicative_pairs"],34)
        self.assertLess(snapshot["missing_pairs"],1262)
        self.assertEqual(sum(snapshot[k] for k in
            ("historical_pairs","indicative_pairs","local_pairs","missing_pairs")),1380)
        self.assertFalse(snapshot["mutates_tripplan"])
        self.assertFalse(snapshot["fare_and_return_verified_2027"])


if __name__=="__main__":
    unittest.main()
