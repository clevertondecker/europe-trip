"""REC03A real widget callbacks and ephemeral state regression coverage."""
import unittest
from copy import deepcopy
from unittest.mock import patch
from time import perf_counter
from streamlit.testing.v1 import AppTest
from rec03a_session import (SCOPE,DRAFT,ACTIVITY,SUGGESTED,MANUAL,INTENT,
                            sync_identity,request_navigation,apply_navigation,clear_recommendation_context)
from recommendation_scope_model import confirm_scope
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,set_interest,remove_interest
from trip_plan_model import new_plan
from rec03a_suggestions_ui import evidence_examples

APP = """
import streamlit as st
from trip01_supplemental_discovery import build_exploration_discovery
from rec03a_session import apply_navigation,sync_identity
from rec03a_suggestions_ui import render_recommendation_activity
from ux502_destination_interests_ui import render_wishlist
from ux64_navigation_ui import render_public_task_tabs
from ux_navigation import bootstrap
from trip_plan_model import new_plan
s=st.session_state
if "advisor_plan" not in s:
    s["advisor_plan"]=new_plan()
bootstrap(s)
sync_identity(s,s.get("test_identity","unconfigured"))
apply_navigation(s)
render_public_task_tabs()
discovery=build_exploration_discovery()
if s["ux_section"]=="Comparar":
    render_recommendation_activity(plan=s["advisor_plan"],discovery=discovery)
else:
    render_wishlist(discovery)
"""

class SessionTests(unittest.TestCase):
    def test_navigation_and_identity_do_not_touch_authoritative_state(self):
        state={"ux502_interests":empty_interests(),"advisor_plan":new_plan(),
               "ux41_favorites":["metz"],"ux36_cloud_dirty":False}
        before=deepcopy(state)
        sync_identity(state,"one")
        request_navigation(state,"suggestions")
        self.assertEqual(apply_navigation(state),"suggestions")
        self.assertEqual(state[ACTIVITY],SUGGESTED)
        self.assertNotIn(INTENT,state)
        state[SCOPE]={"old":True}
        state[DRAFT]=["paris"]
        sync_identity(state,"two")
        self.assertNotIn(SCOPE,state)
        self.assertNotIn(DRAFT,state)
        for key in before:
            self.assertEqual(state[key],before[key])
        clear_recommendation_context(state)

    def test_priority_examples_do_not_order_by_speed_or_invent_times(self):
        destinations=[{"id":"a","priority":"maybe"},{"id":"z","priority":"must_visit"},
                      {"id":"b","priority":"interested"},{"id":"c","priority":"must_visit"}]
        candidate={"evidence":{"a":{"category":"historical","display_min":10},
                               "z":{"category":"reference_only","display_min":90},
                               "b":{"category":"local","display_min":None},
                               "c":{"category":"no_time","display_min":None}}}
        self.assertEqual([d for d,_ in evidence_examples(candidate,destinations)],["z","b","a"])


class RecommendationAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def wishes(self,items):
        doc=empty_interests()
        for d,p in items:
            doc=set_interest(doc,d,p,self.discovery)
        return doc

    def make_app(self,items=(),start="list"):
        a=AppTest.from_string(APP,default_timeout=90)
        a.session_state["ux_area"]="Explorar"
        a.session_state["ux_section"]="Passeios" if start=="list" else "Comparar"
        a.session_state["ux502_view"]="Minha lista"
        a.session_state["ux64_public_task"]="Minha lista" if start=="list" else "Comparar bases"
        a.session_state["rec03a_identity"]="unconfigured"
        a.session_state[ACTIVITY]=SUGGESTED
        a.session_state["ux502_interests"]=self.wishes(items)
        a.session_state["advisor_plan"]=new_plan()
        a.session_state["ux41_favorites"]=["metz"]
        a.session_state["ux36_cloud_dirty"]=False
        return self.run_ok(a)

    def run_ok(self,a):
        a.run()
        self.assertFalse(a.exception, str(a.exception))
        return a

    def click(self,a,key):
        a.button(key=key).click()
        return self.run_ok(a)

    def test_empty_and_discarded_no_engine_call(self):
        for items in ([],[("paris","discarded")]):
            with self.subTest(items=items),patch("rec03a_suggestions_ui.recommend_bases") as engine:
                a=self.make_app(items,"compare")
                self.assertTrue(any("Nenhum destino ativo" in x.value for x in a.info))
                engine.assert_not_called()

    def test_wishlist_to_scope_subset_edit_cancel_return_and_manual(self):
        items=[("paris","must_visit"),("colmar","interested"),("basel","maybe")]
        a=self.make_app(items)
        before={k:deepcopy(a.session_state[k]) for k in
                ("advisor_plan","ux502_interests","ux41_favorites","ux36_cloud_dirty")}
        with patch("rec03a_suggestions_ui.recommend_bases") as engine:
            self.click(a,"rec03a_open_from_wishlist")
            self.assertEqual(a.session_state[ACTIVITY],SUGGESTED)
            self.assertEqual(a.session_state["ux_section"],"Comparar")
            engine.assert_not_called()
        a.multiselect(key="rec03a_scope_widget").set_value(["paris","basel"])
        self.run_ok(a)
        self.click(a,"rec03a_confirm_subset")
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["basel","paris"])
        self.click(a,"rec03a_edit")
        self.click(a,"rec03a_clear_selection")
        self.assertEqual(a.session_state[DRAFT],[])
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["basel","paris"])
        self.click(a,"rec03a_cancel_edit")
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["basel","paris"])
        a.radio(key="rec03a_activity_widget").set_value(MANUAL)
        self.run_ok(a)
        self.assertIsNotNone(a.multiselect(key="ux503_bases"))
        a.multiselect(key="ux503_bases").set_value(["strasbourg","metz"])
        self.run_ok(a)
        manual=list(a.session_state["ux503_bases"])
        a.radio(key="rec03a_activity_widget").set_value(SUGGESTED)
        self.run_ok(a)
        a.radio(key="rec03a_activity_widget").set_value(MANUAL)
        self.run_ok(a)
        self.assertEqual(a.session_state["ux503_bases"],manual)
        a.radio(key="rec03a_activity_widget").set_value(SUGGESTED)
        self.run_ok(a)
        self.click(a,"rec03a_back_wishlist")
        self.assertEqual(a.session_state["ux502_view"],"Minha lista")
        for k,v in before.items():
            self.assertEqual(a.session_state[k],v)

    def test_scope_reconciles_real_edits_and_same_revision_replacement(self):
        a=self.make_app([("paris","interested"),("colmar","maybe")],"compare")
        self.click(a,"rec03a_confirm_all")
        doc=a.session_state["ux502_interests"]
        edited=set_interest(doc,"paris","must_visit",self.discovery)
        a.session_state["ux502_interests"]=edited
        self.run_ok(a)
        self.assertTrue(a.session_state[SCOPE]["confirmed"])
        self.assertEqual(a.session_state[SCOPE]["snapshot"]["revision"],edited["revision"])
        added=set_interest(edited,"basel","maybe",self.discovery)
        a.session_state["ux502_interests"]=added
        self.run_ok(a)
        self.assertFalse(a.session_state[SCOPE]["confirmed"])
        self.assertEqual(a.session_state[SCOPE]["pending_ids"],["basel"])
        self.assertNotIn("basel",a.session_state[SCOPE]["destination_ids"])
        self.click(a,"rec03a_confirm_subset")
        removed=remove_interest(added,"colmar",self.discovery)
        a.session_state["ux502_interests"]=removed
        self.run_ok(a)
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["paris"])
        replacement=deepcopy(removed)
        replacement["items"][0]["priority"]="maybe"
        a.session_state["ux502_interests"]=replacement
        self.run_ok(a)
        self.assertIsNone(a.session_state[SCOPE])

    def test_data23_and_local_and_filter_preservation(self):
        a=self.make_app([("angers","must_visit"),("saint_malo","interested"),("paris","maybe")],"compare")
        original_plan=deepcopy(a.session_state["advisor_plan"])
        self.click(a,"rec03a_confirm_all")
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["angers","paris","saint_malo"])
        a.text_input(key="rec03a_search").set_value("Angers")
        self.run_ok(a)
        a.radio(key="rec03a_activity_widget").set_value(MANUAL)
        self.run_ok(a)
        a.radio(key="rec03a_activity_widget").set_value(SUGGESTED)
        self.run_ok(a)
        self.assertEqual(a.text_input(key="rec03a_search").value,"Angers")
        self.assertEqual(a.session_state["advisor_plan"],original_plan)
        from base_recommendation_model import recommend_bases
        result=recommend_bases(a.session_state["ux502_interests"],a.session_state[SCOPE],discovery=self.discovery)
        angers=next(c for c in result["candidates"] if c["base_id"]=="angers")
        self.assertEqual(angers["evidence"]["angers"]["category"],"local")
        self.assertIsNone(angers["evidence"]["angers"]["display_min"])

    def test_loader_failure_and_identity_reset(self):
        a=self.make_app([("paris","must_visit")],"compare")
        self.click(a,"rec03a_confirm_all")
        with patch("rec03a_suggestions_ui.recommend_bases",side_effect=RuntimeError("loader failure")):
            self.run_ok(a)
            self.assertTrue(a.error)
            self.assertFalse(any("Todas as cidades-base" in x.value for x in a.markdown))
        self.run_ok(a)
        a.session_state["test_identity"]="other"
        self.run_ok(a)
        self.assertNotIn(SCOPE,a.session_state.filtered_state)
        self.assertNotIn(DRAFT,a.session_state.filtered_state)
        self.assertEqual(a.session_state[ACTIVITY],MANUAL)
        a.radio(key="rec03a_activity_widget").set_value(SUGGESTED)
        with patch("rec03a_suggestions_ui.recommend_bases") as engine:
            self.run_ok(a)
            self.assertIsNone(a.session_state[SCOPE])
            self.assertIsNotNone(a.button(key="rec03a_confirm_all"))
            engine.assert_not_called()


if __name__=="__main__":
    unittest.main()
