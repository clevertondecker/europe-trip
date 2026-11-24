"""UX121 overview: group-aware projection, CTA routing and no persisted writes."""
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from attractions_model import load_attractions
from trip_plan_model import new_plan
from itinerary_flow_model import add_undated_choices, FRANCE_STAGE, ITALY_STAGE
from ux502_destination_interests_model import empty_interests,set_interest
from trip01_supplemental_discovery import build_exploration_discovery
from ux_planning_journey_model import project_planning
from ux45_outing_contract import apply_outing
from ux48_weekend_groups_model import empty_groups,create_group,available_weekends
from planning_store import add_assignment


class OverviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.discovery=build_exploration_discovery()

    def setUp(self):
        self.plan=add_undated_choices(new_plan(base="metz"),self.catalog,
            ["basel","colmar","interlaken","obernai","strasbourg"],FRANCE_STAGE)
        self.wishes=set_interest(empty_interests(),"paris","interested",self.discovery)
        self.groups=empty_groups(self.plan)

    def project(self,saved=False):
        before=deepcopy((self.plan,self.wishes,self.groups))
        view=project_planning(self.plan,self.wishes,self.discovery,self.catalog,
                              private_saved=saved,weekend_groups=self.groups)
        self.assertEqual((self.plan,self.wishes,self.groups),before)
        return view

    def test_saved_undated_trip_has_same_next_action(self):
        for saved in (False,True):
            view=self.project(saved)
            self.assertEqual(view["next"],"organize")
            self.assertEqual(view["next_stage"],FRANCE_STAGE)
            self.assertEqual((view["counts"]["planned"],view["counts"]["organized"],len(view["pending"])),(5,0,5))
            self.assertEqual(view["stages"][ITALY_STAGE]["days"],10)
            self.assertEqual(view["stages"][FRANCE_STAGE]["days"],60)
            self.assertEqual(view["stages"][ITALY_STAGE]["planned"],0)
            self.assertEqual(view["unsupported"][0]["id"],"paris")
            self.assertFalse(view["commitments"])

    def test_group_interval_is_not_individual_commitment(self):
        self.plan,_=apply_outing(self.plan,self.catalog,"colmar",[],"Férias restantes",confirmed=True)
        dates=[r["start"] for r in available_weekends(self.groups,self.plan,self.catalog)
               if r["status"]=="livre · não reservado"]
        self.plan=add_assignment(self.plan,dates[-1],"strasbourg")
        self.groups=create_group(self.groups,self.plan,self.catalog,name="Suíça",
                                 destinations=["basel","interlaken"])
        self.assertEqual(self.project()["counts"]["organized"],2)
        from ux48_weekend_groups_model import update_group
        self.groups=update_group(self.groups,self.plan,self.catalog,self.groups["groups"][0]["id"],
                                 start_date=dates[0])
        view=self.project(True)
        self.assertEqual(view["counts"]["organized"],4)
        self.assertEqual(view["counts"]["dated"],1)
        self.assertEqual(len(view["commitments"]),2)
        self.assertEqual([e["kind"] for e in view["commitments"]],["group","individual"])
        self.assertEqual(view["stages"][FRANCE_STAGE]["groups"],1)
        self.assertEqual(view["stages"][FRANCE_STAGE]["pending"],1)
        self.plan,_=apply_outing(self.plan,self.catalog,"obernai",[],"Férias restantes",confirmed=True)
        self.assertEqual(self.project()["next"],"review")

    def test_eligible_before_organization(self):
        self.wishes=set_interest(self.wishes,"angers","interested",self.discovery)
        self.wishes=set_interest(self.wishes,"brussels","must_visit",self.discovery)
        self.assertEqual(self.project()["next"],"build")

    def test_overview_public_stage_navigation_and_local_finance(self):
        source="""
import streamlit as st
from planning_session import active_plan
from attractions_model import load_attractions
from ux_planning_journey_ui import render_planning_journey,apply_planning_request
apply_planning_request(st.session_state)
render_planning_journey(active_plan(),load_attractions(),summary_only=True)
"""
        app=AppTest.from_string(source,default_timeout=90)
        app.session_state["advisor_plan"]=deepcopy(self.plan)
        app.session_state["ux502_interests"]=deepcopy(self.wishes)
        app.session_state["ux36_cloud_status"]="Conflito de versão"
        app.session_state["ux48_weekend_groups"]=deepcopy(self.groups)
        with patch("continuity_ui._private_store",return_value=None):
            app.run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            self.assertEqual({m.label:int(m.value) for m in app.metric},
                             {"Incluídos":5,"Organizados":0,"A organizar":5})
            self.assertTrue(any("Metz" in c.value for c in app.caption))
            self.assertTrue(any("Conflito de versão" in m.value for m in app.markdown))
            self.assertTrue(any("A verificar" in c.value for c in app.caption))
            self.assertIn("ux121_italy_proposal",{b.key for b in app.button})
            self.assertEqual(app.button(key="flow_journey_primary").label,"Organizar visitas pendentes")
            self.assertFalse(any((b.key or "").startswith("flow_edit_save_") for b in app.button))
            app.button(key="flow_journey_primary").click().run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            self.assertEqual(app.session_state["ux_section"],"Organizar viagem")
            self.assertEqual(app.session_state["flow_active_stage"],FRANCE_STAGE)
            self.assertEqual(app.session_state["advisor_plan"],self.plan)
            self.assertEqual(app.session_state["ux502_interests"],self.wishes)
            self.assertEqual(app.session_state["ux48_weekend_groups"],self.groups)
