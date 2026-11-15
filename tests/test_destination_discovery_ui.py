"""Streamlit integration: discovery must work from an empty itinerary."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
class DiscoveryUISmoke(unittest.TestCase):
    def test_discover_then_choose_colmar_without_auto_approval_or_gh_write(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=65).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Descobrir").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertFalse(app.session_state["advisor_plan"]["packages"])
        self.assertNotIn("advisor_generate",{b.key for b in app.button})
        self.assertIn("advisor_discover_add_colmar",{b.key for b in app.button})
        app.button(key="advisor_discover_add_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertIn("colmar",app.session_state["advisor_plan"]["packages"])
        self.assertIn("colmar",app.session_state["explore_packages"])
        self.assertIsNone(app.session_state.get("advisor_github_sha"))
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))
        app.segmented_control(key="itinerary_section").set_value("Calendário").run()
        self.assertIn("advisor_generate",{b.key for b in app.button})

if __name__=="__main__":unittest.main()
