import copy
import unittest
from city_research_round2 import load_round2, validate_round2

class Round2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_round2()

    def test_four_cities_same_fields(self):
        self.assertEqual({x["id"] for x in self.data["cities"]},
                         {"mulhouse", "strasbourg", "metz", "nancy"})
        for city in self.data["cities"]:
            self.assertGreater(city["residential_rent_eur_sqm_month"], 0)
            self.assertGreater(city["restaurant_two_midrange_eur"], 0)

    def test_distinguishes_monthly_residential_from_short_stay(self):
        self.assertIn("não é oferta", self.data["method"]["rent"].lower())
        self.assertEqual(self.data["common_sources"][0]["as_of"], "2026-11-01")

    def test_coworking_not_falsely_ready_for_2027(self):
        for city in self.data["cities"]:
            self.assertFalse(city["coworking"]["verified_2027"])
            self.assertTrue(city["coworking"]["price_basis"])

    def test_new_city_requires_same_research_fields(self):
        invalid = copy.deepcopy(self.data)
        invalid["cities"].append({"id": "colmar"})
        with self.assertRaises((ValueError, KeyError)):
            validate_round2(invalid)

    def test_missing_cowork_schedule_may_be_unknown(self):
        metz = next(city for city in self.data["cities"] if city["id"] == "metz")
        self.assertIsNone(metz["coworking"]["schedule"])
        self.assertIsNone(metz["coworking"]["late_work_compatible"])

if __name__ == "__main__":
    unittest.main()
