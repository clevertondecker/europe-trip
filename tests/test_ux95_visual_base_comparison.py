"""UX95: same-scope visual comparison; never reinterpret evidence as a global rank."""
import unittest
from copy import deepcopy

from streamlit.testing.v1 import AppTest

from base_recommendation_model import recommend_bases
from rec03a_suggestions_ui import (comparison_overview_rows, _overview_cell,
                                     _overview_caveats, _render_quick_comparison)
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests,set_interest
from trip_plan_model import new_plan
from rec03b_handoffs import CHOICE

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

    def test_material_caveats_are_visible_without_reclassifying_evidence(self):
        historical={"category":"historical","display_min":31,
                    "legacy_divergent_sources":True,
                    "station_caveat":"Estação de saída a verificar",
                    "evidence_notes":"Conferir dias de operação",
                    "label":"31 min · histórico · tempos publicados diferentes",
                    "source_url":"https://example.org/historico",
                    "gap_checked_at":"2026-11-01"}
        label=_overview_cell(historical)
        self.assertIn("Histórico · 31 min",label)
        self.assertIn("ver ressalvas",label)
        self.assertIn("Tempos publicados divergentes",_overview_caveats(historical))
        self.assertIn("Estações a verificar",_overview_caveats(historical))
        self.assertIn("Observações da fonte",_overview_caveats(historical))
        indicative={"category":"reference_only","display_min":55,
                    "station_comparability":"city_level_ambiguous",
                    "label":"~55 min · estação pendente"}
        self.assertIn("Indicativo · 55 min",_overview_cell(indicative))
        self.assertIn("ver ressalvas",_overview_cell(indicative))
        self.assertEqual(_overview_caveats({"category":"historical","display_min":30}),[])
        self.assertEqual(_overview_cell({"category":"no_time","display_min":None,
                                         "label":"Tempo não pesquisado"}),
                         "Sem tempo pesquisado")

    def test_zero_one_two_four_visible_bases_and_scope_order(self):
        names={"a":"A","b":"B"}
        cities={str(i):{"name":"Cidade "+str(i),"country":"França"}
                for i in range(4)}
        cells={"a":{"category":"no_time","display_min":None},
               "b":{"category":"local","display_min":None}}
        result={"destinations":[{"id":"b","priority":"interested"},
                                {"id":"a","priority":"must_visit"}],
                "candidates":[{"base_id":str(i),"evidence":deepcopy(cells)}
                              for i in range(4)]}
        original=deepcopy(result)
        self.assertEqual(comparison_overview_rows(result,names,cities,[]),[
            {"Destino desejado":"B"},{"Destino desejado":"★ A"}])
        for count in (1,2,4):
            with self.subTest(count=count):
                rows=comparison_overview_rows(
                    result,names,cities,[str(i) for i in range(count)])
                self.assertEqual(len(rows),2)
                self.assertEqual(len(rows[0]),count+1)
                self.assertEqual([r["Destino desejado"] for r in rows],
                                 ["B","★ A"])
        self.assertEqual(len(comparison_overview_rows(
            result,names,cities,["0","0","1"])[0]),3)
        self.assertEqual(result,original)

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

    def app(self, destinations=("colmar","strasbourg","paris","basel")):
        a=AppTest.from_string(APP,default_timeout=120)
        wishes=empty_interests()
        for place in destinations:
            wishes=set_interest(wishes,place,"interested",self.discovery)
        plan=new_plan()
        a.session_state["ux502_interests"]=wishes
        a.session_state["advisor_plan"]=deepcopy(plan)
        a.session_state["rec03a_identity"]="unconfigured"
        a.run()
        a.button(key="rec03a_confirm_subset").click().run()
        self.assertFalse(a.exception,[x.message for x in a.exception])
        return a,plan,wishes

    def test_no_preview_before_selection_and_one_canonical_comparison_afterward(self):
        app,plan,wishes=self.app()
        self.assertFalse(any("ux97-table" in x.value for x in app.markdown))
        self.assertFalse(any("Destino desejado" in x.value.columns for x in app.dataframe))
        self.assertFalse(any(x.label=="Prévia das sugestões · não é sua seleção"
                             for x in app.expander))
        picks=[x.key for x in app.checkbox
               if x.key and x.key.startswith("rec03a_pick_")]
        self.assertGreaterEqual(len(picks),2)
        app.checkbox(key=picks[0]).check().run()
        self.assertFalse(any("ux97-table" in x.value for x in app.markdown))
        app.checkbox(key=picks[1]).check().run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(sum("ux97-table" in x.value for x in app.markdown),1)
        self.assertFalse(any("Destino desejado" in x.value.columns for x in app.dataframe))
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)

    def test_legacy_preview_helpers_kept_but_not_rendered(self):
        import inspect
        from rec03a_suggestions_ui import render_suggestions
        source=inspect.getsource(render_suggestions)
        self.assertNotIn("_render_quick_comparison(",source)
        self.assertEqual(source.count("render_inline_comparison("),1)

    def test_single_filtered_city_offers_direct_investigation(self):
        app,plan,wishes=self.app(("colmar",))
        app.checkbox(key="rec03a_show_all").check().run()
        app.text_input(key="rec03a_search").set_value("Metz").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("Metz" in x.value and "ux96-city-header" in x.value
                            for x in app.markdown))
        self.assertIn("rec03a_handoff_profile_card_metz",{x.key for x in app.button})
        self.assertFalse(any("ux97-table" in x.value for x in app.markdown))
        app.text_input(key="rec03a_search").set_value("cidade-que-nao-existe-ux95").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertFalse(any("ux96-city-header" in x.value for x in app.markdown))
        app.text_input(key="rec03a_search").set_value("").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)

    def test_browsing_filters_and_pagination_preserve_selection(self):
        app,plan,wishes=self.app(("colmar","paris"))
        app.checkbox(key="rec03a_show_all").check().run()
        self.assertLessEqual(sum(x.key.startswith("rec03a_pick_")
                                 for x in app.checkbox if x.key),4)
        first=next(x.key for x in app.checkbox
                   if x.key and x.key.startswith("rec03a_pick_"))
        app.checkbox(key=first).check().run()
        selected=deepcopy(app.session_state[CHOICE])
        app.text_input(key="rec03a_search").set_value("Metz").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state[CHOICE],selected)
        self.assertFalse(any("ux97-table" in x.value for x in app.markdown))
        if first!="rec03a_pick_metz":
            app.checkbox(key="rec03a_pick_metz").check().run()
            self.assertEqual(len(app.session_state[CHOICE]),2)
            self.assertEqual(sum("ux97-table" in x.value for x in app.markdown),1)
        self.assertEqual(app.session_state["advisor_plan"],plan)
        self.assertEqual(app.session_state["ux502_interests"],wishes)


if __name__=="__main__":
    unittest.main()
