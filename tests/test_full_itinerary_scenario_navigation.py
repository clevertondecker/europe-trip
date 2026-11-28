"""Regression coverage: all UX 3.1 itinerary tabs and six specialist guides."""
import unittest
from tests.nav_helpers import open_public, open_support
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
        open_public(at,"Explorar","Descobrir")
        for task in ("Meus destinos","Organizar","Ferramentas de apoio"):
            with self.subTest(task=task):
                if task=="Ferramentas de apoio":
                    open_support(at,"Consultor de passeios")
                else:
                    open_public(at,"Planejar",task)
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)
                self.assertEqual(at.session_state["scenario_base_selected"],"offenburg")
        open_support(at,"Guias especializados")
        for guide in GUIDES:
            with self.subTest(guide=guide):
                at.selectbox(key="ux_guide_view").set_value(guide).run()
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)


if __name__=="__main__":
    unittest.main()
