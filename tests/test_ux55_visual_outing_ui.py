"""UX 5.5 visual preview stays read-only and uses existing canonical identities."""
import unittest
from unittest.mock import MagicMock, patch

from attractions_model import load_attractions
from itinerary_flow_model import destinations, FRANCE_STAGE, ITALY_STAGE
from ux55_visual_outing_ui import destination_preview, render_destination_preview


class VisualOutingPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = load_attractions()
        cls.choices = destinations(cls.catalog)

    def test_france_uses_canonical_details_and_sources(self):
        dest = next(d for d in self.choices if d["id"] == "colmar")
        view = destination_preview(dest, self.catalog)
        self.assertEqual(dest["stage"], FRANCE_STAGE)
        self.assertEqual(view["name"], dest["name"])
        self.assertEqual(len(view["details"]), len(dest["attractions"]))
        by_id = {a["id"]: a for a in self.catalog["attractions"]}
        for item in view["details"]:
            original = by_id[item["id"]]
            self.assertEqual(item["summary"], original["summary"])
            self.assertEqual(item["source"], original["source_urls"][0])

    def test_italy_stays_in_its_own_stage_without_fake_photos_or_prices(self):
        dest = next(d for d in self.choices if d["id"] == "italy_amalfi")
        self.assertEqual(dest["stage"], ITALY_STAGE)
        view = destination_preview(dest, self.catalog)
        self.assertEqual(view["country"], "Itália")
        self.assertIsNone(view["photo"])
        self.assertEqual([a["id"] for a in view["details"]],
                         [a["id"] for a in dest["attractions"]])
        self.assertTrue(all(a["minutes"] is None for a in view["details"]))

    def test_render_never_commits_or_changes_plan(self):
        dest = next(d for d in self.choices if d["id"] == "colmar")
        fake = MagicMock()
        with patch("ux55_visual_outing_ui.st", fake), patch(
            "ux55_visual_outing_ui.photo_markup", return_value="<div>visual</div>"
        ), patch("ux55_visual_outing_ui.photo_credit", return_value=None):
            render_destination_preview(dest, self.catalog, [])
        self.assertTrue(fake.html.called)
        self.assertEqual(fake.expander.call_count, len(dest["attractions"]))
        self.assertFalse(fake.button.called)


if __name__ == "__main__":
    unittest.main()
