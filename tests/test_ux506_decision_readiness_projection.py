"""Regression: overlays are consumed; journeys require delegated temporal checks."""
import copy
import unittest

from ux506_decision_readiness_projection import (
    build_decision_readiness, compatible_evidence_association,
)
from ux501_destination_discovery_model import build_destination_discovery

DISCOVERY = build_destination_discovery()
ROW = {
    "base_id": "mulhouse", "destination_id": "aachen",
    "minimum_oneway_min": None, "return_weekend_verified": False,
    "local_access_verified": False,
}


def comparison():
    return {
        "base_ids": ["mulhouse", "strasbourg"],
        "destinations": [{"id": "aachen"}],
        "rows": [ROW, {**ROW, "base_id": "strasbourg"}],
    }


RAIL = {
    "origin_id": "lille", "destination_id": "cologne",
    "origin_station_id": "lille_europe",
    "destination_station_id": "cologne_hbf",
    "departure_at": "2026-11-21T09:00+01:00",
    "arrival_at": "2026-11-21T11:48+01:00",
    "duration_min": 168, "source_url": "https://www.sncf-connect.com/",
    "calendar_dates_verified": ["2026-11-21"], "transfers": [],
}
RETURN = {
    "origin_id": "cologne", "destination_id": "lille",
    "origin_station_id": "cologne_hbf",
    "destination_station_id": "lille_europe",
    "departure_at": "2026-11-22T18:00+01:00",
    "arrival_at": "2026-11-22T21:12+01:00",
    "duration_min": 192, "source_url": "https://www.bahn.de/",
    "calendar_dates_verified": ["2026-11-22"], "transfers": [],
}
ACCESS = {
    "attraction_id": "proposed_cologne_cathedral",
    "destination_id": "cologne",
    "arrival_station_id": "cologne_hbf",
    "return_station_id": "cologne_hbf",
    "source_url": "https://www.koelntourismus.de/", "duration_min": 18,
}


class ReadinessProjectionTests(unittest.TestCase):
    def test_public_catalog_gaps_without_winner(self):
        value = comparison()
        original = copy.deepcopy(value)
        result = build_decision_readiness(
            value, discovery=DISCOVERY, tourism_overlay={"entries": []},
            housing_overlay={"bases": []})
        self.assertEqual(result["basket_ids"], ["aachen"])
        self.assertEqual(len(result["base_housing"]), 2)
        self.assertEqual(len(result["journeys"]), 2)
        self.assertTrue(all(x["full_door_to_door_min"] is None
                            for x in result["journeys"]))
        self.assertTrue(all(x["total_stay_price_2027"] is None
                            for x in result["base_housing"]))
        self.assertFalse(result["ranking_available"])
        self.assertIsNone(result["winner_id"])
        self.assertFalse(result["wishlist_modified"])
        self.assertEqual(value, original)

    def test_mismatched_baskets_rejected(self):
        value = comparison()
        value["rows"] = [ROW]
        with self.assertRaises(ValueError):
            build_decision_readiness(value, discovery=DISCOVERY,
                                     tourism_overlay={"entries": []},
                                     housing_overlay={"bases": []})

    def test_tourism_overlay_enriches_existing_destination_without_2027_claim(self):
        value = comparison()
        overlay = {"entries": [{
            "attraction_id": "dq32_aachen_07", "destination_id": "aachen",
            "opening_state": "verified_current_rule", "opening_rule": "Sunday 13-17",
            "source_url": "https://www.aachenerdom.de/en/",
            "checked_at": "2026-11-17", "valid_for_2027": False,
        }]}
        overview = build_decision_readiness(
            value, discovery=DISCOVERY, tourism_overlay=overlay,
            housing_overlay={"bases": []})
        city = overview["destinations"][0]
        self.assertEqual(city["published_opening_hours"], 1)
        self.assertEqual(city["enriched_current_opening_rules"], 1)
        self.assertEqual(overview["tourism_source_scope"],
                         "pilot_overlay_and_legacy_catalog")
        self.assertFalse(city["visit_ready_for_2027"])
        self.assertFalse(overview["wishlist_modified"])

    def test_overlay_identity_and_future_unsupported(self):
        invalid = {"entries": [{
            "attraction_id": "dq32_aachen_07", "destination_id": "strasbourg",
            "opening_state": "verified_current_rule", "opening_rule": "Monday",
            "source_url": "https://www.aachenerdom.de/en/",
            "valid_for_2027": False,
        }]}
        with self.assertRaises(ValueError):
            build_decision_readiness(comparison(), discovery=DISCOVERY,
                                     tourism_overlay=invalid,
                                     housing_overlay={"bases": []})

    def test_station_direction_and_missing_components_block(self):
        bad = compatible_evidence_association(
            RAIL, RETURN, {**ACCESS, "arrival_station_id": "other_station"},
            schedule_validator=lambda *_a, **_kw: {"status": "documented_legs_only"})
        self.assertEqual(bad["association_status"], "not_composable")
        self.assertIn("station_mismatch", bad["reasons"])
        wrong = compatible_evidence_association(
            RAIL, RETURN, {**ACCESS, "destination_id": "aachen"},
            schedule_validator=lambda *_a, **_kw: {"status": "documented_legs_only"})
        self.assertIn("attraction_destination_mismatch", wrong["reasons"])
        missing = compatible_evidence_association(RAIL, None, ACCESS)
        self.assertIn("missing_component", missing["reasons"])

    def test_saturday_sunday_and_schedules_are_delegated(self):
        seen = []
        def weekend_checker(out, back, *, attraction_window=None):
            seen.append((out["departure_at"], back["departure_at"]))
            return {"status": "documented_legs_only"}
        result = compatible_evidence_association(
            RAIL, RETURN, ACCESS, schedule_validator=weekend_checker)
        self.assertEqual(len(seen), 1)
        self.assertEqual(result["association_status"],
                         "historical_schedule_checked_components_only")
        self.assertIsNone(result["full_door_to_door_min"])
        self.assertFalse(result["outing_feasible_2027"])

        def invalid_order(*args, **kwargs):
            return {"status": "incompatible", "reason": "schedule_order_inconsistent"}
        before_arrival = {**RETURN, "departure_at": "2026-11-21T10:00+01:00"}
        incompatible = compatible_evidence_association(
            RAIL, before_arrival, ACCESS, schedule_validator=invalid_order)
        self.assertEqual(incompatible["association_status"], "not_composable")
        self.assertIn("schedule_order_inconsistent", incompatible["reasons"])

        calendar_missing = compatible_evidence_association(
            RAIL, RETURN, ACCESS,
            schedule_validator=lambda *_a, **_kw: {
                "status": "partial_calendar", "reason": "service_dates_not_verified"})
        self.assertEqual(calendar_missing["association_status"], "not_composable")
        self.assertIn("service_dates_not_verified", calendar_missing["reasons"])

    def test_without_temporal_validator_only_identity_matches(self):
        result = compatible_evidence_association(
            RAIL, RETURN, ACCESS,
            schedule_validator=lambda *_a, **_kw: {"status": "documented_legs_only"})
        self.assertEqual(result["temporal_status"], "documented_legs_only")


if __name__ == "__main__":
    unittest.main()
