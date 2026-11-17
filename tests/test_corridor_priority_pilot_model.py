"""Small fixed public corridor research before geometric expansion."""
import json
import tempfile
from pathlib import Path
import unittest

from corridor_priority_pilot_model import load_pilot, pilot_matrix, DATA


class CorridorPilotTests(unittest.TestCase):
    def test_fixed_public_basket_and_historical_source_precedence(self):
        result = pilot_matrix()
        self.assertEqual(result["bases"], ["mulhouse", "strasbourg", "lille"])
        self.assertEqual(result["basket_ids"], ["aachen", "baden_baden", "cologne"])
        self.assertEqual(len(result["matrix"]), 9)
        self.assertEqual(len({(x["base_id"], x["destination_id"])
                              for x in result["matrix"]}), 9)
        self.assertGreaterEqual(result["coverage_time_count"], 2)
        self.assertEqual(result["operator_pages_sourced"], 4)
        self.assertFalse(result["private_wishlist_accessed"])
        self.assertFalse(result["trip_plan_modified"])
        self.assertFalse(result["ranking_available"])
        self.assertTrue(all(x["cost_for_two_2027"] is None for x in result["matrix"]))

    def test_route_page_cannot_assert_2027_or_time(self):
        data = json.loads(DATA.read_text(encoding="utf-8"))
        data["route_page_references"][0]["applicable_2027"] = True
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "bad.json"
            file.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_pilot(file)

    def test_evidence_and_absence_are_separate(self):
        result = pilot_matrix()
        rows = {(x["base_id"], x["destination_id"]): x
                for x in result["matrix"]}
        self.assertEqual(rows[("strasbourg", "baden_baden")]["status"], "historical_time")
        self.assertIsNone(rows[("mulhouse", "aachen")]["minimum_oneway_station_min"])
        self.assertIn(rows[("mulhouse", "cologne")]["status"],
                      ("operator_page_without_sourced_duration", "historical_time"))
        self.assertTrue(all(not x["return_weekend_2027_verified"]
                            for x in rows.values()))


if __name__ == "__main__":
    unittest.main()
