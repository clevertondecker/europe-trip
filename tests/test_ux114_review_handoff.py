"""UX114: contextual review is the existing UX34 confirmation, never a shortcut."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from base_change_model import destination_catalog
from rec03b_handoffs import CHOICE
from rec03a_suggestions_ui import _review_destinations
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,set_interest
from trip_plan_model import new_plan


APP = """
import streamlit as st
from rec03a_suggestions_ui import render_recommendation_activity,close_base_review
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
if "advisor_plan" not in st.session_state:
    st.session_state["advisor_plan"]=new_plan()
render_recommendation_activity(plan=st.session_state["advisor_plan"],
                               discovery=build_exploration_discovery())
st.button("Cancelar revisão",key="ux114_test_cancel",on_click=close_base_review)
"""


class UX114ExplicitReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def ready(self,bases=("metz","nancy"),destinations=("paris","colmar","strasbourg")):
        app=AppTest.from_string(APP,default_timeout=120)
        wishes=empty_interests()
        for city in destinations:
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

    def test_selected_eligible_review_preserves_plan_and_restores_advanced_filters(self):
        app=self.ready(("metz","lille"))
        before=deepcopy(app.session_state["advisor_plan"])
        app.session_state["ux34_candidates"]=["nancy"]
        app.session_state["ux34_destinations"]=["colmar"]
        app.session_state["ux34_apply_ack"]=True
        app.button(key="ux114_open_review").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["ux114_review_base"],"metz")
        ctx=app.session_state["ux114_review_context"]
        self.assertEqual(set(ctx["approved_destinations"]),{"paris","colmar","strasbourg"})
        self.assertEqual(app.session_state["ux34_candidates"],["metz"])
        self.assertEqual(app.session_state["advisor_plan"],before)
        self.assertEqual(app.session_state[CHOICE],["metz","lille"])
        app.button(key="ux114_test_cancel").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("ux114_review_context",app.session_state)
        self.assertEqual(app.session_state["ux34_candidates"],["nancy"])
        self.assertEqual(app.session_state["ux34_destinations"],["colmar"])
        self.assertNotIn("ux34_apply_ack",app.session_state)
        self.assertEqual(app.session_state["advisor_plan"],before)

    def test_research_only_candidates_cannot_start_review(self):
        app=self.ready(("lille","freiburg"))
        self.assertNotIn("ux114_open_review",{b.key for b in app.button})
        self.assertTrue(any("Somente pesquisa" in x.value for x in app.caption))
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"mulhouse")

    def test_partial_and_empty_catalog_never_silently_replace_destinations(self):
        supported,missing=_review_destinations(("paris","unsupported_ux114","colmar"))
        self.assertEqual(supported,["paris","colmar"])
        self.assertEqual(missing,["unsupported_ux114"])
        self.assertEqual(_review_destinations(("unsupported_ux114",)),
                         ([],["unsupported_ux114"]))
        app=AppTest.from_string("""
import streamlit as st
from rec03a_suggestions_ui import render_base_review_scope
state=st.session_state
ctx={"supported_destinations":[],"unsupported_destinations":["unknown"],
     "approved_destinations":None}
render_base_review_scope(ctx)
""",default_timeout=30).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("Nenhum destino" in x.value for x in app.error))
        self.assertNotIn("ux114_confirm_scope",{x.key for x in app.button})

    def test_nine_supported_destinations_require_explicit_selection(self):
        catalog=destination_catalog()
        ids=[d["id"] for d in self.discovery["destinations"]
             if d["id"] in catalog][:9]
        self.assertEqual(len(ids),9)
        app=self.ready(destinations=tuple(ids))
        app.button(key="ux114_open_review").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        ctx=app.session_state["ux114_review_context"]
        self.assertEqual(ctx["approved_destinations"],None)
        self.assertEqual(len(ctx["supported_destinations"]),9)
        self.assertEqual(app.session_state["ux34_destinations"],[])
        self.assertEqual(app.session_state["ux114_review_overlimit"],9)

    def _open_in_real_application(self):
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=120).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        wishes=empty_interests()
        for city in ("paris","colmar","strasbourg"):
            wishes=set_interest(wishes,city,"interested",self.discovery)
        app.session_state["ux502_interests"]=wishes
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        app.button(key="rec03a_confirm_subset").click().run()
        for base in ("metz","nancy"):
            app.text_input(key="rec03a_search").set_value(base).run()
            app.checkbox(key="rec03a_pick_"+base).check().run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
        app.segmented_control(key="ux112_active_view").set_value("Minha comparação").run()
        app.selectbox(key="ux114_preferred_base").set_value("metz").run()
        app.button(key="ux114_open_review").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertIn("ux114_review_back",{x.key for x in app.button})
        self.assertTrue(app.multiselect(key="ux34_candidates").disabled)
        self.assertTrue(app.multiselect(key="ux34_destinations").disabled)
        self.assertEqual(app.multiselect(key="ux34_candidates").value,["metz"])
        self.assertEqual(app.session_state["advisor_plan"],original)
        return app,original

    def test_real_widget_journey_can_cancel_without_changing_plan(self):
        app,original=self._open_in_real_application()
        app.button(key="ux114_review_back").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("ux114_review_base",app.session_state)
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(app.session_state[CHOICE],["metz","nancy"])

    def test_leaving_comparison_invalidates_context_without_plan_change(self):
        app,original=self._open_in_real_application()
        app.button(key="ux_sidebar_nav_0").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("ux114_review_context",app.session_state)
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_changed_wishlist_priority_invalidates_pending_context(self):
        app,original=self._open_in_real_application()
        wishes=app.session_state["ux502_interests"]
        app.session_state["ux502_interests"]=set_interest(
            wishes,"paris","maybe",self.discovery)
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("ux114_review_context",app.session_state)
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_financial_premise_change_requires_a_new_explicit_review(self):
        app,original=self._open_in_real_application()
        app.button(key="ux34_open_review").click().run()
        app.checkbox(key="ux34_apply_ack").check().run()
        days=app.number_input(key="ux34_days").value
        app.number_input(key="ux34_days").set_value(days+1).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertNotIn("ux34_review",app.session_state)
        self.assertNotIn("ux34_apply_ack",app.session_state)
        self.assertEqual(app.session_state["advisor_plan"],original)

    def test_real_widget_journey_confirms_only_official_base(self):
        app,original=self._open_in_real_application()
        app.button(key="ux34_open_review").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(app.button(key="ux34_confirm_apply").disabled)
        # Explicit checkbox is required before the apply action can be used.
        app.checkbox(key="ux34_apply_ack").check().run()
        app.button(key="ux34_confirm_apply").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        current=app.session_state["advisor_plan"]
        self.assertEqual(current["base_city"],"metz")
        self.assertGreater(current["revision"],original["revision"])
        for key in ("total_days","italy_days","packages","budget_scenario"):
            self.assertEqual(current[key],original[key])
        self.assertNotIn("ux114_review_base",app.session_state)
        self.assertTrue(any("Cidade-base oficial atualizada" in x.value
                            for x in app.success))


if __name__=="__main__":
    unittest.main()
