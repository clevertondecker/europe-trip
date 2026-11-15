"""Regression coverage: all UX 3.1 itinerary tabs and six specialist guides."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from ux_navigation import GUIDES

ROOT=Path(__file__).resolve().parents[1]


class FullItineraryNavigationTests(unittest.TestCase):
    def test_all_itinerary_areas_preserve_official_base(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        official=at.session_state["advisor_plan"]["base_city"]
        at.radio(key="ux_area").set_value("Explorar").run()
        at.segmented_control(key="ux_mode").set_value("Simulação").run()
        at.selectbox(key="scenario_sidebar").set_value("offenburg").run()
        at.radio(key="ux_area").set_value("Meu roteiro").run()
        for area in ("Visão geral","Itália","França","Calendário","Sugestões"):
            with self.subTest(area=area):
                at.segmented_control(key="ux_section").set_value(area).run()
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)
                self.assertEqual(at.session_state["scenario_base_selected"],"offenburg")
        at.segmented_control(key="ux_section").set_value("Sugestões").run()
        at.segmented_control(key="ux_suggestion").set_value("Guias especializados").run()
        for guide in GUIDES:
            with self.subTest(guide=guide):
                at.selectbox(key="ux_guide_view").set_value(guide).run()
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)


if __name__=="__main__":
    unittest.main()
