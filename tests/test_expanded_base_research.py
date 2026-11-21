"""Expanded evidence research never publishes fabricated 2027 rents or ranks."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest
from base_research_expanded_model import (
    PRESETS,COUNTRY_FLAGS,load_research,load_rail,
    observed_housing,normalized_score,research_overview,find_city,decision_readiness)

ROOT=Path(__file__).resolve().parents[1]


class ExpandedBaseResearchModelTests(unittest.TestCase):
    def setUp(self):
        self.study=load_research()
        self.rail=load_rail()

    def test_adaptive_candidate_count_and_no_2027_claim(self):
        result=research_overview(self.study)
        self.assertEqual(result["candidate_count"],len(self.study["cities"]))
        self.assertEqual(result["candidate_count"],34)
        self.assertEqual(result["shortlist_count"],12)
        self.assertEqual(result["housing_offer_count"],35)
        self.assertEqual(result["three_observed_offers"],11)
        self.assertEqual(result["three_eligible_2027_quotes"],0)
        self.assertEqual(result["ranking_ready_count"],0)
        self.assertEqual(result["country_counts"],
                         {"França":20,"Alemanha":9,"Bélgica":3,"Luxemburgo":2})
        self.assertTrue(all(c["ranking_status"]=="not_decision_ready"
                            for c in self.study["cities"]))

    def test_monthly_listing_median_is_not_full_stay_price(self):
        trier=observed_housing(find_city(self.study,"trier"))
        self.assertEqual(trier["median_eur_month"],1000)
        self.assertEqual(trier["two_adult_listings_documented"],3)
        self.assertIsNone(trier["total_for_56_to_60_nights_eur"])
        lille=observed_housing(find_city(self.study,"lille"))
        self.assertEqual(lille["count"],2)
        self.assertIsNone(lille["total_for_56_to_60_nights_eur"])
        kehl=observed_housing(find_city(self.study,"kehl"))
        self.assertEqual(kehl["count"],0)
        self.assertIsNone(kehl["median_eur_month"])
        self.assertFalse(decision_readiness(find_city(self.study,"trier"))["eligible_for_final_ranking"])

    def test_weighted_rank_never_rewards_missing_data(self):
        self.assertEqual({key:sum(values) for key,values in PRESETS.items()},
                         {"general":100,"economy":100,"explorer":100})
        for preset in PRESETS:
            empty=normalized_score({},preset)
            self.assertIsNone(empty["score_0_100"])
            self.assertEqual(empty["upper_bound"],100)
            self.assertEqual(empty["lower_bound"],0)
            self.assertEqual(empty["evidence_weight"],0)
        partial=normalized_score({"temporary_housing":100}, "general")
        self.assertIsNone(partial["score_0_100"])
        self.assertEqual(partial["lower_bound"],30)
        self.assertEqual(partial["upper_bound"],100)
        self.assertEqual(partial["evidence_weight"],30)
        full=normalized_score({x:75 for x in (
            "temporary_housing","rail_connectivity","viable_destinations",
            "outing_cost","daily_life_remote_work","practical_country_diversity")},
                              "general")
        self.assertEqual(full["score_0_100"],75)
        with self.assertRaises(ValueError):
            normalized_score({"outing_cost":-1},"explorer")

    def test_rail_sources_mean_vs_min_are_distinct_and_not_2027(self):
        self.assertEqual(len(self.rail["segments"]),11)
        new={(r["from"],r["to"]) for r in self.rail["segments"]}
        self.assertTrue({
            ("nancy","luxembourg_city"),("dijon","beaune"),
            ("strasbourg","mulhouse"),("karlsruhe","strasbourg"),
            ("aachen","cologne")
        } <= new)
        self.assertTrue(all(not r.get("return_verified_2027",False)
                            for r in self.rail["segments"]))
        off=next(r for r in self.rail["segments"] if r["from"]=="offenburg")
        self.assertEqual(off["fastest_minutes"],25)
        self.assertEqual(off["representative_regional_minutes"],29)
        self.assertEqual(off["average_minutes"],34)
        self.assertEqual(off["services_on_sample_day"],27)
        self.assertEqual(self.rail["basis_date"],"2026-11-16")
        self.assertTrue(all(x["source_url"].startswith("https://")
                            for x in self.rail["segments"]))
        germany=next(p for p in self.rail["passes"]
                     if p["country"]=="Alemanha")
        self.assertEqual(germany["monthly_cost_eur_2027"],66.8)

    def test_read_only_screening_does_not_modify_data(self):
        original=deepcopy(self.study)
        for city in self.study["cities"]:
            observed_housing(city)
            decision_readiness(city)
        research_overview(self.study)
        self.assertEqual(original,self.study)


class ExpandedBaseResearchAppTests(unittest.TestCase):
    def test_new_mode_navigation_preserves_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux42_city_activity").set_value("Comparar favoritas").run()
        original=deepcopy(app.session_state["advisor_plan"])
        self.assertEqual(app.session_state["ux42_city_activity"],"Comparar favoritas")
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        # UX 4.0: filters and city details are contextual rather than on entry.
        self.assertEqual(app.session_state["ux42_city_activity"],"Comparar favoritas")
        app.segmented_control(key="ux42_city_activity").set_value(
            "Explorar cidades").run()
        self.assertIn("expanded_bases_country_filter",{x.key for x in app.selectbox})
        app.segmented_control(key="ux42_city_activity").set_value(
            "Explorar cidades").run()
        self.assertIn("expanded_bases_detail_city",{x.key for x in app.selectbox})
        self.assertIn("expanded_bases_rank_preset",{x.key for x in app.segmented_control})
        app.selectbox(key="expanded_bases_detail_city").set_value("trier").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)


if __name__=="__main__":
    unittest.main()
