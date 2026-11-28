import copy
import json
import tempfile
import unittest
from pathlib import Path

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
