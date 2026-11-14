import unittest
from finance_lifestyle import FRENCH_BUDGET, audit_subtotals, lifestyle_outcome

SCENARIOS = {
    "60k": {"reported_total_brl": 59975, "cap_brl": 60000, "emergency_reserve_brl": 4000},
    "70k": {"reported_total_brl": 69683, "cap_brl": 70000, "emergency_reserve_brl": 5000},
}
class LifestyleTests(unittest.TestCase):
    def test_french_subtotals_match_official_history(self):
        subtotals=audit_subtotals()
        self.assertEqual(subtotals["60k"]["french_subtotal"],23659)
        self.assertEqual(subtotals["70k"]["french_subtotal"],29427)

    def test_identical_dining_spend_preserves_original_total(self):
        for name, scenario in SCENARIOS.items():
            allocated=FRENCH_BUDGET[name]["dining"]
            weeks=FRENCH_BUDGET[name]["french_days"]/7
            price=allocated/(weeks*6.3)
            result=lifestyle_outcome(scenario,name,1,price,6.3)
            self.assertAlmostEqual(result["new_total_brl"],scenario["reported_total_brl"],places=2)

    def test_no_outings_releases_only_dining_allocation(self):
        for name,scenario in SCENARIOS.items():
            result=lifestyle_outcome(scenario,name,0,60,6.3)
            self.assertEqual(result["dining_simulated_brl"],0)
            self.assertEqual(result["new_total_brl"],scenario["reported_total_brl"]-FRENCH_BUDGET[name]["dining"])
            self.assertEqual(result["emergency_reserve_in_total_brl"],scenario["emergency_reserve_brl"])

    def test_frequent_dinners_bust_budget(self):
        out=lifestyle_outcome(SCENARIOS["70k"],"70k",3,60,6.3)
        self.assertLess(out["remaining_brl"],0)

    def test_optional_extras_only_once(self):
        a=lifestyle_outcome(SCENARIOS["60k"],"60k",1,60,6.3)
        b=lifestyle_outcome(SCENARIOS["60k"],"60k",1,60,6.3,100,200,300)
        self.assertAlmostEqual(b["new_total_brl"]-a["new_total_brl"],600)

    def test_invalid_scenario_and_amounts(self):
        with self.assertRaises(ValueError):
            lifestyle_outcome(SCENARIOS["60k"],"unknown",1,60,6.3)
        with self.assertRaises(ValueError):
            lifestyle_outcome(SCENARIOS["60k"],"60k",1,60,0)
        with self.assertRaises(ValueError):
            lifestyle_outcome(SCENARIOS["60k"],"60k",8,60,6.3)
        with self.assertRaises(ValueError):
            lifestyle_outcome(SCENARIOS["60k"],"60k",-1,60,6.3)

if __name__=="__main__":
    unittest.main()
