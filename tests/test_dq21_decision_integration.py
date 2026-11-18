import unittest
from unittest.mock import patch
from importlib.util import find_spec
from trip_plan_model import new_plan
from copy import deepcopy
from dq21_decision_model import decision_research,MODULES

class DQ21DecisionTests(unittest.TestCase):
    def test_fallback_for_unmerged_research_prs(self):
        with patch("dq21_decision_model.import_module",
                   side_effect=ModuleNotFoundError("not merged",name=MODULES[0])):
            a=decision_research(["mulhouse","strasbourg"])
        self.assertEqual(a["status"],"aguardando_modulos")
        self.assertFalse(a["plan_changed"])

    def test_invalid_city_favorites_or_one_city(self):
        for cities in (["mulhouse"],["mulhouse","mulhouse"],["mulhouse","lille"]):
            with self.subTest(cities=cities),self.assertRaises(ValueError):
                decision_research(cities)
        with self.assertRaises(ValueError):
            decision_research(["mulhouse","freiburg"],brazil_hours=(9,18))

    def test_merged_three_module_contract_and_plan_integrity(self):
        if any(find_spec(name) is None for name in MODULES):
            self.skipTest("Research PRs A/B/C remain independent")
        p=new_plan()
        original=deepcopy(p)
        j=decision_research(["mulhouse","strasbourg","freiburg"],
                            work_day="2027-10-31",brazil_hours=(9,18))
        self.assertEqual(j["status"],"available")
        self.assertEqual(len(j["routes"]),15)
        self.assertEqual(len(j["urban"]),3)
        self.assertEqual(len(j["airports"]),3)
        self.assertEqual(j["validated_weekend_trip_count"],0)
        self.assertFalse(j["all_roundtrips_to_base_2027_verified"])
        self.assertIsNone(j["ranking"])
        self.assertIsNone(j["2027_total_cost_eur"])
        self.assertEqual(p,original)

    def test_streamlit_favorites_and_original_persistence_not_lost(self):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        root=Path(__file__).resolve().parents[1]
        app=AppTest.from_file(str(root/"app.py"),default_timeout=120).run()
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux42_city_activity").set_value("Comparar favoritas").run()
        app.multiselect(key="ux41_favorites_widget").set_value(
            ["mulhouse","strasbourg","freiburg"]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("Pesquisa" in e.label for e in app.expander))

if __name__=="__main__":unittest.main()
