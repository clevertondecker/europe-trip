"""DATA17: itinerary candidates are independently discoverable; snapshots stay frozen."""
import unittest

from ux501_destination_discovery_model import build_destination_discovery, filter_destinations
from trip01_supplemental_discovery import append_trip01_candidates
from attractions_model import load_attractions, load_base_routes
from dq32_macro_opportunities_model import load_macro_tourism


class MissingGuideDestinationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = build_destination_discovery()
        cls.discovery = append_trip01_candidates(cls.base)

    def test_obernai_and_lucerne_searchable(self):
        for name, key in (("Obernai", "obernai"), ("Lucerna", "lucerne")):
            with self.subTest(name=name):
                matches = filter_destinations(self.discovery, query=name)
                self.assertEqual([row["id"] for row in matches], [key])
                self.assertEqual(matches[0]["attraction_count"], 3)
                photo = matches[0]["photo"]
                self.assertTrue(photo["url"].startswith(("https://upload.wikimedia.org/", "https://thumb.wikimedia.org/")))
                self.assertTrue(photo["source_page"].startswith("https://commons.wikimedia.org/wiki/File:"))
                self.assertTrue(photo["author"])
                self.assertIn("CC BY-SA", photo["license"])
                self.assertFalse(matches[0]["verified_weekend_return"])
                self.assertFalse(matches[0]["officially_selected"])

    def test_overlay_is_additive_and_does_not_mutate_input(self):
        self.assertEqual(self.discovery["destination_count"],
                         self.base["destination_count"] + 2)
        self.assertEqual(self.discovery["unique_attractions_count"],
                         self.base["unique_attractions_count"] + 6)
        self.assertEqual(len(self.base["destinations"]), 46)
        self.assertEqual(len({d["id"] for d in self.discovery["destinations"]}),
                         self.discovery["destination_count"])
        self.assertEqual(self.base, build_destination_discovery())
        for p in self.discovery["destinations"]:
            if p["id"] in ("obernai", "lucerne"):
                self.assertTrue(all(a["source_url"].startswith("https://")
                                    for a in p["attractions"]))

    def test_frozen_catalog_routes_and_macro_are_unchanged(self):
        self.assertEqual(len(load_attractions()["destinations"]), 14)
        self.assertEqual(len(load_attractions()["attractions"]), 65)
        self.assertEqual(len(load_macro_tourism()["attractions"]), 30)
        self.assertFalse(any(d in ("obernai", "lucerne")
                             for d in load_base_routes()["destinations"]))

    def test_no_fake_fares_or_verified_weekend_returns(self):
        for p in self.discovery["destinations"]:
            if p["id"] in ("obernai", "lucerne"):
                self.assertIsNone(p["feasible_from_base"])
                self.assertEqual(p["research_status"],
                                 "supplemental_attractions_documented")


if __name__ == "__main__":
    unittest.main()
