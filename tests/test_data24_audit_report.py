"""DATA24A: public audit parity, provenance, deterministic report and stale detection."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from data24_audit_model import build_audit, attributed_photo
from data24_coverage_model import rail_coverage
from tools.data24_research_coverage import input_manifest, render_report, render_annex, render_legacy_annex, main


class AuditReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch("data24_audit_model.rail_coverage", wraps=rail_coverage) as resolver:
            cls.audit = build_audit()
        assert resolver.call_count == 1

    def test_separate_universes_and_exclusive_status(self):
        v = self.audit
        a = v["attractions"]
        counts = a["counts"]
        self.assertEqual(v["rail_counts"]["total"],
                         len(v["base_ids"]) * len(v["destination_ids"]))
        self.assertEqual(len(v["rail_pairs"]), v["rail_counts"]["total"])
        self.assertEqual(counts["destinations"], len(v["destination_ids"]))
        self.assertEqual(counts["attractions"], len(a["rows"]))
        self.assertEqual(counts["attractions"], sum(x["attractions"] for x in a["destinations"]))
        self.assertEqual(counts["attractions"], sum(counts[key] for key in
                         ("ticket_published", "ticket_unknown", "ticket_not_applicable")))
        for field in ("total", "eligible", "timed", "historical", "indicative", "local", "missing"):
            self.assertEqual(v["rail_counts"][field],
                             sum(row[field] for row in v["rail_by_destination"].values()))
        self.assertTrue(all(not p["return_2027_verified"] and
                            p["full_door_to_door_min"] is None for p in v["rail_pairs"]))
        self.assertFalse(v["official_plan_modified"])

    def test_source_contracts_and_no_inferred_photos_or_access(self):
        for row in self.audit["attractions"]["rows"]:
            if row["ticket_status"] == "operator_published":
                self.assertIsNotNone(row["ticket"]["amount"])
                self.assertTrue(row["ticket"]["per"])
                self.assertTrue(row["ticket"]["currency"])
            self.assertEqual(row["photo_attributed"], attributed_photo(row["photo"]))
            for access in row["station_access"]:
                self.assertIsNotNone(access["duration_min"])
                self.assertTrue(access["source_url"])
        for pair in self.audit["rail_pairs"]:
            if pair["category"] in ("historical", "reference_only"):
                self.assertIsNotNone(pair["display_min"])
                self.assertTrue(pair["source_url"])
            for fare in pair["fare_observations"]:
                self.assertTrue(fare["source_url"])
                self.assertIsNotNone(fare["fare_from_eur_person_oneway"])
        self.assertFalse(attributed_photo({"url": "https://example.com"}))

    def test_preserve_legacy_evidence_and_dq31_basket(self):
        v = self.audit
        self.assertEqual(len(v["legacy_evidence"]), v["legacy_summary"]["cities"])
        self.assertEqual({row["id"] for row in v["legacy_evidence"]},
                         {row["id"] for row in v["legacy_dq31"]["rows"]})
        self.assertTrue(v["legacy_dq31"]["basket"]["ids"])
        for row in v["legacy_evidence"]:
            self.assertIn("housing", row)
            self.assertIn("international_countries_with_time", row)
            for criterion in row["criteria"].values():
                self.assertIn("checks", criterion)
                self.assertIn("scoring_gap", criterion)
            for evidence in row["evidence"]:
                self.assertTrue({"indicator", "value", "unit", "observed_at", "scope",
                                 "kind", "source_url", "limitation"}.issubset(evidence))

    def test_deterministic_rendering_and_stale_check(self):
        manifest = input_manifest(self.audit)
        before = deepcopy(self.audit)
        report = render_report(self.audit, manifest)
        annex = render_annex(self.audit, manifest)
        self.assertEqual(report, render_report(self.audit, manifest))
        self.assertEqual(annex, render_annex(self.audit, manifest))
        self.assertEqual(json.loads(annex)["inputs"], manifest)
        self.assertEqual(self.audit, before)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.md"
            with patch("tools.data24_research_coverage.build_audit", return_value=self.audit):
                self.assertEqual(main(["--output", str(path)]), 0)
                self.assertEqual(main(["--output", str(path), "--check-annex"]), 0)
                path.with_suffix(".json").unlink()
                self.assertEqual(main(["--output", str(path), "--check"]), 0)
                self.assertEqual(main(["--output", str(path), "--check-annex"]), 1)
                path.write_text("stale", encoding="utf-8")
                self.assertEqual(main(["--output", str(path), "--check"]), 1)

    def test_committed_report_is_current(self):
        root = Path(__file__).resolve().parents[1]
        report = root / "docs/audits/data24_research_coverage.md"
        self.assertEqual(report.read_text(encoding="utf-8"),
                         render_report(self.audit))
    
    def test_removed_inventory_is_not_imported_by_app(self):
        root = Path(__file__).resolve().parents[1]
        app = (root / "app.py").read_text(encoding="utf-8")
        self.assertNotIn("render_weight_coverage", app)
        self.assertIn('preserved_modes = ["Estudos de troca","Referências históricas"]', app)
        self.assertIn('"Evidências e lacunas":"Referências históricas"', app)
        self.assertIn('"Pesos das 30 cidades":"Referências históricas"', app)
        self.assertIn('"Comparar mesmas viagens":"Referências históricas"', app)
        self.assertIn("render_city_decision(", app)

    def test_content_fingerprint_and_legacy_artifact(self):
        changed = deepcopy(self.audit)
        changed["rail_pairs"][0]["source_url"] = "https://example.org/reviewed"
        self.assertNotEqual(input_manifest(self.audit), input_manifest(changed))
        self.assertEqual(render_report(self.audit, {"unrelated": "a"}),
                         render_report(self.audit, {"unrelated": "b"}))
        legacy = render_legacy_annex(self.audit)
        decoded = json.loads(legacy)
        for key in ("legacy_evidence", "legacy_dq31", "legacy_summary"):
            self.assertEqual(decoded[key], json.loads(json.dumps(self.audit[key])))
        path = Path(__file__).resolve().parents[1] / "docs/audits/data24_legacy_evidence.json"
        self.assertEqual(path.read_text(encoding="utf-8"), legacy)
