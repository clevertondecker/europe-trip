"""UX96: cosmetic components cannot invent photos, metrics or selection."""
import unittest
from copy import deepcopy
from html import escape
from streamlit.testing.v1 import AppTest
from ux96_comparison_visual_ui import city_card_header,selected_context
from rec03b_handoffs import CHOICE
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests, set_interest
from trip_plan_model import new_plan


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


APP = """
import streamlit as st
from rec03a_suggestions_ui import render_recommendation_activity
from trip01_supplemental_discovery import build_exploration_discovery
from trip_plan_model import new_plan
if "advisor_plan" not in st.session_state:
    st.session_state["advisor_plan"] = new_plan()
render_recommendation_activity(plan=st.session_state["advisor_plan"],
                               discovery=build_exploration_discovery())
"""


class ComparisonVisualIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery=build_exploration_discovery()

    def _confirmed_app(self):
        app=AppTest.from_string(APP,default_timeout=120)
        wishes=empty_interests()
        for place in ("colmar","paris","strasbourg","angers","basel"):
            wishes=set_interest(wishes,place,"interested",self.discovery)
        app.session_state["ux502_interests"]=wishes
        app.session_state["advisor_plan"]=new_plan()
        app.session_state["rec03a_identity"]="unconfigured"
        app.run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.button(key="rec03a_confirm_subset").click().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        return app

    def _selected_strip(self,app):
        strips=[m.value for m in app.markdown if 'class="ux96-selection-strip"' in m.value]
        self.assertEqual(len(strips),1)
        return strips[0]

    def _assert_unchanged(self,app,original_plan,original_wishes):
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original_plan)
        self.assertEqual(app.session_state["ux502_interests"],original_wishes)
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],
                         original_plan["base_city"])
        self.assertFalse(any(x.key==CHOICE+"_widget" for x in app.multiselect))

    def test_choice_strip_cards_and_ux87_sync_on_select_and_unselect(self):
        app=self._confirmed_app()
        original_plan=deepcopy(app.session_state["advisor_plan"])
        original_wishes=deepcopy(app.session_state["ux502_interests"])
        self.assertIn("Selecione cidades",self._selected_strip(app))
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        self.assertFalse(any(x.label=="Conhecer cidade, mapa e custos" for x in app.expander))

        app.checkbox(key="rec03a_show_all").check().run()
        app.text_input(key="rec03a_search").set_value("Mulhouse").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.checkbox(key="rec03a_pick_mulhouse").check().run()
        self.assertEqual(app.session_state[CHOICE],["mulhouse"])
        self.assertIn("Mulhouse",self._selected_strip(app))
        self.assertTrue(any(x.label=="Conhecer cidade, mapa e custos" for x in app.expander))
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        self._assert_unchanged(app,original_plan,original_wishes)

        app.text_input(key="rec03a_search").set_value("Metz").run()
        self.assertIn("Mulhouse",self._selected_strip(app))
        app.checkbox(key="rec03a_pick_metz").check().run()
        self.assertEqual(app.session_state[CHOICE],["mulhouse","metz"])
        self.assertIn("Mulhouse",self._selected_strip(app))
        self.assertIn("Metz",self._selected_strip(app))
        self.assertTrue(app.checkbox(key="rec03a_pick_metz").value)
        cards=[x.value for x in app.markdown if "ux96-city-header" in x.value]
        self.assertTrue(any("Metz" in x and "Selecionada" in x for x in cards))
        self.assertTrue(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        self.assertEqual(sum("#### Cidades selecionadas" in x.value
                             for x in app.markdown),0)
        self.assertFalse(any("2 de até 5 cidades selecionadas" in x.value
                             for x in app.markdown))
        self._assert_unchanged(app,original_plan,original_wishes)

        app.checkbox(key="rec03a_pick_metz").uncheck().run()
        self.assertEqual(app.session_state[CHOICE],["mulhouse"])
        self.assertIn("Mulhouse",self._selected_strip(app))
        self.assertNotIn("Metz",self._selected_strip(app))
        self.assertFalse(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        self._assert_unchanged(app,original_plan,original_wishes)

    def test_search_and_pagination_preserve_off_page_choice_and_visual_state(self):
        app=self._confirmed_app()
        plan=deepcopy(app.session_state["advisor_plan"])
        wishes=deepcopy(app.session_state["ux502_interests"])
        app.checkbox(key="rec03a_show_all").check().run()
        app.text_input(key="rec03a_search").set_value("Mulhouse").run()
        app.checkbox(key="rec03a_pick_mulhouse").check().run()
        app.text_input(key="rec03a_search").set_value("Metz").run()
        app.checkbox(key="rec03a_pick_metz").check().run()
        before=list(app.session_state[CHOICE])
        app.text_input(key="rec03a_search").set_value("").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        app.number_input(key="rec03a_page").set_value(2).run()
        self.assertEqual(app.session_state[CHOICE],before)
        self.assertIn("Mulhouse",self._selected_strip(app))
        self.assertIn("Metz",self._selected_strip(app))
        self._assert_unchanged(app,plan,wishes)

        app.text_input(key="rec03a_search").set_value("Mulhouse").run()
        self.assertTrue(app.checkbox(key="rec03a_pick_mulhouse").value)
        cards=[x.value for x in app.markdown if "ux96-city-header" in x.value]
        self.assertTrue(any("Mulhouse" in x and "Selecionada" in x for x in cards))
        app.checkbox(key="rec03a_show_all").uncheck().run()
        self.assertEqual(app.session_state[CHOICE],before)
        self._assert_unchanged(app,plan,wishes)

    def test_five_choices_through_widgets_enforce_limit_and_allow_replacement(self):
        app=self._confirmed_app()
        plan=deepcopy(app.session_state["advisor_plan"])
        wishes=deepcopy(app.session_state["ux502_interests"])
        app.checkbox(key="rec03a_show_all").check().run()
        picks=[x.key for x in app.checkbox if x.key and x.key.startswith("rec03a_pick_")]
        self.assertEqual(len(picks),4)
        chosen=[]
        for key in picks:
            self.assertFalse(app.checkbox(key=key).disabled)
            app.checkbox(key=key).check().run()
            chosen.append(key.removeprefix("rec03a_pick_"))
            self.assertEqual(list(app.session_state[CHOICE]),chosen)
            self.assertTrue(app.checkbox(key=key).value)
            self._assert_unchanged(app,plan,wishes)

        app.number_input(key="rec03a_page").set_value(2).run()
        next_page=[x.key for x in app.checkbox
                   if x.key and x.key.startswith("rec03a_pick_")]
        self.assertGreaterEqual(len(next_page),2)
        fifth,sixth=next_page[:2]
        self.assertFalse(app.checkbox(key=fifth).disabled)
        app.checkbox(key=fifth).check().run()
        chosen.append(fifth.removeprefix("rec03a_pick_"))
        self.assertEqual(list(app.session_state[CHOICE]),chosen)
        self.assertEqual(len(chosen),5)
        self.assertTrue(app.checkbox(key=fifth).value)
        self.assertTrue(app.checkbox(key=sixth).disabled)
        self.assertFalse(app.checkbox(key=sixth).value)
        strip=self._selected_strip(app)
        for base in chosen:
            self.assertIn(base,app.session_state[CHOICE])
        self.assertEqual(strip.count('class="ux96-selected-chip"'),5)
        self.assertTrue(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        self._assert_unchanged(app,plan,wishes)

        app.checkbox(key=fifth).uncheck().run()
        chosen.remove(fifth.removeprefix("rec03a_pick_"))
        self.assertEqual(list(app.session_state[CHOICE]),chosen)
        self.assertFalse(app.checkbox(key=sixth).disabled)
        app.checkbox(key=sixth).check().run()
        chosen.append(sixth.removeprefix("rec03a_pick_"))
        self.assertEqual(list(app.session_state[CHOICE]),chosen)
        self.assertEqual(len(app.session_state[CHOICE]),5)
        self.assertEqual(self._selected_strip(app).count('class="ux96-selected-chip"'),5)
        self.assertTrue(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        app.run()
        self.assertEqual(list(app.session_state[CHOICE]),chosen)
        self.assertTrue(app.checkbox(key=sixth).value)
        self._assert_unchanged(app,plan,wishes)

    def test_five_selected_cities_wrap_without_parallel_selection(self):
        from base_research_expanded_model import load_research
        app=self._confirmed_app()
        plan=deepcopy(app.session_state["advisor_plan"])
        wishes=deepcopy(app.session_state["ux502_interests"])
        choices=[c["id"] for c in load_research(include_candidates=True)["cities"]][:5]
        app.session_state[CHOICE]=choices
        app.run()
        strip=self._selected_strip(app)
        for base in choices:
            self.assertIn(base and next(x["name"] for x in
                load_research(include_candidates=True)["cities"] if x["id"]==base),strip)
        self.assertEqual(len(app.session_state[CHOICE]),5)
        self.assertTrue(any(x.key=="rec03a_inline_matrix" for x in app.checkbox))
        self._assert_unchanged(app,plan,wishes)
