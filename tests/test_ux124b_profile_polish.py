"""UX124B visual contracts: evidence-preserving compact presentation."""
import unittest
from copy import deepcopy
from streamlit.testing.v1 import AppTest
from base_research_expanded_model import load_research
from city_profiles_model import load_profiles
from ux124_city_profile_model import city_profile,personalize_routes
from ux124b_profile_presentation import city_intro,practical_facts,compact_money,route_preview,route_display,route_list_html,ticket_text

class ProfilePolishTests(unittest.TestCase):
    def test_intro_and_fact_dedup_without_mutating_any_profile(self):
        rows=load_profiles(canonical=load_research(include_candidates=True))["cities"]
        original=deepcopy(rows)
        for profile in rows:
            intro=city_intro(profile)
            self.assertNotIn("Cidade cadastrada no corredor",intro)
            self.assertTrue(intro)
            self.assertLessEqual(len(practical_facts(profile)),2)
            self.assertNotIn(intro,practical_facts(profile))
        self.assertEqual(rows,original)

    def test_currency_and_ticket(self):
        self.assertEqual(compact_money(1350),"€ 1.350")
        self.assertEqual(compact_money(1350.5),"€ 1.350,50")
        self.assertEqual(compact_money(None),"Não pesquisado")
        self.assertIn("ida e volta",ticket_text({"amount":12,"per":"adult_return","currency":"EUR"}))
        self.assertNotIn("gratuito",ticket_text({}).lower())

    def test_preview_includes_missing_local_and_priorities(self):
        v=city_profile("mulhouse")
        routes=personalize_routes(v["routes"],{"basel":"interested","paris":"maybe","mulhouse":"must_visit","colmar":"discarded"})
        selected=route_preview(routes)
        self.assertEqual([r["destination_id"] for r in selected],["mulhouse","basel","paris"])
        self.assertEqual(route_display(selected[0])["time"],"Local")
        original=deepcopy(routes)
        self.assertIn("Basel",route_list_html(selected))
        self.assertEqual(routes,original)
        fake={"name":"<script>","cell":{"category":"no_time","label":"Tempo não pesquisado"},"priority":"must_visit"}
        self.assertNotIn("<script>",route_list_html([fake]))
        self.assertIn("Sem tempo",route_list_html([fake]))

    def test_preview_does_not_hide_missing_imperdible_or_change_cell(self):
        rows=[{"destination_id":"missing","name":"Sem dado","priority":"must_visit",
               "cell":{"category":"no_time","label":"Tempo não pesquisado"}},
              {"destination_id":"local","name":"Local","priority":"interested",
               "cell":{"category":"local","label":"Local — acesso a verificar"}},
              {"destination_id":"rail","name":"Trem","priority":"maybe",
               "cell":{"category":"historical","display_min":20,
                       "label":"20 min · histórico · tempos publicados diferentes"}}]
        original=deepcopy(rows)
        preview=route_preview(rows)
        self.assertEqual(preview,rows)
        self.assertEqual(route_display(preview[2])["time"],"20 min")
        self.assertIn("tempos publicados diferentes",route_display(preview[2])["qualifier"])
        self.assertEqual(rows,original)

    def test_overview_navigation_single_details_and_no_eager_other_topics(self):
        app=AppTest.from_string(
            'from ux124_city_profile_ui import render_city_profile\n'
            'from ux502_destination_interests_model import empty_interests,set_interest\n'
            'import streamlit as st\n'
            'if "ux502_interests" not in st.session_state: st.session_state["ux502_interests"]=set_interest(empty_interests(),"basel","must_visit")\n'
            'render_city_profile("mulhouse")',default_timeout=120).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.metric[0].value,"€ 1.350")
        self.assertEqual(app.metric[1].value,"1 de 1")
        self.assertEqual([e.label for e in app.expander],["Fontes e pendências da pesquisa"])
        self.assertFalse(any("Investigue por assunto" in m.value for m in app.markdown))
        self.assertTrue(any("ux124b-routes" in m.value for m in app.markdown))
        self.assertFalse(app.dataframe)
        before=deepcopy(app.session_state["ux502_interests"])
        app.button(key="ux124_overview_logistics_mulhouse").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.segmented_control(key="ux124_topic_mulhouse").value,"Logística")
        self.assertEqual(app.segmented_control(key="ux124_routes_mulhouse").value,"Minha lista")
        self.assertTrue(app.dataframe)
        self.assertEqual(app.session_state["ux502_interests"],before)

if __name__=="__main__":
    unittest.main()
