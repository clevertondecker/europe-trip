"""Regression tests: research documentation cannot become fake city ratings."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from base_coverage_model import (
    REQUIREMENTS,coverage_matrix,coverage_summary,city_evidence,
)
from base_research_expanded_model import load_research,load_rail,PRESETS
from five_base_comparison_model import load_five_base_evidence
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class CoverageModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research=load_research()
        cls.five=load_five_base_evidence()
        cls.general=coverage_matrix("general")
        cls.by_id={r["id"]:r for r in cls.general}

    def test_all_30_are_represented_and_shortlist_is_12(self):
        self.assertEqual(len(self.general),30)
        expected={"mulhouse","strasbourg","metz","nancy","lille","dijon",
                  "freiburg","offenburg","karlsruhe","trier","aachen","liege"}
        self.assertEqual({r["id"] for r in self.general if r["shortlist"]},
                         expected)
        self.assertEqual(coverage_summary(self.general)["shortlist"],12)

    def test_housing_study_is_visible_but_not_bookable_2027(self):
        for name in ("mulhouse","strasbourg","metz","nancy","offenburg"):
            row=self.by_id[name]
            self.assertGreater(row["housing"]["count"],0)
            self.assertGreater(row["documentary_weighted_percent"],0)
            self.assertIsNone(row["score_0_100"])
            self.assertEqual(row["scoring_weight_percent"],0)
            self.assertEqual(row["housing"]["total_for_56_to_60_nights_eur"],None)
            self.assertFalse(row["decision_ready"])

    def test_documentary_coverage_is_separate_from_scoring_coverage(self):
        row=self.by_id["strasbourg"]
        self.assertGreater(row["route_basket_with_time"],0)
        self.assertGreater(row["route_time_coverage_percent"],0)
        self.assertLessEqual(row["route_basket_with_time"],15)
        self.assertEqual(row["route_return_verified"],0)
        self.assertGreater(row["criteria"]["rail_connectivity"]["documented_count"],0)
        self.assertEqual(row["criteria"]["rail_connectivity"]["comparable_score"],None)
        self.assertTrue(all(r["scoring_weight_percent"]==0 for r in self.general))

    def test_frozen_weights_and_documentary_facts_between_profiles(self):
        self.assertTrue(all(sum(weights)==100 for weights in PRESETS.values()))
        for profile in PRESETS:
            rows=coverage_matrix(profile)
            self.assertEqual(len(rows),30)
            for row in rows:
                before=self.by_id[row["id"]]
                self.assertEqual(row["criteria"],before["criteria"])
                self.assertEqual(row["route_basket_with_time"],
                                 before["route_basket_with_time"])
                self.assertIsNone(row["score_0_100"])

    def test_no_listing_url_or_unobserved_train_becomes_price_or_route(self):
        for row in self.general:
            for source in row["evidence"]:
                self.assertTrue(source["source_url"].startswith("https://"))
                self.assertFalse(source["comparable_for_final_score"])
                self.assertTrue(source["revalidate_for_2027"])
                if source["criterion"]=="outing_cost":
                    self.assertIsInstance(source["value"],(int,float))
                    self.assertGreater(source["value"],0)
                    self.assertEqual(source["unit"],"EUR/pessoa/ida")
            self.assertLessEqual(row["route_basket_with_time"],15)

    def test_empty_city_is_not_scored_zero(self):
        dummy=deepcopy(self.research["cities"][0])
        dummy["id"]="unresearched_test_city"
        dummy["housing_offers"]=[]
        dummy["country"]="Chile"
        dummy["shortlist"]=False
        dummy["eligible_2027_quotes"]=0
        row=city_evidence(dummy,study=self.research)
        self.assertEqual(row["documentary_weighted_percent"] if
                         "documentary_weighted_percent" in row else 0,0)
        self.assertEqual(row["status"],"Não pesquisado")
        self.assertIsNone(row["score_0_100"])

    def test_two_types_of_housing_source_not_conflated(self):
        row=self.by_id["offenburg"]
        self.assertTrue(row["criteria"]["temporary_housing"]["checks"][1]["documented"])
        self.assertFalse(row["criteria"]["temporary_housing"]["checks"][2]["documented"])
        self.assertFalse(row["criteria"]["temporary_housing"]["checks"][3]["documented"])
        self.assertTrue(any("Resultados do portal incluem Strasbourg" in
                            item["limitation"] for item in row["evidence"]))

    def test_research_update_sources_do_not_change_comparability(self):
        row=self.by_id["trier"]
        self.assertTrue(any("CFL" in x["indicator"] or
                            "Luxembourg" in str(x["scope"])
                            for x in row["evidence"]))
        self.assertIsNone(row["score_0_100"])
        self.assertEqual(row["scoring_weight_percent"],0)


class CoverageStreamlitTests(unittest.TestCase):
    def test_30_city_tab_reachable_and_no_official_change(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        original=deepcopy(at.session_state["advisor_plan"])
        at.radio(key="ux_area").set_value("Explorar").run()
        at.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        at.segmented_control(key="ux_compare_mode").set_value(
            "Pesos das 30 cidades").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertTrue(any("Comparar 30 cidades-base" in x.value
                            for x in at.markdown))
        self.assertTrue(any(x.label=="Cidades" and x.value=="30"
                            for x in at.metric))
        at.checkbox(key="ux_30_only_finalists").uncheck().run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        at.segmented_control(key="ux_30_weight_profile").set_value(
            "Economia").run()
        self.assertFalse(at.exception,[x.message for x in at.exception])
        self.assertEqual(at.session_state["advisor_plan"],original)


if __name__=="__main__":
    unittest.main()
