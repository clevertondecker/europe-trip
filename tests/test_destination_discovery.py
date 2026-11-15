"""Regression suite for discovery, factual uncertainty, finance and approval."""
import unittest
from copy import deepcopy
from attractions_model import load_attractions,load_base_routes
from data_model import load_data
from trip_plan_model import new_plan
from destination_recommender import recommend_destinations
from recommended_itineraries import approve_destination,approve_profile_scenario,reject_destination
from travel_profile_scenarios import build_profile_scenarios
from travel_optimizer import propose_schedule

class DiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.routes=load_base_routes()
        cls.trip=load_data()
    def test_empty_plan_discovers_real_destinations_without_fake_calendar(self):
        plan=new_plan()
        self.assertEqual(propose_schedule(plan,self.catalog,self.routes),[])
        recs=recommend_destinations(plan,self.catalog,self.routes)
        self.assertGreater(len(recs),0)
        self.assertTrue(all(r["selected_attractions"] for r in recs))
        self.assertTrue(all(r["route_source"].startswith("https://") for r in recs))
        self.assertTrue(all(r["destination_id"]!="oeschinen" for r in recs))
    def test_exclusion_and_selected_never_recommended(self):
        plan=new_plan()
        baseline=recommend_destinations(plan,self.catalog,self.routes)
        target=baseline[0]
        modified=approve_destination(plan,target,approved=True)
        self.assertNotIn(target["destination_id"],
            {r["destination_id"] for r in recommend_destinations(modified,self.catalog,self.routes)})
        excluded=reject_destination(plan,target["destination_id"],approved=True)
        self.assertNotIn(target["destination_id"],
            {r["destination_id"] for r in recommend_destinations(excluded,self.catalog,self.routes)})
    def test_approval_changes_only_on_confirmation(self):
        plan=new_plan()
        rec=recommend_destinations(plan,self.catalog,self.routes)[0]
        self.assertEqual(approve_destination(plan,rec,False),plan)
        changed=approve_destination(plan,rec,True)
        self.assertEqual(changed["revision"],plan["revision"]+1)
        self.assertEqual(plan["packages"],{})
        with self.assertRaises(ValueError):
            approve_destination(changed,rec,True)
    def test_base_changes_discovery_route(self):
        a=recommend_destinations(new_plan(base="mulhouse"),self.catalog,self.routes)
        b=recommend_destinations(new_plan(base="metz"),self.catalog,self.routes)
        colmar_a=next(r for r in a if r["destination_id"]=="colmar")
        colmar_b=next(r for r in b if r["destination_id"]=="colmar")
        self.assertNotEqual(colmar_a["train_minutes_one_way"],colmar_b["train_minutes_one_way"])
    def test_three_scenarios_have_different_concrete_packages(self):
        plan=new_plan()
        scenarios=build_profile_scenarios(plan,self.catalog,self.routes,self.trip,
            False,6.35,7.1)
        self.assertEqual([x["profile"] for x in scenarios],["economy","balanced","experience"])
        self.assertGreater(len({tuple(x["new_destinations"]) for x in scenarios}),1)
        for scenario in scenarios:
            self.assertIs(scenario["quote_complete_for_2027"],False)
            self.assertEqual(scenario["base_revision"],plan["revision"])
            self.assertIsInstance(scenario["missing_costs"],list)
            self.assertEqual(scenario["financial"]["result"]["margin"],
                             round(scenario["financial"]["scenario"]["cap_brl"]-
                                   scenario["financial"]["result"]["total"],2))
    def test_profile_requires_explicit_acceptance_and_blocks_stale(self):
        plan=new_plan()
        proposal=build_profile_scenarios(plan,self.catalog,self.routes,self.trip,
            False,6.35,7.1)[1]
        self.assertEqual(approve_profile_scenario(plan,proposal,False),plan)
        approved=approve_profile_scenario(plan,proposal,True)
        self.assertGreater(len(approved["packages"]),0)
        self.assertEqual(plan["packages"],{})
        with self.assertRaises(ValueError):approve_profile_scenario(approved,proposal,True)
    def test_overnight_is_not_auto_confirmed(self):
        plan=new_plan()
        options=recommend_destinations(plan,self.catalog,self.routes,
                                       allow_overnight=True)
        alpine=[x for x in options if x["kind"]=="overnight"]
        self.assertTrue(alpine)
        self.assertTrue(all(x["missing"] for x in alpine))
        self.assertTrue(all(x["trip_type"]=="Pernoite a investigar" for x in alpine))

if __name__=="__main__":unittest.main()
