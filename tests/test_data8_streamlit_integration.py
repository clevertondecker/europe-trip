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

    def test_cost_simulator_inactive_does_not_set_amounts(self):
        script = ("from data8_tourism_ui import render_data8_cost_simulator\n"
                  "render_data8_cost_simulator('aachen')\n")
        app=AppTest.from_string(script).run()
        self.assertFalse(app.exception)
        self.assertEqual(len(app.checkbox),1)
        self.assertFalse(app.checkbox[0].value)

if __name__=="__main__":
    unittest.main()
