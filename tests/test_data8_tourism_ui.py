import copy
import unittest
from data8_tourism_ui import (
    parse_user_range, build_data8_card, destination_research_overview,
    compose_legacy_attraction_details,
)

class Data8UIProjectionTests(unittest.TestCase):
    def test_aachen_card_preserves_provenance_and_unknown_future(self):
        c=build_data8_card("dq32_aachen_07")
        self.assertEqual(c["admission"]["state"],"free_general_entry")
        self.assertEqual(c["duration"]["state"],"editorial_estimate")
        self.assertEqual(c["local_walk"]["state"],"editorial_two_direction_range")
        self.assertFalse(c["actual_station_connection_verified"])
        self.assertFalse(c["valid_for_2027"])

    def test_missing_and_unreconciled_distinct(self):
        self.assertIsNone(build_data8_card("noncanonical_cologne"))
        cologne=destination_research_overview("cologne")
        self.assertEqual(cologne["researched_attractions"],0)
        self.assertEqual(len(cologne["unreconciled_candidates"]),1)
        self.assertIsNone(cologne["unreconciled_candidates"][0]["canonical_attraction_id"])
        self.assertFalse(cologne["trip_plan_mutated"])

    def test_editable_ranges_are_not_implicit_free_prices(self):
        self.assertIsNone(parse_user_range(""))
        a=parse_user_range("30-65")
        self.assertEqual((a["min_eur"],a["max_eur"]),(30,65))
        for raw in ("30","60-20","-1-2","abc","10.123-20","10-100001"):
            with self.subTest(raw=raw),self.assertRaises(ValueError):
                parse_user_range(raw)

    def test_partial_enrichment_does_not_hide_historical_fields(self):
        legacy={
            "attraction_id":"brussels_atomium", "name":"Atomium",
            "description":"Descrição do catálogo histórico",
            "why_visit":"Referência antiga com contexto adicional",
            "opening_rule":"Consultar horário histórico",
            "opening_source_url":"https://example.org/historical-hours",
            "ticket_main":{"amount":18,"currency":"EUR","status":"historical"},
            "additional_activity":{"name":"Atividade histórica","amount":4,"currency":"EUR"},
            "visit_minutes":90,"visit_duration_status":"catalog_historical",
            "last_mile_observations":[{"direction":"station_to_attraction"}],
        }
        before=copy.deepcopy(legacy)
        composed=compose_legacy_attraction_details(legacy)
        self.assertEqual(legacy,before)
        self.assertIsNotNone(composed["data8"])
        self.assertEqual(composed["description"],legacy["description"])
        self.assertEqual(composed["admission"]["origin"],"legacy")
        self.assertEqual(composed["admission"]["amount"],18)
        self.assertEqual(composed["opening_rule"],legacy["opening_rule"])
        self.assertEqual(composed["legacy_visit_minutes"],90)
        self.assertEqual(composed["additional_activity"],legacy["additional_activity"])
        self.assertEqual(len(composed["legacy_last_mile_observations"]),1)
        self.assertIn(legacy["opening_source_url"],composed["sources"])
        self.assertEqual(len(composed["sources"]),len(set(composed["sources"])))

    def test_new_published_opening_and_legacy_description_coexist(self):
        legacy={"attraction_id":"strasbourg_cathedral", "name":"Catedral",
            "description":"Texto original a preservar", "why_visit":"História do catálogo",
            "opening_rule":None,"opening_source_url":None,
            "ticket_main":{"amount":None,"status":"unknown"},
            "additional_activity":None,"visit_minutes":None,
            "last_mile_observations":[]}
        row=compose_legacy_attraction_details(legacy)
        self.assertEqual(row["description"],legacy["description"])
        self.assertEqual(row["opening_origin"],"data8")
        self.assertTrue(row["opening_rule"])
        self.assertEqual(row["admission"]["state"],"unknown")
        self.assertIsNotNone(row["data8_duration"])

    def test_explicit_transport_assumption_from_ui_parser(self):
        r=parse_user_range("30-65",roundtrip=True)
        self.assertEqual(r["journey_scope"],"roundtrip_two_adults")
        self.assertNotIn("journey_scope",parse_user_range("30-65"))

    def test_research_card_is_read_only(self):
        from data8_priority_tourism_model import load_priority_lot
        from data8_local_access_model import load_access_dataset
        tourism=load_priority_lot()
        access=load_access_dataset(tourism=tourism)
        before=copy.deepcopy(tourism),copy.deepcopy(access)
        build_data8_card("strasbourg_cathedral",tourism=tourism,access=access)
        self.assertEqual((tourism,access),before)

if __name__=="__main__":
    unittest.main()
