"""DQ3.0: provenance, unknowns and unified adapter regressions."""
import unittest
from copy import deepcopy

from dq30_mobility_evidence_model import (
    load_mobility_pilot, validate_mobility_pilot, access_by_attraction,
)
from rail_evidence_unified_model import load_rail_evidence, route_evidence
from attractions_model import load_attractions


class DQ30PilotTests(unittest.TestCase):
    def setUp(self):
        self.data = load_mobility_pilot()

    def test_pilot_uses_canonical_attraction_ids(self):
        catalog = load_attractions()
        by_id = {x["id"]: x for x in catalog["attractions"]}
        for record in self.data["attraction_access"]:
            self.assertIn(record["attraction_id"], by_id)
            self.assertEqual(record["destination_id"],
                             by_id[record["attraction_id"]]["destination_id"])
            self.assertIsNone(record["coordinates"])
            self.assertIsNone(record["walk_duration_min"])

    def test_no_2027_return_or_route_inference(self):
        self.assertFalse(self.data["2027_return_verified"])
        for record in self.data["rail_service_observations"]:
            self.assertFalse(record["return_verified"])
            self.assertFalse(record["valid_for_2027"])
            self.assertIsNone(record["last_mile_min"])
        invalid = deepcopy(self.data)
        invalid["rail_service_observations"][0]["return_verified"] = True
        with self.assertRaises(ValueError):
            validate_mobility_pilot(invalid)

    def test_advertised_fare_is_not_normal_tariff(self):
        for x in self.data["rail_service_observations"]:
            if x["fare_from_eur_person_oneway"] is not None:
                self.assertEqual(x["fare_kind"], "advertised_from_conditional")

    def test_same_pair_keeps_distinct_services_and_original_precedence(self):
        evidence = load_rail_evidence()
        result = route_evidence(evidence, "offenburg", "strasbourg")
        dated = [x for x in result["observations"]
                 if x["source_dataset"] == "dq30_dated_operator_2026"]
        self.assertEqual(len(dated), 2)
        self.assertEqual({x["minimum_oneway_min"] for x in dated}, {25,29})
        self.assertFalse(result["return_2027_verified"])
        self.assertFalse(result["comparable"])

    def test_unresearched_is_not_zero_or_invented_walking(self):
        self.assertIsNone(access_by_attraction(self.data, "missing_id"))
        p = access_by_attraction(self.data, "brussels_grand_place")
        self.assertIsNone(p["walk_distance_m"])
        self.assertIsNone(p["walk_duration_min"])
        self.assertIsNone(p["coordinates"])


if __name__ == "__main__":
    unittest.main()
