import copy
import unittest
from data26b1_fare_reference_model import (
    load_fare_references, validate_fare_references, fare_reference_coverage, official_source,
)

class FareReferencesTest(unittest.TestCase):
    def setUp(self):
        self.data = load_fare_references()

    def test_production_contract(self):
        result = fare_reference_coverage(data=self.data)
        for counts in (result["scope"], result["batch"], *result["by_base"].values(), *result["by_destination"].values()):
            self.assertLessEqual(counts["legacy"], counts["with_references"])
            self.assertLessEqual(counts["with_references"], counts["total"])

    def test_sources(self):
        for domain in ("www.bahn.de", "www.sbb.ch", "www.cfl.lu", "www.belgiantrain.be", "www.nsinternational.com", "www.eurostar.com"):
            self.assertTrue(official_source("https://" + domain + "/tickets"))
        for url in ("https://bahn.de.evil.org", "http://bahn.de", "https://bahn.de@evil.org", "https://bahn.de:444"):
            self.assertFalse(official_source(url))

    def test_duplicate_alias_scope(self):
        data = copy.deepcopy(self.data)
        data["scope"]["destinations"].append("brussels")
        with self.assertRaises(ValueError):
            validate_fare_references(data)

    def test_duplicate_alias_observation(self):
        data = copy.deepcopy(self.data)
        row = copy.deepcopy(next(r for r in data["references"] if r["destination_id"] == "bruxelles"))
        row["destination_id"] = "brussels"
        data["references"].append(row)
        with self.assertRaises(ValueError):
            validate_fare_references(data)

    def test_legitimate_date_difference(self):
        data = copy.deepcopy(self.data)
        row = copy.deepcopy(next(r for r in data["references"] if r["status"] == "observed_calendar"))
        row["travel_date"] = "2027-01-09"
        data["references"].append(row)
        validate_fare_references(data)

    def test_wrong_country_and_date(self):
        for field, value in (("destination_country", "XX"), ("researched_at", "2028-01-01"), ("source_capture_date", "2028-01-01")):
            data = copy.deepcopy(self.data)
            data["references"][0][field] = value
            with self.assertRaises(ValueError):
                validate_fare_references(data)

    def test_historical_price_preserved(self):
        historical = next(r for r in self.data["references"] if r["status"] == "divergent_price")
        self.assertNotEqual(historical["amount_minor"], historical["review"]["amount_minor"])
        self.assertIsNone(historical["source_capture_date"])

    def test_gap_classification(self):
        data = copy.deepcopy(self.data)
        gap = next(r for r in data["gaps"] if r["reason"] == "research_pending")
        gap["researched_at"] = data["checked_at"]
        with self.assertRaises(ValueError):
            validate_fare_references(data)

    def test_distinct_pair_union(self):
        data = {"scope": {"bases": ["mulhouse", "lille"], "destinations": ["paris"],
                          "batch_destinations": ["paris"]},
                "references": [{"origin_id": "mulhouse", "destination_id": "paris", "status": "observed_calendar"},
                               {"origin_id": "lille", "destination_id": "paris", "status": "not_reproduced"}]}
        row = {"origin_id": "mulhouse", "destination_id": "paris",
               "fare_from_eur_person_oneway": 20, "source_url": "https://www.sncf-connect.com/train",
               "mode": "rail", "fare_conditions": "advertised", "evidence_date": "2026-11-27"}
        legacy = {"observations": [row, {**row, "origin_id": "lille", "mode": "bus"}]}
        result = fare_reference_coverage(data, legacy, {"records": []})["scope"]
        self.assertEqual(result["legacy"], 1)
        self.assertEqual(result["with_references"], 1)
        self.assertEqual(result["complete_roundtrip"], 0)

    def test_data24_parity(self):
        from data24_coverage_model import rail_coverage
        before = rail_coverage()
        fare_reference_coverage(data=self.data)
        after = rail_coverage()
        self.assertEqual(before, after)
