"""Regression: city-base and 60k/70k selection reprice immediately and honestly."""
import unittest
from copy import deepcopy
from data_model import load_data
from trip_plan_model import new_plan
from advisor_finance import advisor_projection,city_reference_rent

class AdvisorFinanceReactivityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.trip=load_data()
        cls.cost={"known_by_currency":{"EUR":0.0,"CHF":0.0},"missing":[]}
    def calculate(self,base="metz",scenario="70k",profile="balanced",use_city=True):
        p=new_plan(base=base,profile=profile)
        p["budget_scenario"]=scenario
        return advisor_projection(self.trip,False,p,self.cost,6.35,7.1,use_city_rent=use_city)
    def test_city_reference_is_distinct_by_base(self):
        self.assertEqual(city_reference_rent("metz"),1000)
        self.assertEqual(city_reference_rent("nancy"),900)
        metz=self.calculate("metz")
        nancy=self.calculate("nancy")
        self.assertNotEqual(metz["result"]["total"],nancy["result"]["total"])
        self.assertEqual(metz["result"]["margin"],round(70000-metz["result"]["total"],2))
        self.assertEqual(nancy["result"]["margin"],round(70000-nancy["result"]["total"],2))
    def test_budget_scenario_changes_projection(self):
        sixty=self.calculate(scenario="60k")
        seventy=self.calculate(scenario="70k")
        self.assertNotEqual(sixty["scenario"]["cap_brl"],seventy["scenario"]["cap_brl"])
        self.assertNotEqual(sixty["result"]["margin"],seventy["result"]["margin"])
    def test_no_attractions_keeps_ticket_subtotal_zero(self):
        result=self.calculate()
        self.assertEqual(result["known_billets_brl"],0)
        self.assertFalse(result["has_unknown_costs"])
    def test_profile_has_no_fictional_financial_impact(self):
        normal=self.calculate(profile="balanced")
        maximum=self.calculate(profile="experience")
        self.assertEqual(normal["result"]["total"],maximum["result"]["total"])
        self.assertFalse(maximum["profile_affects_price"])
    def test_manual_baseline_toggle_is_explicit(self):
        fixed=self.calculate("metz",use_city=False)
        rent=self.calculate("metz",use_city=True)
        self.assertIsNone(fixed["rent_eur_month"])
        self.assertNotEqual(fixed["result"]["total"],rent["result"]["total"])
        self.assertEqual(rent["city_rent_mode"],"reference_2026")
if __name__=="__main__":unittest.main()
