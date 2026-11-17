"""Unit contracts: no invented feasibility, direction, or precedence."""
import unittest
from copy import deepcopy

from route_research_evidence_model import (
    observation_id, journey_identity, legacy_projection,
    validate_observation, validate_observations,
)

BASE = {
    "schema_version": 1,
    "origin_id": "Strasbourg",
    "destination_id": "Colmar",
    "source_nature": "operator_date_specific_schedule",
    "evidence_state": "timed_observation",
    "temporal_validity": "historical_sample",
    "checked_at": "2026-11-17",
    "travel_date": "2026-11-16",
    "departure_local": "08:30",
    "arrival_local": "09:02",
    "origin_station_id": "strasbourg_gare",
    "destination_station_id": "colmar_gare",
    "service_id": "TER-1",
    "operator": "SNCF TER",
    "duration_min": 32,
    "transfers": 0,
    "source_url": "https://www.sncf-connect.com/",
}


class EvidenceContractTests(unittest.TestCase):
    def test_distinct_directions_and_stations(self):
        other = {**BASE, "origin_id": BASE["destination_id"],
                 "destination_id": BASE["origin_id"]}
        station = {**BASE, "destination_station_id": "colmar_other"}
        self.assertNotEqual(journey_identity(BASE), journey_identity(other))
        self.assertNotEqual(journey_identity(BASE), journey_identity(station))

    def test_deduplication_is_idempotent(self):
        result = validate_observations([BASE, deepcopy(BASE)])
        self.assertEqual(result["count"], 1)
        self.assertEqual(result["observations"][0]["observation_id"], observation_id(BASE))

    def test_conflicting_sources_remain(self):
        second = {**BASE, "duration_min": 37,
                  "source_url": "https://www.bahn.de/"}
        result = validate_observations([BASE, second])
        self.assertEqual(result["count"], 2)
        self.assertEqual(len(result["conflicts"]), 1)

    def test_unknown_has_no_duration(self):
        row = {**BASE, "evidence_state": "unknown", "duration_min": None,
               "temporal_validity": "validity_unknown", "source_url": None}
        self.assertIsNone(validate_observation(row)["duration_min"])
        with self.assertRaises(ValueError):
            validate_observation({**row, "duration_min": 0})

    def test_published_future_not_inferred(self):
        with self.assertRaises(ValueError):
            validate_observation({**BASE, "temporal_validity": "future_date_explicitly_verified"})
        with self.assertRaises(ValueError):
            validate_observation({**BASE, "source_nature": "operator_route_summary",
                                  "travel_date": "2027-10-05",
                                  "temporal_validity": "future_date_explicitly_verified"})
        valid = {**BASE, "travel_date": "2027-10-05",
                 "temporal_validity": "future_date_explicitly_verified"}
        self.assertEqual(validate_observation(valid)["travel_date"], "2027-10-05")

    def test_invalid_dates_urls_and_values(self):
        for key, value in (
            ("checked_at", "2026-02-30"), ("source_url", "http://example.com"),
            ("duration_min", -1), ("duration_min", True), ("transfers", -1),
            ("departure_local", "25:30"), ("origin_station_id", ""),
        ):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                validate_observation({**BASE, key: value})

    def test_editorial_note_never_becomes_timed_rail(self):
        with self.assertRaises(ValueError):
            validate_observation({**BASE, "source_nature": "manual_editorial_note"})

    def test_legacy_adapter_remains_read_only(self):
        before = legacy_projection("strasbourg", "colmar")
        after = legacy_projection("strasbourg", "colmar")
        self.assertEqual(before, after)
        self.assertFalse(before["return_2027_verified"])
        self.assertFalse(before["comparable"])


if __name__ == "__main__":
    unittest.main()
