"""Streamlit integration: discovery must work from an empty itinerary."""
import unittest
from tests.nav_helpers import open_support
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]
class DiscoveryUISmoke(unittest.TestCase):
    def test_discover_then_choose_colmar_without_auto_approval_or_gh_write(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=65).run()
        open_support(app,"Descobrir")
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertFalse(app.session_state["advisor_plan"]["packages"])
        self.assertNotIn("advisor_generate",{b.key for b in app.button})
        self.assertIn("advisor_discover_add_colmar",{b.key for b in app.button})
        app.button(key="advisor_discover_add_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertNotIn("colmar",app.session_state["advisor_plan"]["packages"])
        self.assertIn("ux45_discovery_confirm_colmar",{b.key for b in app.button})
        app.button(key="ux45_discovery_confirm_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertIn("colmar",app.session_state["advisor_plan"]["packages"])
        self.assertIn("colmar",app.session_state["explore_packages"])
        self.assertIn("discovery_go_my_outings",{b.key for b in app.button})
        self.assertTrue(any("Colmar" in item.value and "Meu planejamento" in item.value
                            for item in app.success))
        self.assertTrue(any("Projeção recalculada" in item.value for item in app.caption))
        app.button(key="discovery_go_my_outings").click().run()
        self.assertEqual(app.session_state["ux_section"],"Organizar viagem")
        self.assertEqual(app.session_state["flow_active_destination"],"colmar")
        self.assertEqual(app.session_state["flow_active_stage"],"França")
        self.assertIn("flow_edit_save_colmar",{b.key for b in app.button})
        self.assertIn("ux45_back_to_origin",{b.key for b in app.button})
        self.assertIsNone(app.session_state.get("advisor_github_sha"))
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))
        app.segmented_control(key="ux64_public_task").set_value("Organizar").run()
        app.segmented_control(key="ux120_mode").set_value("Calendário").run()
        app.segmented_control(key="ux120_calendar_layout").set_value("Completo").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn("advisor_generate",{b.key for b in app.button})

if __name__=="__main__":unittest.main()
