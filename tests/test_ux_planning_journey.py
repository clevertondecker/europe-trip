"""Planning journey must permit direct wishlist -> draft review without comparison."""
import unittest
from copy import deepcopy
from ux_planning_journey_model import project_planning
from ux502_destination_interests_model import empty_interests,set_interest
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
from attractions_model import load_attractions
from itinerary_flow_model import add_undated_choices,FRANCE_STAGE,ITALY_STAGE

class PlanningJourneyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()
        cls.catalog=load_attractions()

    def test_filled_wishlist_prioritizes_build_not_compare(self):
        plan=new_plan()
        wishes=empty_interests()
        for d in ("paris","colmar","angers"):
            wishes=set_interest(wishes,d,"must_visit",self.discovery)
        before=deepcopy((plan,wishes))
        view=project_planning(plan,wishes,self.discovery,self.catalog)
        self.assertEqual(view["next"],"build")
        self.assertEqual(view["counts"]["wished"],3)
        self.assertEqual(view["eligible_count"],2)
        self.assertEqual([r["id"] for r in view["unsupported"]],["angers"])
        self.assertEqual((plan,wishes),before)
        added=add_undated_choices(plan,self.catalog,["paris","colmar"],FRANCE_STAGE)
        review=project_planning(added,wishes,self.discovery,self.catalog)
        self.assertEqual(review["next"],"review")
        self.assertEqual(review["counts"]["planned"],2)
        self.assertEqual(review["counts"]["organized"],0)
        self.assertEqual(len(review["pending"]),2)
        self.assertFalse(review["private_saved"])

    def test_empty_wishlist_existing_draft_is_reviewable(self):
        plan=add_undated_choices(new_plan(),self.catalog,["paris"],FRANCE_STAGE)
        self.assertEqual(project_planning(plan,empty_interests(),self.discovery,self.catalog)["next"],"review")

    def test_navigation_intent_preserves_plan_and_rejects_account_change(self):
        from ux_planning_journey_ui import request_planning,apply_planning_request
        state={"advisor_plan":new_plan(),"rec03a_identity":"owner"}
        before=deepcopy(state["advisor_plan"])
        request_planning(state,"build",FRANCE_STAGE)
        apply_planning_request(state)
        self.assertEqual(state["ux_section"],"Organizar viagem")
        self.assertEqual(state["flow_journey_stage_hint"],FRANCE_STAGE)
        self.assertEqual(state["advisor_plan"],before)
        request_planning(state,"review")
        state["rec03a_identity"]="other"
        apply_planning_request(state)
        self.assertEqual(state["flow_journey_view"],"build")
        self.assertEqual(state["advisor_plan"],before)

    def test_empty_plan_and_wishlist(self):
        view=project_planning(new_plan(),empty_interests(),self.discovery,self.catalog)
        self.assertEqual(view["next"],"choose")
        self.assertEqual(view["counts"]["planned"],0)

class PlanningJourneyAppTests(unittest.TestCase):
    def test_bulk_confirm_and_review_without_navigation(self):
        from streamlit.testing.v1 import AppTest
        from unittest.mock import patch
        discovery=build_exploration_discovery()
        wishes=empty_interests()
        for d in ("paris","colmar","angers"):
            wishes=set_interest(wishes,d,"must_visit",discovery)
        script="""
import streamlit as st
from attractions_model import load_attractions
from planning_session import active_plan
from ux_planning_journey_ui import render_planning_journey
render_planning_journey(active_plan(),load_attractions())
"""
        app=AppTest.from_string(script,default_timeout=90)
        plan=new_plan()
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.session_state["ux_area"]="Meu roteiro"
        app.session_state["ux_section"]="Meu planejamento"
        # No real cloud write; test the existing canonical review/save surface.
        with patch("continuity_ui._private_store",return_value=None):
            app.run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.button(key="flow_journey_primary").label,"Montar meu roteiro")
            app.button(key="flow_journey_primary").click().run()
            self.assertFalse(app.exception,str(app.exception))
            key="flow_journey_batch_"+FRANCE_STAGE
            app.button(key=key+"_all").click().run()
            self.assertFalse(app.exception,str(app.exception))
            self.assertEqual(app.session_state["advisor_plan"],plan)
            self.assertEqual(set(app.multiselect(key=key).value),{"paris","colmar"})
            app.button(key=key+"_confirm").click().run()
            self.assertFalse(app.exception,str(app.exception))
            current=app.session_state["advisor_plan"]
            self.assertEqual(current["revision"],plan["revision"]+1)
            self.assertEqual(current["base_city"],plan["base_city"])
            self.assertEqual(current["assignments"],{})
            self.assertEqual(app.session_state["ux502_interests"],wishes)
            self.assertEqual(app.session_state["flow_journey_view"],"review")
            self.assertEqual(app.session_state["ux_area"],"Meu roteiro")
            self.assertEqual(app.session_state["ux_section"],"Meu planejamento")
            self.assertTrue(any("Revisar e salvar meu rascunho" in x.value for x in app.markdown))
            self.assertTrue(any("Nuvem privada" in x.value for x in app.warning))

if __name__=="__main__":
    unittest.main()
