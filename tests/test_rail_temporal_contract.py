"""Shared time contract: explicit offset or unknown, never guessed."""
import unittest

from rail_temporal_contract import normalize_service_instants


class RailTemporalContractTests(unittest.TestCase):
    def test_historical_clock_without_offset_stays_noncomparable(self):
        row = {"travel_date": "2026-11-21", "departure_local": "08:00",
               "arrival_local": "09:00"}
        self.assertEqual(normalize_service_instants(row)["precision"],
                         "local_clock_only")
        with self.assertRaises(ValueError):
            normalize_service_instants(row, require_offsets=True)

    def test_explicit_offset_clock_adapter(self):
        row = {"travel_date": "2026-11-21",
               "departure_local": "23:40", "arrival_local": "00:30",
               "arrival_date": "2026-11-22",
               "departure_utc_offset": "+01:00",
               "arrival_utc_offset": "+01:00"}
        result = normalize_service_instants(row, require_offsets=True)
        self.assertEqual(result["precision"], "offset_aware")
        self.assertLess(result["departure"], result["arrival"])

    def test_crosses_midnight_without_arrival_date_not_inferred(self):
        row = {"travel_date": "2026-11-21",
               "departure_local": "23:40", "arrival_local": "00:30",
               "departure_utc_offset": "+01:00",
               "arrival_utc_offset": "+01:00"}
        with self.assertRaises(ValueError):
            normalize_service_instants(row, require_offsets=True)

    def test_dst_fall_back_same_wall_hour_with_different_offsets(self):
        row = {
            "departure_at": "2026-10-25T02:20+02:00",
            "arrival_at": "2026-10-25T02:50+01:00",
            "origin_timezone": "Europe/Brussels",
            "destination_timezone": "Europe/Amsterdam",
        }
        actual = normalize_service_instants(row, require_offsets=True)
        self.assertEqual(actual["precision"], "offset_aware")
        self.assertEqual(
            int((actual["arrival"] - actual["departure"]).total_seconds()) // 60,
            90,
        )

    def test_timestamp_without_offset_and_wrong_dst_offset(self):
        with self.assertRaises(ValueError):
            normalize_service_instants({
                "departure_at": "2026-11-21T09:00",
                "arrival_at": "2026-11-21T10:00",
            }, require_offsets=True)
        with self.assertRaises(ValueError):
            normalize_service_instants({
                "departure_at": "2026-07-10T08:00+01:00",
                "arrival_at": "2026-07-10T09:00+01:00",
                "origin_timezone": "Europe/Brussels",
            }, require_offsets=True)


if __name__ == "__main__":
    unittest.main()
