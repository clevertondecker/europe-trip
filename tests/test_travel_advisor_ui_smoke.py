"""Streamlit advisor smoke: preview, reject, accept, never implicitly save."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]

class AdvisorUISmoke(unittest.TestCase):
    def test_advisor_review_and_approval_gate(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=60).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        app.selectbox(key="ux_improve_view").set_value("Descobrir").run()
        self.assertEqual(len(app.exception),0,[x.message for x in app.exception])
        original=app.session_state["advisor_plan"]["revision"]
        # A plan without selected attractions must show discovery, not fake options.
        keys={element.key for element in app.button}
        self.assertNotIn("advisor_generate",keys)
        self.assertIn("advisor_discover_add_colmar",keys)
        self.assertEqual(app.session_state["advisor_plan"]["revision"],original)
        app.selectbox(key="advisor_base").set_value("strasbourg").run()
        self.assertEqual(len(app.exception),0,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"mulhouse")
        app.button(key="advisor_confirm_base").click().run()
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"strasbourg")

if __name__=="__main__":unittest.main()
