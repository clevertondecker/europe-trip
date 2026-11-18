"""Fixture-based review tests: no dependency on 30x46 fixed catalog."""
import copy
import unittest
from rail_component_contract import build_component_records

URL="https://www.bahn.de/reisen/view/verbindung/aachen/karlsruhe.shtml"

def pair(a,b,cat="missing",minutes=None):
    return {"base_id":a,"destination_id":b,"base_name":a,"destination_name":b,
            "category":cat,"oneway_min":minutes,
            "source_url":URL if minutes is not None else None,
            "source_checked_at":"2026-11-18" if minutes is not None else None,
            "return_2027_verified":False,"door_to_door_2027_verified":False,
            "fare_couple_2027_eur":None}

def observation(**fields):
    return {"state":"documented","source_url":URL,
            "source_dataset":"test_fixture","checked_at":"2026-11-18",**fields}

def inv(*rows):
    return {"pairs":list(rows),"total_pairs":len(rows)}

class ComponentReviewTests(unittest.TestCase):
    def test_historical_and_indicative_do_not_prove_return(self):
        rows=build_component_records(inv(pair("a","b","historical",70),
             pair("a","c","indicative",120)))
        self.assertEqual([r["component_states"]["outbound_rail_duration"]["state"]
                          for r in rows],["historical_only","indicative_reference"])
        for row in rows:
            self.assertIn("independent_return_service",row["research_required"])
            self.assertIn("last_mile_return_to_station",row["research_required"])
            self.assertEqual(row["component_states"]["return_service_calendar"]["state"],"not_evaluated")
            self.assertFalse(row["confirmed_2027"])

    def test_independent_last_miles_and_different_stations(self):
        evidence={
            "outbound_arrival_station":observation(station_id="arrival_hbf"),
            "return_departure_station":observation(station_id="return_sud"),
            "last_mile_outbound":observation(
                direction="arrival_station_to_attraction",
                from_id="arrival_hbf",to_id="museum",duration_min=12),
            "last_mile_return":observation(
                direction="attraction_to_return_station",
                from_id="museum",to_id="return_sud",duration_min=15),
        }
        row=build_component_records(inv(pair("a","b","historical",70)),
            evidence_by_pair={("a","b"):evidence})[0]
        self.assertNotIn("last_mile_to_attraction",row["research_required"])
        self.assertNotIn("last_mile_return_to_station",row["research_required"])
        self.assertNotIn("outbound_last_mile_station_alignment",row["research_required"])
        self.assertNotIn("return_last_mile_station_alignment",row["research_required"])
        self.assertNotEqual(row["station_identities"]["outbound_arrival_station_id"],
                            row["station_identities"]["return_departure_station_id"])
        self.assertFalse(row["confirmed_2027"])

    def test_missing_return_last_mile_never_inherits_outbound(self):
        row=build_component_records(inv(pair("a","b","historical",70)),
            evidence_by_pair={("a","b"):{
                "last_mile_outbound":observation(direction="arrival_station_to_attraction",
                    from_id="hbf",to_id="museum",duration_min=12)}})[0]
        self.assertEqual(row["component_states"]["last_mile_return"]["state"],"not_evaluated")
        self.assertIn("last_mile_return_to_station",row["research_required"])

    def test_mismatch_requires_alignment_not_incompatibility(self):
        row=build_component_records(inv(pair("a","b","historical",70)),
            evidence_by_pair={("a","b"):{
                "return_departure_station":observation(station_id="a_hbf"),
                "last_mile_return":observation(direction="attraction_to_return_station",
                    from_id="museum",to_id="b_sud",duration_min=12)}})[0]
        self.assertIn("return_last_mile_station_alignment",row["research_required"])
        self.assertNotEqual(row["component_states"]["last_mile_return"]["state"],"incompatible")

    def test_transfer_and_calendar_independent_from_return(self):
        row=build_component_records(inv(pair("a","b","indicative",120)))[0]
        for key in ("outbound_transfers","return_transfers",
                    "return_service_calendar","return_rail_duration"):
            self.assertEqual(row["component_states"][key]["state"],"not_evaluated")
        for key in ("outbound_transfer_details","return_transfer_details",
                    "return_service_calendar","independent_return_service"):
            self.assertIn(key,row["research_required"])

    def test_local_has_unknown_two_direction_urban_access(self):
        row=build_component_records(inv(pair("a","a","local")))[0]
        self.assertIsNone(row["known_outbound_oneway_min"])
        self.assertEqual(row["component_states"]["return_rail_duration"]["state"],"not_applicable")
        self.assertEqual(row["component_states"]["local_access_outbound"]["state"],"not_evaluated")
        self.assertEqual(row["component_states"]["local_access_return"]["state"],"not_evaluated")

    def test_lookup_state_is_supported_only_after_exact_lookup(self):
        data=inv(pair("a","b"))
        raw=observation(state="unknown_after_lookup",lookup_performed=True,
            lookup_outcome="no_match",lookup_base_id="a",lookup_destination_id="b",
            lookup_component="return_service_calendar")
        row=build_component_records(data,evidence_by_pair={
            ("a","b"):{"return_service_calendar":raw}})[0]
        self.assertEqual(row["component_states"]["return_service_calendar"]["state"],"unknown_after_lookup")
        self.assertIn("return_service_calendar",row["research_required"])
        for invalid in (dict(raw,lookup_base_id="c"),dict(raw,source_dataset=""),
                        dict(raw,lookup_performed=False)):
            with self.assertRaises(ValueError):
                build_component_records(data,evidence_by_pair={
                    ("a","b"):{"return_service_calendar":invalid}})

    def test_partial_fare_and_historical_calendar_never_confirm(self):
        data=inv(pair("a","b","historical",70))
        fare=observation(traveler_count=2,currency="EUR",amount_eur=28,
                         fare_date="2027-10-01",journey_scope="outbound_two_adults")
        row=build_component_records(data,evidence_by_pair={
            ("a","b"):{"two_adults_fare":fare}})[0]
        self.assertIn("two_adults_fare",row["research_required"])
        with self.assertRaises(ValueError):
            build_component_records(data,evidence_by_pair={("a","b"):{
                "return_service_calendar":observation(service_date="2026-11-18",
                    runs_on_date=True)}})

    def test_multiple_snapshots_and_no_mutation(self):
        first=inv(pair("a","a","local"),pair("a","b","missing"))
        second=inv(*first["pairs"],pair("c","b","indicative",85))
        old=copy.deepcopy((first,second))
        self.assertEqual(len(build_component_records(first)),2)
        self.assertEqual(len(build_component_records(second)),3)
        self.assertEqual((first,second),old)

if __name__=="__main__":
    unittest.main()
