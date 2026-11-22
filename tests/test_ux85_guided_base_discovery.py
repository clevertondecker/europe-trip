"""UX85: a simple, useful base-discovery entry without parallel selections."""
import unittest
from copy import deepcopy

from streamlit.testing.v1 import AppTest

from rec03a_suggestions_ui import _featured_ids
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
