"""Runtime smoke coverage for the new Streamlit exploration flow."""
import unittest
from nav_helpers import open_public
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class ExplorerSmokeTests(unittest.TestCase):
    def test_route_screen_and_base_switch(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=60).run()
        open_public(app,"Planejar","Visão geral")
        app.button(key="ux125b_home_base_outings").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="attractions_scenario_base").set_value("strasbourg").run()
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"mulhouse")
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="attractions_scenario_base").set_value("metz").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="attractions_scenario_base").set_value("nancy").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="attractions_scenario_base").set_value("mulhouse").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])

    def test_choose_and_save_destination(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=60).run()
        open_public(app,"Planejar","Visão geral")
        app.button(key="ux125b_home_base_outings").click().run()
        app.button(key="explore_open_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.button(key="explore_save_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertIn("colmar",app.session_state["explore_packages"])
        app.button(key="explore_schedule_add").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertTrue(app.session_state["explore_calendar"])
        app.button(key="explore_to_budget").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertEqual(app.session_state["main_navigation"],"Orçamento")
        self.assertIn("explore_budget_reference",app.session_state)
if __name__=="__main__":unittest.main()
