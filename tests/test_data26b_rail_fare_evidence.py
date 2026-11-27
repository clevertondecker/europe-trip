import copy
import unittest
from data26b_rail_fare_evidence_model import project_rail_fares, load_rail_fares

def leg(origin, destination, start, end):
    return dict(origin_id=origin, destination_id=destination,
                origin_station_id=origin+"-station", destination_station_id=destination+"-station",
                departure_at="2027-10-02T"+start+"+02:00",
                arrival_at="2027-10-02T"+end+"+02:00",
                calendar_dates_verified=["2027-10-02"], transfer_count=0,
                source_url="https://example.org/service")

def fixture():
    return {"schema_version": 1, "quotes": [dict(
        id="fixture", outbound=leg("mulhouse","colmar","08:00","08:30"),
        inbound=leg("colmar","mulhouse","18:00","18:30"),
        checked_at="2026-11-27", source_url="https://example.org/fare",
        currency="EUR", travelers=2, total_minor=4000,
        mandatory_fees_included=True, fare_class="standard",
        fare_conditions="non-refundable", availability="documented_offer")]}

class RailFareTest(unittest.TestCase):
    def test_empty_production(self):
        self.assertEqual(load_rail_fares()["documented"], 0)

    def test_roundtrip_documentation_not_confirmation(self):
        payload = fixture()
        before = copy.deepcopy(payload)
        result = project_rail_fares(payload)
        self.assertEqual(payload, before)
        self.assertEqual(result["roundtrips"], 1)
        self.assertEqual(result["complete_documentation"], 1)
        self.assertFalse(result["records"][0]["valid_for_2027"])
        self.assertEqual(result["independently_verified"], 0)

    def test_unknown_price(self):
        payload = fixture()
        payload["quotes"][0]["total_minor"] = None
        self.assertEqual(project_rail_fares(payload)["complete_documentation"], 0)

    def test_invalid_fields(self):
        for field, value in [("total_minor", True), ("total_minor", -1),
                             ("travelers", 1), ("currency", "XYZ"),
                             ("source_url", "http://example.org"),
                             ("checked_at", "2027-10-03"),
                             ("availability", "unknown")]:
            with self.subTest(field=field, value=value):
                payload = fixture()
                payload["quotes"][0][field] = value
                with self.assertRaises(ValueError):
                    project_rail_fares(payload)

    def test_duplicate(self):
        payload = fixture()
        duplicate = copy.deepcopy(payload["quotes"][0])
        duplicate["id"] = "second"
        payload["quotes"].append(duplicate)
        with self.assertRaises(ValueError):
            project_rail_fares(payload)

    def test_wrong_return(self):
        payload = fixture()
        payload["quotes"][0]["inbound"] = leg("colmar","strasbourg","18:00","18:30")
        with self.assertRaises(ValueError):
            project_rail_fares(payload)
