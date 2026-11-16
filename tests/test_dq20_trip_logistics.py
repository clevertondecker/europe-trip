"""Airport transfers are verified legs, not door-to-door flights to Brazil."""
import unittest
from dq20_trip_logistics_model import load_airport_links,compare_airport_access,airport_comparison_rows

class DQ20LogisticsTests(unittest.TestCase):
    def test_three_bases_and_multiple_options(self):
        x=compare_airport_access()
        self.assertEqual([c["base_id"] for c in x["cities"]],
                         ["mulhouse","strasbourg","freiburg"])
        self.assertGreaterEqual(len(airport_comparison_rows(x)),4)
        self.assertIsNone(x["italy_exit_candidate"])
        self.assertIsNone(x["italy_scenario_last_day_location"])

    def test_airport_leg_is_not_entire_journey(self):
        x=compare_airport_access()
        self.assertTrue(all(row["total_time_min"] is None and
                            not row["flight_brazil_verified"]
                            for row in airport_comparison_rows(x)))
        self.assertFalse(x["flight_to_brazil_from_each_airport_verified"])
        self.assertIsNone(x["roundtrip_airfare_2027_eur"])

    def test_italy_proposal_is_explicit_and_not_approved(self):
        a=compare_airport_access(itinerary_variant="balanced")
        self.assertTrue(a["italy_scenario_last_day_location"])
        self.assertIsNone(a["italy_exit_candidate"])
        self.assertFalse(a["plan_mutated"])
        with self.assertRaises(ValueError):
            compare_airport_access(itinerary_variant="not_a_scenario")
        with self.assertRaises(ValueError):
            compare_airport_access(italy_exit_candidate="Milan")

    def test_source_and_known_segment_only(self):
        raw=load_airport_links()
        self.assertEqual(raw["naples_italy_connection"]["approx_bus_minutes"],15)
        x=compare_airport_access(raw,italy_exit_candidate="naples")
        self.assertEqual(x["italy_exit_candidate"],"naples")
        freiburg=next(c for c in x["cities"] if c["base_id"]=="freiburg")
        self.assertEqual(freiburg["airport_options"][0]["known_segment_observations"][0]["approx_min_range"],[60,60])

if __name__=="__main__":
    unittest.main()
