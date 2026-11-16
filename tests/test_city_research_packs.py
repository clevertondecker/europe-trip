"""Research packs 1-3: cross-check existing 12 finalists, evidence and safety."""
import unittest
from copy import deepcopy
from pathlib import Path
from streamlit.testing.v1 import AppTest

from city_research_packs_model import (
    load_city_packs,validate_city_packs,pack_for_city,pack_summary,
)
from base_research_expanded_model import load_research
from trip_plan_model import new_plan

ROOT=Path(__file__).resolve().parents[1]


class ResearchPackModelTests(unittest.TestCase):
    def setUp(self):
        self.canonical=load_research()
        self.data=load_city_packs(canonical=self.canonical)

    def test_canonical_finalists_and_legacy_housing_preserved(self):
        finalists={r["id"] for r in self.canonical["cities"] if r["shortlist"]}
        self.assertEqual({r["city_id"] for r in self.data["cities"]},finalists)
        self.assertEqual(len(finalists),12)
        stats=pack_summary(self.data)
        self.assertEqual(stats["historical_housing_observations"],35)
        self.assertEqual(stats["restaurant_city_count"],4)
        self.assertEqual(stats["coworking_city_count"],4)
        self.assertEqual(stats["neighborhood_references"],26)
        self.assertEqual(stats["rail_operator_references"],5)
        self.assertEqual(stats["comparable_climate_cities"],6)
        self.assertEqual(stats["housing_confirmed_2027"],0)

    def test_no_historical_data_becomes_booked(self):
        for pack in self.data["cities"]:
            climate=pack["climate"]
            if climate["months_9_10_11"] is not None:
                self.assertEqual(set(climate["months_9_10_11"]),{"9","10","11"})
                self.assertTrue(climate["source_url"].startswith("https://"))
                self.assertEqual(climate["normal_period"],"1991–2020")
            self.assertIsNone(pack["daily_life"]["complete_comparable_basket_eur"])
            for rail in pack["weekend_rail_references"]:
                self.assertFalse(rail["weekend_return_confirmed"])
                self.assertFalse(rail["valid_for_2027"])
                self.assertFalse(rail["last_mile_verified"])
            for listing in pack["housing"]["historical_listings"]:
                self.assertFalse(listing["available_after_2027_09_04"])
                self.assertFalse(listing["confirmed_56_to_60_nights"])

    def test_missing_data_not_converted_to_zero(self):
        self.assertIsNone(pack_for_city(self.data,"freiburg")["daily_life"]["restaurant_two_midrange_eur_2026"])
        self.assertIsNone(pack_for_city(self.data,"freiburg")["daily_life"]["grocery_basket_eur"])
        self.assertIsNone(pack_for_city(self.data,"freiburg")["climate"]["months_9_10_11"])

    def test_invalid_published_booking_fare_or_neighborhood_fails(self):
        p=deepcopy(self.data)
        p["cities"][0]["housing"]["historical_listings"][0]["available_after_2027_09_04"]=True
        with self.assertRaises(ValueError):validate_city_packs(p,self.canonical)
        p=deepcopy(self.data)
        p["cities"][0]["climate"]["months_9_10_11"]={"9":{"tmean_c":15,"precip_mm":40}}
        with self.assertRaises(ValueError):validate_city_packs(p,self.canonical)
        p=deepcopy(self.data)
        p["cities"][0]["weekend_rail_references"][0]["weekend_return_confirmed"]=True
        with self.assertRaises(ValueError):validate_city_packs(p,self.canonical)
        p=deepcopy(self.data)
        p["cities"][0]["neighborhoods"][0]["source_url"]="invalid"
        with self.assertRaises(ValueError):validate_city_packs(p,self.canonical)

    def test_readonly_does_not_mutate_plan(self):
        plan=new_plan()
        saved=deepcopy(plan)
        item=pack_for_city(self.data,"mulhouse")
        item["missing"].clear()
        self.assertTrue(pack_for_city(self.data,"mulhouse")["missing"])
        self.assertEqual(plan,saved)


class ResearchPacksAppTest(unittest.TestCase):
    def test_existing_exploration_renders_with_research_sections(self):
        app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=110).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        original=deepcopy(app.session_state["advisor_plan"])
        app.radio(key="ux_area").set_value("Explorar").run()
        app.segmented_control(key="ux_section").set_value("Cidades-base").run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],original)


if __name__=="__main__":
    unittest.main()
