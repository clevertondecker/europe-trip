"""Preset trip budgets must include concrete itineraries and require approval."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest
from data_model import load_data
from attractions_model import load_attractions,load_base_routes
from trip_plan_model import new_plan
from travel_profile_scenarios import build_profile_scenarios
from predefined_budget_model import preset_budget_summary

ROOT=Path(__file__).resolve().parents[1]


class PredefinedBudgetTests(unittest.TestCase):
    def test_every_profile_has_concrete_default_attractions_even_with_empty_plan(self):
        plan=new_plan()
        original=deepcopy(plan)
        profiles=build_profile_scenarios(plan,load_attractions(),load_base_routes(),
                                         load_data(),False,6.3,7.1)
        self.assertEqual(len(profiles),3)
        for option in profiles:
            summary=preset_budget_summary(option,plan,6.3,7.1)
            self.assertTrue(summary["packages"],option["label"])
            self.assertTrue(all(ids for ids in summary["packages"].values()))
            self.assertEqual(summary["new"],sorted(summary["packages"]))
            self.assertGreater(summary["allowance_brl"],0)
            self.assertEqual(summary["known_brl"],option["financial"]["known_billets_brl"])
        self.assertEqual(original,plan)

    def test_budget_cannot_mutate_official_before_confirmation(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="ux_area").set_value("Orçamento").run()
        app.segmented_control(key="ux_section").set_value("Simulações").run()
        app.segmented_control(key="ux_budget_view").set_value("Consultor de passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        original=deepcopy(app.session_state["advisor_plan"])
        self.assertIn("budget_preset_review_button",{b.key for b in app.button})
        app.selectbox(key="budget_preset_profile").set_value("balanced").run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.button(key="budget_preset_review_button").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertIn("budget_preset_confirm",{b.key for b in app.button})
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.button(key="budget_preset_cancel").click().run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.button(key="budget_preset_review_button").click().run()
        app.button(key="budget_preset_confirm").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertGreater(len(app.session_state["advisor_plan"]["packages"]),0)
        self.assertEqual(app.session_state["itinerary_section"],"Meus passeios")
        self.assertGreater(app.session_state["advisor_plan"]["revision"],original["revision"])
        self.assertEqual(app.session_state["advisor_plan"]["packages"],
                         app.session_state["explore_packages"])

    def test_empty_my_outings_displays_reserved_budget_and_preset_link(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=95).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        text=" ".join(x.value for x in list(app.markdown)+list(app.caption))
        self.assertIn("Quanto dos passeios já está previsto",text)
        self.assertIn("Projeção global do casal",text)
        self.assertIn("outing_go_budget_presets",{b.key for b in app.button})
        app.button(key="outing_go_budget_presets").click().run()
        self.assertEqual(app.session_state["itinerary_section"],"Orçamento")


if __name__=="__main__":
    unittest.main()
