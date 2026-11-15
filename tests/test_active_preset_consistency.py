"""Cross-screen consistency: selected profile has a visible, prefilled preview.

The canonical TripPlan stays untouched until a traveler explicitly approves.
"""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from active_preset import active_preset
from attractions_model import load_attractions,load_base_routes
from data_model import load_data
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class ActivePresetConsistency(unittest.TestCase):
    def test_active_preset_follows_base_and_profile_without_mutating_plan(self):
        plan=new_plan()
        original=deepcopy(plan)
        catalog=load_attractions()
        routes=load_base_routes()
        trip_data=load_data()
        preview=active_preset(plan,catalog,routes,trip_data,False,6.3,7.1)
        self.assertEqual(preview["summary"]["profile"],"balanced")
        self.assertEqual(len(preview["summary"]["packages"]),4)
        self.assertEqual(len(plan["packages"]),0)
        plan["profile"]="economy"
        cheap=active_preset(plan,catalog,routes,trip_data,False,6.3,7.1)
        self.assertEqual(len(cheap["summary"]["packages"]),2)
        self.assertEqual(cheap["summary"]["profile"],"economy")
        plan["base_city"]="strasbourg"
        moved=active_preset(plan,catalog,routes,trip_data,False,6.3,7.1)
        self.assertEqual(moved["summary"]["base_city"],"strasbourg")
        self.assertEqual(original["packages"],plan["packages"])
        self.assertTrue(all(p["option"]["base_revision"]==0
                            for p in (preview,cheap,moved)))

    def test_my_outings_shows_preset_and_approval_requires_confirm(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        initial=deepcopy(app.session_state["advisor_plan"])
        text="\n".join(x.value for x in list(app.markdown)+list(app.caption))
        self.assertIn("Roteiro pré-definido · Equilibrado",text)
        self.assertIn("Pré-selecionado",text)
        self.assertIn("Passeios confirmados",text)
        self.assertIn("active_preset_start",{b.key for b in app.button})
        app.button(key="active_preset_start").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn("active_preset_confirm",{b.key for b in app.button})
        self.assertEqual(app.session_state["advisor_plan"],initial)
        app.button(key="active_preset_cancel").click().run()
        self.assertEqual(app.session_state["advisor_plan"],initial)
        app.button(key="active_preset_start").click().run()
        app.button(key="active_preset_confirm").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        official=app.session_state["advisor_plan"]
        self.assertEqual(len(official["packages"]),4)
        self.assertEqual(official["revision"],initial["revision"]+1)
        self.assertEqual(app.session_state["explore_packages"],official["packages"])
        self.assertIn("outing_edit_",",".join(b.key or "" for b in app.button))
        self.assertNotIn("active_preset_start",{b.key for b in app.button})

    def test_profile_switch_updates_preview_and_all_screens(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        app.selectbox(key="advisor_profile").set_value("economy").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["packages"],{})
        text="\n".join(x.value for x in app.markdown)
        self.assertIn("Roteiro pré-definido · Econômico",text)
        app.segmented_control(key="itinerary_section").set_value("Descobrir").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any("Roteiro Econômico sugerido" in x.value for x in app.info))
        app.segmented_control(key="itinerary_section").set_value("Calendário").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any("Roteiro Econômico sugerido" in x.value for x in app.info))
        app.segmented_control(key="itinerary_section").set_value("Visão geral").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn("flow_add_open_button",{b.key for b in app.button})
        # Old read-only advisor is still available by an explicit toggle.
        app.toggle(key="flow_show_legacy_dashboard").set_value(True).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any("Roteiro Econômico sugerido" in x.value for x in app.info))
        self.assertIn("dashboard_go_preset",{b.key for b in app.button})


if __name__=="__main__":
    unittest.main()
