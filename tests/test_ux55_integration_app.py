"""UX55 integration AppTest: existing canonical selection and navigation."""
from copy import deepcopy
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]


def open_planning():
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=110).run()
    at.button(key="ux_sidebar_nav_2").click().run()
    at.segmented_control(key="ux_section").set_value("Meu planejamento").run()
    at.button(key="flow_add_open_button").click().run()
    return at


class UX55AppIntegrationTests(unittest.TestCase):
    def test_discover_without_commit_then_select_and_edit(self):
        at = open_planning()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        before = deepcopy(at.session_state["advisor_plan"])
        at.selectbox(key="flow_add_destination").set_value("italy_amalfi").run()
        self.assertEqual(at.session_state["advisor_plan"], before)
        at.multiselect(key="flow_pick_italy_amalfi").set_value(["italy_amalfi__1"]).run()
        self.assertEqual(at.session_state["advisor_plan"], before)
        at.button(key="flow_add_confirm").click().run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        self.assertEqual(at.session_state["advisor_plan"]["revision"], before["revision"] + 1)
        at.multiselect(key="flow_pick_italy_amalfi").set_value(
            ["italy_amalfi__1", "italy_amalfi__2"]).run()
        at.button(key="flow_add_update").click().run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        self.assertEqual(len(at.session_state["advisor_plan"]["flexible_visits"][0]["attractions"]), 2)

    def test_stage_switch_and_search_destination_no_write(self):
        at = open_planning()
        before = deepcopy(at.session_state["advisor_plan"])
        at.segmented_control(key="flow_stage").set_value("França").run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        at.selectbox(key="flow_add_destination").set_value("colmar").run()
        at.text_input(key="flow_search").set_value("nancy").run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        self.assertEqual(at.session_state["advisor_plan"], before)
        at.segmented_control(key="flow_stage").set_value("Itália").run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        self.assertEqual(at.session_state["advisor_plan"], before)

    def test_max_five_and_explorer_return(self):
        at = open_planning()
        at.segmented_control(key="flow_stage").set_value("França").run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        self.assertIn("ux55_open_explorer", {b.key for b in at.button})
        before = deepcopy(at.session_state["advisor_plan"])
        at.button(key="ux55_open_explorer").click().run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        self.assertEqual(at.session_state["ux_area"], "Explorar")
        self.assertEqual(at.session_state["ux_section"], "Passeios")
        self.assertEqual(at.session_state["advisor_plan"], before)


if __name__ == "__main__":
    unittest.main()
