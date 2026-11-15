"""Regression: an outing guide is recomputed from the chosen base and attractions."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from attractions_model import load_attractions,load_base_routes
from trip_plan_model import new_plan
from outing_guide_model import build_outing_guide,additional_estimate

ROOT=Path(__file__).resolve().parents[1]


class OutingGuideModelTests(unittest.TestCase):
    def setUp(self):
        self.catalog=load_attractions()
        self.routes=load_base_routes()
        self.colmar=[a["id"] for a in self.catalog["attractions"]
                     if a["destination_id"]=="colmar"][:2]

    def test_changing_base_updates_rail_minutes_fare_and_known_cost(self):
        plan=new_plan()
        before=deepcopy(plan)
        mulhouse=build_outing_guide(plan,self.catalog,self.routes,"colmar",self.colmar)
        self.assertEqual(mulhouse["train_minutes_one_way"],18)
        self.assertEqual(mulhouse["roundtrip_train_minutes_station_only"],36)
        self.assertEqual(mulhouse["fare_eur_person_oneway"],5.4)
        self.assertEqual(mulhouse["known_transport"]["EUR"],21.6)
        self.assertEqual(mulhouse["known_cost"]["EUR"],21.6)
        self.assertIn("Carte Fluo", " ".join(mulhouse["missing"]))
        self.assertGreater(mulhouse["visit_minutes_editorial"],0)
        self.assertTrue(mulhouse["optional"])
        plan["base_city"]="strasbourg"
        strasbourg=build_outing_guide(plan,self.catalog,self.routes,"colmar",self.colmar)
        self.assertEqual(strasbourg["train_minutes_one_way"],32)
        self.assertEqual(strasbourg["fare_eur_person_oneway"],7.9)
        self.assertEqual(strasbourg["known_transport"]["EUR"],31.6)
        self.assertNotEqual(mulhouse["known_cost"],strasbourg["known_cost"])
        plan["base_city"]="metz"
        unknown=build_outing_guide(plan,self.catalog,self.routes,"colmar",self.colmar)
        self.assertIsNone(unknown["train_minutes_one_way"])
        self.assertIsNone(unknown["fare_eur_person_oneway"])
        self.assertEqual(unknown["known_transport"]["EUR"],0)
        self.assertTrue(any("Tempo ferroviário" in item for item in unknown["missing"]))
        self.assertEqual(before["packages"],plan["packages"])

    def test_incomplete_costs_and_what_if_are_never_official_prices(self):
        plan=new_plan()
        saved=deepcopy(plan)
        guide=build_outing_guide(plan,self.catalog,self.routes,"colmar",self.colmar)
        known=additional_estimate(guide,eur_fx=6.3,chf_fx=7.1)
        self.assertIsNone(known["scenario_brl"])
        assumed=additional_estimate(guide,eur_fx=6.3,chf_fx=7.1,
                                    dining_per_person_eur=25,
                                    local_transport_per_person_eur=5,
                                    extra_for_couple_eur=10)
        self.assertGreater(assumed["scenario_brl"],known["known_brl"])
        self.assertEqual(guide["quote_complete_for_2027"],False)
        self.assertIn("Alimentação do casal durante o passeio",guide["missing"])
        self.assertEqual(saved,plan)
        with self.assertRaises(ValueError):
            additional_estimate(guide,eur_fx=6.3,chf_fx=7.1,
                                dining_per_person_eur=-1,
                                local_transport_per_person_eur=2,
                                extra_for_couple_eur=0)

    def test_rejects_wrong_attractions_and_does_not_invent_road_distance(self):
        plan=new_plan()
        with self.assertRaises(ValueError):
            build_outing_guide(plan,self.catalog,self.routes,"colmar",["invalid"])
        guide=build_outing_guide(plan,self.catalog,self.routes,"colmar",self.colmar)
        self.assertIsNone(guide["distance_km_documented"])
        self.assertGreater(guide["distance_straight_km"],0)
        self.assertFalse(guide["route"]["weekend_return_verified"])

    def test_local_excursion_shows_unknown_urban_transport(self):
        plan=new_plan()
        selected=[a["id"] for a in self.catalog["attractions"]
                  if a["destination_id"]=="mulhouse"][:2]
        guide=build_outing_guide(plan,self.catalog,self.routes,"mulhouse",selected)
        self.assertTrue(guide["local"])
        self.assertIsNone(guide["train_minutes_one_way"])
        self.assertIn("Deslocamento urbano/local a verificar",guide["missing"])


class OutingGuideUITests(unittest.TestCase):
    def test_changing_base_updates_confirmed_card_and_add_optional_is_explicit(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="ux_area").set_value("Meu roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Meus passeios").run()
        app.button(key="outing_add_open").click().run()
        app.selectbox(key="outing_new_destination").set_value("colmar").run()
        catalog=load_attractions()
        ids=[a["id"] for a in catalog["attractions"] if a["destination_id"]=="colmar"]
        app.multiselect(key="outing_new_attractions").set_value(ids[:2]).run()
        app.button(key="outing_add_save").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any(m.label=="Trem de ida" and m.value=="18 min" for m in app.metric))
        original=deepcopy(app.session_state["advisor_plan"])
        app.selectbox(key="advisor_base").set_value("strasbourg").run()
        self.assertEqual(app.session_state["advisor_plan"]["base_city"],"mulhouse")
        app.button(key="advisor_confirm_base").click().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any(m.label=="Trem de ida" and m.value=="32 min" for m in app.metric))
        self.assertEqual(app.session_state["advisor_plan"]["packages"],original["packages"])
        app.checkbox(key="official_guide_colmar_extra_enabled").check().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertEqual(app.session_state["advisor_plan"]["packages"],original["packages"])
        guide=build_outing_guide(app.session_state["advisor_plan"],catalog,
                                 load_base_routes(),"colmar",ids[:2])
        if guide["optional"]:
            extra=guide["optional"][0]["id"]
            app.button(key="official_guide_colmar_add_"+extra).click().run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            self.assertIn(extra,app.session_state["advisor_plan"]["packages"]["colmar"])
            self.assertEqual(app.session_state["explore_packages"],
                             app.session_state["advisor_plan"]["packages"])

    def test_discovery_and_budget_can_open_the_same_guide(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=100).run()
        app.radio(key="main_navigation").set_value("Roteiro").run()
        app.segmented_control(key="itinerary_section").set_value("Descobrir").run()
        self.assertIn("discovery_guide_toggle_colmar",{c.key for c in app.checkbox})
        app.checkbox(key="discovery_guide_toggle_colmar").check().run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any(m.label=="Trem de ida" for m in app.metric))
        self.assertEqual(app.session_state["advisor_plan"]["packages"],{})
        app.segmented_control(key="itinerary_section").set_value("Orçamento").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertTrue(any(c.key.startswith("budget_guide_toggle_") for c in app.checkbox))


if __name__=="__main__":
    unittest.main()
