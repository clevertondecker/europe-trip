"""UX94: progressive simulation keeps the official TripPlan immutable."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]


class ProgressiveBudgetAppTests(unittest.TestCase):
    def test_durations_base_and_teto_are_only_hypothetical(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        official=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("ux94_simulation_city",{x.key for x in app.selectbox})
        self.assertIn("unified_stay",{x.key for x in app.slider})
        self.assertIn("unified_outings",{x.key for x in app.slider})
        app.slider(key="unified_stay").set_value(65).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)
        app.selectbox(key="ux94_simulation_city").set_value("nancy").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["scenario_base_selected"],"nancy")
        self.assertEqual(app.session_state["advisor_plan"],official)
        changed="60k" if official["budget_scenario"]=="70k" else "70k"
        app.segmented_control(key="unified_scenario").set_value(changed).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],official)


if __name__=="__main__":
    unittest.main()
