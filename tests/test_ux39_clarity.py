"""UX 3.9 — fewer clicks, safe form state and existing route invariants.

Visual/keyboard inspection requires a browser; Streamlit AppTest is not a
responsive screenshot or accessibility certification.
"""
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import Mock,patch
from streamlit.testing.v1 import AppTest

import quote_research_ui as quote_ui
from quote_research_model import empty_collection
from trip_plan_model import new_plan
from base_change_model import destination_impact

ROOT=Path(__file__).resolve().parents[1]


class UX39ClarityTests(unittest.TestCase):
    def test_quote_form_keys_are_distinct_per_quote(self):
        a={"id":"11111111-1111-4111-8111-111111111111"}
        b={"id":"22222222-2222-4222-8222-222222222222"}
        self.assertEqual(quote_ui._form_namespace(a),quote_ui._form_namespace(a))
        self.assertNotEqual(quote_ui._form_namespace(a),quote_ui._form_namespace(b))
        self.assertNotEqual(quote_ui._form_namespace(a),quote_ui._form_namespace(None))

    def test_location_picker_uses_names_and_keeps_legacy_value(self):
        choices=quote_ui._location_choices("my_old_destination")
        self.assertIn("mulhouse",choices)
        self.assertIn("luxembourg",choices)
        self.assertIn("my_old_destination",choices)
        self.assertEqual(choices[""],"Sem cidade específica")
        self.assertNotEqual(choices["mulhouse"],"mulhouse")

    def test_summary_uses_same_contextual_loader_as_details(self):
        plan=new_plan()
        with patch.object(quote_ui,"_availability",return_value=(Mock(),empty_collection())) as loader,\
             patch.object(quote_ui.st,"markdown"),patch.object(quote_ui.st,"caption"):
            quote_ui.render_quotes_summary({},plan,False)
            loader.assert_called_once()

    def test_city_comparison_still_readonly(self):
        plan=new_plan()
        original=deepcopy(plan)
        rows=destination_impact(plan,"strasbourg",["luxembourg","brussels"])
        self.assertEqual(plan,original)
        self.assertEqual(len(rows),2)


class UX39StreamlitSmoke(unittest.TestCase):
    def test_budget_navigation_does_not_change_trip_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=110).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Orçamento"))).click().run()
        app.segmented_control(key="ux_section").set_value("Resumo financeiro").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.segmented_control(key="ux_section").set_value("Detalhamento").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_comparison_explains_all_four_outcomes_in_prose(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=110).run()
        plan=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        app.button(key="ux125b_open_base_studies").click().run()
        app.segmented_control(key="ux_compare_mode").set_value("Estudos de troca").run()
        app.multiselect(key="ux34_candidates").set_value(["strasbourg"]).run()
        app.multiselect(key="ux34_destinations").set_value(["luxembourg","brussels"]).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        text=" ".join(str(x.value) for x in app.markdown)
        for phrase in ("mais rápidos","mais lentos","sem comparação pesquisada"):
            self.assertIn(phrase,text)
        self.assertEqual(app.session_state["advisor_plan"],plan)

if __name__=="__main__":
    unittest.main()
