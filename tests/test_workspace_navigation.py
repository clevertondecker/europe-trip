"""Workspace smoke tests for task-oriented Roteiro navigation."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class WorkspaceNavigationTests(unittest.TestCase):
    def test_task_navigation_preserves_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        options=["Meus passeios","Descobrir","Orçamento","Calendário","Simular roteiros"]
        original=app.session_state["advisor_plan"]["plan_id"]
        for area in options:
            app.segmented_control(key="itinerary_section").set_value(area).run()
            self.assertFalse(app.exception,area+": "+str([x.message for x in app.exception]))
            self.assertEqual(app.session_state["advisor_plan"]["plan_id"],original)
        app.segmented_control(key="itinerary_section").set_value("Descobrir").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIsNotNone(app.selectbox(key="workspace_destination_category"))
        self.assertIsNotNone(app.selectbox(key="workspace_discovery_sort"))
        app.selectbox(key="workspace_discovery_sort").set_value("Nome (A–Z)").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.segmented_control(key="itinerary_section").set_value("Orçamento").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("scenario_review_button_balanced",{b.key for b in app.button})
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        self.assertIn("outing_add_open",{b.key for b in app.button})
        self.assertNotIn("scenario_review_button_balanced",{b.key for b in app.button})
        app.segmented_control(key="itinerary_section").set_value("Simular roteiros").run()
        self.assertIn("scenario_review_button_balanced",{b.key for b in app.button})
        app.segmented_control(key="itinerary_section").set_value("Guias e pesquisas").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])

if __name__=="__main__":
    unittest.main()
