"""UX114: only explicit, eligible candidates enter the existing official review."""
import unittest
from copy import deepcopy

from streamlit.testing.v1 import AppTest

from rec03b_handoffs import CHOICE
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests, set_interest
from trip_plan_model import new_plan


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


class UX114ExplicitReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def ready(self, bases):
        app=AppTest.from_string(APP,default_timeout=120)
        wishes=empty_interests()
        for city in ("paris","colmar","strasbourg"):
            wishes=set_interest(wishes,city,"interested",self.discovery)
        app.session_state["ux502_interests"]=wishes
        app.session_state["advisor_plan"]=new_plan()
        app.session_state["rec03a_identity"]="unconfigured"
        app.run()
        app.button(key="rec03a_confirm_subset").click().run()
        app.session_state[CHOICE]=list(bases)
        app.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        return app

    def test_review_selected_eligible_city_never_changes_plan(self):
        app=self.ready(["metz","lille"])
        initial=deepcopy(app.session_state["advisor_plan"])
        self.assertIn("ux114_open_review",{b.key for b in app.button})
        self.assertEqual(app.selectbox(key="ux114_preferred_base").value,"metz")
        app.button(key="ux114_open_review").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux114_review_base"],"metz")
        self.assertEqual(app.session_state["ux34_candidates"],["metz"])
        self.assertEqual(app.session_state["advisor_plan"],initial)
        self.assertEqual(app.session_state[CHOICE],["metz","lille"])

    def test_research_only_cities_are_not_approvable(self):
        app=self.ready(["lille","freiburg"])
        self.assertNotIn("ux114_open_review",{b.key for b in app.button})
        self.assertTrue(any("Somente pesquisa" in x.value for x in app.caption))
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"mulhouse")

    def test_more_than_eight_destinations_never_truncated_silently(self):
        app=AppTest.from_string("""
import streamlit as st
from rec03a_suggestions_ui import _open_base_review,close_base_review
from base_change_model import destination_catalog
from trip_plan_model import new_plan
if "advisor_plan" not in st.session_state:
    st.session_state["advisor_plan"]=new_plan()
destinations=list(destination_catalog())[:9]
st.button("Review",key="review",on_click=_open_base_review,
          args=("metz",tuple(destinations)))
st.button("Cancel",key="cancel",on_click=close_base_review)
""",default_timeout=90).run()
        before=deepcopy(app.session_state["advisor_plan"])
        app.button(key="review").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux114_review_overlimit"],9)
        self.assertEqual(app.session_state["ux34_destinations"],[])
        self.assertEqual(app.session_state["advisor_plan"],before)
        app.button(key="cancel").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("ux114_review_base",app.session_state)
        self.assertEqual(app.session_state["advisor_plan"],before)


if __name__=="__main__":
    unittest.main()
