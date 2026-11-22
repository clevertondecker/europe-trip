"""UX95: same-scope visual comparison; never reinterpret evidence as a global rank."""
import unittest
from copy import deepcopy

from streamlit.testing.v1 import AppTest

from base_recommendation_model import recommend_bases
from rec03a_suggestions_ui import comparison_overview_rows, _overview_cell
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,set_interest
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


class QuickComparisonProjectionTests(unittest.TestCase):
    def test_evidence_categories_do_not_infer_roundtrip_or_time(self):
        self.assertTrue(_overview_cell({"category":"historical","display_min":75}).startswith("Histórico · "))
        self.assertTrue(_overview_cell({"category":"reference_only","display_min":85}).startswith("Indicativo · "))
        self.assertEqual(_overview_cell({"category":"local","display_min":None}),
                         "Local · acesso pendente")
        self.assertEqual(_overview_cell({"category":"no_time","display_min":None}),
                         "Sem tempo pesquisado")

    def test_same_destinations_under_each_city_preserves_priorities_and_sources(self):
        result={"candidates":[
            {"base_id":"mulhouse","evidence":{
                "colmar":{"category":"historical","display_min":31,"source_url":"https://example.org"},
                "basel":{"category":"reference_only","display_min":43}}},
            {"base_id":"metz","evidence":{
                "colmar":{"category":"no_time","display_min":None},
                "basel":{"category":"local","display_min":None}}},
        ],"destinations":[{"id":"colmar","priority":"must_visit"},
                           {"id":"basel","priority":"interested"}]}
        cities={"mulhouse":{"name":"Mulhouse","country":"França"},
                "metz":{"name":"Metz","country":"França"}}
        original=deepcopy((result,cities))
        rows=comparison_overview_rows(result,{"colmar":"Colmar","basel":"Basileia"},
                                      cities,["mulhouse","metz","mulhouse"])
        self.assertEqual(len(rows),2)
        self.assertEqual(list(rows[0]),["Destino desejado","Mulhouse · França","Metz · França"])
        self.assertEqual(rows[0]["Destino desejado"],"★ Colmar")
        self.assertTrue(rows[0]["Mulhouse · França"].startswith("Histórico"))
        self.assertEqual(rows[0]["Metz · França"],"Sem tempo pesquisado")
        self.assertEqual(rows[1]["Metz · França"],"Local · acesso pendente")
        self.assertEqual((result,cities),original)


class QuickComparisonAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def test_matrix_is_visible_before_selection_and_plan_is_unchanged(self):
        app=AppTest.from_string(APP,default_timeout=120)
        wishes=empty_interests()
        for destination in ("colmar","strasbourg","paris","basel"):
            wishes=set_interest(wishes,destination,"interested",self.discovery)
        app.session_state["ux502_interests"]=wishes
        app.session_state["advisor_plan"]=new_plan()
        app.session_state["rec03a_identity"]="unconfigured"
        app.run()
        app.button(key="rec03a_confirm_subset").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        tables=[x for x in app.dataframe if x.key=="rec03a_quick_matrix"]
        self.assertEqual(len(tables),1)
        self.assertEqual(len(tables[0].value),4)
        self.assertGreaterEqual(len(tables[0].value.columns),3)
        before=deepcopy(app.session_state["advisor_plan"])
        picks=[x.key for x in app.checkbox
               if x.key and x.key.startswith("rec03a_pick_")]
        self.assertGreaterEqual(len(picks),2)
        app.checkbox(key=picks[0]).check().run()
        app.checkbox(key=picks[1]).check().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],before)
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        self.assertEqual(len([x for x in app.dataframe
                              if x.key=="rec03a_quick_matrix"]),1)

    def test_browse_is_paged_and_scope_and_selection_remain_canonical(self):
        app=AppTest.from_string(APP,default_timeout=120)
        wishes=set_interest(empty_interests(),"colmar","must_visit",self.discovery)
        wishes=set_interest(wishes,"paris","interested",self.discovery)
        app.session_state["ux502_interests"]=wishes
        app.session_state["advisor_plan"]=new_plan()
        app.session_state["rec03a_identity"]="unconfigured"
        app.run()
        app.button(key="rec03a_confirm_subset").click().run()
        app.checkbox(key="rec03a_show_all").check().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        matrix=[x for x in app.dataframe if x.key=="rec03a_quick_matrix"]
        self.assertEqual(len(matrix),1)
        self.assertLessEqual(len(matrix[0].value.columns),5)
        self.assertEqual(len(matrix[0].value),2)
        first=next(x.key for x in app.checkbox
                   if x.key and x.key.startswith("rec03a_pick_"))
        app.checkbox(key=first).check().run()
        selected=deepcopy(app.session_state.get("rec03b_selected_base_ids",[]))
        app.text_input(key="rec03a_search").set_value("Metz").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],new_plan())
        self.assertEqual(len([x for x in app.dataframe
                              if x.key=="rec03a_quick_matrix"]),1)


if __name__=="__main__":
    unittest.main()
