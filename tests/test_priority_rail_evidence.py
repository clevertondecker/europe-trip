"""Priority rail evidence: ten real source-scoped observations and safe aliases."""
import unittest
from copy import deepcopy

from attractions_model import load_base_routes
from base_explorer_model import load_exploration
from five_base_comparison_model import load_five_base_evidence
from base_change_model import known_route, destination_catalog, destination_impact
from trip_plan_model import new_plan

DESTINATIONS=("luxembourg","interlaken","brussels","bruges_be","rotterdam")
BASES=("mulhouse","strasbourg")


class PriorityRailEvidenceTests(unittest.TestCase):
    def test_10_priority_routes_have_sourced_historical_times(self):
        for base in BASES:
            for dest in DESTINATIONS:
                with self.subTest(base=base, destination=dest):
                    row=known_route(base,dest)
                    self.assertIsInstance(row["minutes"],int)
                    self.assertGreater(row["minutes"],0)
                    self.assertIsInstance(row["representative_minutes"],int)
                    self.assertGreaterEqual(row["representative_minutes"],row["minutes"])
                    self.assertTrue(row["source"].startswith("https://"))
                    self.assertIsNone(row["fare"])
                    self.assertFalse(row["return_verified"])

    def test_sources_distinguish_official_and_secondary(self):
        for base in BASES:
            self.assertIn("sncf-connect.com",known_route(base,"brussels")["source"])
            self.assertIn("sncf-connect.com",known_route(base,"luxembourg")["source"])
            self.assertIn("thetrainline.com",known_route(base,"interlaken")["source"])
            self.assertIn("thetrainline.com",known_route(base,"bruges_be")["source"])

    def test_luxembourg_aliases_match_exact_same_route(self):
        for base in BASES:
            self.assertEqual(known_route(base,"luxembourg"),known_route(base,"luxembourg_city"))
        names=destination_catalog()
        self.assertIn("luxembourg",names)
        self.assertNotIn("luxembourg_city",names)

    def test_belgian_brugge_has_explicit_station(self):
        for base in BASES:
            route=known_route(base,"bruges_be")
            self.assertIn("Brugge",route["destination_station"])

    def test_legacy_datasets_still_validate(self):
        load_base_routes()
        load_exploration()
        load_five_base_evidence()

    def test_comparison_is_read_only_and_uses_typical_time(self):
        plan=new_plan()
        original=deepcopy(plan)
        rows=destination_impact(plan,"strasbourg",list(DESTINATIONS))
        self.assertEqual(5,len(rows))
        self.assertTrue(all(row["delta_minutes"] is not None for row in rows))
        self.assertEqual(plan,original)
        self.assertEqual(plan["revision"],original["revision"])
        for row in rows:
            self.assertIsNone(row["official_fare"])
            self.assertIsNone(row["candidate_fare"])
        self.assertEqual(
            next(x for x in rows if x["destination_id"]=="luxembourg")["delta_minutes"],
            154-211)

    def test_no_inference_for_unknown_routes(self):
        missing=known_route("nancy","rotterdam")
        self.assertIsNone(missing["minutes"])
        self.assertFalse(missing["return_verified"])


if __name__ == "__main__":
    unittest.main()
