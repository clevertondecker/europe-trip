"""Progressive shortlisted-rail research stays source-scoped and read-only."""
import unittest
from copy import deepcopy
from base_change_model import known_route,destination_impact
from attractions_model import load_base_routes
from base_explorer_model import load_exploration
from trip_plan_model import new_plan


class RailFinalistExpansionTests(unittest.TestCase):
    EXPECTED={
        ("nancy","luxembourg"):(91,106),
        ("nancy","brussels"):(211,244),
        ("metz","brussels"):(199,221),
        ("lille","luxembourg"):(231,278),
    }

    def test_four_new_official_sourced_observations(self):
        for (base,destination),(fast,typical) in self.EXPECTED.items():
            with self.subTest(base=base,destination=destination):
                row=known_route(base,destination)
                self.assertEqual(row["minutes"],fast)
                self.assertEqual(row["representative_minutes"],typical)
                self.assertIn("sncf-connect.com",row["source"])
                self.assertIsNone(row["fare"])
                self.assertFalse(row["return_verified"])
                self.assertGreaterEqual(typical,fast)

    def test_original_10_priority_routes_unchanged(self):
        for base in ("mulhouse","strasbourg"):
            for destination in ("luxembourg","interlaken","brussels","bruges_be","rotterdam"):
                row=known_route(base,destination)
                self.assertIsInstance(row["minutes"],int)
                self.assertFalse(row["return_verified"])

    def test_legacy_schema_and_exploratory_only(self):
        load_base_routes()
        exploration=load_exploration()
        self.assertEqual(exploration["schema_version"],1)

    def test_cross_base_comparison_never_updates_plan(self):
        plan=new_plan()
        old=deepcopy(plan)
        comparison=destination_impact(plan,"nancy",["luxembourg","brussels"])
        self.assertEqual(len(comparison),2)
        self.assertEqual(plan,old)
        self.assertIsNone(comparison[1]["official_minutes"])
        self.assertFalse(any("roundtrip_couple_eur" in item for item in comparison))

    def test_unresearched_remains_unknown(self):
        self.assertIsNone(known_route("nancy","bruges_be")["minutes"])
        self.assertIsNone(known_route("metz","rotterdam")["minutes"])


if __name__=="__main__":unittest.main()
