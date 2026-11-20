"""DATA17: candidates mentioned in the visual guide are discoverable without inventing fares."""
import unittest
from ux501_destination_discovery_model import build_destination_discovery, filter_destinations
from base_explorer_model import load_exploration
from dq32_macro_opportunities_model import load_macro_tourism
from rail_evidence_unified_model import canonical_place


class MissingGuideDestinationsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = build_destination_discovery()

    def test_obernai_and_lucerne_are_searchable(self):
        for query, city_id in [("Obernai", "obernai"), ("Lucerna", "lucerne")]:
            with self.subTest(query=query):
                hits = filter_destinations(self.catalog, query=query)
                self.assertEqual([p["id"] for p in hits], [city_id])
                self.assertGreaterEqual(hits[0]["attraction_count"], 3)
                self.assertFalse(hits[0]["verified_weekend_return"])
                self.assertFalse(hits[0]["officially_selected"])

    def test_sources_and_distinct_canonical_ids(self):
        discovery_ids = [d["id"] for d in self.catalog["destinations"]]
        self.assertEqual(len(discovery_ids), len(set(discovery_ids)))
        for item in self.catalog["destinations"]:
            if item["id"] in ("obernai", "lucerne"):
                self.assertEqual(len(item["attractions"]), 3)
                self.assertTrue(all(a["source_url"].startswith("https://") for a in item["attractions"]))
        self.assertEqual(canonical_place("luxembourg"), canonical_place("luxembourg_city"))

    def test_unknown_transport_not_created_as_verified_route(self):
        options = load_exploration()
        for item in options["routes"]:
            if item["destination_id"] in ("obernai", "lucerne"):
                self.assertFalse(item["return_verified_2027"])
        macro = load_macro_tourism()
        added = [x for x in macro["attractions"] if x["city_id"] in ("obernai", "lucerne")]
        self.assertEqual(len(added), 6)
        self.assertTrue(all(x["ticket_eur"] is None and x["availability_2027"] is None for x in added))


if __name__ == "__main__":
    unittest.main()
