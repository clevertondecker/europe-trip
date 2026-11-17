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
        self.assertEqual(sum(x["coordinates"] is not None for x in self.data["attractions"]),26)
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

    def _routed_fixture(self, *, station_id="strasbourg_gare",
                       attraction_id="strasbourg_cathedral"):
        """Synthetic verified public access points; never persisted as real evidence."""
        data=deepcopy(self.data)
        station=next(x for x in data["stations"] if x["id"]==station_id)
        attraction=next(x for x in data["attractions"] if x["attraction_id"]==attraction_id)
        station["pedestrian_access_points"]=[{
            "id":"station_public_exit_test","parent_id":station_id,
            "kind":"public_exit",
            "coordinates":{"lat":48.5851,"lon":7.7342},
            "source_url":"https://example.org/official-station-exit",
            "checked_at":"2026-11-17",
            "verification_status":"verified_public_access",
        }]
        attraction["pedestrian_access_points"]=[{
            "id":"attraction_entrance_test","parent_id":attraction_id,
            "kind":"public_entrance",
            "coordinates":{"lat":48.5818,"lon":7.7511},
            "source_url":"https://example.org/official-attraction-entrance",
            "checked_at":"2026-11-17",
            "verification_status":"verified_public_access",
        }]
        route=next(x for x in data["walking_routes"]
                   if x["origin_id"]==station_id)
        route.update(status="pedestrian_routed",distance_m=1100,
                     duration_min=15,geometry_status="verified_pedestrian_routing",
                     method="pedestrian_routing_engine",profile="pedestrian",
                     source_url="https://example.org/routing-request",
                     checked_at="2026-11-17",origin_access_id="station_public_exit_test",
                     destination_access_id="attraction_entrance_test",
                     engine="Valhalla",engine_version="3.6.0",
                     geometry_source_url="https://example.org/routing-geometry",
                     routing_observed_at="2026-11-17",
                     coordinate_conflict_unresolved=False)
        return data,route

    def test_routed_evidence_supported_only_with_verified_public_access(self):
        fixture,route=self._routed_fixture()
        validate_walking_access(fixture,self.catalog)
        route["origin_access_id"]=None
        with self.assertRaises(ValueError):
            validate_walking_access(fixture,self.catalog)

    def test_routing_requires_provenance_profile_geometry_and_version(self):
        for field,bad in [
            ("engine",None),("engine_version",None),
            ("profile","driving"),("method","haversine"),
            ("geometry_source_url",None),("routing_observed_at",None),
            ("geometry_status","not_available")]:
            data,route=self._routed_fixture()
            route[field]=bad
            with self.subTest(field=field),self.assertRaises((ValueError,TypeError)):
                validate_walking_access(data,self.catalog)

    def test_station_centroid_does_not_count_as_public_exit(self):
        fixture,route=self._routed_fixture()
        station=fixture["stations"][0]
        station["pedestrian_access_points"]=[]
        with self.assertRaises(ValueError):
            validate_walking_access(fixture,self.catalog)

    def test_unresolved_station_conflict_blocks_routed_trip(self):
        fixture,route=self._routed_fixture()
        fixture["stations"][0]["coordinate_conflict_unresolved"]=True
        with self.assertRaises(ValueError):
            validate_walking_access(fixture,self.catalog)

    def test_official_and_pending_state_are_backwards_compatible(self):
        data=deepcopy(self.data)
        official=next(r for r in data["walking_routes"]
                      if r["status"]=="operator_published_walk_duration")
        self.assertEqual(official["duration_min"],20)
        official["status"]="official_published"
        validate_walking_access(data,self.catalog)
        official["status"]="pending_verification"
        official["duration_min"]=None
        official["method"]=None
        official["source_url"]=None
        official["checked_at"]=None
        validate_walking_access(data,self.catalog)
        official["duration_min"]=20
        with self.assertRaises(ValueError):
            validate_walking_access(data,self.catalog)

    def test_station_conflict_and_access_data_do_not_claim_routing_ready(self):
        brugge=next(s for s in self.data["stations"] if s["id"]=="brugge_station")
        self.assertFalse(brugge["coordinate_conflict_unresolved"])
        self.assertEqual(brugge["coordinate_reconciliation"]["status"],
                         "representative_station_location_reconciled_only")
        self.assertFalse(brugge["pedestrian_access_points"])
        for row in self.data["walking_routes"]:
            self.assertIsNone(row["origin_access_id"])
            self.assertIsNone(row["destination_access_id"])

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

    def test_reconciliation_requires_source_and_is_not_entrance(self):
        self.reject(lambda d: d["stations"][4].update(
            coordinate_reconciliation={"status":"representative_station_location_reconciled_only",
                                       "sources":[],"checked_at":"2026-11-17",
                                       "reason":"not verified"}))
        self.reject(lambda d: d["stations"][4].update(
            pedestrian_routing_ready=True))
        station=next(x for x in self.data["stations"] if x["id"]=="brugge_station")
        self.assertFalse(station["pedestrian_access_points"])
        self.assertFalse(station["pedestrian_routing_ready"])

    def test_researched_attractions_keep_precision_and_provenance(self):
        confirmed=[x for x in self.data["attractions"] if x["coordinates"]]
        self.assertEqual(len(confirmed),26)
        self.assertTrue(all(x["coordinate_source_url"].startswith("https://")
                            and x["coordinate_precision"] in ("area_centroid","attraction_point")
                            for x in confirmed))
        self.assertFalse(any(x["entrance_verified"] for x in self.data["attractions"]))
        self.assertEqual({x["attraction_id"] for x in self.data["attractions"] if not x["coordinates"]},
                         {x["attraction_id"] for x in self.data["research_attempts"]})
        self.assertEqual(len(self.data["candidate_sequences"]),6)
        self.assertTrue(all(x["research_source_url"].startswith("https://")
                            for x in self.data["candidate_sequences"]))

    def test_no_engine_result_inferred_from_station_representatives(self):
        self.assertEqual(self.data["routing_provider_assessment"]["status"],"not_run")
        self.assertFalse(any(r["status"]=="pedestrian_routed" for r in self.data["walking_routes"]))
        self.assertFalse(any(r["distance_m"] is not None for r in self.data["walking_routes"]))
        self.assertEqual(sum(r["duration_min"] is not None for r in self.data["walking_routes"]),1)

    def test_official_7km_loop_does_not_create_segment_distances(self):
        walks=self.data["published_walking_itineraries"]
        self.assertEqual(len(walks),1)
        self.assertEqual(walks[0]["distance_m"],7000)
        self.assertEqual(walks[0]["destination_id"],"rotterdam")
        self.assertEqual(walks[0]["end_station_id"],"rotterdam_centraal_station")
        self.assertEqual(walks[0]["route_scope"],"entire_loop_not_individual_segments")
        self.assertIsNone(walks[0]["duration_min"])
        self.assertFalse(any(x["distance_m"] is not None for x in self.data["walking_routes"]))

    def test_official_itinerary_rejects_incompatible_scopes_and_ids(self):
        self.reject(lambda d: d["published_walking_itineraries"][0].update(distance_m=-7000))
        self.reject(lambda d: d["published_walking_itineraries"][0].update(route_scope="single_segment"))
        self.reject(lambda d: d["published_walking_itineraries"][0].update(source_url=None))
        self.reject(lambda d: d["published_walking_itineraries"][0].update(included_attraction_ids=["colmar_heads"]))
        self.reject(lambda d: d["published_walking_itineraries"].append(
            deepcopy(d["published_walking_itineraries"][0])))

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
