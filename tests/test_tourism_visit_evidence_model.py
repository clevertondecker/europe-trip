"""Tourist research cannot silently rewrite catalog or promise future hours."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from tourism_visit_evidence_model import (
    DATA, load_visit_evidence, visit_decision_overview,
    validate_opening_schedule, evaluate_visit_window,
)
from datetime import datetime


class TouristVisitEvidenceTests(unittest.TestCase):
    def test_three_existing_canonical_ids_and_2027_gaps(self):
        doc = load_visit_evidence()
        self.assertEqual(len(doc["entries"]), 3)
        self.assertEqual({x["attraction_id"] for x in doc["entries"]},
                         {"dq32_aachen_07","dq32_baden_baden_27","strasbourg_cathedral"})
        self.assertTrue(all(not x["valid_for_2027"] for x in doc["entries"]))
        self.assertTrue(all(x["station_to_attraction_min"] is None
                            for x in doc["entries"]))
        overview = visit_decision_overview()
        self.assertEqual(overview["2027_date_specific_opening_confirmed"], 0)
        self.assertFalse(overview["wishlist_mutated"])

    def test_structured_hours_closures_and_2027_caveat(self):
        schedule = {
            "state": "partial", "timezone": "Europe/Paris",
            "source_url": "https://example.org/official-hours",
            "checked_at": "2026-11-17",
            "weekly_intervals": {"5": [{"open": "09:00", "close": "12:00"},
                                       {"open": "14:00", "close": "17:00"}]},
            "exceptions": [], "seasons": [], "validity": {},
        }
        self.assertEqual(validate_opening_schedule(schedule)["state"], "partial")
        historical = evaluate_visit_window(schedule,
            earliest_start=datetime.fromisoformat("2026-11-21T10:00+01:00"),
            latest_end=datetime.fromisoformat("2026-11-21T12:00+01:00"),
            duration_min=90)
        self.assertEqual(historical["status"], "historical_window_compatible")
        self.assertFalse(historical["verified_for_date"])
        late = evaluate_visit_window(schedule,
            earliest_start=datetime.fromisoformat("2027-10-23T10:00+02:00"),
            latest_end=datetime.fromisoformat("2027-10-23T12:00+02:00"),
            duration_min=70)
        self.assertFalse(late["verified_for_date"])
        closed = {**schedule, "exceptions": [
            {"date": "2026-11-21", "state": "closed"}]}
        blocked = evaluate_visit_window(closed,
            earliest_start=datetime.fromisoformat("2026-11-21T10:00+01:00"),
            latest_end=datetime.fromisoformat("2026-11-21T12:00+01:00"),
            duration_min=70)
        self.assertEqual(blocked["status"], "closed_on_date")
        overlapping = {**schedule, "weekly_intervals": {"5": [
            {"open": "09:00", "close": "12:00"},
            {"open": "11:00", "close": "14:00"}]}}
        with self.assertRaises(ValueError):
            validate_opening_schedule(overlapping)

    def test_invalid_price_source_or_future_claim_fails(self):
        orig = json.loads(DATA.read_text(encoding="utf-8"))
        changes = []
        false_free = copy.deepcopy(orig)
        false_free["entries"][0]["entry_ticket"]["amount"] = 12
        changes.append(false_free)
        bad_source = copy.deepcopy(orig)
        bad_source["entries"][1]["source_url"] = "http://example.org"
        changes.append(bad_source)
        fake_2027 = copy.deepcopy(orig)
        fake_2027["entries"][2]["valid_for_2027"] = True
        changes.append(fake_2027)
        with TemporaryDirectory() as d:
            file = Path(d) / "source.json"
            for item in changes:
                file.write_text(json.dumps(item),encoding="utf-8")
                with self.assertRaises(ValueError):
                    load_visit_evidence(file)


if __name__ == "__main__":
    unittest.main()
