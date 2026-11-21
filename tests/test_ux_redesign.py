"""Human-readable recommendations and canonical cross-page journey."""
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from advisor_presentation import present_risks,proposal_comparison,simple_next_step
from trip_plan_model import new_plan
from planning_store import change_plan
import planning_session

ROOT=Path(__file__).resolve().parents[1]
class AdvisorPresentationTests(unittest.TestCase):
    def test_prioritizes_and_deduplicates(self):
        rows=[
            {"code":"MISSING_PRICES","severity":"WARNING","affected":"budget",
             "message":"missing","resolution":"Verificar valores","source":""},
            {"code":"OVER_BUDGET","severity":"CRITICAL","affected":"budget",
             "message":"over","resolution":"Rever despesas","source":""},
            {"code":"OVER_BUDGET","severity":"CRITICAL","affected":"budget",
             "message":"over","resolution":"Rever despesas","source":""}]
        cards=present_risks(rows)
        self.assertEqual(len(cards),2)
        self.assertEqual(cards[0]["title"],"O planejamento ultrapassou o orçamento")
        self.assertEqual(cards[0]["category"],"Orçamento")
    def test_calendar_preview_never_claims_savings(self):
        p=new_plan()
        proposal={"assignments":{"2027-09-24":"colmar"},"unresolved":[]}
        comparison=proposal_comparison(p,proposal,{"known_by_currency":{"EUR":20,"CHF":0}})
        self.assertTrue(comparison["can_apply"])
        self.assertIsNone(comparison["cost_difference_verified"])
        self.assertIn("Não há economia confirmada",comparison["claim"])
        self.assertEqual(p["assignments"],{})
    def test_empty_plan_gives_actionable_instruction(self):
        self.assertIn("escolhendo atrações",simple_next_step(new_plan(),[]))

class PlanningUXFlowTests(unittest.TestCase):
    def test_home_explore_advisor_budget_share_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=75).run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertIsNotNone(app.button(key="home_choose_attractions"))
        app.button(key="home_choose_attractions").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertEqual(app.session_state["main_navigation"],"Roteiro")
        self.assertEqual(app.session_state["itinerary_section"],"Guias e pesquisas")
        app.button(key="explore_open_colmar").click().run()
        app.button(key="explore_save_colmar").click().run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        selected=app.session_state["advisor_plan"]["packages"]
        self.assertIn("colmar",selected)
        self.assertEqual(selected,app.session_state["explore_packages"])
        app.button(key="ux_sidebar_nav_2").click().run()
        app.segmented_control(key="ux_section").set_value("Meu planejamento").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["packages"],selected)
        app.radio(key="main_navigation").set_value("Orçamento").run()
        self.assertEqual(len(app.exception),0,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["packages"],selected)
        self.assertNotIn("explore_budget_reference",app.session_state)
    def test_autosave_never_queues_without_optin(self):
        plan=new_plan()
        state={"advisor_plan":deepcopy(plan)}
        with patch.object(planning_session.st,"session_state",state):
            planning_session.update_fields(profile="economy")
            self.assertFalse(state.get("advisor_autosave_pending",False))
            state["advisor_autosave_optin"]=True
            state["advisor_public_repo_ack"]=True
            planning_session.update_fields(profile="balanced")
            # UX75: even an old opt-in to public autosave must not queue
            # publication. The explicit private opt-in is handled separately.
            self.assertFalse(state.get("advisor_autosave_pending",False))
            self.assertEqual(state["advisor_plan"]["revision"],2)

if __name__=="__main__":unittest.main()
