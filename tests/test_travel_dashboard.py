"""Tests for the read-only travel dashboard and its navigation."""
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions,load_base_routes
from data_model import load_data
from travel_dashboard_ui import dashboard_model
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class TravelDashboardTests(unittest.TestCase):
    def test_model_empty_plan_uses_real_projection_without_mutation(self):
        plan=new_plan()
        before=plan.copy()
        model=dashboard_model(plan,load_attractions(),load_base_routes(),
                              load_data(),False)
        self.assertEqual(model["stats"]["destinations"],0)
        self.assertEqual(model["destinations"],[])
        self.assertEqual(model["base"]["id"],plan["base_city"])
        self.assertEqual(model["unknown_costs"],0)
        self.assertIn("total",model["projection"])
        self.assertEqual(plan,before)

    def test_selected_destinations_and_assigned_dates(self):
        plan=new_plan()
        catalog=load_attractions()
        attraction=next(a for a in catalog["attractions"]
                        if a["destination_id"]=="strasbourg")
        plan["packages"]={"strasbourg":[attraction["id"]]}
        plan["assignments"]={"2027-09-26":"strasbourg"}
        model=dashboard_model(plan,catalog,load_base_routes(),load_data(),False)
        self.assertEqual(model["stats"]["destinations"],1)
        self.assertEqual(model["stats"]["scheduled_days"],1)
        self.assertEqual(model["destinations"][0]["name"],"Strasbourg")
        self.assertEqual(model["destinations"][0]["dates"],["2027-09-26"])

    def test_overview_and_navigation(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Visão geral").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("flow_add_open_button",{button.key for button in app.button})
        self.assertIn("flow_go_budget",{button.key for button in app.button})
        app.toggle(key="flow_show_legacy_dashboard").set_value(True).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("dashboard_go_budget",{button.key for button in app.button})
        self.assertIn("dashboard_go_discover",{button.key for button in app.button})
        plan_id=app.session_state["advisor_plan"]["plan_id"]
        app.button(key="dashboard_go_budget").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["plan_id"],plan_id)


if __name__=="__main__":
    unittest.main()
