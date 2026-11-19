"""DATA19 immutable catalog and fail-closed researched Nancy cards."""
import unittest
from copy import deepcopy
from pathlib import Path
from data19_nancy_attractions_model import load_data19,validate_data19
from attractions_model import load_attractions
from data16_commons_photo_model import parse_metadata
class NancyAttractionData19Tests(unittest.TestCase):
    def setUp(self):self.data=load_data19()
    def test_unique_details_and_no_canonical_duplicates(self):
        self.assertEqual(validate_data19(self.data),{"total":11,"city":5,"metro":1,"regional":5})
        originals=load_attractions()["attractions"]
        self.assertEqual(len([a for a in originals if a["destination_id"]=="nancy"]),6)
        self.assertFalse({x["id"] for x in self.data["attraction_candidates"]}&{a["id"] for a in originals})
    def test_all_unverified_travel_and_2027_stay_unknown(self):
        for x in self.data["attraction_candidates"]:
            self.assertGreater(len(x["description"]),65)
            for k in ("rail_minutes","last_mile_minutes","door_to_door_minutes","ticket_eur"):
                self.assertIsNone(x[k])
            self.assertFalse(x["open_2027_verified"])
            self.assertFalse(x["return_2027_verified"])
            self.assertFalse(x["photo"]["license_verified_for_reuse"])
    def test_reject_fabricated_data(self):
        for field,value in (("rail_minutes",20),("ticket_eur",0),("return_2027_verified",True),("open_2027_verified",True)):
            with self.subTest(field=field):
                copy=deepcopy(self.data)
                copy["attraction_candidates"][0][field]=value
                with self.assertRaises(ValueError):validate_data19(copy)
    def test_reject_duplicate_or_missing_photo(self):
        d=deepcopy(self.data)
        d["attraction_candidates"][1]["id"]=d["attraction_candidates"][0]["id"]
        with self.assertRaises(ValueError):validate_data19(d)
        d=deepcopy(self.data)
        d["attraction_candidates"][0]["photo"]["file_title"]=""
        with self.assertRaises(ValueError):validate_data19(d)
    def test_photo_license_gate_does_not_allow_unlicensed_media(self):
        info={"query":{"pages":{"1":{"title":"File:Example.jpg","imageinfo":[{
          "thumburl":"https://upload.wikimedia.org/test.jpg","extmetadata":{
          "Artist":{"value":"A"},"LicenseShortName":{"value":"All rights reserved"},
          "LicenseUrl":{"value":"https://example.com"}}}]}}}}
        self.assertIsNone(parse_metadata(info,"Example.jpg"))
