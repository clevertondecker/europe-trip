"""Last-mile access is not interchangeable across arrival stations or entrances."""
import unittest
from attraction_last_mile_model import (
    load_access_pilot, matching_access_options,
    station_to_attraction_duration, validate_access_observation,
)

EXAMPLE = {
    "attraction_id":"strasbourg_cathedral", "destination_id":"strasbourg",
    "arrival_station_id":"strasbourg_gare", "entrance_id":"cathedral_main_door",
    "mode":"walk", "state":"verified_sample", "duration_min":22, "distance_m":1600,
    "source_url":"https://www.visitstrasbourg.fr/", "checked_at":"2026-11-17",
    "observed_for_date":"2026-11-17", "evidence_method":"published_station_walk_route",
    "line_or_walk_id":"station-walk",
}


class LastMileTests(unittest.TestCase):
    def test_partial_pilot_never_claims_minutes(self):
        pilot = load_access_pilot()
        self.assertEqual(len(pilot["observations"]), 3)
        self.assertTrue(all(x["duration_min"] is None for x in pilot["observations"]))
        self.assertTrue(any(x["attraction_id"] is None
                            for x in pilot["unreconciled_manual_notes"]))

    def test_station_entrance_mode_and_conflicts(self):
        alt = {**EXAMPLE, "mode":"tram", "duration_min":15,
               "line_or_walk_id":"line-a", "source_url":"https://www.cts-strasbourg.eu/"}
        options = matching_access_options(
            [EXAMPLE, alt], arrival_station_id="strasbourg_gare",
            attraction_id="strasbourg_cathedral")
        self.assertEqual(len(options), 2)
        ambiguous = station_to_attraction_duration(
            [EXAMPLE, alt], arrival_station_id="strasbourg_gare",
            attraction_id="strasbourg_cathedral")
        self.assertIsNone(ambiguous["duration_min"])
        self.assertEqual(ambiguous["status"], "unknown_or_conflicting")
        unique = station_to_attraction_duration(
            [EXAMPLE], arrival_station_id="strasbourg_gare",
            attraction_id="strasbourg_cathedral", entrance_id="cathedral_main_door")
        self.assertEqual(unique["duration_min"], 22)

    def test_wrong_station_does_not_infer_transfer(self):
        result = station_to_attraction_duration(
            [EXAMPLE], arrival_station_id="strasbourg_other",
            attraction_id="strasbourg_cathedral")
        self.assertIsNone(result["duration_min"])
        self.assertEqual(result["options"], [])

    def test_unverified_durations_and_ids_rejected(self):
        for row in (
            {**EXAMPLE, "duration_min":0},
            {**EXAMPLE, "arrival_station_id":None},
            {**EXAMPLE, "evidence_method":None},
            {**EXAMPLE, "state":"partial"},
        ):
            with self.subTest(row=row), self.assertRaises(ValueError):
                validate_access_observation(row)
        with self.assertRaises(ValueError):
            validate_access_observation(
                EXAMPLE, valid_attraction_ids={"other_attraction"})


if __name__ == "__main__":
    unittest.main()
