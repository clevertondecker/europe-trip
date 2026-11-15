"""Planning controls are visible without opening advanced help."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


class PlanningSettingsDefaultsTests(unittest.TestCase):
    def test_settings_show_style_and_preserve_option_keys(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.selectbox(key="advisor_profile").label,"Estilo de viagem")
        self.assertEqual(app.selectbox(key="advisor_profile").value,"balanced")
        app.selectbox(key="advisor_profile").set_value("economy").run()
        self.assertEqual(app.session_state["advisor_plan"]["profile"],"economy")
        self.assertFalse(app.exception,[e.message for e in app.exception])


if __name__=="__main__":
    unittest.main()
