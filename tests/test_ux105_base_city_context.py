"""UX105: context-only enrichment without fake train times or selection changes."""
from __future__ import annotations
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ux105_base_city_context import context_for_base, load_city_context
from ux100_base_card_photos import base_card_photo_record


class CityContextTests(unittest.TestCase):
    def test_four_exact_cities_have_sources_for_transport_and_attractions(self):
        cities=load_city_context()
        self.assertEqual(set(cities),{"aachen","angers","annecy","arlon"})
        for base,record in cities.items():
            with self.subTest(base=base):
                self.assertGreaterEqual(len(record["mobility"]),2)
                self.assertGreaterEqual(len(record["attractions"]),3)
                self.assertTrue(record["gaps"])
                for section in ("mobility","attractions"):
                    for item in record[section]:
                        self.assertTrue(item["source_url"].startswith("https://"))
                        self.assertTrue(item["detail"])
                self.assertNotIn("minutes",record)
                self.assertNotIn("time",record)
                self.assertNotIn("fare_eur",record)

    def test_unknown_city_no_inferred_neighbouring_data(self):
        self.assertIsNone(context_for_base("not_registered"))
        self.assertIsNone(context_for_base("angers_other"))

    def test_2027_is_not_asserted_as_validated_route_data(self):
        from ux105_base_city_context import DATA_PATH
        data=DATA_PATH.read_text(encoding="utf-8")
        self.assertIn("não verificados",data)
        for base in ("aachen","angers","annecy","arlon"):
            with self.subTest(base=base):
                self.assertTrue(any("2027" in gap for gap in context_for_base(base)["gaps"]))

    def test_data23_rail_minima_remain_historical_context(self):
        from data23_france_candidates_model import base_routes
        for city in ("angers","annecy"):
            routes=base_routes(city)
            self.assertEqual(len(routes),3)
            for route in routes:
                self.assertEqual(route["reference_kind"],
                                 "official_operator_minimum")
                self.assertFalse(route["valid_for_2027"])
                self.assertFalse(route["return_2027_verified"])
                self.assertFalse(route["door_to_door_verified"])
                self.assertTrue(route["source_url"].startswith("https://"))

    def test_photo_fallback_for_angers_and_annecy_is_city_matched(self):
        for base in ("angers","annecy"):
            with self.subTest(base=base):
                photo=base_card_photo_record(base)
                self.assertIsNotNone(photo)
                self.assertIn("commons.wikimedia.org/wiki/File:",photo["source_page"])
                self.assertTrue(photo["author"])
                self.assertTrue(photo["license_url"].startswith(
                    "https://creativecommons.org/licenses/"))

    def test_optional_context_panels_do_not_mutate_state(self):
        code = """
import streamlit as st
from ux105_base_city_context import render_base_context_summary, render_base_context_details
st.session_state["advisor_plan"]={"base_city":"mulhouse"}
render_base_context_summary("angers")
render_base_context_details("angers")
"""
        app=AppTest.from_string(code,default_timeout=60).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertEqual(app.session_state["advisor_plan"],{"base_city":"mulhouse"})
        self.assertTrue(any("Pesquisa local:" in c.value for c in app.caption))


if __name__=="__main__":
    unittest.main()
