"""ARCH contract: research gaps concern complete outings, not just outbound train times."""
from copy import deepcopy
import unittest

from rail_gap_coverage_audit_model import (
    build_rail_coverage_inventory,
    component_research_backlog,
    component_gap_summary,
    research_backlog,
)


class RailComponentBacklogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inventory = build_rail_coverage_inventory()

    def test_inventory_preserves_legacy_missing_outbound_contract(self):
        before = deepcopy(self.inventory)
        only_outbound = research_backlog(self.inventory)
        all_components = component_research_backlog(self.inventory)
        counts = component_gap_summary(all_components)
        self.assertEqual(len(only_outbound), self.inventory["missing_pairs"])
        self.assertEqual(len(all_components), self.inventory["total_pairs"])
        self.assertEqual(counts["pairs"], self.inventory["total_pairs"])
        self.assertEqual(counts["by_category"],
            {"historical": self.inventory["historical_pairs"],
             "indicative": self.inventory["indicative_pairs"],
             "local": self.inventory["local_pairs"],
             "missing": self.inventory["missing_pairs"]})
        self.assertEqual(counts["missing_components"]["independent_return_service"],
                         self.inventory["total_pairs"]-self.inventory["local_pairs"])
        self.assertEqual(counts["missing_components"]["local_access_return"],
                         self.inventory["local_pairs"])
        self.assertEqual(counts["missing_components"]["two_adults_fare"],
                         self.inventory["total_pairs"]-self.inventory["local_pairs"])
        self.assertEqual(counts["missing_components"]["attraction_opening_window"],
                         self.inventory["total_pairs"])
        self.assertEqual(self.inventory, before)

    def test_documented_outbound_never_implies_a_verified_return(self):
        rows = component_research_backlog(self.inventory)
        for row in rows:
            self.assertIsNone(row.get("return_train_minutes"))
            self.assertFalse(row["return_2027_verified"])
            self.assertFalse(row["confirmed_2027"])
            if row["category"] in ("historical", "indicative"):
                self.assertGreater(row["known_outbound_oneway_min"], 0)
                self.assertIn("independent_return_service", row["research_required"])
                self.assertIn("station_reconciliation", row["research_required"])
                self.assertIn("last_mile_to_attraction", row["research_required"])
                self.assertNotIn("published_oneway_duration", row["research_required"])
            elif row["category"] == "local":
                self.assertIsNone(row["known_outbound_oneway_min"])
                self.assertNotIn("independent_return_service", row["research_required"])
                self.assertIn("local_access_outbound", row["research_required"])
            else:
                self.assertIsNone(row["known_outbound_oneway_min"])
                self.assertIn("published_oneway_duration", row["research_required"])

    def test_reject_inconsistent_or_fabricated_availability(self):
        original = deepcopy(self.inventory)
        cases = [
            ("category", "verified_for_2027"),
            ("return_2027_verified", True),
            ("fare_couple_2027_eur", 12),
            ("door_to_door_2027_verified", True),
        ]
        for key, value in cases:
            with self.subTest(key=key):
                data = deepcopy(original)
                data["pairs"][0][key] = value
                with self.assertRaises(ValueError):
                    component_research_backlog(data)
        self.assertEqual(original, self.inventory)

    def test_local_stays_local_without_synthetic_zero_mobility(self):
        rows = component_research_backlog(self.inventory)
        local = [x for x in rows if x["category"] == "local"]
        self.assertEqual(len(local), 30)
        self.assertTrue(all(x["base_id"] == x["destination_id"] for x in local))
        self.assertTrue(all(x["known_outbound_oneway_min"] is None for x in local))
        self.assertTrue(all("local_transport_two_adults_cost" in x["research_required"]
                            for x in local))


if __name__ == "__main__":
    unittest.main()
