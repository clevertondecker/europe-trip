"""Regression tests for all exploratory home-base outing previews."""
import unittest
from copy import deepcopy

from attractions_model import load_attractions
from base_explorer_model import load_exploration
from base_scenario_model import base_options
from rail_evidence_unified_model import load_rail_evidence
from outing_base_coverage_model import preview_for_base


class AlternateBaseOutingCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog=load_attractions()
        cls.rail=load_rail_evidence()
        cls.exploration=load_exploration()
        cls.options=base_options()

    def get(self,city):
        return preview_for_base(
            city,catalog=self.catalog,rail=self.rail,
            exploration=self.exploration,options=self.options)

    def test_every_one_of_30_bases_shows_same_canonical_attractions(self):
        self.assertEqual(len(self.options),30)
        canonical={x["id"] for x in self.catalog["attractions"]}
        for base in self.options:
            with self.subTest(base=base["id"]):
                view=self.get(base["id"])
                actual={x["id"] for dest in view["destinations"]
                        for x in dest["attractions"]}
                self.assertEqual(actual,canonical)
                self.assertEqual(view["catalog_destinations"],14)
                self.assertEqual(view["catalog_attractions"],65)
                self.assertTrue(view["advisory_only"])
                self.assertFalse(view["trip_plan_modified"])

    def test_lille_uses_real_existing_samples_without_foreign_fares(self):
        view=self.get("lille")
        self.assertGreaterEqual(view["timed_destination_count"],4)
        brussels=next(r for r in view["destinations"] if r["destination_id"]=="brussels")
        self.assertIsNotNone(brussels["train_oneway_min"])
        self.assertTrue(brussels["train_evidence_url"].startswith("https://"))
        self.assertEqual(brussels["train_status"],"historical_station_to_station")
        self.assertIsNone(brussels["full_couple_cost_eur"])
        self.assertFalse(brussels["weekend_return_verified_2027"])

    def test_offenburg_and_karlsruhe_can_show_documented_train(self):
        for city in ("offenburg","karlsruhe"):
            with self.subTest(city=city):
                self.assertGreater(self.get(city)["timed_destination_count"],0)

    def test_unresearched_freiburg_does_not_claim_no_trains(self):
        view=self.get("freiburg")
        self.assertEqual(view["timed_destination_count"],0)
        self.assertEqual(view["status"],"attractions_only")
        self.assertTrue(all(r["train_oneway_min"] is None for r in view["destinations"]))
        self.assertTrue(all(r["full_couple_cost_eur"] is None for r in view["destinations"]))

    def test_local_access_not_assumed_free_or_zero(self):
        colmar=self.get("colmar")
        local=next(r for r in colmar["destinations"] if r["destination_id"]=="colmar")
        self.assertTrue(local["local"])
        self.assertIsNone(local["train_oneway_min"])
        self.assertIsNone(local["last_mile_min"])
        self.assertIsNone(local["full_couple_cost_eur"])
        self.assertEqual(local["train_status"],"local_transport_unverified")

    def test_luxembourg_city_alias_is_local_without_zero_cost(self):
        view=self.get("luxembourg_city")
        local=next(r for r in view["destinations"] if r["destination_id"]=="luxembourg")
        self.assertTrue(local["local"])
        self.assertEqual(local["train_status"],"local_transport_unverified")
        self.assertIsNone(local["train_oneway_min"])
        self.assertIsNone(local["full_couple_cost_eur"])

    def test_no_canonical_input_mutation_and_defensive_return(self):
        original=deepcopy(self.catalog)
        result=self.get("lille")
        result["destinations"][0]["attractions"][0]["name"]="MODIFIED"
        self.assertEqual(self.catalog,original)
        self.assertNotEqual(self.get("lille")["destinations"][0]["attractions"][0]["name"],
                            "MODIFIED")

    def test_unknown_base_rejected(self):
        with self.assertRaises(ValueError):
            self.get("not_a_real_city")


if __name__=="__main__":
    unittest.main()
