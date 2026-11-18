import unittest
from data8_couple_cost_model import estimate_couple_excursion,load_cost_addons

def rng(a,b):
    return {"min_eur":a,"max_eur":b,"state":"user_editorial_assumption",
            "method":"user-selected planning range"}

class CoupleCostTests(unittest.TestCase):
    def test_known_free_main_and_paid_optional_tour_are_separate(self):
        result=estimate_couple_excursion(["dq32_aachen_07"],
            selected_addons=["aachen_cathedral_guided_tour"],
            intercity_couple=rng(10,20),local_couple=rng(5,15),
            dining_couple=rng(30,60),eur_to_brl=6)
        self.assertEqual(result["known_general_and_optional_eur"],17)
        self.assertEqual(result["full_scenario_range_eur"],[62,112])
        self.assertEqual(result["partial_planning_range_brl"],[372,672])
        self.assertFalse(result["valid_for_2027"])
        self.assertFalse(result["plan_mutated"])

    def test_without_transport_or_food_is_not_complete_quote(self):
        result=estimate_couple_excursion(["dq32_aachen_07"])
        self.assertIsNone(result["full_scenario_range_eur"])
        self.assertIn("intercity_couple",result["missing"])
        self.assertIn("dining_couple",result["missing"])

    def test_external_is_not_free_and_unknown_is_not_zero(self):
        r=estimate_couple_excursion(["dq32_aachen_07","dq32_aachen_08"],
            intercity_couple=rng(20,60),local_couple=rng(0,15),
            dining_couple=rng(30,70))
        self.assertIn("dq32_aachen_08",r["exterior_without_main_ticket"])
        self.assertIsNone(r["known_reference_breakdown"][1]["known_eur"])
        x=estimate_couple_excursion(["brussels_atomium"],
            intercity_couple=rng(60,100),local_couple=rng(10,30),
            dining_couple=rng(20,60))
        self.assertIn("brussels_atomium",x["exterior_without_main_ticket"])
        self.assertTrue(x["fare_counted_once_per_destination"])

    def test_unknown_ticket_does_not_suggest_full_price(self):
        result=estimate_couple_excursion(["brussels_eu_quarter"],
            intercity_couple=rng(60,120),local_couple=rng(10,20),
            dining_couple=rng(20,50))
        self.assertIn("ingresso:brussels_eu_quarter",result["missing"])
        self.assertIsNone(result["full_scenario_range_eur"])

    def test_reject_bad_scope_and_double_count(self):
        for ids in (["dq32_aachen_07","strasbourg_cathedral"],
                    ["dq32_aachen_07","dq32_aachen_07"]):
            with self.assertRaises(ValueError):
                estimate_couple_excursion(ids)
        with self.assertRaises(ValueError):
            estimate_couple_excursion(["dq32_aachen_07"],intercity_couple=rng(50,10))
        with self.assertRaises(ValueError):
            estimate_couple_excursion(["dq32_aachen_07"],eur_to_brl=0)
        self.assertEqual(len(load_cost_addons()["optional_activities"]),1)

if __name__=="__main__":
    unittest.main()
