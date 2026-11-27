import unittest
from data26b1_fare_reference_model import load_fare_references, fare_reference_coverage

class FareReferencesTest(unittest.TestCase):
    def test_production_contract(self):
        data = load_fare_references()
        result = fare_reference_coverage(data=data)
        for counts in result.values():
            self.assertLessEqual(counts["legacy"], counts["with_references"])
            self.assertLessEqual(counts["with_references"], counts["total"])

    def test_distinct_pair_union(self):
        data = {"scope": {"bases": ["mulhouse", "lille"], "destinations": ["paris"],
                          "batch_destinations": ["paris"]},
                "references": [{"origin_id": "mulhouse", "destination_id": "paris"},
                               {"origin_id": "lille", "destination_id": "paris"}]}
        legacy = {"observations": [{"origin_id": "mulhouse", "destination_id": "paris",
                   "fare_from_eur_person_oneway": 20, "source_url": "https://example.org"}]}
        result = fare_reference_coverage(data, legacy, {"records": []})["scope"]
        self.assertEqual(result, {"total": 2, "legacy": 1, "with_references": 2,
                                  "batch_references": 2, "complete_roundtrip": 0})
