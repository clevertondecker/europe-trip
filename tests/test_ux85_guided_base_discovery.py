"""UX85: a simple, useful base-discovery entry without parallel selections."""
import unittest
import inspect
from copy import deepcopy

from streamlit.testing.v1 import AppTest

from rec03a_suggestions_ui import _featured_ids, render_suggestions
from rec03b_handoff_ui import selected_card_bases
from rec03b_handoffs import CHOICE
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
from ux502_destination_interests_model import empty_interests,set_interest


APP = """
import streamlit as st
from rec03a_suggestions_ui import render_recommendation_activity
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
if "advisor_plan" not in st.session_state:
    st.session_state["advisor_plan"]=new_plan()
render_recommendation_activity(plan=st.session_state["advisor_plan"],
                               discovery=build_exploration_discovery())
"""


class CardSelectionTests(unittest.TestCase):
    def test_documentary_highlights_are_deduplicated_and_limited(self):
        result={"candidates":[{"base_id":str(x)} for x in range(10)],
                "highlight_sections":{
                    "complete_reference_groups":["0","1","2"],
                    "conditional_all_must_identified":["2","3","4","5"],
                    "conditional_must_pending":["0","6"]}}
        self.assertEqual(_featured_ids(result),["0","1","2","3"])
        self.assertEqual(_featured_ids({
            "candidates":result["candidates"],"highlight_sections":{
                "complete_reference_groups":[],
                "conditional_all_must_identified":[],
                "conditional_must_pending":[]}}),[])
        self.assertEqual(len(result["candidates"]),10)

    def test_choice_projection_is_read_only_and_never_truncates(self):
        state={CHOICE:["a","b","a","missing","c","d","e","f"]}
        before=deepcopy(state)
        self.assertEqual(selected_card_bases(state,["a","b","c","d","e","f"]),
                         ["a","b","c","d","e","f"])
        self.assertEqual(state,before)
        self.assertEqual(selected_card_bases({CHOICE:"corrupt"},["a"]),[])

    def test_card_checkboxes_control_only_choice_and_respect_five_max(self):
        code="""
import streamlit as st
from rec03b_handoff_ui import render_card_choice
for base in ["a","b","c","d","e","f"]:
    render_card_choice(base,["a","b","c","d","e","f"])
"""
        app=AppTest.from_string(code,default_timeout=30).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        for base in ["a","b","c","d","e"]:
            app.checkbox(key="rec03a_pick_"+base).check().run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state[CHOICE],["a","b","c","d","e"])
        self.assertTrue(app.checkbox(key="rec03a_pick_f").disabled)
        app.checkbox(key="rec03a_pick_a").uncheck().run()
        self.assertFalse(app.checkbox(key="rec03a_pick_f").disabled)
        app.checkbox(key="rec03a_pick_f").check().run()
        self.assertEqual(app.session_state[CHOICE],["b","c","d","e","f"])


class GuidedComparisonTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def app(self):
        a=AppTest.from_string(APP,default_timeout=120)
        wishes=empty_interests()
        for city in ("paris","colmar","strasbourg","angers","basel"):
            wishes=set_interest(wishes,city,"interested",self.discovery)
        a.session_state["ux502_interests"]=wishes
        a.session_state["advisor_plan"]=new_plan()
        a.session_state["rec03a_identity"]="unconfigured"
        return a.run()

    def test_first_visit_and_ready_resume_need_no_radio_or_reconfirmation(self):
        a=self.app()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertEqual(len([b for b in a.button if b.key=="rec03a_confirm_subset"]),1)
        self.assertFalse(any(x.key=="rec03a_activity_widget" for x in a.radio))
        self.assertEqual(sum("ui-page-header" in m.value for m in a.markdown),1)
        plan=deepcopy(a.session_state["advisor_plan"])
        wishes=deepcopy(a.session_state["ux502_interests"])
        a.button(key="rec03a_confirm_subset").click().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertFalse(any(b.key=="rec03a_confirm_subset" for b in a.button))
        self.assertFalse(any(x.key=="rec03a_activity_widget" for x in a.radio))
        self.assertEqual(sum("ui-page-header" in m.value for m in a.markdown),1)
        self.assertLessEqual(sum(x.key.startswith("rec03a_pick_")
                                for x in a.checkbox if x.key),4)
        self.assertTrue(any(x.key=="rec03a_show_all" for x in a.checkbox))
        self.assertEqual(a.session_state["advisor_plan"],plan)
        self.assertEqual(a.session_state["ux502_interests"],wishes)
        a.run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertFalse(any(b.key=="rec03a_confirm_subset" for b in a.button))


    def test_exploration_precedes_one_inline_comparison(self):
        # UX112 removes the redundant preview and secondary focus selection.
        source=inspect.getsource(render_suggestions)
        self.assertNotIn("render_card_selection_summary(",source)
        self.assertNotIn("_render_quick_comparison(",source)
        self.assertIn('view=st.segmented_control("Área da pesquisa"',source)
        self.assertLess(source.index('search=st.text_input("Pesquisar cidade ou país"'),
                        source.index('show_all=st.checkbox('))
        self.assertIn('render_selection_toolbar(options,cities,navigation="explore")',source)
        self.assertIn('render_selection_toolbar(options,cities,navigation="compare")',source)
        self.assertIn("size=4",source)
        self.assertIn("render_planning_handoff(plan,interests=wishes",source)

    def test_two_highlight_cards_show_inline_comparison(self):
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        keys=[x.key for x in a.checkbox if x.key and x.key.startswith("rec03a_pick_")]
        self.assertGreaterEqual(len(keys),2)
        for key in keys[:2]:
            a.checkbox(key=key).check().run()
            self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertEqual(len(a.session_state[CHOICE]),2)
        city_headers=" ".join(x.value for x in a.markdown
                              if "ux96-city-header" in x.value)
        self.assertIn("Históricos",city_headers)
        self.assertIn("Indicativos",city_headers)
        self.assertFalse(any("ux97-table" in x.value for x in a.markdown))
        a.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertFalse(any(x.key=="rec03a_handoff_compare" for x in a.button))
        self.assertTrue(any("ux97-table" in x.value for x in a.markdown))
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in a.checkbox))
        self.assertTrue(any(x.key=="rec03a_inline_sources" for x in a.checkbox))
        self.assertEqual(len([x for x in a.multiselect
                              if x.key==CHOICE+"_widget"]),0)
        self.assertFalse(any("ux96-city-header" in x.value for x in a.markdown))

    def test_comparison_auto_appears_for_three_and_five_bases(self):
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        from base_research_expanded_model import load_research
        candidates=[c["id"] for c in load_research(include_candidates=True)["cities"]]
        a.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        for n in (3,5):
            with self.subTest(n=n):
                a.session_state[CHOICE]=candidates[:n]
                a.run()
                self.assertFalse(a.exception,[x.message for x in a.exception])
                self.assertEqual(a.session_state[CHOICE],candidates[:n])
                self.assertTrue(any("ux97-table" in x.value for x in a.markdown))
                self.assertFalse(any(x.key=="rec03a_handoff_compare" for x in a.button))
                self.assertFalse(any(x.key==CHOICE+"_widget" for x in a.multiselect))
                self.assertFalse(any(x.key=="rec03a_focus_city" for x in a.selectbox))
        a.session_state[CHOICE]=[]
        a.run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in a.checkbox))
        a.session_state[CHOICE]=candidates[:1]
        a.run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in a.checkbox))

    def test_other_city_selection_survives_filters_and_browse_switch(self):
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        first=next(x.key for x in a.checkbox if x.key and x.key.startswith("rec03a_pick_"))
        a.checkbox(key=first).check().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        other="angers" if not first.endswith("_angers") else "metz"
        a.checkbox(key="rec03a_show_all").check().run()
        a.text_input(key="rec03a_search").set_value(other).run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        a.checkbox(key="rec03a_pick_"+other).check().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        selected=list(a.session_state[CHOICE])
        self.assertEqual(set(selected),{first.removeprefix("rec03a_pick_"),other})
        self.assertFalse(any("ux97-table" in x.value for x in a.markdown))
        a.button(key="ux112_open_comparison").click().run()
        self.assertTrue(any("ux97-table" in x.value for x in a.markdown))
        a.button(key="ux112_open_exploration").click().run()
        a.checkbox(key="rec03a_show_all").uncheck().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertEqual(a.session_state[CHOICE],selected)
        a.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertTrue(any("ux97-table" in x.value for x in a.markdown))

    def test_search_without_opening_catalog_and_preserve_canonical_plan(self):
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        before=deepcopy(a.session_state["advisor_plan"])
        self.assertFalse(a.checkbox(key="rec03a_show_all").value)
        self.assertIn("rec03a_search",{x.key for x in a.text_input})
        a.text_input(key="rec03a_search").set_value("Metz").run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertFalse(a.checkbox(key="rec03a_show_all").value)
        self.assertIn("rec03a_pick_metz",{x.key for x in a.checkbox})
        self.assertEqual(a.session_state["advisor_plan"],before)

    def test_legacy_overlimit_selection_requires_explicit_removal(self):
        from base_research_expanded_model import load_research
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        original=deepcopy(a.session_state["advisor_plan"])
        ids=[c["id"] for c in load_research(include_candidates=True)["cities"]][:6]
        a.session_state[CHOICE]=ids
        a.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertEqual(len(a.session_state[CHOICE]),6)
        self.assertTrue(any("mais de cinco cidades" in x.value for x in a.warning))
        self.assertFalse(any("ux97-table" in x.value for x in a.markdown))
        a.button(key="ux111_remove_"+ids[-1]).click().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertEqual(a.session_state[CHOICE],ids[:5])
        self.assertTrue(any("ux97-table" in x.value for x in a.markdown))
        self.assertEqual(a.session_state["advisor_plan"],original)

    def test_active_view_survives_widget_rerun(self):
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        a.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertEqual(a.session_state["ux112_active_view_shadow"],"Minha comparação")
        a.run()
        self.assertEqual(a.segmented_control(key="ux112_active_view").value,
                         "Minha comparação")
        a.segmented_control(key="ux112_active_view").set_value("Explorar alternativas").run()
        self.assertEqual(a.session_state["ux112_active_view_shadow"],"Explorar alternativas")

    def test_identity_change_cleans_ephemeral_review_but_not_trip_plan(self):
        from rec03a_session import sync_identity
        original=new_plan()
        state={"rec03a_identity":"owner:previous",CHOICE:["metz"],
               "ux112_active_view":"Minha comparação",
               "ux112_active_view_shadow":"Minha comparação",
               "ux114_review_context":{"base":"metz"},
               "ux34_candidates":["metz"],"ux34_destinations":["paris"],
               "ux34_review":{"pending":True},"ux34_apply_ack":True,
               "advisor_plan":deepcopy(original),"ux41_favorites":["metz"]}
        sync_identity(state,"owner:new")
        for key in (CHOICE,"ux112_active_view","ux112_active_view_shadow",
                    "ux114_review_context","ux34_candidates","ux34_destinations",
                    "ux34_review","ux34_apply_ack"):
            self.assertNotIn(key,state)
        self.assertEqual(state["advisor_plan"],original)
        self.assertEqual(state["ux41_favorites"],["metz"])

    def test_overlimit_feedback_never_claims_negative_capacity(self):
        from base_research_expanded_model import load_research
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        ids=[c["id"] for c in load_research(include_candidates=True)["cities"]][:6]
        a.session_state[CHOICE]=ids
        a.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertFalse(any("-1 vaga" in x.value for x in a.caption))
        self.assertTrue(any("acima do limite" in x.value for x in a.caption)
                        or any("mais de cinco" in x.value for x in a.warning))

    def test_selection_below_filter_remains_authoritative(self):
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        a.checkbox(key="rec03a_show_all").check().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertTrue(any(x.key=="rec03a_search" for x in a.text_input))
        # The catalog is still searchable; no duplicate multiselect for bases.
        self.assertFalse(any(x.key==CHOICE+"_widget" for x in a.multiselect))
        self.assertEqual(len([x for x in a.checkbox
                              if x.key and x.key.startswith("rec03a_pick_")]),
                         len({x.key for x in a.checkbox
                              if x.key and x.key.startswith("rec03a_pick_")}))


if __name__=="__main__":
    unittest.main()
