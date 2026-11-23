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


    def test_single_cta_follows_all_visible_cards_in_each_view(self):
        # Structural guard for UX85's temporary native CTA; UX87 will replace
        # this handoff region with inline comparison after the same cards.
        source=inspect.getsource(render_suggestions)
        self.assertEqual(source.count("render_card_selection_summary(result,cities,selection_already_shown=True)"),1)
        self.assertLess(source.index("for index,candidate in enumerate(visible):"),
                        source.index("render_card_selection_summary(result,cities,selection_already_shown=True)"))
        self.assertLess(source.index("_render_quick_comparison(result,names,cities,"),
                        source.index("for index,candidate in enumerate(visible):"))
        self.assertLess(source.index("for index,base in enumerate(featured):"),
                        source.index("render_card_selection_summary(result,cities,selection_already_shown=True)"))
        self.assertIn("size=4",source)

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
        self.assertFalse(any(x.key=="rec03a_handoff_compare" for x in a.button))
        self.assertTrue(any("ux97-table" in x.value for x in a.markdown))
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in a.checkbox))
        self.assertTrue(any(x.key=="rec03a_inline_sources" for x in a.checkbox))
        self.assertEqual(len([x for x in a.multiselect
                              if x.key==CHOICE+"_widget"]),0)
        city_headers=" ".join(x.value for x in a.markdown
                              if "ux96-city-header" in x.value)
        self.assertIn("Históricos",city_headers)
        self.assertIn("Indicativos",city_headers)

    def test_comparison_auto_appears_for_three_and_five_bases(self):
        a=self.app()
        a.button(key="rec03a_confirm_subset").click().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        from base_research_expanded_model import load_research
        candidates=[c["id"] for c in load_research(include_candidates=True)["cities"]]
        for n in (3,5):
            with self.subTest(n=n):
                a.session_state[CHOICE]=candidates[:n]
                a.run()
                self.assertFalse(a.exception,[x.message for x in a.exception])
                self.assertEqual(a.session_state[CHOICE],candidates[:n])
                self.assertTrue(any("ux97-table" in x.value for x in a.markdown))
                self.assertFalse(any(x.key=="rec03a_handoff_compare" for x in a.button))
                self.assertFalse(any(x.key==CHOICE+"_widget" for x in a.multiselect))
                self.assertEqual(len([x for x in a.selectbox
                                      if x.key=="rec03a_focus_city"]),1)
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
        self.assertTrue(any("ux97-table" in x.value for x in a.markdown))
        a.checkbox(key="rec03a_show_all").uncheck().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        self.assertEqual(a.session_state[CHOICE],selected)
        self.assertTrue(any("ux97-table" in x.value for x in a.markdown))

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
