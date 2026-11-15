"""Scenario comparison and single-outing approval regression tests."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions,load_base_routes
from data_model import load_data
from trip_plan_model import new_plan
from travel_profile_scenarios import build_profile_scenarios
from scenario_comparison_model import scenario_comparison,comparison_table,approval_diff
from scenario_editor_model import new_board,reprice_board,change_board

ROOT=Path(__file__).resolve().parents[1]


class ScenarioComparisonModelTests(unittest.TestCase):
    def setUp(self):
        self.plan=new_plan()
        self.catalog=load_attractions()
        self.routes=load_base_routes()
        self.data=load_data()
        self.scenarios=build_profile_scenarios(
            self.plan,self.catalog,self.routes,self.data,False,6.3,7.1)

    def test_comparison_is_grounded_preserves_plan_and_limits(self):
        previous=deepcopy(self.plan)
        model=scenario_comparison(self.plan,self.scenarios,6.3,7.1)
        self.assertEqual(len(model["rows"]),3)
        self.assertEqual([x["destinations"] for x in model["rows"]],
                         [len(s["proposal_packages"]) for s in self.scenarios])
        self.assertEqual(len(comparison_table(model)),3)
        self.assertEqual(model["rows"][0]["weights"]["cost"],45)
        self.assertEqual(self.plan,previous)
        for row,scenario in zip(model["rows"],self.scenarios):
            self.assertEqual(row["pending_count"],len(scenario["missing_costs"]))
            self.assertAlmostEqual(row["total_brl"],float(scenario["financial"]["result"]["total"]))
            self.assertEqual(row["new_destinations"],
                             len(set(scenario["proposal_packages"])-set(previous["packages"])))

    def test_existing_destinations_kept_when_above_economic_capacity(self):
        previous=deepcopy(self.plan)
        for d in ("colmar","mulhouse","strasbourg"):
            attraction=next(x for x in self.catalog["attractions"] if x["destination_id"]==d)
            self.plan["packages"][d]=[attraction["id"]]
        scenarios=build_profile_scenarios(
            self.plan,self.catalog,self.routes,self.data,False,6.3,7.1)
        model=scenario_comparison(self.plan,scenarios,6.3,7.1)
        self.assertGreaterEqual(model["by_profile"]["economy"]["destinations"],3)
        self.assertTrue(set(self.plan["packages"])<=set(scenarios[0]["proposal_packages"]))
        self.assertEqual(previous["packages"],{})

    def test_finance_diff_never_mutates_canonical(self):
        previous=deepcopy(self.plan)
        proposal=self.scenarios[1]
        board=new_board(self.plan,proposal)
        sim=reprice_board(board,self.plan,self.catalog,self.routes,self.data,False,6.3,7.1)
        diff=approval_diff(self.plan,board,sim,6.3,7.1,self.catalog,self.routes)
        self.assertEqual(diff["attractions_before"],0)
        self.assertEqual(diff["attractions_after"],sum(map(len,board["packages"].values())))
        self.assertEqual(diff["new"],sorted(board["packages"]))
        self.assertEqual(self.plan,previous)


class ScenarioComparisonUITests(unittest.TestCase):
    def test_single_suggestion_adds_to_real_plan_and_reprices(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Simular roteiros").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        original=deepcopy(app.session_state["advisor_plan"])
        candidate=next(x for x in app.session_state["scenario_edit_balanced"]["packages"]
                       if x not in original["packages"])
        keys={b.key for b in app.button}
        self.assertIn("scenario_style_choose_economy",keys)
        self.assertIn("scenario_add_official_balanced_"+candidate,keys)
        app.button(key="scenario_add_official_balanced_"+candidate).click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn(candidate,app.session_state["advisor_plan"]["packages"])
        self.assertEqual(app.session_state["advisor_plan"]["revision"],original["revision"]+1)
        self.assertEqual(app.session_state["advisor_plan"]["packages"],
                         app.session_state["explore_packages"])
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        self.assertIn("outing_edit_"+candidate,{b.key for b in app.button})


if __name__=="__main__":
    unittest.main()
