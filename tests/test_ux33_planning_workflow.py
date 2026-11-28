"""UX 3.3 acceptance: one settings authority, safe what-if, and continuity."""
import unittest
from nav_helpers import open_public
from copy import deepcopy
from pathlib import Path
from datetime import date
from streamlit.testing.v1 import AppTest

from trip_plan_model import new_plan
from attractions_model import load_attractions
from itinerary_flow_model import upsert_choice
from planning_workflow_model import (
    settings,preview_settings,approve_settings,compare_alternative,
    resume_target,breadcrumb,
)
from ux_navigation import SECTIONS,route,from_legacy

ROOT=Path(__file__).resolve().parents[1]


class WorkflowDomainTests(unittest.TestCase):
    def test_settings_preview_only_until_confirmed_and_preserves_itinerary(self):
        plan=new_plan()
        plan=upsert_choice(plan,load_attractions(),"italy_amalfi",
                           ["italy_amalfi__1"],"Durante a Costa Amalfitana")
        original=deepcopy(plan)
        proposal=preview_settings(plan,{
            "total_days":72,"italy_days":11,"profile":"experience",
            "budget_scenario":"60k","mandatory_destinations":["colmar"],
        })
        self.assertEqual(plan,original)
        self.assertEqual(proposal["original_revision"],plan["revision"])
        self.assertEqual(approve_settings(plan,proposal),original)
        confirmed=approve_settings(plan,proposal,confirmed=True)
        self.assertEqual(confirmed["revision"],plan["revision"]+1)
        self.assertEqual(confirmed["packages"],original["packages"])
        self.assertEqual(confirmed["flexible_visits"],original["flexible_visits"])
        self.assertEqual(confirmed["mandatory_destinations"],["colmar"])
        self.assertEqual(settings(confirmed)["budget_scenario"],"60k")
        with self.assertRaises(ValueError):
            approve_settings(confirmed,proposal,confirmed=True)

    def test_new_duration_cannot_strand_already_dated_visits(self):
        plan=new_plan()
        plan["assignments"]={"2027-11-17":"colmar"}
        with self.assertRaises(ValueError):
            preview_settings(plan,{"total_days":65})
        plan2=upsert_choice(new_plan(),load_attractions(),"italy_amalfi",
                            ["italy_amalfi__1"],"Durante a Costa Amalfitana")
        plan2["flexible_visits"][0]["exact_date"]="2027-09-18"
        with self.assertRaises(ValueError):
            preview_settings(plan2,{"italy_days":8})

    def test_exploratory_city_can_never_become_official_from_comparison(self):
        plan=new_plan()
        before=deepcopy(plan)
        comparison=compare_alternative(plan,{
            "base_city":"offenburg","total_days":72,
            "budget_scenario":"60k"})
        self.assertEqual(plan,before)
        self.assertFalse(comparison["can_apply_official"])
        self.assertEqual(comparison["alternative"]["base_city"],"offenburg")
        self.assertEqual(comparison["official"]["base_city"],"mulhouse")
        self.assertIn("hospedagem de 2027",comparison["not_quoted"])
        self.assertIn("passeios escolhidos",comparison["unchanged"])
        with self.assertRaises(ValueError):
            preview_settings(plan,{"base_city":"offenburg"})

    def test_historical_plan_recovery_and_three_itinerary_activities(self):
        plan=new_plan()
        plan.pop("flexible_visits")
        self.assertEqual(resume_target(plan)["task"],"Meu planejamento")
        plan["packages"]={"colmar":["colmar_attraction_1"]}
        self.assertEqual(resume_target(plan)["destination_id"],"colmar")
        self.assertEqual(breadcrumb("França","Colmar"),(
            "Meu roteiro","Meu planejamento","Temporada europeia","Colmar"))
        self.assertEqual(SECTIONS["Meu roteiro"],(
            "Meu planejamento","Organizar viagem","Melhorar meu roteiro"))
        self.assertEqual(from_legacy("Roteiro","Itália"),
                         ("Meu roteiro","Melhorar meu roteiro"))
        self.assertEqual(route("Meu roteiro","Organizar viagem",
                               research="Calendário completo")[1],"Calendário")


