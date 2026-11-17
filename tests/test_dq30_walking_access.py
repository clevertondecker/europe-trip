"""DQ3.0 P2 evidence quality regressions; no TripPlan mutation."""
from copy import deepcopy
import unittest

from attractions_model import load_attractions
from dq30_walking_access_model import (
    load_walking_access, validate_walking_access, attraction_access, destination_access
)
from dq30_mobility_evidence_model import load_mobility_pilot
from trip_plan_model import new_plan


class WalkingAccessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_attractions()

    def setUp(self):
        self.data = load_walking_access(catalog=self.catalog)

    def reject(self, mutate):
        invalid = deepcopy(self.data)
        mutate(invalid)
        with self.assertRaises((ValueError, KeyError, TypeError)):
            validate_walking_access(invalid, self.catalog)

    def test_complete_P0_inventory_and_verified_points(self):
        expected = {x["id"] for x in self.catalog["attractions"]
                    if x["destination_id"] in self.data["destinations"]}
        self.assertEqual({x["attraction_id"] for x in self.data["attractions"]}, expected)
        self.assertEqual(len(expected), 30)
        self.assertEqual(sum(x["coordinates"] is not None for x in self.data["attractions"]),13)
        self.assertEqual(len(self.data["stations"]),6)
        self.assertFalse(any(x["entrance_verified"] for x in self.data["attractions"]))

    def test_invalid_coordinates_and_fake_entrance(self):
        self.reject(lambda d: d["attractions"][0].update(
            coordinates={"lat":100.0,"lon":7.0},coordinate_precision="entrance"))
        self.reject(lambda d: d["attractions"][0].update(entrance_verified=True))
        self.reject(lambda d: d["stations"][0].update(coordinates={"lat":float("nan"),"lon":7.0}))

    def test_missing_ids_and_duplicates(self):
        self.reject(lambda d: d["attractions"][0].update(attraction_id="fake_attraction"))
        self.reject(lambda d: d["attractions"].append(deepcopy(d["attractions"][0])))
        self.reject(lambda d: d["walking_routes"].append(deepcopy(d["walking_routes"][0])))
        self.reject(lambda d: d["walking_routes"][0].update(origin_id="nonexistent"))
        self.reject(lambda d: d["candidate_sequences"][0].update(attraction_ids=["basel_munster","strasbourg_cathedral"]))

    def test_source_required_for_confirmed_coordinates_or_walking(self):
        self.reject(lambda d: d["attractions"][0].update(coordinate_source_url=None))
        route_index = next(i for i,r in enumerate(self.data["walking_routes"])
                           if r["duration_min"] is not None)
        self.reject(lambda d: d["walking_routes"][route_index].update(source_url=None))
        self.reject(lambda d: d["walking_routes"][route_index].update(checked_at=None))
        self.reject(lambda d: d["walking_routes"][route_index].update(method=None))

    def test_distance_mode_and_inference_guards(self):
        self.reject(lambda d: d["walking_routes"][0].update(distance_m=-1))
        self.reject(lambda d: d["walking_routes"][0].update(duration_min=-3))
        self.reject(lambda d: d["walking_routes"][0].update(mode="rail"))
        self.reject(lambda d: d["walking_routes"][0].update(distance_kind="straight_line"))
        self.reject(lambda d: d["walking_routes"][0].update(distance_m=500,
                      status="operator_published_walk_duration",
                      method="haversine",source_url="https://example.com",
                      checked_at="2026-11-17"))
        self.assertEqual(sum(r["duration_min"] is not None for r in self.data["walking_routes"]),1)
        self.assertFalse(any(r["distance_m"] is not None for r in self.data["walking_routes"]))

    def test_three_requested_consumer_examples_and_legacy(self):
        mapping = [
            ("strasbourg_cathedral", "strasbourg_gare", None),
            ("brussels_grand_place", "brussels_central", None),
            ("bruges_markt", "brugge_station", 20),
        ]
        for aid, station, expected_time in mapping:
            entry = attraction_access(aid, evidence=self.data)
            self.assertEqual(entry["arrival_station"]["id"], station)
            self.assertEqual(entry["station_route"]["duration_min"], expected_time)
            self.assertIsNone(entry["station_route"]["distance_m"])
        self.assertIsNotNone(attraction_access("strasbourg_cathedral",evidence=self.data)["historical_access"])
        self.assertIsNotNone(load_mobility_pilot())
        self.assertIsNone(attraction_access("missing",evidence=self.data))

    def test_read_only_and_trip_plan_unchanged(self):
        plan = new_plan()
        before = deepcopy(plan)
        original = deepcopy(self.data)
        entry = destination_access("bruges_be", evidence=self.data)
        entry["stations"][0]["name"] = "changed"
        self.assertEqual(plan,before)
        self.assertEqual(self.data,original)


if __name__ == "__main__":
    unittest.main()
