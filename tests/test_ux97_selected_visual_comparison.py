"""UX97: visual comparison is a read-only view of UX87 and CHOICE."""
from __future__ import annotations
import unittest
from copy import deepcopy
from streamlit.testing.v1 import AppTest
from ux97_comparison_visual_ui import selected_matrix_html,summary_panel_html,_cell_html
from ux502_destination_interests_model import empty_interests,set_interest
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
from rec03b_handoffs import CHOICE

APP="""
import streamlit as st
from rec03a_suggestions_ui import render_recommendation_activity
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
if "advisor_plan" not in st.session_state:
    st.session_state["advisor_plan"]=new_plan()
render_recommendation_activity(plan=st.session_state["advisor_plan"],
                               discovery=build_exploration_discovery())
"""


def fixture(n=2):
    bases=[f"base_{i}" for i in range(n)]
    return {
        "base_ids":bases,
        "names":{base:base.replace("_"," ").title() for base in bases},
        "destinations":[{"id":"paris","name":"Paris","priority":"must_visit"},
                        {"id":"basel","name":"Basileia","priority":"interested"}],
        "cells":{(base,d):{"category":"historical","display_min":75,
                           "label":"1h15 · histórico",
                           "source_url":"https://example.com/rail"}
                 for base in bases for d in ("paris","basel")},
        "common_timed_destination_ids":["paris","basel"],
        "counts":{base:{"historical":2,"reference_only":0,"local":0,
                        "no_time":0} for base in bases}
    }


class VisualProjectionTests(unittest.TestCase):
    def test_same_scope_two_three_five_bases_with_no_new_times(self):
        for n in (2,3,5):
            with self.subTest(n=n):
                data=fixture(n)
                before=deepcopy(data)
                html=selected_matrix_html(data)
                self.assertIn('class="ux97-table"',html)
                self.assertEqual(html.count("<tr>"),3)
                self.assertEqual(html.count("<td>"),n*2)
                self.assertEqual(html.count("1h15"),n*2)
                self.assertIn("★",html)
                self.assertIn("2 / 2",summary_panel_html(data))
                self.assertEqual(data,before)

    def test_badges_are_semantic_and_unknown_has_no_implicit_zero(self):
        expected=(("historical","Histórico"),("reference_only","Indicativo"),
                  ("local","Acesso local pendente"),("no_time","Sem tempo"))
        for category,label in expected:
            cell={"category":category,"display_min":70 if category in
                  ("historical","reference_only") else None}
            html=_cell_html(cell)
            self.assertIn(label,html)
            if category in ("local","no_time"):
                self.assertNotIn("0 min",html)
                self.assertNotIn("1h10",html)
        with self.assertRaises(ValueError):
            _cell_html({"category":"no_time","display_min":15})
        with self.assertRaises(ValueError):
            _cell_html({"category":"historical","display_min":None})

    def test_escaping_and_source_caveat_accessibility(self):
        data=fixture(2)
        data["names"][data["base_ids"][0]]='<script>alert(1)</script>'
        data["destinations"][0]["name"]="<b>Paris</b>"
        data["cells"][(data["base_ids"][0],"paris")]["label"]='<img src=x onerror=alert(1)>'
        data["cells"][(data["base_ids"][0],"paris")]["station_caveat"]="verificar"
        result=selected_matrix_html(data)
        self.assertNotIn("<script>",result)
        self.assertNotIn("<b>Paris</b>",result)
        self.assertNotIn("<img ",result)
        self.assertIn("&lt;script&gt;",result)
        self.assertIn("ⓘ",result)
        self.assertIn("role=\"region\"",result)

    def test_reject_invalid_scope_or_duplicate_cells(self):
        data=fixture(2)
        data["cells"].pop((data["base_ids"][0],"paris"))
        with self.assertRaises(ValueError):
            selected_matrix_html(data)
        data=fixture(1)
        with self.assertRaises(ValueError):
            selected_matrix_html(data)


class SelectedVisualAppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def test_visual_matrix_always_shows_selected_and_technical_sources_stay_optional(self):
        app=AppTest.from_string(APP,default_timeout=120)
        wishes=empty_interests()
        for city in ("colmar","paris","strasbourg"):
            wishes=set_interest(wishes,city,"interested",self.discovery)
        plan=new_plan()
        app.session_state["ux502_interests"]=deepcopy(wishes)
        app.session_state["advisor_plan"]=deepcopy(plan)
        app.session_state["rec03a_identity"]="unconfigured"
        app.run()
        app.button(key="rec03a_confirm_subset").click().run()
        picks=[x.key for x in app.checkbox if x.key and x.key.startswith("rec03a_pick_")]
        self.assertGreaterEqual(len(picks),2)
        for key in picks[:2]:
            app.checkbox(key=key).check().run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(len(app.session_state[CHOICE]),2)
        self.assertTrue(any("ux97-table" in m.value for m in app.markdown))
        self.assertTrue(any("ux97-metrics" in m.value for m in app.markdown))
        # The native UX87 technical table is still opt-in.
        self.assertTrue(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        app.checkbox(key="rec03a_inline_matrix").check().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertGreaterEqual(len(app.dataframe),1)
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)


if __name__=="__main__":
    unittest.main()
