"""Runtime smoke coverage for the new Streamlit exploration flow."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class ExplorerSmokeTests(unittest.TestCase):
    def test_route_screen_and_base_switch(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=60).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Explorar atrações").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="explore_base").set_value("strasbourg").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="explore_base").set_value("metz").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="explore_base").set_value("nancy").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.selectbox(key="explore_base").set_value("mulhouse").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])

    def test_choose_and_save_destination(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=60).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Explorar atrações").run()
        app.button(key="explore_open_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        app.button(key="explore_save_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertIn("colmar",app.session_state["explore_packages"])
if __name__=="__main__":unittest.main()
