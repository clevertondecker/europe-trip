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
from ux132_coverage_page import render_research_coverage
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
elif s["ux_section"]=="Cobertura dos dados":
    render_research_coverage(discovery=discovery)
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

    def test_automatic_highlights_do_not_select_cities(self):
        from rec03b_handoffs import CHOICE
        a=self.make_app([("paris","must_visit"),("basel","interested")],"compare")
        self.click(a,"rec03a_confirm_subset")
        self.assertEqual(a.session_state[CHOICE] if CHOICE in a.session_state else [],[])
        self.assertTrue(any("Sugestões automáticas para seus destinos" in m.value for m in a.markdown))
        self.assertTrue(any("Não avalia preços de passagens" in c.value for c in a.caption))
        self.assertNotIn("Cobertura dos dados",a.segmented_control(key="ux112_active_view").options)
        self.assertIn("Cobertura dos dados",a.segmented_control(key="ux64_public_task").options)
        before=deepcopy(a.session_state["advisor_plan"])
        a.checkbox(key="rec03a_show_all").check()
        self.run_ok(a)
        self.assertTrue(any("Catálogo de cidades-base" in m.value for m in a.markdown))
        picks=[c for c in a.checkbox if c.key and c.key.startswith("rec03a_pick_")]
        self.assertTrue(picks)
        key=picks[0].key
        a.checkbox(key=key).check()
        self.run_ok(a)
        chosen=key.removeprefix("rec03a_pick_")
        self.assertEqual(a.session_state[CHOICE],[chosen])
        self.assertEqual(a.session_state["advisor_plan"],before)
        a.segmented_control(key="ux64_public_task").set_value("Cobertura dos dados")
        self.run_ok(a)
        a.segmented_control(key="ux64_public_task").set_value("Comparar bases")
        self.run_ok(a)
        self.assertEqual(a.session_state[CHOICE],[chosen])
        self.assertTrue(a.checkbox(key=key).value)
        self.assertEqual(a.session_state["advisor_plan"],before)

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
        a.multiselect(key="rec03a_scope_widget").set_value([])
        self.run_ok(a)
        self.assertEqual(a.session_state[DRAFT],[])
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["basel","paris"])
        self.click(a,"rec03a_cancel_edit")
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["basel","paris"])
        from rec03b_handoffs import CHOICE
        a.session_state["ux504_bases_shadow"]=["strasbourg","metz"]
        a.session_state[INTENT]="manual"
        self.run_ok(a)
        self.assertEqual(a.session_state[CHOICE],["strasbourg","metz"])
        self.assertEqual(a.session_state["ux112_active_view"],"Minha comparação")
        self.assertTrue(any('class="ux97-table"' in m.value for m in a.markdown))
        self.assertFalse(any(x.key=="ux503_bases" for x in a.multiselect))
        self.assertNotIn("ux125_open_manual_comparison",{b.key for b in a.button})
        a.session_state[INTENT]="suggestions"
        self.run_ok(a)
        self.assertEqual(a.session_state[CHOICE],["strasbourg","metz"])
        a.segmented_control(key="ux112_active_view").set_value("Explorar alternativas")
        self.run_ok(a)
        self.assertEqual(a.session_state["ux112_active_view"],"Explorar alternativas")
        self.click(a,"rec03a_back_wishlist")
        self.assertEqual(a.session_state["ux502_view"],"Minha lista")
        for k,v in before.items():
            self.assertEqual(a.session_state[k],v)

    def test_coverage_preserves_confirmed_scope_and_comparison(self):
        from rec03b_handoffs import CHOICE
        a=self.make_app([("paris","must_visit"),("basel","interested")],"compare")
        self.click(a,"rec03a_confirm_subset")
        a.session_state[CHOICE]=["strasbourg","metz"]
        self.run_ok(a)
        keys=(SCOPE,CHOICE,"advisor_plan","ux502_interests","ux41_favorites","ux36_cloud_dirty")
        before={key:deepcopy(a.session_state[key]) for key in keys}
        with patch("rec03a_suggestions_ui.recommend_bases") as engine:
            a.segmented_control(key="ux64_public_task").set_value("Cobertura dos dados")
            self.run_ok(a)
            self.assertTrue(any(m.label=="Cobertura ferroviária" for m in a.metric))
            engine.assert_not_called()
        for key,value in before.items():
            self.assertEqual(a.session_state[key],value)
        a.segmented_control(key="ux64_public_task").set_value("Comparar bases")
        self.run_ok(a)
        a.segmented_control(key="ux112_active_view").set_value("Minha comparação")
        self.run_ok(a)
        self.assertTrue(any('class="ux97-table"' in m.value for m in a.markdown))
        for key,value in before.items():
            self.assertEqual(a.session_state[key],value)

    def test_coverage_preserves_edit_draft_and_navigation_handoffs(self):
        from rec03b_handoffs import CHOICE
        a=self.make_app([("paris","must_visit"),("basel","interested")],"compare")
        self.click(a,"rec03a_confirm_subset")
        a.session_state[CHOICE]=["strasbourg","metz"]
        self.run_ok(a)
        self.click(a,"rec03a_edit")
        a.multiselect(key="rec03a_scope_widget").set_value(["paris"])
        self.run_ok(a)
        keys=(SCOPE,DRAFT,CHOICE,"advisor_plan","ux502_interests",
              "ux41_favorites","ux36_cloud_dirty")
        before={key:deepcopy(a.session_state[key]) for key in keys}
        self.assertEqual(before[DRAFT],["paris"])
        a.segmented_control(key="ux64_public_task").set_value("Cobertura dos dados")
        self.run_ok(a)
        self.assertTrue(any(m.label=="Cobertura ferroviária" for m in a.metric))
        for key,value in before.items():
            self.assertEqual(a.session_state[key],value)
        a.segmented_control(key="ux132_domain").set_value("Transporte ferroviário")
        self.run_ok(a)
        a.segmented_control(key="ux132_coverage_section").set_value("Cidades-base")
        self.run_ok(a)
        a.text_input(key="ux132_search_bases").set_value("Metz")
        self.run_ok(a)
        a.selectbox(key="ux132_sort_bases").select("Mais lacunas")
        self.run_ok(a)
        a.selectbox(key="ux132_status_bases").select("Indicativo")
        self.run_ok(a)
        a.selectbox(key="ux132_connection_bases").select("annecy")
        self.run_ok(a)
        a.segmented_control(key="ux132_domain").set_value("Atrações turísticas")
        self.run_ok(a)
        a.text_input(key="ux132c1_search").set_value("Colmar")
        self.run_ok(a)
        for key,value in before.items():
            self.assertEqual(a.session_state[key],value)
        a.segmented_control(key="ux132_domain").set_value("Morar e trabalhar")
        self.run_ok(a)
        a.selectbox(key="ux132c2_scope").select("all")
        self.run_ok(a)
        a.selectbox(key="ux132c2_base").select("trier")
        self.run_ok(a)
        for key,value in before.items():
            self.assertEqual(a.session_state[key],value)
        a.session_state[INTENT]="wishlist"
        self.run_ok(a)
        self.assertEqual(a.session_state["ux64_public_task"],"Minha lista")
        a.session_state[INTENT]="suggestions"
        self.run_ok(a)
        self.assertEqual(a.session_state["ux64_public_task"],"Comparar bases")
        a.segmented_control(key="ux64_public_task").set_value("Cobertura dos dados")
        self.run_ok(a)
        self.assertEqual(a.segmented_control(key="ux132_domain").value,"Morar e trabalhar")
        self.assertEqual(a.selectbox(key="ux132c2_scope").value,"all")
        self.assertEqual(a.selectbox(key="ux132c2_base").value,"trier")
        a.segmented_control(key="ux132_domain").set_value("Atrações turísticas")
        self.run_ok(a)
        self.assertTrue(any(m.label=="Atrações únicas" for m in a.metric))
        self.assertEqual(a.text_input(key="ux132c1_search").value,"Colmar")
        a.segmented_control(key="ux132_domain").set_value("Transporte ferroviário")
        self.run_ok(a)
        self.assertTrue(any(m.label=="Cobertura ferroviária" for m in a.metric))
        self.assertEqual(a.text_input(key="ux132_search_bases").value,"Metz")
        self.assertEqual(a.selectbox(key="ux132_sort_bases").value,"Mais lacunas")
        self.assertEqual(a.selectbox(key="ux132_connection_bases").value,"annecy")
        a.segmented_control(key="ux64_public_task").set_value("Comparar bases")
        self.run_ok(a)
        a.segmented_control(key="ux112_active_view").set_value("Explorar alternativas")
        self.run_ok(a)
        self.assertEqual(a.multiselect(key="rec03a_scope_widget").value,["paris"])
        for key,value in before.items():
            self.assertEqual(a.session_state[key],value)
        self.click(a,"rec03a_cancel_edit")
        a.session_state[INTENT]="manual"
        self.run_ok(a)
        self.assertEqual(a.session_state["ux112_active_view"],"Minha comparação")
        self.assertTrue(any('class="ux97-table"' in m.value for m in a.markdown))
        self.assertEqual(a.session_state[CHOICE],before[CHOICE])
        a.segmented_control(key="ux64_public_task").set_value("Cobertura dos dados")
        self.run_ok(a)
        self.assertEqual(a.text_input(key="ux132_search_bases").value,"Metz")
        self.assertEqual(a.selectbox(key="ux132_connection_bases").value,"annecy")
        self.assertEqual(a.session_state[CHOICE],before[CHOICE])

    def test_scope_reconciles_real_edits_and_same_revision_replacement(self):
        a=self.make_app([("paris","interested"),("colmar","maybe")],"compare")
        self.click(a,"rec03a_confirm_subset")
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
        self.click(a,"rec03a_confirm_subset")
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["angers","paris","saint_malo"])
        a.checkbox(key="rec03a_show_all").check()
        self.run_ok(a)
        a.text_input(key="rec03a_search").set_value("Angers")
        self.run_ok(a)
        a.session_state[INTENT]="manual"
        self.run_ok(a)
        a.session_state[INTENT]="suggestions"
        self.run_ok(a)
        a.segmented_control(key="ux112_active_view").set_value("Explorar alternativas")
        self.run_ok(a)
        self.assertEqual(a.text_input(key="rec03a_search").value,"Angers")
        self.assertEqual(a.session_state["advisor_plan"],original_plan)
        from base_recommendation_model import recommend_bases
        from comparison_destinations_model import project_comparison_destinations
        from attractions_model import load_attractions
        projection=project_comparison_destinations(a.session_state["ux502_interests"],original_plan,self.discovery,load_attractions())
        result=recommend_bases(projection,a.session_state[SCOPE],discovery=self.discovery)
        self.assertIn(result["state"],("comparable","partial_evidence","insufficient_evidence"))
        angers=next(c for c in result["candidates"] if c["base_id"]=="angers")
        self.assertEqual(angers["evidence"]["angers"]["category"],"local")
        self.assertIsNone(angers["evidence"]["angers"]["display_min"])

    def test_planned_only_destination_appears_and_new_visit_requires_review(self):
        from attractions_model import load_attractions
        from itinerary_flow_model import add_undated_choices,FRANCE_STAGE
        a=self.make_app([], "compare")
        wishes=deepcopy(a.session_state["ux502_interests"])
        plan=add_undated_choices(a.session_state["advisor_plan"],load_attractions(),["basel"],FRANCE_STAGE)
        a.session_state["advisor_plan"]=plan
        self.run_ok(a)
        self.assertEqual(a.multiselect(key="rec03a_scope_widget").value,["basel"])
        self.click(a,"rec03a_confirm_subset")
        self.assertTrue(a.session_state[SCOPE]["confirmed"])
        self.assertEqual(a.session_state[SCOPE]["destination_ids"],["basel"])
        plan=add_undated_choices(plan,load_attractions(),["colmar"],FRANCE_STAGE)
        a.session_state["advisor_plan"]=plan
        self.run_ok(a)
        self.assertFalse(a.session_state[SCOPE]["confirmed"])
        self.assertEqual(a.session_state[SCOPE]["pending_ids"],["colmar"])
        self.assertEqual(a.multiselect(key="rec03a_scope_widget").value,["basel"])
        self.assertEqual(a.session_state["advisor_plan"],plan)
        self.assertEqual(a.session_state["ux502_interests"],wishes)

    def test_loader_failure_and_identity_reset(self):
        a=self.make_app([("paris","must_visit")],"compare")
        self.click(a,"rec03a_confirm_subset")
        with patch("rec03a_suggestions_ui.recommend_bases",side_effect=RuntimeError("loader failure")):
            self.run_ok(a)
            self.assertTrue(a.error)
            self.assertFalse(any("Todas as cidades-base" in x.value for x in a.markdown))
        self.run_ok(a)
        a.session_state["test_identity"]="other"
        self.run_ok(a)
        # The safer default reopens a PROPOSED scope, never a confirmed one.
        # Identity reset must not resurrect the previous analyzed scope.
        self.assertIsNone(a.session_state[SCOPE])
        self.assertEqual(a.session_state[DRAFT],["paris"])
        self.assertEqual(a.session_state[ACTIVITY],SUGGESTED)
        with patch("rec03a_suggestions_ui.recommend_bases") as engine:
            self.run_ok(a)
            self.assertIsNone(a.session_state[SCOPE])
            self.assertIsNotNone(a.button(key="rec03a_confirm_subset"))
            engine.assert_not_called()


if __name__=="__main__":
    unittest.main()
