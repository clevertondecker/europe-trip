"""2026 evidence-based travel budget: verification, coverage and no double count."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions,load_base_routes
from trip_plan_model import new_plan
from outing_guide_model import build_outing_guide
from research_cost_model import (load_research,menu_examples,transit_examples,
                                 rail_cost_options,outing_research_snapshot,
                                 selected_trip_research,compare_city_bases)

ROOT=Path(__file__).resolve().parents[1]


class ResearchPriceTests(unittest.TestCase):
    def setUp(self):
        self.evidence=load_research()
        self.catalog=load_attractions()
        self.routes=load_base_routes()
        self.plan=new_plan()
        self.colmar_ids=[a["id"] for a in self.catalog["attractions"]
                         if a["destination_id"]=="colmar"][:2]

    def test_prices_have_provenance_not_fake_market_average(self):
        self.assertEqual(self.evidence["schema_version"],1)
        self.assertEqual(len(self.evidence["food"]),13)
        sample=menu_examples("colmar",self.evidence)
        self.assertEqual(sample["count"],2)
        self.assertEqual(sample["median"],16.5)
        self.assertEqual(sample["status"],"small_convenience_sample")
        self.assertEqual(sample["representativeness"],
                         "not_statistically_representative")
        self.assertEqual(menu_examples("metz",self.evidence)["median"],None)
        self.assertEqual(menu_examples("basel",self.evidence)["currency"],"CHF")
        self.assertEqual(menu_examples("basel",self.evidence)["count"],4)
        self.assertEqual(len(transit_examples("strasbourg",self.evidence)),2)

    def test_full_fare_and_fluo_card_not_under_counted(self):
        rail=rail_cost_options("mulhouse","colmar",2,self.evidence)
        self.assertEqual(rail["regular_roundtrip_eur"],43.2)
        self.assertEqual(rail["discounted_roundtrip_without_card_eur"],21.6)
        self.assertEqual(rail["weekend_with_new_card_eur"],51.6)
        self.assertIsNone(rail_cost_options("strasbourg","colmar",2,self.evidence)
                          ["regular_roundtrip_eur"])
        self.assertIsNone(rail_cost_options("mulhouse","basel",2,self.evidence)
                          ["weekend_with_new_card_eur"])
        self.assertIsNone(rail_cost_options("metz","colmar",2,self.evidence)
                          ["regular_roundtrip_eur"])

    def test_partial_one_lunch_example_never_becomes_total_quote(self):
        original=deepcopy(self.plan)
        guide=build_outing_guide(self.plan,self.catalog,self.routes,"colmar",
                                 self.colmar_ids)
        snap=outing_research_snapshot(guide,6.3,7.1,self.evidence)
        self.assertEqual(snap["scenario_status"],"illustrative_partial")
        self.assertAlmostEqual(snap["lunch_plus_rail_and_known_tickets_brl"],480.06)
        self.assertEqual(snap["quote_complete_for_2027"],False)
        self.assertTrue(snap["exchange_rates_hypothetical"])
        self.plan["base_city"]="strasbourg"
        moved=build_outing_guide(self.plan,self.catalog,self.routes,"colmar",
                                 self.colmar_ids)
        other=outing_research_snapshot(moved,6.3,7.1,self.evidence)
        self.assertIsNone(other["lunch_plus_rail_and_known_tickets_brl"])
        self.assertEqual(other["scenario_status"],"insufficient_data")
        self.assertEqual(original["packages"],self.plan["packages"])

    def test_four_base_comparison_does_not_treat_unknown_routes_as_fast_or_free(self):
        self.plan["packages"]={"colmar":self.colmar_ids}
        old=deepcopy(self.plan)
        rows=compare_city_bases(self.plan,self.catalog,self.routes,6.3,7.1,
                                self.evidence)
        self.assertEqual(len(rows),4)
        by={row["base"]:row for row in rows}
        self.assertEqual(by["mulhouse"]["known_train_roundtrip_minutes"],36)
        self.assertEqual(by["strasbourg"]["known_train_roundtrip_minutes"],64)
        self.assertIn("colmar",by["metz"]["unknown_duration_destinations"])
        self.assertEqual(by["metz"]["priced_outings"],0)
        self.assertTrue(by["metz"]["not_full_cost"])
        self.assertEqual(old,self.plan)

    def test_selected_itineraries_report_partial_coverage(self):
        self.plan["packages"]={"colmar":self.colmar_ids}
        baseline=deepcopy(self.plan)
        result=selected_trip_research(self.plan,self.catalog,self.routes,6.3,7.1,
                                      self.evidence)
        self.assertEqual(result["priced_count"],1)
        self.assertEqual(result["total_count"],1)
        self.assertTrue(result["not_comparable_to_global_budget_directly"])
        self.plan["packages"]["basel"]=[
            next(a["id"] for a in self.catalog["attractions"]
                 if a["destination_id"]=="basel")]
        incomplete=selected_trip_research(self.plan,self.catalog,self.routes,6.3,7.1,
                                          self.evidence)
        self.assertEqual(incomplete["priced_count"],1)
        self.assertEqual(incomplete["total_count"],2)
        self.assertIn("basel",incomplete["unpriced_destinations"])
        self.assertEqual(baseline["packages"]["colmar"],self.plan["packages"]["colmar"])


class ResearchPriceUITests(unittest.TestCase):
    def test_guide_shows_researched_prices_without_applying_to_official_plan(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Descobrir").run()
        app.checkbox(key="discovery_guide_toggle_colmar").check().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        text=" ".join(x.label for x in app.expander)
        self.assertIn("Pesquisa de preços",text)
        self.assertEqual(app.session_state["advisor_plan"]["packages"],{})
        app.segmented_control(key="itinerary_section").set_value("Orçamento").run()
        self.assertTrue(any("Comparar preços de alimentação pesquisados" in x.label
                            for x in app.expander))
        self.assertFalse(app.exception,[e.message for e in app.exception])

    def test_confirmed_excursions_show_researched_budget_separately(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any("custos pesquisados de alimentação" in x.label.lower()
                            for x in app.expander))
        self.assertTrue(any("Câmbio" in x.label for x in app.expander))
        self.assertTrue(any("Comparar cidade-base" in x.label for x in app.expander))


if __name__=="__main__":
    unittest.main()
