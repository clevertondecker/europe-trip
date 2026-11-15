"""End-to-end smoke for an unsupported-but-researched exploratory city."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


class CrossPageExplorationTests(unittest.TestCase):
    def test_offenburg_never_changes_official_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        original=app.session_state["advisor_plan"].copy()
        app.radio(key="ux_area").set_value("Explorar").run()
        app.selectbox(key="scenario_sidebar").set_value("offenburg").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"offenburg")
        self.assertEqual(app.session_state["advisor_plan"],original)

        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Explorar bases").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)

        app.radio(key="main_navigation").set_value("Orçamento").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"offenburg")
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],original["base_city"])

        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Guias e pesquisas").run()
        app.selectbox(key="attractions_scenario_base").set_value("offenburg").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],original["base_city"])


if __name__=="__main__":
    unittest.main()
