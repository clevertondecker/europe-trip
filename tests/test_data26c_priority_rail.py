import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rail_reference_projection_model import decorate_comparison

from data26c_priority_rail_model import DATA, load_data26c_rail
from data24_coverage_model import rail_coverage
from data25_priority_rail_model import RESEARCH_BASE_IDS


class PriorityRailResearchTests(unittest.TestCase):
    def test_exact_direction_and_unsupported_claims(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        for field, value in (
            ("source_url", "https://www.sncf-connect.com/train/trajet/saumur/lille"),
            ("published_average_min", 1),
            ("valid_for_2027", True),
            ("return_weekend_verified", True),
        ):
            with self.subTest(field=field), tempfile.TemporaryDirectory() as tmp:
                altered = copy.deepcopy(payload)
                altered["records"][0][field] = value
                path = Path(tmp) / "research.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_data26c_rail(path)

    def test_secondary_source_cannot_be_mislabeled_or_reversed(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        index = next(i for i, row in enumerate(payload["records"])
                     if (row["origin_id"], row["destination_id"]) == ("metz", "arlon"))
        for changes in (
            {"source_url": "https://www.thetrainline.com/en/train-times/arlon-to-metz"},
            {"confidence": "medium"},
            {"evidence_type": "official_route_minimum", "confidence": "medium",
             "evidence_level": "operator_city_level"},
        ):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as tmp:
                altered = copy.deepcopy(payload)
                altered["records"][index].update(changes)
                path = Path(tmp) / "research.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_data26c_rail(path)

    def test_new_batch_is_directional_and_tiers_are_visible(self):
        data = load_data26c_rail()
        cells = rail_coverage()["pairs"]
        for key, kind in (
            (("metz", "stuttgart"), "official_route_minimum"),
            (("nancy", "stuttgart"), "official_route_minimum"),
            (("metz", "arlon"), "secondary_sample"),
            (("nancy", "arlon"), "secondary_sample"),
            (("strasbourg", "dinan"), "secondary_sample"),
            (("mulhouse", "saumur"), "secondary_sample"),
            (("metz", "trier"), "secondary_sample"),
            (("nancy", "trier"), "secondary_sample"),
            (("strasbourg", "trier"), "secondary_sample"),
            (("metz", "offenburg"), "secondary_sample"),
            (("nancy", "offenburg"), "secondary_sample"),
            (("metz", "kehl"), "secondary_sample"),
            (("nancy", "baden_baden"), "secondary_sample"),
            (("metz", "baden_baden"), "secondary_sample"),
            (("metz", "aachen"), "secondary_sample"),
            (("nancy", "aachen"), "secondary_sample"),
            (("lille", "baden_baden"), "secondary_sample"),
            (("nancy", "interlaken"), "secondary_sample"),
            (("metz", "interlaken"), "secondary_sample"),
            (("metz", "liege"), "secondary_sample"),
            (("strasbourg", "arlon"), "secondary_sample"),
            (("metz", "namur"), "secondary_sample"),
            (("strasbourg", "namur"), "secondary_sample"),
        ):
            with self.subTest(pair=key):
                record = data["by_pair"][key]
                cell = cells[key]["cell"]
                self.assertEqual(record["evidence_type"], kind)
                self.assertEqual(cell["category"], "reference_only")
                self.assertEqual(cell["source_kind"], kind)
                self.assertEqual(cell["confidence"], record["confidence"])
                self.assertEqual(cell["source_url"], record["source_url"])
                self.assertFalse(cell["valid_for_2027"])
                self.assertFalse(cell["weekend_return_known"])
                if kind == "secondary_sample":
                    self.assertIn("referência secundária", cell["label"])
                    self.assertNotIn("operadora", cell["label"])
                    self.assertEqual(cell["confidence"], "low")
                else:
                    self.assertIn("operadora", cell["label"])
        for key in (("strasbourg", "dinan"), ("mulhouse", "saumur")):
            self.assertEqual(data["by_pair"][key]["previous_attempts"][0]["reason"],
                             "technical_failure")

    def test_trier_requires_exact_published_station_source(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        index = next(i for i, row in enumerate(payload["records"])
                     if (row["origin_id"], row["destination_id"]) == ("metz", "trier"))
        for changes in (
            {"source_url": "https://www.thetrainline.com/en/train-times/metz-to-trier"},
            {"published_arrival_station": "Trier Süd"},
            {"source_url": "https://www.thetrainline.com/en/train-times/trier-hbf-to-metz"},
        ):
            with self.subTest(changes=changes), tempfile.TemporaryDirectory() as tmp:
                altered = copy.deepcopy(payload)
                altered["records"][index].update(changes)
                path = Path(tmp) / "research.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_data26c_rail(path)
        record = load_data26c_rail()["by_pair"][("metz", "trier")]
        self.assertEqual(record["published_arrival_station"], "Trier Hbf")
        self.assertEqual(record["station_status"], "not_reconciled")
        self.assertIsNone(record["destination_station_id"])

    def test_aachen_and_lille_station_sources_are_not_citywide_claims(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        scenarios = (
            (("metz", "aachen"), {"published_arrival_station": "Aachen West"}),
            (("nancy", "aachen"), {"source_url": "https://www.thetrainline.com/en/train-times/aachen-hbf-to-nancy"}),
            (("lille", "baden_baden"), {"published_origin_station": "Lille Flandres"}),
            (("lille", "baden_baden"), {"source_url": "https://www.thetrainline.com/en/train-times/lille-to-baden-baden"}),
        )
        for key, changes in scenarios:
            with self.subTest(key=key, changes=changes), tempfile.TemporaryDirectory() as tmp:
                altered = copy.deepcopy(payload)
                record = next(row for row in altered["records"]
                              if (row["origin_id"], row["destination_id"]) == key)
                record.update(changes)
                path = Path(tmp) / "research.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_data26c_rail(path)
        data = load_data26c_rail()["by_pair"]
        for key, _ in scenarios:
            self.assertEqual(data[key]["station_status"], "not_reconciled")
            self.assertIsNone(data[key]["origin_station_id"])
            self.assertIsNone(data[key]["destination_station_id"])
            self.assertIsNone(data[key]["transfer_count"])
            self.assertFalse(data[key]["return_weekend_verified"])

    def test_interlaken_and_liege_require_exact_station_and_direction(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        scenarios = (
            (("metz", "interlaken"), {"published_arrival_station": "Interlaken West"}),
            (("nancy", "interlaken"), {"source_url": "https://www.thetrainline.com/en/train-times/interlaken-ost-to-nancy"}),
            (("metz", "liege"), {"published_arrival_station": "Liège-Saint-Lambert"}),
            (("metz", "liege"), {"source_url": "https://www.thetrainline.com/en/train-times/metz-to-liege"}),
        )
        for key, changes in scenarios:
            with self.subTest(key=key, changes=changes), tempfile.TemporaryDirectory() as tmp:
                altered = copy.deepcopy(payload)
                record = next(row for row in altered["records"]
                              if (row["origin_id"], row["destination_id"]) == key)
                record.update(changes)
                path = Path(tmp) / "research.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_data26c_rail(path)
        data = load_data26c_rail()["by_pair"]
        for key, _ in scenarios:
            self.assertEqual(data[key]["station_status"], "not_reconciled")
            self.assertIsNone(data[key]["destination_station_id"])
            self.assertIsNone(data[key]["transfer_count"])
            self.assertFalse(data[key]["return_weekend_verified"])

    def test_selected_observation_has_no_inherited_provenance(self):
        record = load_data26c_rail()["by_pair"][("metz", "interlaken")]
        row = {"base_id": "metz", "destination_id": "interlaken",
               "evidence_status": "not_researched", "minimum_oneway_min": None,
               "source_url": "https://example.org/historical",
               "divergent_sources": False}
        contaminated = {
            "status": "unreproduced_snapshot", "display_min": None,
            "display_basis": "unknown", "average_min": 999,
            "arrival_station": "Interlaken West", "origin_station_id": "other",
            "checked_at": "2025-01-01", "fastest_provenance": "unverified",
            "rechecked_average_min": 888, "original_snapshot_average_min": 777,
            "fare_couple_eur": 123, "commercial_brand": "other",
            "service_date": "2027-09-18", "weekend_return_known": True,
            "valid_for_2027": True, "typical_time_known": True,
        }
        empty = {"by_pair": {}}
        with patch("rail_reference_projection_model.planning_reference", return_value=contaminated):
            cell = decorate_comparison({"rows": [row]}, references=empty,
                gap_overlay=empty, connectivity_overlay=empty, priority_overlay=empty,
                lille_overlay=empty, data13_overlay=empty, supplemental_overlay=empty,
                candidate_overlay={}, data25_overlay=empty,
                data26c_overlay={"by_pair": {("metz", "interlaken"): record}}
            )["cells"][("metz", "interlaken")]
        self.assertEqual(cell["display_min"], record["oneway_min"])
        self.assertEqual(cell["average_min"], record["published_average_min"])
        self.assertEqual(cell["checked_at"], record["source_checked_at"])
        self.assertEqual(cell["source_url"], record["source_url"])
        self.assertEqual(cell["reference_source_url"], record["source_url"])
        self.assertEqual(cell["confidence"], record["confidence"])
        self.assertEqual(cell["evidence_notes"], record["note"])
        self.assertEqual(cell["published_arrival_station"], "Interlaken Ost")
        self.assertIsNone(cell["published_origin_station"])
        self.assertIsNone(cell["origin_station_id"])
        self.assertIsNone(cell["destination_station_id"])
        self.assertEqual(cell["station_status"], "not_reconciled")
        self.assertIn("Interlaken Ost", cell["station_caveat"])
        for key in ("arrival_station", "rechecked_average_min", "original_snapshot_average_min",
                    "fare_couple_eur", "commercial_brand", "service_date"):
            self.assertNotIn(key, cell)
        self.assertFalse(cell["weekend_return_known"])
        self.assertFalse(cell["valid_for_2027"])
        self.assertFalse(cell["typical_time_known"])
        self.assertEqual(cell["historical_source_url"], row["source_url"])

    def test_published_origin_is_preserved_without_reconciliation(self):
        cell = rail_coverage()["pairs"][("lille", "baden_baden")]["cell"]
        self.assertEqual(cell["published_origin_station"], "Lille-Europe")
        self.assertIsNone(cell["origin_station_id"])
        self.assertEqual(cell["station_status"], "not_reconciled")
        self.assertIn("Lille-Europe", cell["station_caveat"])

    def test_quality_review_cannot_combine_versions_or_claim_2027(self):
        payload = json.loads(DATA.read_text(encoding="utf-8"))
        scenarios = (
            (("lille", "saumur"), lambda review: review.update(selected_summary_reproduced=True)),
            (("metz", "interlaken"), lambda review: review.update(destination_country="FR")),
            (("metz", "interlaken"), lambda review: review.update(direction="both")),
            (("metz", "interlaken"), lambda review: review.update(service_legs_verified=True)),
            (("strasbourg", "dinan"), lambda review: review.update(valid_for_2027=True)),
            (("strasbourg", "dinan"), lambda review: review["samples"][0].update(average_min=1)),
        )
        for key, mutate in scenarios:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as tmp:
                altered = copy.deepcopy(payload)
                row = next(r for r in altered["records"]
                           if (r["origin_id"], r["destination_id"]) == key)
                mutate(row["quality_review"])
                path = Path(tmp) / "research.json"
                path.write_text(json.dumps(altered), encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_data26c_rail(path)

    def test_original_42_records_have_individual_quality_audits(self):
        data = load_data26c_rail()["records"]
        # Freeze the original review cohort; subsequent batches may extend it.
        cohort = data[:42]
        self.assertEqual(len(cohort), 42)
        self.assertEqual(sum(r["evidence_type"] == "official_route_minimum" for r in cohort), 21)
        self.assertEqual(sum(r["evidence_type"] == "secondary_sample" for r in cohort), 21)
        for row in cohort:
            with self.subTest(pair=(row["origin_id"], row["destination_id"])):
                review = row["quality_review"]
                self.assertEqual(review["source_url"], row["source_url"])
                self.assertEqual(review["direction"], "outbound_only")
                self.assertFalse(review["service_legs_verified"])
                self.assertFalse(review["valid_for_2027"])
                self.assertEqual(review["selected_summary_reproduced"], any(
                    (s["minimum_min"], s["average_min"]) ==
                    (row["oneway_min"], row["published_average_min"])
                    for s in review["samples"]))
        ambiguous = next(r for r in cohort if (r["origin_id"], r["destination_id"]) ==
                         ("strasbourg", "arlon"))
        self.assertIn("Flixbus", ambiguous["note"])
        self.assertIn("inconclusiva", ambiguous["note"])
        self.assertEqual(ambiguous["confidence"], "low")
        self.assertFalse(ambiguous["valid_for_2027"])

    def test_documentary_coverage_before_after(self):
        dataset = load_data26c_rail()
        baseline = rail_coverage(projection_options={"data26c_overlay": {"by_pair": {}}})
        updated = rail_coverage()
        self.assertEqual(baseline["base_ids"], updated["base_ids"])
        self.assertEqual(baseline["destination_ids"], updated["destination_ids"])
        self.assertEqual(set(baseline["pairs"]), set(updated["pairs"]))
        gains = set()
        for key, pair in baseline["pairs"].items():
            old = pair["cell"]
            new = updated["pairs"][key]["cell"]
            if old["category"] == "no_time" and new["category"] == "reference_only":
                gains.add(key)
                self.assertIn(key, dataset["by_pair"])
                record = dataset["by_pair"][key]
                self.assertEqual(new["display_min"], record["oneway_min"])
                self.assertEqual(new["source_url"], record["source_url"])
                self.assertEqual(new["average_min"], record["published_average_min"])
                self.assertFalse(new["valid_for_2027"])
                self.assertFalse(new["weekend_return_known"])
            else:
                self.assertEqual(old, new)
        self.assertTrue(gains)
        for key in dataset["by_pair"]:
            self.assertIn(key, baseline["pairs"])
        for base in RESEARCH_BASE_IDS:
            self.assertEqual(baseline["by_base"][base]["eligible"], updated["by_base"][base]["eligible"])
        self.assertEqual(baseline["global"]["eligible"], updated["global"]["eligible"])
        self.assertEqual(updated["global"]["timed"] - baseline["global"]["timed"], len(gains))
        print("DATA26C_PRIORITY_PROGRESS", {
            base: {
                "eligible": updated["by_base"][base]["eligible"],
                "before": baseline["by_base"][base]["timed"],
                "after": updated["by_base"][base]["timed"],
                "remaining": updated["by_base"][base]["missing"],
                "missing_ids": sorted(d for (b, d), p in updated["pairs"].items()
                                      if b == base and p["cell"]["category"] == "no_time"),
            }
            for base in RESEARCH_BASE_IDS
        })
