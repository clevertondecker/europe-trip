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
        fare_conditions="non-refundable", availability="documented_offer",
        passenger_profile="two_adults", discount_eligibility="none",
        ticket_structure="integrated", checked_at_time=None,
        refundability="not_allowed", changeability="not_allowed")]}

class RailFareTest(unittest.TestCase):
    def test_empty_fixture(self):
        self.assertEqual(project_rail_fares({"schema_version": 1, "quotes": []})["documented"], 0)

    def test_production_contract(self):
        self.assertEqual(load_rail_fares()["independently_verified"], 0)

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

    def test_conflict_and_distinct_services(self):
        payload = fixture()
        other = copy.deepcopy(payload["quotes"][0])
        other["id"] = "other"
        other["total_minor"] = 5000
        payload["quotes"].append(other)
        with self.assertRaisesRegex(ValueError, "conflitantes"):
            project_rail_fares(payload)
        other["outbound"]["service_id"] = "another-service"
        self.assertEqual(project_rail_fares(payload)["documented"], 2)

    def test_distinct_transfers(self):
        payload = fixture()
        other = copy.deepcopy(payload["quotes"][0])
        other["id"] = "other"
        for q, station in zip((payload["quotes"][0], other), ("station-a", "station-b")):
            q["outbound"].update(transfer_count=1, transfer_legs=[dict(
                station_id=station, arrival_at="2027-10-02T08:10+02:00",
                departure_at="2027-10-02T08:15+02:00", source_url="https://example.org/transfer")])
        payload["quotes"].append(other)
        self.assertEqual(project_rail_fares(payload)["documented"], 2)

    def test_distinct_commercial_conditions_and_times(self):
        for field, value in [("discount_eligibility", "card"), ("ticket_structure", "separate"),
                             ("checked_at_time", "2026-11-27T12:00+01:00")]:
            payload = fixture()
            other = copy.deepcopy(payload["quotes"][0])
            other.update(id="other")
            other[field] = value
            payload["quotes"].append(other)
            self.assertEqual(project_rail_fares(payload)["documented"], 2)

    def test_scope_and_fees(self):
        for fees in (True, False, None):
            payload = fixture()
            q = payload["quotes"][0]
            q.update(inbound=None, mandatory_fees_included=fees, total_minor=0)
            result = project_rail_fares(payload)["records"][0]
            self.assertEqual(result["scope"], "oneway")
            self.assertEqual(result["quote"]["total_minor"], 0)
            self.assertEqual(result["complete_documentation"], fees is True)
            self.assertFalse(result["return_temporally_coherent"])

    def test_unknown_availability_and_calendar(self):
        payload = fixture()
        q = payload["quotes"][0]
        q.update(availability="unknown", total_minor=None)
        q["inbound"]["calendar_dates_verified"] = []
        result = project_rail_fares(payload)["records"][0]
        self.assertTrue(result["return_temporally_coherent"])
        self.assertFalse(result["return_calendar_documented"])
        self.assertFalse(result["complete_documentation"])

    def test_overnight_and_different_offsets(self):
        payload = fixture()
        q = payload["quotes"][0]
        q["inbound"].update(departure_at="2027-10-02T23:30+02:00",
                            arrival_at="2027-10-03T00:30+01:00")
        result = project_rail_fares(payload)["records"][0]
        self.assertTrue(result["return_temporally_coherent"])
        self.assertFalse(result["outing_feasible"])

    def test_equivalent_utc_consultation_is_duplicate(self):
        payload = fixture()
        first = payload["quotes"][0]
        first["checked_at_time"] = "2026-11-27T23:30+00:00"
        second = copy.deepcopy(first)
        second.update(id="second", checked_at="2026-11-28",
                      checked_at_time="2026-11-28T00:30+01:00")
        payload["quotes"].append(second)
        with self.assertRaisesRegex(ValueError, "duplicada"):
            project_rail_fares(payload)

    def test_commercial_unknown_and_scope_counts(self):
        payload = fixture()
        q = payload["quotes"][0]
        q["refundability"] = None
        self.assertEqual(project_rail_fares(payload)["complete_roundtrip"], 0)
        q["refundability"] = "conditional"
        self.assertEqual(project_rail_fares(payload)["complete_roundtrip"], 1)
        q["inbound"] = None
        result = project_rail_fares(payload)
        self.assertEqual(result["complete_roundtrip"], 0)
        self.assertEqual(result["complete_oneway"], 1)

    def test_data24_parity_with_populated_fares(self):
        from data24_coverage_model import rail_coverage
        from ux132_research_coverage_model import build_coverage_view
        from unittest.mock import patch
        before = rail_coverage()
        with patch("data26b_rail_fare_evidence_model.load_rail_fares",
                   return_value=project_rail_fares(fixture())):
            view = build_coverage_view()
            after = rail_coverage()
        self.assertEqual(before, after)
        self.assertEqual(view["global"], before["global"])
        self.assertEqual(view["pairs"], before["pairs"])

    def test_streamlit_multiple_fare_cards(self):
        from streamlit.testing.v1 import AppTest
        payload = fixture()
        other = copy.deepcopy(payload["quotes"][0])
        other.update(id="unknown", inbound=None, total_minor=None,
                     availability="unknown", mandatory_fees_included=None)
        payload["quotes"].append(other)
        third = copy.deepcopy(payload["quotes"][0])
        third.update(id="zero", total_minor=0, mandatory_fees_included=False,
                     checked_at="2026-11-28")
        payload["quotes"].append(third)
        script = (
            "from ux132_research_coverage_ui import render_fare_evidence\n"
            "from data26b_rail_fare_evidence_model import project_rail_fares\n"
            "view = {'bases': [{'id': 'mulhouse', 'name': 'Mulhouse'}], "
            "'destinations': [{'id': 'colmar', 'name': 'Colmar'}]}\n"
            "render_fare_evidence(view, project_rail_fares(" + repr(payload) + "))\n"
        )
        app = AppTest.from_string(script).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertFalse(app.warning)
        text = " ".join(str(x.value) for x in [*app.markdown, *app.caption])
        for expected in ("Mulhouse", "Colmar", "Ida e retorno", "Somente ida",
                         "EUR 40,00", "EUR 0,00", "Preço desconhecido",
                         "Disponibilidade desconhecida", "Calendário documentado",
                         "2 adultos", "Valor observado", "Total documentado"):
            self.assertIn(expected, text)


    def test_production_dated_service_samples_are_not_quotes(self):
        result = load_rail_fares()
        samples = result["schedule_samples"]
        self.assertEqual(result["dated_roundtrip_samples"], 5)
        self.assertEqual({s["outbound"]["origin_id"]: s["gross_destination_minutes"]
                          for s in samples}, {
            "lille": 799, "metz": 682, "nancy": 684,
            "mulhouse": 580, "strasbourg": 720,
        })
        for sample in samples:
            self.assertEqual(sample["roundtrip_status"], "documented_legs_only")
            self.assertEqual(sample["station_identity_scope"], "source_published_not_reconciled")
            self.assertIsNone(sample["net_visit_minutes"])
            self.assertFalse(sample["last_mile_verified"])
            self.assertFalse(sample["outing_feasible"])
            self.assertFalse(sample["valid_for_2027"])
            for leg in (sample["outbound"], sample["inbound"]):
                self.assertTrue(leg["calendar_date_applicable"])
                self.assertEqual(leg["departure_at"][:10], "2026-11-29")
                self.assertEqual(leg["transfer_count"], 0)
                self.assertTrue(leg["service_id"])
            self.assertNotIn("quote", sample)
            self.assertNotIn("total_minor", sample)
        # Date-specific service evidence cannot promote the fare coverage.
        from data26b1_fare_reference_model import fare_reference_coverage
        self.assertEqual(fare_reference_coverage(quotes=result),
                         fare_reference_coverage(quotes=project_rail_fares({"schema_version": 1, "quotes": [
                             r["quote"] for r in result["records"]]})))

    def test_schedule_samples_reject_wrong_dates_prices_and_station_conflicts(self):
        import json
        from data26b_rail_fare_evidence_model import PATH
        payload = json.loads(PATH.read_text(encoding="utf-8"))
        payload["schedule_samples"] = [payload["schedule_samples"][0]]
        for modify in (
            lambda s: s.update(total_minor=4000),
            lambda s: s.update(checked_at="2026-12-05"),
            lambda s: s["inbound"].update(calendar_dates_verified=["2026-12-06"]),
            lambda s: s["inbound"].update(origin_station_id="sncf_published:paris_est"),
            lambda s: s["inbound"].update(origin_station_label="Paris Est"),
            lambda s: s["inbound"].update(departure_at="2026-11-29T08:00:00+01:00"),
            lambda s: s["outbound"].update(departure_at="2026-11-29T08:12:00+02:00"),
        ):
            with self.subTest(modification=modify):
                altered = copy.deepcopy(payload)
                modify(altered["schedule_samples"][0])
                with self.assertRaises(ValueError):
                    project_rail_fares(altered)

    def test_schedule_sample_ui_separate_from_quote_cards(self):
        from streamlit.testing.v1 import AppTest
        script = """
from ux132_research_coverage_ui import render_fare_evidence
from data26b_rail_fare_evidence_model import load_rail_fares
render_fare_evidence({"bases": [{"id": "lille", "name": "Lille"}],
                      "destinations": [{"id": "paris", "name": "Paris"}]}, load_rail_fares())
"""
        app = AppTest.from_string(script).run(timeout=30)
        self.assertFalse(app.exception)
        self.assertFalse(app.warning)
        tables = [d.value for d in app.dataframe if "Janela bruta" in d.value.columns]
        self.assertEqual(len(tables), 1)
        self.assertEqual(len(tables[0]), 5)
        self.assertIn("13h19", list(tables[0]["Janela bruta"]))
        rendered = " ".join(str(x.value) for x in [*app.markdown, *app.caption])
        self.assertIn("Não são cotações para dois adultos", rendered)
        self.assertIn("7014", rendered)
        self.assertIn("7093", rendered)
