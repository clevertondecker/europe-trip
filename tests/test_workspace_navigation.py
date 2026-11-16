"""Workspace smoke tests for task-oriented Roteiro navigation."""
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class WorkspaceNavigationTests(unittest.TestCase):
    def test_task_navigation_preserves_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=90).run()
        original=app.session_state["advisor_plan"]["plan_id"]
        flows=[
            ("Meu roteiro","Meu planejamento",None),
            ("Meu roteiro","Melhorar meu roteiro","Descobrir"),
            ("Orçamento","Simulações","Consultor de passeios"),
            ("Meu roteiro","Organizar viagem",None),
            ("Meu roteiro","Melhorar meu roteiro","Simular roteiros"),
            ("Explorar","Passeios",None),
        ]
        for area,section,detail in flows:
            with self.subTest(area=area,section=section,detail=detail):
                app.radio(key="ux_area").set_value(area).run()
                app.segmented_control(key="ux_section").set_value(section).run()
                if detail and section=="Melhorar meu roteiro":
                    app.selectbox(key="ux_improve_view").set_value(detail).run()
                elif detail=="Consultor de passeios":
                    app.segmented_control(key="ux_budget_view").set_value(detail).run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
                self.assertEqual(app.session_state["advisor_plan"]["plan_id"],original)
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Melhorar meu roteiro").run()
        app.selectbox(key="ux_improve_view").set_value("Descobrir").run()
        self.assertIsNotNone(app.selectbox(key="workspace_destination_category"))
        self.assertIsNotNone(app.selectbox(key="workspace_discovery_sort"))
        app.selectbox(key="workspace_discovery_sort").set_value("Nome (A–Z)").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.selectbox(key="ux_improve_view").set_value("Simular roteiros").run()
        self.assertIn("scenario_review_button_balanced",{b.key for b in app.button})

if __name__=="__main__":
    unittest.main()
