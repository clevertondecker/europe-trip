"""D integrates A/B/C only when available; prior favorites remain functional."""
import unittest
from unittest.mock import patch
from importlib.util import find_spec
from copy import deepcopy
from dq20_comparison_model import pilot_comparison,REQUIRED_MODULES
from trip_plan_model import new_plan

class DQ20IntegrationTests(unittest.TestCase):
    def test_waits_for_source_prs_without_error(self):
        error=ModuleNotFoundError("no source",name=REQUIRED_MODULES[0])
        with patch("dq20_comparison_model.import_module",side_effect=error):
            view=pilot_comparison(["mulhouse","strasbourg"])
        self.assertEqual(view["status"],"aguardando_pesquisas")
        self.assertFalse(view["plan_mutated"])

    def test_rejects_other_cities_and_duplicates(self):
        for ids in (["mulhouse"],["mulhouse","lille"],["mulhouse","mulhouse"],
                    ["mulhouse","strasbourg","freiburg","trier"]):
            with self.subTest(ids=ids):
                with self.assertRaises(ValueError):pilot_comparison(ids)

    def test_combined_deployment_when_research_modules_exist(self):
        if any(find_spec(m) is None for m in REQUIRED_MODULES):
            self.skipTest("PRs A/B/C pending approval in independent branches")
        before=new_plan()
        original=deepcopy(before)
        view=pilot_comparison(["mulhouse","strasbourg","freiburg"],work_hours=(9,18))
        self.assertEqual(view["status"],"research_available")
        self.assertEqual(len(view["routes"]),15)
        self.assertEqual(len(view["urban"]),3)
        self.assertEqual(len(view["logistics"]),3)
        self.assertEqual(len(view["destinations"]),5)
        self.assertIsNone(view["complete_transport_minutes"])
        self.assertIsNone(view["overall_winner"])
        self.assertFalse(view["plan_mutated"])
        self.assertEqual(before,original)

    def test_streamlit_favorites_still_render_without_source_prs(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        root=Path(__file__).resolve().parents[1]
        app=AppTest.from_file(str(root/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux42_city_activity").set_value("Comparar favoritas").run()
        app.multiselect(key="ux41_favorites_widget").set_value(
            ["mulhouse","strasbourg","freiburg"]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)

if __name__=="__main__":
    unittest.main()
