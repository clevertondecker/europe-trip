"""Workspace smoke tests for task-oriented Roteiro navigation."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class WorkspaceNavigationTests(unittest.TestCase):
    def test_task_navigation_preserves_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        options=["Meus passeios","Descobrir","Orçamento","Calendário"]
        original=app.session_state["advisor_plan"]["plan_id"]
        for area in options:
            app.segmented_control(key="itinerary_section").set_value(area).run()
            self.assertFalse(app.exception,area+": "+str([x.message for x in app.exception]))
            self.assertEqual(app.session_state["advisor_plan"]["plan_id"],original)
        app.segmented_control(key="itinerary_section").set_value("Guias e pesquisas").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])

if __name__=="__main__":
    unittest.main()
