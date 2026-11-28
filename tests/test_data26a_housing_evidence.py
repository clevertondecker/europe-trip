"""DATA26A: validated documentary records, no promotion to 2027 verification."""
import json
import unittest
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory

from base_research_expanded_model import load_research
from data26a_housing_evidence_model import (
    CHECKS, load_housing_observations, project_housing_observations,
    validate_housing_observations,
)
from ux132c2_living_coverage_model import (
    build_living_view, city_detail, scope_rows, scope_counts,
    documented_housing_counts, ALL,
)
from data24_audit_model import build_audit
from tools.data24_research_coverage import REPORT, render_report


def record(i, *, base="metz", checkin="2027-09-25", checkout="2027-11-22", currency="EUR"):
    # Synthetic only: never committed to the production evidence inventory.
    q = {
        "base_id": base, "checkin": checkin, "checkout": checkout,
        "source_url": f"https://example.org/listing/{i}", "checked_at": "2026-11-27",
        "currency": currency, "travelers": 2,
        **dict.fromkeys(CHECKS, True),
        "rent_total": 2000, "cleaning_fee": 0, "service_fee": 50,
        "mandatory_taxes": 30, "utilities_total": 100, "refundable_deposit": 500,
    }
    return {"id": f"quote-{i}", "listing_id": f"example:listing-{i}", "quote": q,
            "evidence_url": f"https://example.org/evidence/{i}",
            "contract_terms": "Fixture: short stay terms",
            "cancellation_terms": "Fixture: cancellation terms"}


def payload(*records):
    return {"schema_version": 1, "quotes": list(records)}


class HousingEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.research = load_research(include_candidates=True)

    def project(self, data):
        return project_housing_observations(data, research=self.research)

    def test_empty_fixture_valid_production_inventory_and_historical_audit(self):
        source = load_housing_observations(research=self.research)
        self.assertEqual(self.project(payload())["documented"], 0)
        self.assertEqual(self.project(source)["documented"], len(source["quotes"]))
        self.assertEqual(self.project(source)["independently_verified"], 0)
        self.assertEqual(REPORT.read_bytes(), render_report(build_audit(projection_options={"data26c_overlay": {"by_pair": {}}})).encode("utf-8"))

    def test_validated_file_flows_to_coverage_without_promoting_confirmation(self):
        data = payload(record(1), record(2), record(3))
        before = deepcopy(data)
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "quotes.json"
            path.write_text(json.dumps(data), encoding="utf-8")
            loaded = load_housing_observations(path, research=self.research)
        view = build_living_view(research=self.research, housing_observations=loaded)
        row = city_detail(view, "metz")
        current = row["housing_observations"]
        self.assertEqual(current["documented"], 3)
        self.assertEqual(current["largest_comparable_documented_group"], 3)
        self.assertEqual(current["independently_verified"], 0)
        first = current["groups"][0]["records"][0]
        self.assertEqual(first["evaluation"]["expense_total"], 2180)
        self.assertEqual(first["evaluation"]["refundable_deposit_separate"], 500)
        self.assertEqual(first["evaluation"]["upfront_cash_exposure"], 2680)
        self.assertFalse(first["evaluation"]["decision_ready_for_dates"])
        self.assertEqual(first["quote"], data["quotes"][0]["quote"])
        self.assertEqual(first["evidence_url"], data["quotes"][0]["evidence_url"])
        self.assertIsNone(row["housing"]["total_2027"])
        self.assertIsNone(row["remote_work"]["residential_internet_2027"])
        self.assertIn("três cotações comparáveis de 2027", row["research_gaps"]["decision_blockers"])
        counts = documented_housing_counts(scope_rows(view))
        self.assertEqual(counts["with_documented_quotes"], 1)
        self.assertEqual(counts["with_three_comparable_documented_quotes"], 1)
        self.assertEqual(counts["bases"], 5)
        self.assertEqual(documented_housing_counts(scope_rows(view, ALL))["bases"], 7)
        self.assertEqual(scope_counts(view), scope_counts(build_living_view()))
        self.assertEqual(data, before)

    def test_different_dates_and_currency_never_count_as_three_comparable(self):
        data = payload(record(1), record(2, currency="CHF"),
                       record(3, checkin="2027-09-26", checkout="2027-11-23"))
        result = self.project(data)["by_base"]["metz"]
        self.assertEqual(result["documented"], 3)
        self.assertEqual(len(result["groups"]), 3)
        self.assertEqual(result["largest_comparable_documented_group"], 1)

    def test_unknown_negative_and_zero_preserved(self):
        r = record(1)
        r["quote"]["internet_verified"] = False
        r["quote"]["available_on_dates"] = None
        r["quote"]["mandatory_taxes"] = None
        r["contract_terms"] = None
        result = self.project(payload(r))["by_base"]["metz"]["groups"][0]["records"][0]
        self.assertIs(result["quote"]["internet_verified"], False)
        self.assertIsNone(result["quote"]["available_on_dates"])
        self.assertEqual(result["quote"]["cleaning_fee"], 0)
        self.assertIsNone(result["evaluation"]["expense_total"])
        self.assertFalse(result["documented_complete"])
        self.assertIn("condicoes_do_contrato", result["missing_requirements"])

    def test_invalid_source_fields_and_duplicates(self):
        for field, value in (("currency", "BRL"), ("travelers", True),
                             ("checkin", "2028-09-25"), ("checked_at", "2027-10-01"),
                             ("rent_total", -1), ("rent_total", float("nan")),
                             ("internet_verified", "true"), ("source_url", "http://example.org"),
                             ("base_id", "unknown"), ("source_url", "https://")):
            with self.subTest(field=field, value=value):
                r = record(1)
                r["quote"][field] = value
                with self.assertRaises(ValueError):
                    validate_housing_observations(payload(r), research=self.research)
        r = record(1)
        r["independently_verified"] = True
        with self.assertRaises(ValueError):
            self.project(payload(r))
        r = record(2)
        r["listing_id"] = record(1)["listing_id"]
        with self.assertRaises(ValueError):
            self.project(payload(record(1), r))
        r = record(2)
        r["quote"]["source_url"] = record(1)["quote"]["source_url"]
        with self.assertRaises(ValueError):
            self.project(payload(record(1), r))


if __name__ == "__main__":
    unittest.main()
