import unittest
from streamlit.testing.v1 import AppTest

class Data8StreamlitIntegrationTests(unittest.TestCase):
    def test_research_card_is_renderable_without_plan_mutation(self):
        script = ("from data8_tourism_ui import render_data8_attraction_details\n"
                  "render_data8_attraction_details('dq32_aachen_07')\n")
        app=AppTest.from_string(script).run()
        self.assertFalse(app.exception)
        text=" ".join(str(x.value) for x in app.get("caption"))
        self.assertIn("estimativa editorial",text)
        self.assertIn("gratuita",text)

    def test_candidate_without_id_does_not_create_catalog_card(self):
        script = ("from data8_tourism_ui import render_data8_destination_preview\n"
                  "render_data8_destination_preview('cologne')\n")
        app=AppTest.from_string(script).run()
        self.assertFalse(app.exception)
        text=" ".join(str(x.value) for x in app.get("caption"))
        self.assertIn("não cadastrada",text)

    def test_destination_preview_owns_cost_simulator(self):
        app=AppTest.from_string("from data8_tourism_ui import render_data8_destination_preview\nrender_data8_destination_preview('aachen')\n").run()
        self.assertFalse(app.exception)
        self.assertEqual(app.checkbox(key="data8_enable_cost_aachen").value,False)

    def test_cost_simulator_inactive_does_not_set_amounts(self):
        script = ("from data8_tourism_ui import render_data8_cost_simulator\n"
                  "render_data8_cost_simulator('aachen')\n")
        app=AppTest.from_string(script).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.checkbox),1)
        self.assertFalse(app.checkbox[0].value)

    def test_composed_renderer_keeps_legacy_when_data8_is_partial(self):
        script=("from data8_tourism_ui import render_composed_attraction_details\n"
                "render_composed_attraction_details({"
                "'attraction_id':'brussels_atomium','name':'Atomium',"
                "'description':'Descrição legada relevante',"
                "'why_visit':'Nota original','opening_rule':'Horário histórico',"
                "'opening_source_url':'https://example.org/hours',"
                "'ticket_main':{'amount':18,'currency':'EUR'},"
                "'additional_activity':{'name':'Visita extra','amount':4,'currency':'EUR'},"
                "'visit_minutes':90,'visit_duration_status':'historical',"
                "'last_mile_observations':[{'direction':'walk'}]})\n")
        app=AppTest.from_string(script).run()
        self.assertFalse(app.exception)
        rendered=" ".join(str(x.value) for x in app.get("caption"))
        self.assertIn("Ingresso histórico de referência: 18",rendered)
        self.assertIn("Atividade adicional do catálogo",rendered)
        self.assertIn("Duração registrada no catálogo",rendered)
        self.assertIn("Acessos históricos registrados",rendered)

    def test_interactive_external_scope_requires_user_selection(self):
        script=("from data8_tourism_ui import render_data8_cost_simulator\n"
                "render_data8_cost_simulator('aachen')\n")
        app=AppTest.from_string(script).run()
        self.assertFalse(app.exception)
        app.checkbox[0].set_value(True).run()
        self.assertFalse(app.exception)
        app.multiselect[0].set_value(["dq32_aachen_08"]).run()
        self.assertFalse(app.exception)
        self.assertEqual(app.selectbox[0].value,"unknown")
        self.assertEqual(len(app.text_input),4)
        for i, amount in enumerate(("20-40","0-10","30-50")):
            app.text_input[i].set_value(amount).run()
        self.assertFalse(app.exception)
        warnings=" ".join(str(x.value) for x in app.warning)
        self.assertIn("Estimativa incompleta",warnings)
        app.selectbox[0].set_value("external_visit").run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Cenário completo" in str(x.value) for x in app.success))

    def test_interactive_unknown_admission_cannot_become_free(self):
        script=("from data8_tourism_ui import render_data8_cost_simulator\n"
                "render_data8_cost_simulator('brussels')\n")
        app=AppTest.from_string(script).run()
        app.checkbox[0].set_value(True).run()
        app.multiselect[0].set_value(["brussels_atomium"]).run()
        app.selectbox[0].set_value("external_visit").run()
        for i, amount in enumerate(("50-90","10-20","30-60")):
            app.text_input[i].set_value(amount).run()
        self.assertFalse(app.exception)
        self.assertTrue(any("Estimativa incompleta" in str(x.value)
                            for x in app.warning))
        self.assertFalse(app.success)

if __name__=="__main__":
    unittest.main()
