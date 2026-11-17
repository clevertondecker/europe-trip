"""The registered universe is not interchangeable with exploratory candidates."""
import unittest

from geographic_base_screening_model import geographic_screening


class GeographicScreeningTests(unittest.TestCase):
    def test_six_registered_three_exploratory(self):
        result = geographic_screening()
        self.assertEqual(len(result["registered_bases"]), 6)
        self.assertEqual(len(result["exploratory_candidates"]), 3)
        self.assertEqual(len(result["base_destination_matrix"]), 18)
        self.assertEqual(result["existing_pairs"], 18)
        self.assertEqual(result["exploratory_pairs_in_coverage"], 0)
        self.assertEqual({c["id"] for c in result["exploratory_candidates"]},
                         {"maastricht", "basel", "amsterdam"})
        self.assertTrue(all(x["registration_status"] == "registered"
                            for x in result["registered_bases"]))
        self.assertTrue(all(x["registration_status"] == "exploratory_not_registered"
                            for x in result["exploratory_candidates"]))

    def test_fixed_basket_for_all(self):
        result = geographic_screening(basket=["cologne", "aachen"])
        self.assertEqual(result["basket_ids"], ["cologne", "aachen"])
        for city in result["registered_bases"]:
            self.assertEqual(
                [x["destination_id"] for x in result["base_destination_matrix"]
                 if x["base_id"] == city["id"]], ["cologne", "aachen"])

    def test_unknown_not_treated_as_impossible(self):
        result = geographic_screening()
        rows = result["base_destination_matrix"]
        self.assertTrue(any(r["historical_oneway_station_minutes"] is None
                            for r in rows))
        self.assertTrue(all(r["journey_feasible"] is None for r in rows))
        self.assertFalse(result["ranking_available"])
        self.assertFalse(result["official_plan_modified"])
        self.assertFalse(result["wishlist_modified"])

    def test_basket_canonical_ids_and_duplicates(self):
        self.assertEqual(geographic_screening(basket=["köln"])["basket_ids"], ["cologne"])
        for basket in ([], ["cologne", "koln"], ["unknown_city"]):
            with self.subTest(basket=basket), self.assertRaises(ValueError):
                geographic_screening(basket=basket)


if __name__ == "__main__":
    unittest.main()
