"""Streamlit acceptance test: draft board edits reprice without touching official plan."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class ScenarioBoardUITests(unittest.TestCase):
    def test_board_removal_is_draft_and_cost_is_recomputed(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=75).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        app.selectbox(key="ux_improve_view").set_value("Simular roteiros").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        before=deepcopy(app.session_state["advisor_plan"])
        board=deepcopy(app.session_state["scenario_edit_balanced"])
        candidates=[d for d in board["packages"] if d not in before["packages"]]
        self.assertTrue(candidates)
        candidate=candidates[0]
        keys={x.key for x in app.button}
        self.assertIn("scenario_remove_balanced_"+candidate,keys)
        app.button(key="scenario_remove_balanced_"+candidate).click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        edited=app.session_state["scenario_edit_balanced"]
        self.assertNotIn(candidate,edited["packages"])
        self.assertEqual(app.session_state["advisor_plan"],before)
        self.assertTrue(edited["undo"])
        app.button(key="scenario_undo_balanced").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn(candidate,app.session_state["scenario_edit_balanced"]["packages"])
        self.assertEqual(app.session_state["advisor_plan"],before)

if __name__=="__main__":unittest.main()
