"""Exploratory French bases never silently change the approved travel plan."""
import unittest
from copy import deepcopy
from pathlib import Path

from streamlit.testing.v1 import AppTest

from base_explorer_model import (
    load_exploration,route_detail,compare_bases,
    base_opportunities,stay_projection)
from trip_plan_model import new_plan,BASES
from data_model import load_data


ROOT=Path(__file__).resolve().parents[1]


class BaseExplorerModelTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_exploration()
        self.plan=new_plan()
        self.trip_data=load_data()

    def test_eight_bases_are_separate_from_official_plan_schema(self):
        bases={x["id"] for x in self.catalog["bases"]}
        self.assertEqual(len(bases),8)
        self.assertTrue({"lille","arras","dijon","reims"}<=bases)
        self.assertTrue(BASES<=bases)
        self.assertNotIn("lille",BASES)
        self.assertTrue(all(not x["return_verified_2027"] for x in
                            self.catalog["routes"]))

    def test_lille_amsterdam_is_only_a_conditional_reference(self):
        route=route_detail(self.catalog,"lille","amsterdam")
        self.assertEqual(route["minutes"],169)
        self.assertEqual(route["roundtrip_train_minimum_minutes"],338)
        self.assertEqual(route["fare_from"],69)
        self.assertEqual(route["all_legs_at_from_fare_eur"],276)
        self.assertFalse(route["return_verified_2027"])
        self.assertIn("sncf-connect.com",route["source_url"])
        self.assertIn("fim de semana",route["classification"])
        unknown=route_detail(self.catalog,"arras","amsterdam")
        self.assertIsNone(unknown["minutes"])
        self.assertIsNone(unknown["all_legs_at_from_fare_eur"])
        self.assertEqual(unknown["classification"],"Sem dados suficientes")

    def test_base_comparisons_disclose_missing_time_and_fares(self):
        catalog_before=deepcopy(self.catalog)
        compared=compare_bases(self.catalog,
            ["lille","strasbourg","metz"],
            ["amsterdam","brussels","colmar","basel"])
        self.assertEqual(len(compared),3)
        by={x["base_id"]:x for x in compared}
        self.assertEqual(by["lille"]["time_coverage"],2)
        self.assertEqual(by["lille"]["fare_coverage"],2)
        self.assertFalse(by["lille"]["fully_priced"])
        self.assertEqual(by["metz"]["fare_coverage"],0)
        self.assertIsNone(by["metz"]["illustrative_fare_if_all_min_eur"])
        self.assertFalse(by["metz"]["verified_2027"])
        self.assertEqual(catalog_before,self.catalog)
        with self.assertRaises(ValueError):
            compare_bases(self.catalog,["lille"],[])
        with self.assertRaises(ValueError):
            compare_bases(self.catalog,["lille","lille"],["amsterdam"])

    def test_split_stay_replaces_rent_and_ignores_deposit_as_expense(self):
        initial=deepcopy(self.plan)
        result=stay_projection(self.plan,self.trip_data,False,6.3,
            "lille","strasbourg",20,1600,1400,220,900,800)
        self.assertEqual(result["days_france"],60)
        self.assertEqual(result["days_first"],20)
        self.assertEqual(result["days_second"],40)
        self.assertAlmostEqual(result["housing_single_a_eur"],3200)
        self.assertAlmostEqual(result["housing_single_b_eur"],2800)
        self.assertAlmostEqual(result["housing_split_eur"],2933.33,places=2)
        self.assertEqual(result["cash_deposit_split_eur"],1700)
        self.assertFalse(result["deposits_are_expense"])
        self.assertEqual(result["split_delta_vs_a_brl"],
                         round(result["split_total_brl"]-
                               result["single_a_total_brl"],2))
        self.assertEqual(self.plan,initial)
        self.assertFalse(result["intercity_trains_included"])
        self.assertFalse(result["quoted_for_2027"])
        with self.assertRaises(ValueError):
            stay_projection(self.plan,self.trip_data,False,6.3,
                            "lille","lille",20,1600,1600,200)
        with self.assertRaises(ValueError):
            stay_projection(self.plan,self.trip_data,False,6.3,
                            "lille","strasbourg",20,1600,1400,-20)
        with self.assertRaises(ValueError):
            stay_projection(self.plan,self.trip_data,False,0,
                            "lille","strasbourg",20,1600,1400,200)

    def test_local_destinations_remain_unpriced_unless_documented(self):
        seen=base_opportunities(self.catalog,"dijon")
        ids={r["destination_id"] for r in seen}
        self.assertTrue({"beaune","lausanne","lyon"}<=ids)
        self.assertEqual(route_detail(self.catalog,"dijon","lausanne")["fare_from"],29)
        self.assertIsNone(route_detail(self.catalog,"dijon","beaune")["fare_from"])
        with self.assertRaises(ValueError):
            route_detail(self.catalog,"not_a_base","amsterdam")


