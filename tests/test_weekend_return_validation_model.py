"""Return evidence tests: two train legs are not a complete outing."""
import unittest
from weekend_return_validation_model import (
    validate_service_leg, weekend_roundtrip_evidence,
)

OUT = {
    "origin_id":"liege", "destination_id":"maastricht",
    "origin_station_id":"liege_guillemins", "destination_station_id":"maastricht_centraal",
    "departure_local":"2026-11-21T08:00+01:00",
    "arrival_local":"2026-11-21T08:45+01:00",
    "calendar_dates_verified":["2026-11-21"],
    "transfers":[], "source_url":"https://www.belgiantrain.be/en/",
}
BACK = {
    "origin_id":"maastricht", "destination_id":"liege",
    "origin_station_id":"maastricht_centraal", "destination_station_id":"liege_guillemins",
    "departure_local":"2026-11-21T18:10+01:00",
    "arrival_local":"2026-11-21T18:55+01:00",
    "calendar_dates_verified":["2026-11-21"],
    "transfers":[], "source_url":"https://www.belgiantrain.be/en/",
}
ACCESS = {
    "arrival_station_id":"maastricht_centraal", "return_station_id":"maastricht_centraal",
    "access_to_min":20, "access_back_min":20, "visit_minutes":80,
    "opens_at":"2026-11-21T09:00+01:00", "closes_at":"2026-11-21T17:00+01:00",
    "access_source_url":"https://www.visitmaastricht.com/en/",
    "opening_source_url":"https://www.visitmaastricht.com/en/",
}


class ReturnValidationTests(unittest.TestCase):
    def test_never_claims_future_viability_from_documents(self):
        without = weekend_roundtrip_evidence(OUT, BACK)
        self.assertEqual(without["status"], "documented_legs_only")
        self.assertFalse(without["outing_feasible"])
        with_window = weekend_roundtrip_evidence(OUT, BACK, attraction_window=ACCESS)
        self.assertEqual(with_window["status"], "historical_schedule_coherent_only")
        self.assertFalse(with_window["outing_feasible"])
        self.assertFalse(with_window["valid_for_2027"])

    def test_direction_calendar_station_and_order(self):
        mismatch = {**BACK, "destination_id": "lille"}
        self.assertEqual(weekend_roundtrip_evidence(OUT, mismatch)["reason"],
                         "reversed_city_pair_mismatch")
        no_calendar = {**BACK, "calendar_dates_verified":[]}
        self.assertEqual(weekend_roundtrip_evidence(OUT, no_calendar)["status"],
                         "partial_calendar")
        wrong_station = {**ACCESS, "arrival_station_id":"wrong"}
        self.assertEqual(
            weekend_roundtrip_evidence(OUT, BACK, attraction_window=wrong_station)["reason"],
            "station_mismatch")
        too_early = {**BACK, "departure_local":"2026-11-21T08:10+01:00"}
        self.assertEqual(weekend_roundtrip_evidence(OUT, too_early)["reason"],
                         "schedule_order_inconsistent")

    def test_opening_and_last_mile(self):
        closed = {**ACCESS, "closes_at":"2026-11-21T09:20+01:00"}
        self.assertEqual(weekend_roundtrip_evidence(OUT, BACK,
                                                   attraction_window=closed)["reason"],
                         "opening_or_useful_time_conflict")
        missing = {**ACCESS, "access_to_min":None}
        self.assertEqual(weekend_roundtrip_evidence(OUT, BACK,
                                                   attraction_window=missing)["status"],
                         "missing_access_evidence")

    def test_transfer_chain_and_positive_time(self):
        bad = {**OUT, "transfers":[{
            "station_id":"other", "arrival_local":"2026-11-21T08:30+01:00",
            "departure_local":"2026-11-21T08:25+01:00",
            "source_url":"https://www.belgiantrain.be/en/"}]}
        with self.assertRaises(ValueError):
            validate_service_leg(bad)
        wrong = {**OUT, "arrival_local":"2026-11-21T07:50+01:00"}
        with self.assertRaises(ValueError):
            validate_service_leg(wrong)

    def test_missing_leg(self):
        self.assertEqual(weekend_roundtrip_evidence(OUT, None)["status"],
                         "insufficient_evidence")


if __name__ == "__main__":
    unittest.main()
