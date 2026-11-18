"""Vertical decision regression using an explicitly synthetic travel fixture.

No research dataset is mutated. Independent PR modules are checked after
integration; on the standalone comparator branch these tests skip only the
optional cross-branch consumers.
"""
from copy import deepcopy
from datetime import date
import unittest

from trip_plan_model import new_plan
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import (
    empty_interests, set_interest, selected_destinations_for_comparison)
from ux503_destination_base_comparison_model import compare_wishlist_bases
from ux506_decision_readiness_projection import (
    build_decision_readiness, compatible_evidence_association)


class VerticalDecisionIntegrationTests(unittest.TestCase):
    def test_catalog_to_wishlist_to_comparison_preserves_plan(self):
        discovery=build_destination_discovery()
        wishes=empty_interests()
        for dest in ("aachen","baden_baden","cologne"):
            wishes=set_interest(wishes,dest,"interested",discovery)
        before_wishes=deepcopy(wishes)
        plan=new_plan(base="mulhouse")
        before_plan=deepcopy(plan)
        comparison=compare_wishlist_bases(
            wishes,["mulhouse","strasbourg","lille"],discovery=discovery)
        readiness=build_decision_readiness(comparison,discovery=discovery)
        self.assertEqual(readiness["basket_ids"],
                         selected_destinations_for_comparison(wishes,discovery))
        self.assertEqual(len(readiness["journeys"]),9)
        self.assertEqual(len(readiness["base_housing"]),3)
        self.assertEqual(wishes,before_wishes)
        self.assertEqual(plan,before_plan)
        self.assertFalse(readiness["ranking_available"])
        self.assertIsNone(readiness["winner_id"])
        self.assertTrue(all(x["full_door_to_door_min"] is None
                            for x in readiness["journeys"]))

    def test_bidirectional_access_and_real_weekend_adapter_synthetic(self):
        try:
            from attraction_last_mile_model import bidirectional_access
            from weekend_return_validation_model import weekend_roundtrip_evidence
        except ModuleNotFoundError:
            self.skipTest("Cross-branch modules #119 and #120 not yet merged")
        source="https://www.example.org/synthetic-fixture-not-research"
        outgoing={
            "origin_id":"lille","destination_id":"cologne",
            "origin_station_id":"lille_europe",
            "destination_station_id":"cologne_hbf",
            "departure_at":"2026-11-21T08:00+01:00",
            "arrival_at":"2026-11-21T10:20+01:00",
            "calendar_dates_verified":["2026-11-21"],
            "transfers":[],"source_url":source,"duration_min":140,
        }
        returning={
            "origin_id":"cologne","destination_id":"lille",
            "origin_station_id":"cologne_hbf",
            "destination_station_id":"lille_europe",
            "departure_at":"2026-11-22T18:00+01:00",
            "arrival_at":"2026-11-22T20:40+01:00",
            "calendar_dates_verified":["2026-11-22"],
            "transfers":[],"source_url":source,"duration_min":160,
        }
        def access(direction,minutes,day):
            return {
                "direction":direction,"station_id":"cologne_hbf",
                "attraction_id":"synthetic_cathedral",
                "destination_id":"cologne","entrance_id":"main",
                "mode":"walk","state":"verified_sample",
                "duration_min":minutes,"source_url":source,
                "checked_at":"2026-11-17","observed_for_date":day,
                "evidence_method":"synthetic_test_only",
            }
        pair=bidirectional_access([
            access("station_to_attraction",15,"2026-11-21"),
            access("attraction_to_station",27,"2026-11-22")],
            attraction_id="synthetic_cathedral",
            arrival_station_id="cologne_hbf",
            return_station_id="cologne_hbf",
            arrival_date="2026-11-21",return_date="2026-11-22")
        self.assertEqual(pair["status"],"both_directions_documented")
        window={
            "visit_minutes":90,
            "opens_at":"2026-11-21T09:00+01:00",
            "closes_at":"2026-11-21T18:00+01:00",
            "opening_source_url":source,
        }
        result=compatible_evidence_association(
            outgoing,returning,pair,attraction_window=window,
            schedule_validator=weekend_roundtrip_evidence)
        self.assertEqual(result["temporal_status"],
                         "historical_schedule_coherent_only")
        self.assertIsNone(result["full_door_to_door_min"])
        self.assertFalse(result["outing_feasible_2027"])
        mismatched=deepcopy(pair)
        mismatched["to_station"]["station_id"]="deutz"
        rejected=compatible_evidence_association(
            outgoing,returning,mismatched,attraction_window=window,
            schedule_validator=weekend_roundtrip_evidence)
        self.assertIn("station_mismatch",rejected["reasons"])

if __name__=="__main__":
    unittest.main()
