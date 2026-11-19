"""Fail-closed DATA16 research candidates; no claim of 2027 travel feasibility."""
from copy import deepcopy
from pathlib import Path
import unittest
from data16_three_base_attraction_model import load_data16,validate_data16
from dq32_macro_opportunities_model import load_macro_tourism

ROOT=Path(__file__).resolve().parents[1]

class Data16ThreeBaseResearchTests(unittest.TestCase):
    def setUp(self):
        self.data=load_data16()

    def test_each_city_has_five_sourced_new_candidates(self):
        self.assertEqual(validate_data16(self.data),{"bases":3,"candidates":15})
        seen={x["id"] for x in load_macro_tourism()["attractions"]}
        for candidate in self.data["attraction_candidates"]:
            self.assertNotIn(candidate["id"],seen)
            self.assertIsNone(candidate["door_to_door_min"])
            self.assertIsNone(candidate["minimum_oneway_min"])

    def test_photos_are_all_traced_and_license_not_invented(self):
        photos=[r["photo"] for r in self.data["attraction_candidates"]]
        self.assertEqual(len(photos),15)
        self.assertTrue(all(p["source_page"].startswith(
            "https://commons.wikimedia.org/wiki/File:") for p in photos))
        self.assertTrue(all(p["license_verified_for_reuse"] is False for p in photos))
        self.assertTrue(photos[-1]["contextual"])

    def test_no_source_url_is_proof_of_return_or_lodging(self):
        for row in self.data["attraction_candidates"]:
            self.assertFalse(row["return_verified_2027"])
            self.assertFalse(row["open_2027_verified"])
            self.assertIsNone(row["ticket_eur"])
        for base in self.data["base_profiles"].values():
            self.assertTrue(base["housing_note"])

    def test_invalid_research_rejected(self):
        for issue in ("fake_time","fake_fare","fake_return","fake_open","bad_url","duplicate","unknown_city"):
            with self.subTest(issue=issue):
                data=deepcopy(self.data)
                x=data["attraction_candidates"][0]
                if issue=="fake_time":x["door_to_door_min"]=10
                elif issue=="fake_fare":x["ticket_eur"]=0
                elif issue=="fake_return":x["return_verified_2027"]=True
                elif issue=="fake_open":x["open_2027_verified"]=True
                elif issue=="bad_url":x["source_url"]="https://"
                elif issue=="duplicate":data["attraction_candidates"][1]["id"]=x["id"]
                else:x["base_id"]="not_a_base"
                with self.assertRaises(ValueError):
                    validate_data16(data)

if __name__=="__main__":
    unittest.main()
