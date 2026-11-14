import unittest
from unified_budget import resolve_french_budget, scenario_total
class UnifiedBudgetTests(unittest.TestCase):
    def setUp(self):
        self.base={"id":"70k","days":70,"cap_brl":70000,"reported_total_brl":69683,
                   "emergency_reserve_brl":5000,
                   "components":[{"name":"França · aluguel mobiliado","amount":10000},
                                 {"name":"França · supermercado","amount":8000},
                                 {"name":"França · bares e restaurantes","amount":4500},
                                 {"name":"França · transporte urbano","amount":1000},
                                 {"name":"França · passeios e viagens","amount":3000}]}
    def test_live_components_override_historical(self):
        x=resolve_french_budget(self.base,True)
        self.assertEqual(x["source"],"drive")
        self.assertEqual(x["amounts"]["dining"],4500)
    def test_snapshot_distinct(self):
        self.assertEqual(resolve_french_budget(self.base,False)["amounts"]["dining"],4954)
    def test_original_dining_replacement_not_double_counted(self):
        b=resolve_french_budget(self.base,True)
        # €750/60d/1 outing, chosen to exactly match a 4500 dining budget
        outing_price=4500/(60/7*6)
        a=scenario_total(self.base,b,french_days=60,outings_weekly=1,
                         outing_couple_eur=outing_price,fx_brl_per_eur=6)
        self.assertAlmostEqual(a["total"],69683)
        self.assertEqual(a["reserve_already_in_total"],5000)
    def test_extra_changes_only_once(self):
        b=resolve_french_budget(self.base,True)
        a=scenario_total(self.base,b,french_days=60,outings_weekly=0,
                         outing_couple_eur=60,fx_brl_per_eur=6)
        c=scenario_total(self.base,b,french_days=60,outings_weekly=0,
                         outing_couple_eur=60,fx_brl_per_eur=6,
                         flight_delta_brl=200,excursions_delta_brl=300,
                         local_transport_delta_brl=40,rent_delta_brl=60)
        self.assertAlmostEqual(c["total"]-a["total"],600)
    def test_rent_override_is_replacement_not_addition(self):
        b=resolve_french_budget(self.base,True)
        r=scenario_total(self.base,b,french_days=60,outings_weekly=0,
                         outing_couple_eur=60,fx_brl_per_eur=6,
                         rent_override_eur_month=1000)
        self.assertEqual(r["new_components"]["rent"],12000)
    def test_guard_invalid(self):
        b=resolve_french_budget(self.base,True)
        with self.assertRaises(ValueError):
            scenario_total(self.base,b,french_days=60,outings_weekly=10,
                           outing_couple_eur=60,fx_brl_per_eur=6)
    def test_uses_drive_updated_days(self):
        b=resolve_french_budget(self.base,True)
        self.assertEqual(b["french_days"],60)
    def test_no_french_data_stops_instead_of_stale(self):
        with self.assertRaises(ValueError):
            resolve_french_budget({**self.base,"components":[]},True)
if __name__=="__main__":unittest.main()
