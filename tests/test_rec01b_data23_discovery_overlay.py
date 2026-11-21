"""DATA23 discovery integration; canonical sources remain unchanged."""
from copy import deepcopy
import unittest

from data23_discovery_overlay_model import append_data23_destinations
from data23_france_candidates_model import load_data23
from trip01_supplemental_discovery import append_trip01_candidates, build_exploration_discovery
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import empty_interests, set_interest, export_interests, import_interests
from ux503_destination_base_comparison_model import compare_wishlist_bases
from rail_reference_projection_model import decorate_comparison


class Data23DiscoveryOverlayTests(unittest.TestCase):
    def test_curated_catalog_is_additive_and_reversible(self):
        legacy = append_trip01_candidates(build_destination_discovery())
        original = deepcopy(legacy)
        public = build_exploration_discovery()
        by_id = {d["id"]: d for d in public["destinations"]}
        added = set(by_id) - {d["id"] for d in legacy["destinations"]}
        self.assertEqual(added, {"angers", "le_mans", "annecy", "rennes",
                                 "saumur", "saint_malo", "dinan"})
        self.assertEqual(legacy, original)
        self.assertEqual(append_data23_destinations(public), public)
        for destination in original["destinations"]:
            self.assertEqual(by_id[destination["id"]], destination)
        self.assertEqual(public["destination_count"], len(by_id))
        self.assertEqual(public["unique_attractions_count"],
                         sum(d["attraction_count"] for d in by_id.values()))
        sources = {a["id"]: a["source_url"] for a in load_data23()["attractions"]}
        for key in added:
            item = by_id[key]
            self.assertFalse(item["officially_selected"])
            self.assertFalse(item["verified_weekend_return"])
            self.assertIsNone(item["feasible_from_base"])
            self.assertTrue(item["attractions"])
            self.assertEqual(item["planning_support"], "exploration_only")
            self.assertIn(item["photo"]["subject"], [a["name"] for a in item["attractions"]])
            self.assertTrue(item["photo"]["author"])
            self.assertTrue(item["photo"]["license"])
            self.assertTrue(item["photo"]["source_page"].startswith("https://commons.wikimedia.org/"))
            for attr in item["attractions"]:
                self.assertEqual(attr["source_url"], sources[attr["id"]])
        self.assertFalse({"nantes", "tours", "chartres", "aix_les_bains",
                          "geneva", "chamonix"} & set(by_id))

    def test_unsupported_planning_is_visible_in_projection_without_plan_mutation(self):
        from ux61_destination_board_model import build_destination_board, organizer_wishlist_candidates
        from attractions_model import load_attractions
        from itinerary_flow_model import FRANCE_STAGE
        from trip_plan_model import new_plan
        discovery = build_exploration_discovery()
        catalog = load_attractions()
        plan = new_plan()
        wishes = set_interest(empty_interests(), "saumur", "must_visit", discovery)
        before = deepcopy((plan, wishes))
        board = build_destination_board(wishes, plan, discovery, catalog)
        row = next(r for r in board if r["id"] == "saumur")
        self.assertTrue(row["wanted"])
        self.assertFalse(row["planned"])
        self.assertEqual(row["planning_support"], "exploration_only")
        options = organizer_wishlist_candidates(wishes, plan, discovery, catalog, FRANCE_STAGE)
        self.assertIn("saumur", {r["id"] for r in options["unsupported"]})
        self.assertNotIn("saumur", {r["id"] for r in options["eligible"]})
        self.assertEqual((plan, wishes), before)

    def test_wishlist_roundtrip_and_directional_reference(self):
        catalog = build_exploration_discovery()
        original = empty_interests()
        saved = set_interest(original, "saumur", "must_visit", catalog)
        restored = import_interests(export_interests(saved, catalog), catalog)
        self.assertEqual(restored, saved)
        self.assertEqual(original["items"], [])
        revised = set_interest(saved, "paris", "interested", catalog)
        self.assertEqual(import_interests(export_interests(revised, catalog), catalog), revised)
        self.assertEqual(import_interests(export_interests(original, catalog), catalog), original)
        view = compare_wishlist_bases(restored, ["angers", "rennes"], discovery=catalog)
        enriched = decorate_comparison(view)
        cell = enriched["cells"][("angers", "saumur")]
        self.assertEqual(cell["category"], "reference_only")
        self.assertTrue(cell["candidate_connectivity_applied"])
        self.assertFalse(cell["weekend_return_known"])
        self.assertFalse(view["official_plan_modified"])


if __name__ == "__main__":
    unittest.main()
