"""Scenario catalog, portable drafts, and non-mutating selection contracts."""
import unittest
from base_scenario_model import base_options, choose_exploratory_base, expanded_rail_routes
from base_scenario_store import make_scenario,scenario_export,scenario_import


class ScenarioPersistenceTests(unittest.TestCase):
    def test_all_research_candidates_are_selectable(self):
        options=base_options()
        self.assertGreaterEqual(len(options),30)
        ids={x["id"] for x in options}
        self.assertIn("offenburg",ids)
        self.assertIn("mulhouse",ids)
        self.assertEqual(choose_exploratory_base("offenburg",options),"offenburg")

    def test_offenburg_rail_uses_only_documented_oneway_evidence(self):
        routes=expanded_rail_routes("offenburg")
        self.assertEqual(len(routes),1)
        self.assertEqual(routes[0]["destination_id"],"strasbourg")
        self.assertEqual(routes[0]["oneway_minutes"],25)
        self.assertEqual(routes[0]["fare_eur_person_oneway"],13)
        self.assertFalse(routes[0]["return_verified_2027"])
        self.assertNotIn("freiburg",{r["destination_id"] for r in routes})

    def test_roundtrip_is_explicit_and_never_contains_official_plan(self):
        scenario=make_scenario("Offenburg - 60 noites","offenburg",60,"Pesquisa")
        restored=scenario_import(scenario_export(scenario))
        self.assertEqual(restored,scenario)
        self.assertNotIn("TripPlan",str(restored))
        self.assertNotIn("assignments",restored)
        self.assertEqual(restored["status"],"exploratory_only")

    def test_reject_untrusted_file_and_out_of_scope_inputs(self):
        with self.assertRaises(ValueError):
            scenario_import(b"{}")
        with self.assertRaises(ValueError):
            scenario_import(b"x"*128001)
        with self.assertRaises(ValueError):
            make_scenario("test","not_a_real_city",60)
        with self.assertRaises(ValueError):
            make_scenario("test","mulhouse",0)


if __name__ == "__main__":
    unittest.main()