class WorkflowAppTests(unittest.TestCase):
    def test_setup_and_alternative_do_not_change_canonical_plan(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=105).run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        initial=deepcopy(at.session_state["advisor_plan"])
        at.button(key="workflow_open_settings").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        self.assertTrue(any(x.label=="Duração total (dias)" for x in at.number_input))
        self.assertEqual(at.session_state["advisor_plan"],initial)
        # Alternative review may approve settings; keep it in official planning.
        at.button(key="workflow_open_alternative").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        at.selectbox(key="workflow_alt_base").set_value("offenburg").run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        self.assertEqual(at.session_state["advisor_plan"],initial)
        self.assertIn("workflow_alt_detailed_impact",{b.key for b in at.button})
        at.button(key="workflow_alt_detailed_impact").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        self.assertEqual(at.session_state["ux_area"],"Meu roteiro")
        self.assertEqual(at.session_state["ux_section"],"Melhorar meu roteiro")
        self.assertEqual(at.session_state["ux_guide_view"],"Estudos de cidades-base")
        self.assertIn("ux34_candidates",{w.key for w in at.multiselect})
        self.assertEqual(sum(b.key=="workflow_back_to_edit" for b in at.button),1)
        self.assertEqual(at.session_state["scenario_base_selected"],"offenburg")
        self.assertEqual(at.session_state["advisor_plan"],initial)
        at.button(key="workflow_back_to_edit").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        self.assertEqual(at.session_state["ux_section"],"Meu planejamento")

    def test_open_forms_do_not_leak_into_explore(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        original=deepcopy(at.session_state["advisor_plan"])
        at.button(key="workflow_open_settings").click().run()
        self.assertTrue(any(x.label=="Duração total (dias)" for x in at.number_input))
        at.button(key="ux64_sidebar_nav_0").click().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertNotIn("workflow_settings_save",{b.key for b in at.button})
        self.assertFalse(any(x.label=="Duração total (dias)" for x in at.number_input))
        at.button(key="ux64_sidebar_nav_1").click().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertTrue(any(x.label=="Duração total (dias)" for x in at.number_input))
        self.assertEqual(at.session_state["advisor_plan"],original)

    def test_budget_legacy_city_widget_is_not_competing_with_ux94(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux64_sidebar_nav_2").click().run()
        app.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("scenario_sidebar",{x.key for x in app.selectbox})
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.button(key="ux64_sidebar_nav_0").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("scenario_sidebar",{x.key for x in app.selectbox})
        self.assertNotIn("ux_mode",{x.key for x in app.segmented_control})
        self.assertNotIn("ux_days",{x.key for x in app.number_input})
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_alternative_review_does_not_leak_into_wishlist_or_simulations(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        original=deepcopy(at.session_state["advisor_plan"])
        at.button(key="workflow_open_alternative").click().run()
        self.assertIn("workflow_alt_base",{x.key for x in at.selectbox})
        at.button(key="ux64_sidebar_nav_0").click().run()
        at.segmented_control(key="ux64_public_task").set_value("Minha lista").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertNotIn("workflow_alt_base",{x.key for x in at.selectbox})
        self.assertEqual(at.session_state["advisor_plan"],original)
        at.button(key="ux64_sidebar_nav_2").click().run()
        at.segmented_control(key="ux64_public_task").set_value("Simulações").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertNotIn("workflow_alt_base",{x.key for x in at.selectbox})
        self.assertNotIn("workflow_open_alternative",{b.key for b in at.button})
        self.assertNotIn("workflow_alt_confirm",{b.key for b in at.button})
        at.button(key="ux64_sidebar_nav_1").click().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertIn("workflow_alt_base",{x.key for x in at.selectbox})
        self.assertEqual(at.session_state["advisor_plan"],original)

    def test_resume_from_saved_in_session_destination(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=105).run()
        open_public(at,"Planejar","Organizar")
        at.button(key="flow_add_open_button").click().run()
        at.selectbox(key="flow_add_destination").set_value("italy_amalfi").run()
        at.multiselect(key="flow_pick_italy_amalfi").set_value(
            ["italy_amalfi__1"]).run()
        at.button(key="flow_add_confirm").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        open_public(at,"Planejar","Visão geral")
        self.assertIn("home_continue_planning",{b.key for b in at.button})
        at.button(key="home_continue_planning").click().run()
        self.assertFalse(at.exception,[e.message for e in at.exception])
        self.assertEqual(at.session_state["ux_area"],"Meu roteiro")
        self.assertEqual(at.session_state["ux_section"],"Meu planejamento")
        self.assertEqual(at.session_state["advisor_plan"]["flexible_visits"][0][
            "destination_id"],"italy_amalfi")


if __name__=="__main__":
    unittest.main()
