"""A decision layer cannot turn fragmented historical observations into trips."""
import copy
import unittest

from ux506_decision_readiness_projection import (
    build_decision_readiness, compatible_evidence_association,
)
from ux501_destination_discovery_model import build_destination_discovery

DISCOVERY = build_destination_discovery()
ROW = {
    "base_id":"mulhouse", "destination_id":"aachen",
    "minimum_oneway_min":None, "return_weekend_verified":False,
    "local_access_verified":False,
}


class ReadinessProjectionTests(unittest.TestCase):
    def test_public_catalog_gaps_without_winner(self):
        comparison = {
            "base_ids":["mulhouse", "strasbourg"],
            "destinations":[{"id":"aachen"}],
            "rows":[ROW, {**ROW, "base_id":"strasbourg"}],
        }
        original = copy.deepcopy(comparison)
        result = build_decision_readiness(comparison, discovery=DISCOVERY)
        self.assertEqual(result["basket_ids"], ["aachen"])
        self.assertEqual(len(result["base_housing"]), 2)
        self.assertEqual(len(result["journeys"]), 2)
        self.assertTrue(all(x["full_door_to_door_min"] is None for x in result["journeys"]))
        self.assertTrue(all(x["total_stay_price_2027"] is None for x in result["base_housing"]))
        self.assertFalse(result["ranking_available"])
        self.assertIsNone(result["winner_id"])
        self.assertFalse(result["wishlist_modified"])
        self.assertEqual(comparison, original)

    def test_mismatched_baskets_rejected(self):
        invalid = {
            "base_ids":["mulhouse", "lille"], "destinations":[{"id":"aachen"}],
            "rows":[ROW],
        }
        with self.assertRaises(ValueError):
            build_decision_readiness(invalid, discovery=DISCOVERY)

    def test_rail_return_access_must_match_but_no_door_to_door_inference(self):
        rail = {"origin_id":"lille", "destination_id":"cologne",
                "destination_station_id":"cologne_hbf", "travel_date":"2026-11-21",
                "source_url":"https://www.sncf-connect.com/", "duration_min":168}
        ret = {"origin_id":"cologne", "destination_id":"lille",
               "origin_station_id":"cologne_hbf", "travel_date":"2026-11-21",
               "source_url":"https://www.bahn.de/", "duration_min":192}
        access = {"arrival_station_id":"cologne_hbf","return_station_id":"cologne_hbf",
                  "source_url":"https://www.koelntourismus.de/", "duration_min":18}
        matched = compatible_evidence_association(rail, ret, access)
        self.assertEqual(matched["association_status"], "compatible_components_only")
        self.assertIsNone(matched["full_door_to_door_min"])
        self.assertFalse(matched["outing_feasible_2027"])
        bad = compatible_evidence_association(
            rail, ret, {**access, "arrival_station_id":"other_station"})
        self.assertEqual(bad["association_status"], "not_composable")
        self.assertIn("station_mismatch", bad["reasons"])
        missing = compatible_evidence_association(rail, None, access)
        self.assertIn("missing_component", missing["reasons"])


if __name__ == "__main__":
    unittest.main()
