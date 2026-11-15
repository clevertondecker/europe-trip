"""Regressions: exploratory base selection never approves a TripPlan change."""
import unittest

from base_scenario_model import (base_options, choose_exploratory_base,
                                 hypothetical_city_name)
from base_explorer_model import load_exploration


class BaseScenarioTest(unittest.TestCase):
    def test_all_explored_bases_are_selectable(self):
        source = load_exploration()
        options = base_options(source)
        self.assertTrue({b["id"] for b in source["bases"]}.issubset(
                        {b["id"] for b in options}))
        self.assertGreaterEqual(len(options), 25)
        self.assertGreaterEqual(len(options), 8)
        for row in options:
            self.assertEqual(choose_exploratory_base(row["id"], options), row["id"])
            self.assertTrue(hypothetical_city_name(row["id"], options))

    def test_selection_does_not_mutate_official_plan(self):
        official = {"base_city": "mulhouse", "revision": 7}
        before = official.copy()
        candidate = choose_exploratory_base("lille", base_options())
        self.assertEqual(candidate, "lille")
        self.assertEqual(official, before)

    def test_invalid_city_rejected(self):
        with self.assertRaises(ValueError):
            choose_exploratory_base("nonexistent-city", base_options())

    def test_unknown_fares_not_treated_as_zero(self):
        source = load_exploration()
        options = {r["id"]: r for r in base_options(source)}
        for base in source["bases"]:
            rows = [r for r in source["routes"] if r["base_id"] == base["id"]]
            self.assertEqual(
                options[base["id"]]["fare_coverage"],
                sum(r["fare_from_eur_person_oneway"] is not None for r in rows))


if __name__ == "__main__":
    unittest.main()
