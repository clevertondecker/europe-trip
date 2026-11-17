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

    def test_modern_planner_keeps_cards_without_legacy_toggle(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Meu planejamento").run()
        app.segmented_control(key="flow_active_stage").set_value("França").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("flow_show_legacy_dashboard",
                         {toggle.key for toggle in app.toggle})
        self.assertIn("flow_add_open_button",{b.key for b in app.button})
        catalog=load_attractions()
        chosen=next(a for a in catalog["attractions"] if a["destination_id"]=="colmar")
        plan=app.session_state["advisor_plan"].copy()
        plan["packages"]={"colmar":[chosen["id"]]}
        plan["assignments"]={}
        app.session_state["advisor_plan"]=plan
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        # The old, separate gallery is gone; the destination card itself
        # carries its photo, logistics and existing edit control.
        self.assertFalse(any("Lugares que escolhemos" in x.value
                             for x in app.markdown))
        self.assertIn("flow_edit_save_colmar",{b.key for b in app.button})
        self.assertTrue(any("Colmar" in x.value for x in app.markdown))
        self.assertIn("flow_add_open_button",{b.key for b in app.button})



if __name__=="__main__":
    unittest.main()