class BaseExplorerUITests(unittest.TestCase):
    def open_explorer(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        return app

    def test_exploring_new_city_does_not_modify_official_plan(self):
        app=self.open_explorer()
        original=deepcopy(app.session_state["advisor_plan"])
        self.assertNotIn("scenario_sidebar",{x.key for x in app.selectbox})
        app.segmented_control(key="ux42_city_activity").set_value("Passeios e conexões").run()
        app.selectbox(key="base_explorer_city").set_value("lille").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.checkbox(key="ux42_show_advanced").check().run()
        self.assertNotIn("base_explore_apply",{x.key for x in app.button})
        app.button(key="base_explore_favorite").click().run()
        self.assertEqual(app.session_state["advisor_plan"],original)
        self.assertEqual(app.session_state["base_explorer_favorite"]["base"],"lille")
        self.assertEqual(app.session_state["base_explorer_favorite"]["status"],"research_only")

    def test_existing_base_must_be_explicitly_approved(self):
        app=self.open_explorer()
        original=deepcopy(app.session_state["advisor_plan"])
        app.segmented_control(key="ux42_city_activity").set_value("Passeios e conexões").run()
        app.selectbox(key="base_explorer_city").set_value("strasbourg").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.checkbox(key="ux42_show_advanced").check().run()
        self.assertTrue(app.button(key="base_explore_apply").disabled)
        self.assertEqual(app.session_state["advisor_plan"],original)
        app.checkbox(key="base_explore_apply_confirmation_strasbourg").check().run()
        self.assertFalse(app.button(key="base_explore_apply").disabled)
        app.button(key="base_explore_apply").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"strasbourg")
        self.assertEqual(app.session_state["advisor_plan"]["revision"],
                         original["revision"]+1)

    def test_comparison_remains_but_split_stay_is_not_available(self):
        app=self.open_explorer()
        old=deepcopy(app.session_state["advisor_plan"])
        from ux502_destination_interests_model import empty_interests,set_interest
        wishes=set_interest(empty_interests(),"colmar","must_visit")
        wishes=set_interest(wishes,"basel","interested")
        app.session_state["ux502_interests"]=wishes
        app.session_state["rec03a_activity"]="Comparação personalizada"
        app.segmented_control(key="ux_section").set_value("Comparar").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        app.multiselect(key="ux503_bases").set_value(["lille","metz"]).run()
        app.multiselect(key="ux503_visible_destinations").set_value(["colmar","basel"]).run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        matrix=next(f.value for f in app.dataframe if "Destino · prioridade" in f.value.columns)
        self.assertEqual(len(matrix),2)
        self.assertIn("Lille",matrix.columns)
        self.assertIn("Metz",matrix.columns)
        self.assertEqual(app.session_state["ux502_interests"],wishes)
        self.assertEqual(app.session_state["advisor_plan"],old)
        self.assertNotIn("base_compare_destinations",{x.key for x in app.multiselect})
        modes=app.segmented_control(key="ux_compare_mode").options
        self.assertNotIn("Uma ou duas bases",modes)
        self.assertNotIn("Comparar mesmas viagens",modes)
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        app.segmented_control(key="ux42_city_activity").set_value("Passeios e conexões").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertFalse(any(x.key=="ux42_show_split" for x in app.checkbox))
        self.assertFalse(any(x.key and x.key.startswith("base_stay_")
                             for x in app.number_input))
        self.assertEqual(app.session_state["advisor_plan"],old)


if __name__=="__main__":
    unittest.main()
