"""UX photo-catalog completion — offline coverage of every discovered city."""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from streamlit.testing.v1 import AppTest

from destination_photo_assets import ROOT, _manifest, local_destination_photo
from ux501_destination_discovery_model import build_destination_discovery

AUDIT = ROOT / "docs" / "UX_ALL_DESTINATION_PHOTOS_COVERAGE.json"


class FullDestinationImageCoverageTests(unittest.TestCase):
    def test_every_catalog_destination_has_an_actual_photo_source(self):
        catalog = build_destination_discovery()
        assets = _manifest()
        report = json.loads(AUDIT.read_text(encoding="utf-8"))
        self.assertEqual(len(catalog["destinations"]), 46)
        self.assertEqual(report["catalog_destinations"], 46)
        self.assertEqual(report["with_editorial_photo"], 10)
        self.assertEqual(report["with_local_photo"], 36)
        self.assertEqual(report["still_missing"], 0)
        self.assertEqual(len(assets), 36)
        self.assertEqual({d["id"] for d in report["destinations"]},
                         {d["id"] for d in catalog["destinations"]})

        for destination in catalog["destinations"]:
            with self.subTest(destination=destination["id"]):
                if destination.get("photo"):
                    self.assertNotIn(destination["id"], assets)
                    self.assertTrue(destination["photo"]["author"])
                    self.assertTrue(destination["photo"]["license"])
                    continue
                self.assertIn(destination["id"], assets)
                photo = local_destination_photo(destination["id"])
                self.assertIsNotNone(photo)
                self.assertTrue(Path(photo["local_path"]).is_file())
                self.assertTrue(photo["author"])
                self.assertTrue(photo["license"])
                self.assertTrue(photo["alt"])
                self.assertIn("commons.wikimedia.org/wiki/File:",photo["source_page"])
                self.assertTrue(photo["license_url"].startswith(
                    ("https://creativecommons.org/licenses/",
                     "https://creativecommons.org/publicdomain/")))
                with Image.open(photo["local_path"]) as image:
                    self.assertEqual(image.size,(800,450))
                    self.assertEqual(image.format,"WEBP")

    def test_selected_city_photos_are_photographs_not_cartographic_diagrams(self):
        assets=_manifest()
        self.assertEqual(assets["amsterdam"]["filename"],
                         "Amsterdam Canals - July 2006.jpg")
        self.assertEqual(assets["amsterdam"]["author"],"Diliff")
        self.assertEqual(assets["saint_louis"]["filename"],
                         "Ancienne Mairie Saint-Louis (Haut-Rhin).jpg")
        self.assertEqual(assets["saint_louis"]["author"],"Stecha")
        self.assertEqual(assets["belfort"]["license"],"Public domain")
        self.assertIsNotNone(local_destination_photo("belfort"))


class FullPhotoDiscoveryAppTests(unittest.TestCase):
    def test_all_four_catalog_pages_have_no_online_photo_requests(self):
        # The entire 46-destination catalog must render without Wikimedias API.
        with patch("ux501_destination_discovery_ui._cached_visible_photos",
                   side_effect=AssertionError("Runtime photo network request")):
            app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
            initial=deepcopy(app.session_state["advisor_plan"])
            app.radio(key="ux_area").set_value("Explorar").run()
            app.segmented_control(key="ux_section").set_value("Passeios").run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            for page in (2,3,4):
                app.selectbox(key="ux501_page").set_value(page).run()
                self.assertFalse(app.exception,[e.message for e in app.exception])
            self.assertEqual(app.session_state["advisor_plan"],initial)
            self.assertFalse(app.session_state.get("advisor_autosave_pending",False))


if __name__=="__main__":
    unittest.main()
