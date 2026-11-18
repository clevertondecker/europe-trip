"""UX 4.5: full Explorer → official editor → Explorer Streamlit journey."""
from pathlib import Path
from copy import deepcopy
import unittest
from streamlit.testing.v1 import AppTest
from attractions_model import load_attractions

ROOT=Path(__file__).resolve().parents[1]

class ExplorerOutingContinuity(unittest.TestCase):
    def test_add_edit_return_preserves_selection_and_existing_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.slider(key="explore_max_minutes").set_value(120).run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="explore_open_strasbourg").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        attrs=[a["id"] for a in load_attractions()["attractions"]
               if a["destination_id"]=="strasbourg"]
        app.multiselect(key="explore_package_select_strasbourg").set_value(attrs[:2]).run()
        app.button(key="explore_save_strasbourg").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        planned=app.session_state["advisor_plan"]
        self.assertEqual(planned["packages"]["strasbourg"],attrs[:2])
        self.assertEqual(len(planned["packages"]),1)
        self.assertEqual(planned["base_city"],original["base_city"])
        self.assertIn("ux45_explore_to_planner",{b.key for b in app.button})
        app.button(key="ux45_explore_to_planner").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["ux_area"],"Meu roteiro")
        self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
        self.assertIn("flow_edit_save_strasbourg",{b.key for b in app.button})
        self.assertIn("ux45_back_to_origin",{b.key for b in app.button})
        app.button(key="ux45_back_to_origin").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["ux_area"],"Explorar")
        self.assertEqual(app.session_state["ux_section"],"Passeios")
        self.assertEqual(app.session_state["explore_max_minutes"],120)
        self.assertEqual(app.session_state["advisor_plan"]["packages"]["strasbourg"],attrs[:2])
        self.assertNotIn("ux45_origin",app.session_state)

if __name__=="__main__":
    unittest.main()
