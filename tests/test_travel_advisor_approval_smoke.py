import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
class AdvisorApprovalIntegrationTest(unittest.TestCase):
    def test_selected_colmar_plan_is_only_applied_after_approval(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=60).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        app.button(key="explore_open_colmar").click().run()
        app.button(key="explore_save_colmar").click().run()
        self.assertIn("colmar",app.session_state["explore_packages"])
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="ux_section").set_value("Organizar viagem").run()
        app.segmented_control(key="ux_organize_view").set_value("Calendário completo").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        original=app.session_state["advisor_plan"].copy()
        app.button(key="advisor_generate").click().run()
        self.assertEqual(app.session_state["advisor_plan"]["assignments"],{})
        self.assertTrue(app.session_state["advisor_proposals"])
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        # Rejection must retain the same plan and not write GitHub
        app.button(key="advisor_reject_0").click().run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.button(key="advisor_generate").click().run()
        app.button(key="advisor_accept_0").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        plan=app.session_state["advisor_plan"]
        self.assertTrue(plan["assignments"])
        self.assertEqual(plan["revision"],original["revision"]+1)
        self.assertIsNone(app.session_state.get("advisor_github_sha"))
        self.assertIn("colmar",plan["assignments"].values())
if __name__=="__main__":unittest.main()
