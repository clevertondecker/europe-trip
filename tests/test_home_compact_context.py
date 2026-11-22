"""Compact home is a dashboard; scenario configuration lives in task screens."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


class HomeContextTests(unittest.TestCase):
    def test_initial_home_has_no_configuration_or_extra_subnav(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertEqual(at.session_state["ux_area"],"Minha viagem")
        self.assertNotIn("scenario_sidebar",{x.key for x in at.selectbox})
        self.assertNotIn("ux_days",{x.key for x in at.number_input})
        self.assertNotIn("ux_mode",{x.key for x in at.segmented_control})
        self.assertNotIn("ux_section",{x.key for x in at.segmented_control})
        self.assertIn("home_continue_bases",{x.key for x in at.button})
        visible=" ".join(x.value for x in at.caption)
        self.assertIn("Roteiro oficial",visible)

    def test_exploration_configuration_and_home_status_are_connected(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        initial=at.session_state["advisor_plan"]["base_city"]
        at.button(key="home_continue_bases").click().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertEqual(at.session_state["ux_area"],"Explorar")
        self.assertIn("scenario_sidebar",{x.key for x in at.selectbox})
        self.assertIn("ux_days",{x.key for x in at.number_input})
        at.segmented_control(key="ux_mode").set_value("Simulação").run()
        at.selectbox(key="scenario_sidebar").set_value("offenburg").run()
        at.number_input(key="ux_days").set_value(65).run()
        at.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Minha viagem"))).click().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertNotIn("scenario_sidebar",{x.key for x in at.selectbox})
        self.assertNotIn("ux_days",{x.key for x in at.number_input})
        status=" ".join(x.value for x in at.caption)
        self.assertIn("Simulação ativa",status)
        self.assertIn("Offenburg",status)
        self.assertEqual(at.session_state["ux_days_value"],65)
        at.button(key="ux_return_official").click().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertEqual(at.session_state["ux_mode_value"],"Oficial")
        self.assertEqual(at.session_state["scenario_base_selected"],initial)
        self.assertEqual(at.session_state["advisor_plan"]["base_city"],initial)
        at.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Orçamento"))).click().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        # The budget reuses scenario context instead of duplicating controls.
        self.assertNotIn("ux_mode",{x.key for x in at.segmented_control})
        self.assertNotIn("ux_days",{x.key for x in at.number_input})
        self.assertEqual(at.session_state["ux_mode_value"],"Oficial")


if __name__=="__main__":
    unittest.main()
