"""UX96: cosmetic components cannot invent photos, metrics or selection."""
import unittest
from html import escape
from streamlit.testing.v1 import AppTest
from ux96_comparison_visual_ui import city_card_header,selected_context


class ComparisonVisualShellTests(unittest.TestCase):
    def setUp(self):
        self.city={"name":"Mulhouse","country":"França"}
        self.candidate={"historical_count":4,"indicative_count":2,
                        "local_destination_ids":[],"missing_destination_ids":[]}

    def test_real_counts_and_no_image(self):
        html=city_card_header(self.candidate,self.city,is_selected=True)
        for text in ("Mulhouse","França","4 Históricos","2 Indicativos",
                     "0 Locais pendentes","0 Sem tempo","Selecionada"):
            self.assertIn(text,html)
        self.assertNotIn("<img",html.lower())
        self.assertNotIn("€",html)
        self.assertNotIn("melhor",html.lower())
        self.assertNotIn("Reservada",html)

    def test_escaped_city_and_country(self):
        html=city_card_header(self.candidate,
            {"name":"<script>alert(1)</script>","country":"FR & <BR>"})
        self.assertIn("&lt;script&gt;",html)
        self.assertIn("FR &amp; &lt;BR&gt;",html)
        self.assertNotIn("<script>",html)

    def test_selection_strip_is_read_only_deduplicated_upstream(self):
        cities={"colmar":{"name":"Colmar"},"mulhouse":{"name":"Mulhouse"}}
        value=selected_context(["colmar","mulhouse"],cities,6)
        self.assertIn("Colmar",value)
        self.assertIn("Mulhouse",value)
        self.assertIn(">6</strong>",value)
        self.assertNotIn("<input",value)
        self.assertIn("Selecione cidades",selected_context([],cities,6))

    def test_native_checkbox_preserved_in_rendered_card(self):
        code="""
import streamlit as st
from rec03a_suggestions_ui import _card
candidate={"base_id":"colmar","historical_count":0,"indicative_count":4,
           "local_destination_ids":["colmar"],"missing_destination_ids":["x"],
           "must_visit":{"missing":[]},"reasons":[],"weighted_coverage":{"value":None},
           "coverage_limitation":"Pesquisa parcial","evidence":{},
           "raw_rail_evidence":{},"limitation":"Pesquisa parcial"}
_card(candidate,{}, {},{"colmar":{"name":"Colmar","country":"França"}},
      "mulhouse",["colmar"])
"""
        app=AppTest.from_string(code,default_timeout=60).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(len([x for x in app.checkbox
                              if x.key=="rec03a_pick_colmar"]),1)
        self.assertTrue(any("ux96-city-header" in x.value for x in app.markdown))
