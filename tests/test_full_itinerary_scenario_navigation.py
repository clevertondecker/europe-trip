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
        at.button(key="ux64_sidebar_nav_2").click().run()
        at.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        at.checkbox(key="ux127_custom_simulation").check().run()
        at.selectbox(key="ux94_simulation_city").set_value("offenburg").run()
        at.button(key="ux_sidebar_nav_1").click().run()
        at.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Meu roteiro"))).click().run()
        for area in ("Meu planejamento","Organizar viagem","Melhorar meu roteiro"):
            with self.subTest(area=area):
                at.segmented_control(key="ux_section").set_value(area).run()
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)
                self.assertEqual(at.session_state["scenario_base_selected"],"offenburg")
        at.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        at.selectbox(key="ux_improve_view").set_value("Guias especializados").run()
        for guide in GUIDES:
            with self.subTest(guide=guide):
                at.selectbox(key="ux_guide_view").set_value(guide).run()
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)


if __name__=="__main__":
    unittest.main()
