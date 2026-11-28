"""Compact home is a dashboard; scenario configuration lives in task screens."""
import unittest
from nav_helpers import open_public
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
        self.assertNotIn("home_continue_bases",{x.key for x in at.button})
        self.assertIn("ux64_sidebar_nav_0",{x.key for x in at.button})
        self.assertIn("ux125_home_decisions",{x.key for x in at.button})
        visible=" ".join(x.value for x in at.caption)
        self.assertIn("Roteiro oficial",visible)

    def test_exploration_configuration_and_home_status_are_connected(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        initial=at.session_state["advisor_plan"]["base_city"]
        at.button(key="ux64_sidebar_nav_0").click().run()
        at.segmented_control(key="ux64_public_task").set_value("Comparar bases").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertEqual(at.session_state["ux_area"],"Explorar")
        self.assertNotIn("scenario_sidebar",{x.key for x in at.selectbox})
        self.assertNotIn("ux_days",{x.key for x in at.number_input})
        self.assertNotIn("ux_mode",{x.key for x in at.segmented_control})
        # Configure the same hypothetical context through the canonical simulator.
        at.button(key="ux64_sidebar_nav_2").click().run()
        at.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        at.checkbox(key="ux127_custom_simulation").check().run()
        at.selectbox(key="ux94_simulation_city").set_value("offenburg").run()
        at.slider(key="unified_stay").set_value(65).run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertEqual(at.session_state["advisor_plan"]["base_city"],initial)
        open_public(at,"Planejar","Visão geral")
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
        open_public(at,"Orçamento","Visão financeira")
        self.assertFalse(at.exception,[x.message for x in at.exception])
        # The budget reuses scenario context instead of duplicating controls.
        self.assertNotIn("ux_mode",{x.key for x in at.segmented_control})
        self.assertNotIn("ux_days",{x.key for x in at.number_input})
        self.assertEqual(at.session_state["ux_mode_value"],"Oficial")


if __name__=="__main__":
    unittest.main()
