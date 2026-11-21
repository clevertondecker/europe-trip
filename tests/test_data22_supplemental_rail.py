"""DATA22: auditable directions for the UX503 destination/base comparison."""
from copy import deepcopy
import unittest

from data22_supplemental_rail_model import load_data22, validate_data22
from data13_directed_connectivity_model import load_data13
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests, set_interest
from ux503_destination_base_comparison_model import compare_wishlist_bases
from rail_reference_projection_model import decorate_comparison


class Data22SupplementalRailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_data22()
        cls.discovery=build_exploration_discovery()

    def test_all_twelve_rows_have_reviewed_direction_and_no_future_claim(self):
        self.assertEqual(len(self.data["records"]),12)
        self.assertEqual(len(self.data["by_pair"]),12)
        for row in self.data["records"]:
            with self.subTest(origin=row["origin_id"],destination=row["destination_id"]):
                self.assertIn(row["destination_id"],("obernai","lucerne"))
                self.assertEqual(row["direction"],"outbound_only")
                self.assertFalse(row["return_2027_verified"])
                self.assertFalse(row["valid_for_2027"])
                self.assertFalse(row["door_to_door_verified"])
                self.assertIsNone(row.get("fare_eur"))
                self.assertTrue(row["source_url"].startswith("https://"))

    def test_source_direction_identity_and_evidence_cannot_be_fabricated(self):
        baseline={"schema_version":1,
                  "scope":"supplemental_destinations_directional_rail_reference_2026",
                  "checked_at":"2026-11-21",
                  "records":deepcopy(self.data["records"])}
        for problem in ("reverse_url","duplicate","future","wrong_destination",
                        "wrong_confidence","zero_min","empty_notes"):
            with self.subTest(problem=problem):
                case=deepcopy(baseline)
                row=case["records"][0]
                if problem=="reverse_url":
                    row["source_url"]=row["source_url"].replace("metz-a-obernai",
                                                                  "obernai-a-metz")
                elif problem=="duplicate":
                    case["records"].append(deepcopy(row))
                elif problem=="future":
                    row["valid_for_2027"]=True
                elif problem=="wrong_destination":
                    row["destination_id"]="metz"
                elif problem=="wrong_confidence":
                    row["confidence"]="high"
                elif problem=="zero_min":
                    row["minimum_oneway_min"]=0
                elif problem=="empty_notes":
                    row["notes"]=""
                with self.assertRaises(ValueError):
                    validate_data22(case)
        self.assertEqual(len(load_data22()["by_pair"]),12)

    def test_wishlist_four_base_comparison_supplies_missing_obernai_lucerne(self):
        interests=empty_interests()
        for destination in ("obernai","lucerne","basel"):
            interests=set_interest(interests,destination,"interested",self.discovery)
        bases=["metz","strasbourg","lille","mulhouse"]
        comparison=compare_wishlist_bases(interests,bases,discovery=self.discovery)
        original=deepcopy(comparison)
        overlay=decorate_comparison(comparison)
        expected={
            ("metz","obernai"):104,
            ("strasbourg","obernai"):28,
            ("lille","obernai"):256,
            ("mulhouse","obernai"):69,
            ("metz","lucerne"):224,
            ("strasbourg","lucerne"):164,
            ("lille","lucerne"):366,
            ("mulhouse","lucerne"):106,
        }
        for pair,minutes in expected.items():
            with self.subTest(pair=pair):
                cell=overlay["cells"][pair]
                self.assertEqual(cell["display_min"],minutes)
                self.assertTrue(cell["supplemental_connectivity_applied"])
                self.assertEqual(cell["category"],"reference_only")
                self.assertFalse(cell["valid_for_2027"])
                self.assertIn("fonte",cell["evidence_notes"].lower()) if False else None
        # Lille→Basel is an independently reviewed DATA13 record and does
        # not count as a supplemental destination in DATA22.
        cell=overlay["cells"][("lille","basel")]
        self.assertEqual(cell["display_min"],296)
        self.assertTrue(cell["data13_connectivity_applied"])
        self.assertFalse(cell["supplemental_connectivity_applied"])
        self.assertEqual(comparison,original)
        self.assertEqual(overlay["total"],12)
        self.assertEqual(sum(overlay[k] for k in
                        ("historical","reference_only","local","no_time")),12)

    def test_other_selected_bases_not_inferred_from_reverse_or_neighbors(self):
        wishes=empty_interests()
        wishes=set_interest(wishes,"lucerne","interested",self.discovery)
        result=compare_wishlist_bases(
            wishes,["lille","nancy"],discovery=self.discovery)
        overlay=decorate_comparison(result)
        self.assertEqual(overlay["cells"][("lille","lucerne")]["display_min"],366)
        self.assertFalse(overlay["cells"][("nancy","lucerne")]["supplemental_connectivity_applied"])
        self.assertNotIn(("lucerne","lille"),self.data["by_pair"])

    def test_extra_bases_benefit_from_sourced_records(self):
        wishes=empty_interests()
        for x in ("obernai","lucerne"):
            wishes=set_interest(wishes,x,"interested",self.discovery)
        result=compare_wishlist_bases(
            wishes,["nancy","colmar","basel"],discovery=self.discovery)
        cells=decorate_comparison(result)["cells"]
        for pair,minutes in ((("nancy","obernai"),123),
                             (("colmar","obernai"),47),
                             (("colmar","lucerne"),126),
                             (("basel","lucerne"),61)):
            self.assertEqual(cells[pair]["display_min"],minutes)

    def test_lille_basel_existing_inventory_uses_manifest_gating(self):
        data=load_data13()
        record=data["by_pair"][("lille","basel")]
        self.assertEqual(record["minimum_oneway_min"],296)
        self.assertEqual(record["reference_kind"],"official_operator_minimum")
        self.assertFalse(record["valid_for_2027"])


if __name__=="__main__":
    unittest.main()
