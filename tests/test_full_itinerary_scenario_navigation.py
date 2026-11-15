"""Regression coverage for every itinerary tab after a hypothetical base change."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
AREAS=("Visão geral","Itália","Meus passeios","Explorar bases",
       "Descobrir","Orçamento","Calendário","Simular roteiros",
       "Guias e pesquisas")
GUIDES=("Explorar atrações","Itália e Costa Amalfitana",
        "França e escapadas","Transportes e custos",
        "Calendário de pesquisa","Cronograma oficial")


class FullItineraryNavigationTests(unittest.TestCase):
    def test_all_itinerary_areas_preserve_official_base(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        official=at.session_state["advisor_plan"]["base_city"]
        at.radio(key="ux_area").set_value("Explorar").run()
        at.selectbox(key="scenario_sidebar").set_value("offenburg").run()
        at.radio(key="main_navigation").set_value("Roteiro").run()
        for area in AREAS:
            with self.subTest(area=area):
                at.segmented_control(key="itinerary_section").set_value(area).run()
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)
                self.assertEqual(at.session_state["scenario_base_selected"],"offenburg")
        for guide in GUIDES:
            with self.subTest(guide=guide):
                at.selectbox(key="guide_section").set_value(guide).run()
                self.assertFalse(at.exception,[e.message for e in at.exception])
                self.assertEqual(at.session_state["advisor_plan"]["base_city"],official)


if __name__=="__main__":
    unittest.main()
