"""Bundled destination photos must be real, licensed and offline at runtime."""
from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch

from PIL import Image
from streamlit.testing.v1 import AppTest

from destination_photo_assets import (
    ROOT, _manifest, local_destination_photo, preferred_destination_photo,
)
from ux501_destination_discovery_model import build_destination_discovery

FIVE={"aachen","baden_baden","cologne","karlsruhe","kehl"}


class LocalDestinationPhotosTests(unittest.TestCase):
    def test_real_binary_assets_are_complete_and_independent(self):
        records=_manifest()
        self.assertTrue(FIVE.issubset(set(records)))
        self.assertEqual(len(records),36)
        hashes=[]
        for destination_id,record in records.items():
            with self.subTest(city=destination_id):
                photo=local_destination_photo(destination_id)
                self.assertIsNotNone(photo)
                path=Path(photo["local_path"])
                self.assertTrue(path.is_file())
                self.assertGreater(path.stat().st_size,5000)
                self.assertLess(path.stat().st_size,250001)
                with Image.open(path) as img:
                    self.assertEqual(img.format,"WEBP")
                    self.assertEqual(img.size,(800,450))
                    img.verify()
                hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
                self.assertEqual(photo["author"],record["author"])
                self.assertEqual(photo["license"],record["license"])
                self.assertTrue(photo["source_page"].startswith(
                    "https://commons.wikimedia.org/wiki/File:"))
                self.assertTrue(photo["license_url"].startswith((
                    "https://creativecommons.org/licenses/",
                    "https://creativecommons.org/publicdomain/")),
                    f"{destination_id}: missing recognized license URL")
                self.assertTrue(photo["edited"])
        self.assertEqual(len(set(hashes)),len(records),
                         "Different cities must not share a photo")

    def test_editorial_photo_then_local_then_dynamic_fallback(self):
        city={"id":"aachen","photo":None}
        photo=local_destination_photo("aachen")
        external={"url":"https://upload.wikimedia.org/example.jpg"}
        self.assertEqual(preferred_destination_photo(city,external),photo)
        city["photo"]={"url":"https://commons.wikimedia.org/wiki/Special:FilePath/editorial.jpg"}
        self.assertEqual(preferred_destination_photo(city,external),city["photo"])
        self.assertIsNone(local_destination_photo("unregistered_destination"))
        self.assertEqual(preferred_destination_photo(
            {"id":"unregistered_destination","photo":None},external),external)

    def test_catalog_and_plan_not_modified(self):
        catalog=build_destination_discovery()
        initial=deepcopy(catalog)
        for city in FIVE:
            local_destination_photo(city)
        self.assertEqual(catalog,initial)


class LocalDestinationPhotosAppTests(unittest.TestCase):
    def test_first_discovery_page_uses_local_assets_without_querying_them(self):
        import ux501_destination_discovery_ui as ui
        observed=[]
        original=ui._cached_visible_photos
        def fake_dynamic(identity):
            observed.extend(i for i,_ in identity)
            return {}
        with patch.object(ui,"_cached_visible_photos",side_effect=fake_dynamic):
            app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
            initial=deepcopy(app.session_state["advisor_plan"])
            app.radio(key="ux_area").set_value("Explorar").run()
            app.segmented_control(key="ux_section").set_value("Passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertFalse(FIVE.intersection(observed))
        self.assertEqual(app.session_state["advisor_plan"],initial)
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))


if __name__=="__main__":
    unittest.main()
