"""DATA23/UX78 regression coverage across candidate research, photos and railway comparisons."""
from copy import deepcopy
import unittest
from unittest.mock import patch

from base_research_expanded_model import DATA as OLD_BASES,load_research,research_overview
from city_profiles_model import load_profiles,profile_by_id,compact_comparison
from data23_france_candidates_model import (load_data23,validate_data23,
    base_attractions,base_routes,REQUIRED_IDS)
from base_scenario_model import base_options,expanded_rail_routes
from base_coverage_model import coverage_matrix
from rail_reference_projection_model import decorate_comparison
from trip_plan_model import new_plan
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import empty_interests,set_interest
from ux503_destination_base_comparison_model import compare_wishlist_bases
from ux47_photo_ui import photo_markup,photo_credit
import json


class DynamicBaseCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=load_data23()
        cls.research=load_research(include_candidates=True)

    def test_historical_snapshot_unchanged_and_four_candidates_visible(self):
        historical=json.loads(OLD_BASES.read_text(encoding="utf-8"))
        self.assertEqual(len(historical["cities"]),30)
        ids=[x["id"] for x in self.research["cities"]]
        self.assertEqual(len(ids),34)
        self.assertEqual(len(set(ids)),34)
        self.assertEqual(set(ids)-{x["id"] for x in historical["cities"]},REQUIRED_IDS)
        self.assertEqual(research_overview(self.research)["candidate_count"],len(ids))
        self.assertEqual(research_overview(self.research)["shortlist_count"],12)
        self.assertEqual(research_overview(self.research)["three_eligible_2027_quotes"],0)

    def test_dynamic_profile_coverage_matches_candidate_ids(self):
        data=load_profiles(canonical=self.research)
        self.assertEqual({x["city_id"] for x in data["cities"]},
                         {x["id"] for x in self.research["cities"]})
        for city_id in REQUIRED_IDS:
            with self.subTest(city_id=city_id):
                profile=profile_by_id(data,city_id)
                self.assertFalse(profile["shortlist"])
                self.assertIsNone(profile["quality_of_life"]["numeric_score"])
                self.assertFalse(profile["housing"]["availability_2027_verified"])
                self.assertEqual(profile["housing"]["historical_offer_count"],0)

    def test_compact_comparison_tolerates_missing_optional_demographics(self):
        data=load_profiles(canonical=self.research)
        for city_id in ("angers", "le_mans", "annecy", "rennes"):
            with self.subTest(city_id=city_id):
                compact=compact_comparison(data,[city_id,"metz"])
                self.assertEqual(compact[0]["População municipal (ano indicado)"],
                                 "Não pesquisado")
                self.assertEqual(compact[0]["Faixa observada EUR/mês"],
                                 "Não pesquisado")
        modified=deepcopy(data)
        target=next(r for r in modified["cities"] if r["city_id"]=="angers")
        target["demographics"]={}
        self.assertEqual(compact_comparison(modified,["angers","metz"])[0]
                         ["População municipal (ano indicado)"],"Não pesquisado")
        target["demographics"]={"population_municipal":12345,"reference_year":2025}
        self.assertEqual(compact_comparison(modified,["angers","metz"])[0]
                         ["População municipal (ano indicado)"],"12345 (2025)")

    def test_indicative_reference_remains_separate_from_historical_readiness(self):
        discovery=build_destination_discovery()
        for base_id,destination_id in (
            ("le_mans","paris"),("angers","saumur"),
            ("annecy","geneve"),("rennes","saint_malo")
        ):
            with self.subTest(base=base_id,destination=destination_id):
                wishlist=set_interest(empty_interests(),destination_id,
                                      "interested",discovery)
                comparison=compare_wishlist_bases(
                    wishlist,[base_id,"metz"],discovery=discovery,
                    research=self.research)
                enriched=decorate_comparison(comparison)
                cell=enriched["cells"][(base_id,destination_id)]
                self.assertEqual(cell["category"],"reference_only")
                self.assertEqual(cell["display_basis"],"data23_candidate_reference")
                self.assertFalse(cell["weekend_return_known"])
                self.assertFalse(cell["valid_for_2027"])
                self.assertEqual(comparison["summaries"][0]["documented_time_count"],0)
                self.assertFalse(comparison["official_plan_modified"])

    def test_other_pages_include_all_cities_and_no_official_promotion(self):
        options={r["id"]:r for r in base_options(include_candidates=True)}
        self.assertTrue(REQUIRED_IDS <= set(options))
        self.assertTrue(REQUIRED_IDS.isdisjoint({r["id"] for r in base_options()}))
        self.assertTrue(all(not options[x]["official_supported"] for x in REQUIRED_IDS))
        rows=coverage_matrix("general",study=self.research)
        self.assertEqual(len(rows),len(self.research["cities"]))
        by_id={x["id"]:x for x in rows}
        self.assertTrue(REQUIRED_IDS <= set(by_id))
        self.assertTrue(all(by_id[x]["route_return_verified"]==0 for x in REQUIRED_IDS))

    def test_scenario_explorer_reuses_new_base_rail_with_unknown_fares(self):
        for base_id in REQUIRED_IDS:
            with self.subTest(base_id=base_id):
                rows=expanded_rail_routes(base_id)
                self.assertGreaterEqual(len(rows),2)
                self.assertTrue(all(r["fare_eur_person_oneway"] is None
                                    and r["return_verified_2027"] is False
                                    for r in rows))

    def test_photos_exist_for_every_attraction_and_are_credited(self):
        self.assertEqual(len(self.data["attractions"]),12)
        for a in self.data["attractions"]:
            with self.subTest(a=a["id"]):
                photo=a["photo"]
                # Deterministic rendering test: don't depend on live Commons API.
                with patch("ux47_photo_ui.display_photo_url",side_effect=lambda url:url):
                    self.assertIn("Special:FilePath",photo_markup(photo,a["name"]))
                credit=photo_credit(photo)
                self.assertIn(photo["author"],credit)
                self.assertIn(photo["license"],credit)
                self.assertIn("Crédito",credit)

    def test_all_four_have_photos_and_multiple_sourced_rail_options(self):
        for city_id in REQUIRED_IDS:
            with self.subTest(city_id=city_id):
                self.assertGreaterEqual(len(base_attractions(city_id)),3)
                self.assertGreaterEqual(len(base_routes(city_id)),2)
                self.assertTrue(all(a["availability_autumn_2027_verified"] is False
                                    for a in base_attractions(city_id)))

    def test_reject_invented_booking_and_wrong_photo_source(self):
        for scenario in ("availability","fake_photo","bad_author","wrong_direction"):
            with self.subTest(scenario=scenario):
                mutated=deepcopy(self.data)
                if scenario=="availability":
                    mutated["attractions"][0]["availability_autumn_2027_verified"]=True
                if scenario=="fake_photo":
                    mutated["attractions"][0]["photo"]["source_page"]="https://example.com/file"
                if scenario=="bad_author":
                    mutated["attractions"][0]["photo"]["author"]=""
                if scenario=="wrong_direction":
                    mutated["routes"][0]["source_url"]="https://www.sncf-connect.com/train/horaires/saumur/angers"
                with self.assertRaises(ValueError):
                    validate_data23(mutated)

    def test_comparator_adds_new_bases_without_touching_tripplan(self):
        discovery=build_destination_discovery()
        wishlist=set_interest(empty_interests(),"paris","interested",discovery)
        original=deepcopy(wishlist)
        plan=new_plan(base="metz")
        plan_before=deepcopy(plan)
        comparison=compare_wishlist_bases(
            wishlist,["le_mans","rennes","metz"],discovery=discovery,
            research=self.research)
        result=decorate_comparison(comparison)
        self.assertEqual(result["cells"][("le_mans","paris")]["display_min"],56)
        self.assertTrue(result["cells"][("le_mans","paris")]["candidate_connectivity_applied"])
        self.assertTrue(result["cells"][("le_mans","paris")]["valid_for_2027"] is False)
        self.assertEqual(wishlist,original)
        self.assertEqual(plan,plan_before)


class DynamicCandidateUIRegressionTests(unittest.TestCase):
    @patch("base_research_expanded_ui._candidate_photo_markup",
           return_value="<div>Fotografia licenciada</div>")
    def test_new_base_detail_renders_and_cannot_change_saved_plan(self, photo):
        from pathlib import Path
        from streamlit.testing.v1 import AppTest
        app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/"app.py"),
                              default_timeout=120).run()
        original=deepcopy(app.session_state["advisor_plan"])
        app.button(key="ux_sidebar_nav_1").click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux42_city_activity").set_value(
            "Explorar cidades").run()
        app.selectbox(key="expanded_bases_detail_city").set_value("angers").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(app.session_state["expanded_bases_detail_city"],"angers")
        self.assertTrue(photo.called)


if __name__=="__main__":
    unittest.main()
