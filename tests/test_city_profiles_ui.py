"""AppTest smoke: city profiles integrated without mutating the TripPlan."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from city_profiles_model import load_profiles,compact_comparison

ROOT=Path(__file__).resolve().parents[1]


class CityProfilesUITest(unittest.TestCase):
    def test_five_base_profiles_have_source_or_explicit_gap(self):
        data=load_profiles()
        rows=compact_comparison(data,["mulhouse","strasbourg"])
        self.assertEqual(len(rows),2)
        self.assertTrue(all(r["Estadia 2027"]=="Não confirmada" for r in rows))

    def test_exploration_with_profiles_does_not_change_tripplan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=110).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        old=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],old)


if __name__=="__main__":
    unittest.main()
