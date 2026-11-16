import unittest
from trip_plan_model import new_plan
from copy import deepcopy
from dq21_travel_model import evaluate_travel_options,airport_decision_rows,load_travel_extension

class DQ21Travel(unittest.TestCase):
    def test_adds_fra_zrh_to_all_without_promoting_booking(self):
        r=evaluate_travel_options()
        self.assertEqual(len(r["cities"]),3)
        for c in r["cities"]:
            self.assertTrue({"ZRH","FRA"}<={a["airport_code"] for a in c["airport_options"]})
        self.assertTrue(all(row["complete_door_to_door_min"] is None
                       for row in airport_decision_rows(r)))
        self.assertFalse(r["flight_2027_confirmed"])
        self.assertIsNone(r["price_couple_2027"])

    def test_real_2026_rail_segment_is_not_complete_airport_trip(self):
        c=next(x for x in evaluate_travel_options()["cities"] if x["base_id"]=="freiburg")
        fra=next(x for x in c["airport_options"] if x["airport_code"]=="FRA")
        self.assertEqual(fra["known_segment_observations"][0]["minutes"],131)
        self.assertIsNone(fra["door_to_door_minutes"])

    def test_napoli_alibus_published_hours_not_guarantee(self):
        a=evaluate_travel_options(italy_variant="balanced",italy_exit_airport="NAP")
        self.assertEqual(a["naples_alibus_reference"]["service_from_nov_2026"],
                         [["06:00","09:00"],["15:00","18:00"]])
        self.assertFalse(a["naples_alibus_reference"]["confirmed_for_2027"])
        self.assertEqual(a["italy_exit_airport_hypothesis"],"NAP")

    def test_official_plan_untouched(self):
        p=new_plan()
        before=deepcopy(p)
        evaluate_travel_options(italy_variant="balanced",final_brazil_airport="GRU")
        self.assertEqual(p,before)
        with self.assertRaises(ValueError):evaluate_travel_options(italy_exit_airport="MXP")

if __name__=="__main__":unittest.main()
