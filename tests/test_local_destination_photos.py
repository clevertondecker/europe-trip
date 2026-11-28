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
    display_photo_url,
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

    def test_bundled_photo_preferred_over_remote_editorial(self):
        city={"id":"aachen","photo":None}
        photo=local_destination_photo("aachen")
        external={"url":"https://upload.wikimedia.org/example.jpg"}
        self.assertEqual(preferred_destination_photo(city,external),photo)
        city["photo"]={"url":"https://commons.wikimedia.org/wiki/Special:FilePath/editorial.jpg"}
        self.assertEqual(preferred_destination_photo(city,external),photo)
        self.assertIsNone(local_destination_photo("unregistered_destination"))
        self.assertEqual(preferred_destination_photo(
            {"id":"unregistered_destination","photo":None},external),external)

    def test_wikimedia_api_is_authoritative_not_a_guessed_cdn_path(self):
        import io
        import json
        import destination_photo_assets as assets
        from commons_client import NEGATIVE_TTL
        url = "https://commons.wikimedia.org/wiki/Special:FilePath/Interlaken.jpg"
        thumbnail = "https://thumb.wikimedia.org/official/thumb.jpg"
        payload = {"query": {"pages": [{"title": "File:Interlaken.jpg", "imageinfo": [{
            "thumburl": thumbnail,
            "extmetadata": {
                "Artist": {"value": "Example author"},
                "LicenseShortName": {"value": "CC BY-SA 4.0"},
                "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
            },
        }]}]}}
        from collections import OrderedDict
        with patch.object(assets, "_resolution_cache", OrderedDict()), \
                patch.object(assets, "monotonic", return_value=100) as clock, \
                patch("urllib.request.urlopen", side_effect=[
                    TimeoutError("offline"), io.BytesIO(json.dumps(payload).encode())
                ]) as request:
            self.assertEqual(display_photo_url(url), url)
            self.assertEqual(request.call_count, 1)
            clock.return_value = 100 + NEGATIVE_TTL - 1
            self.assertEqual(display_photo_url(url), url)
            self.assertEqual(request.call_count, 1)
            clock.return_value = 100 + NEGATIVE_TTL
            self.assertEqual(display_photo_url(url), thumbnail)
            self.assertEqual(request.call_count, 2)
            clock.return_value += 86400
            self.assertEqual(display_photo_url(url), thumbnail)
            self.assertEqual(display_photo_url(thumbnail), thumbnail)
            self.assertEqual(request.call_count, 2)

    def test_external_failure_has_deterministic_fallback(self):
        from unittest.mock import MagicMock
        import ux501_destination_discovery_ui as ui
        fake=MagicMock()
        entry={"id":"metz","name":"Metz"}
        photo={"url":"https://commons.wikimedia.org/wiki/Special:FilePath/Centre_Pompidou_%C3%A0_Metz.jpg",
               "author":"LuxFoto09","license":"CC BY-SA 4.0",
               "source_page":"https://commons.wikimedia.org/wiki/File:Centre_Pompidou_à_Metz.jpg"}
        with patch.object(ui,"st",fake),patch.object(ui,"display_photo_url",return_value=photo["url"]):
            ui._render_destination_media(entry,photo)
        markup=fake.markdown.call_args_list[0].args[0]
        self.assertIn("Foto indisponível no momento",markup)
        self.assertIn("background-image:url(",markup)
        self.assertNotIn("<img ",markup)
        self.assertIn("role=\"img\"",markup)
        self.assertIn("LuxFoto09",fake.markdown.call_args_list[1].args[0])

    def test_ten_editorial_destinations_keep_attribution_and_fallback(self):
        from attractions_model import load_attractions
        from unittest.mock import MagicMock
        import ux501_destination_discovery_ui as ui
        editorial=[d for d in load_attractions()["destinations"] if d.get("photo")]
        self.assertEqual(len(editorial),10)
        for entry in editorial:
            with self.subTest(destination=entry["id"]):
                fake=MagicMock()
                with patch.object(ui,"st",fake),patch.object(ui,"display_photo_url",return_value=entry["photo"]["url"]):
                    ui._render_destination_media(entry,entry["photo"])
                # Rendering behavior, not mere syntactic URL validation.
                markup=fake.markdown.call_args_list[0].args[0]
                self.assertIn("background-image:url(",markup)
                self.assertNotIn("<img ",markup)
                self.assertIn("Foto indisponível no momento",markup)
                self.assertTrue(entry["photo"]["author"])
                self.assertTrue(entry["photo"]["license"])
                self.assertTrue(entry["photo"]["source_page"].startswith(
                    "https://commons.wikimedia.org/wiki/File:"))

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
            app.button(key="ux_sidebar_nav_"+str(("Minha viagem", "Explorar", "Meu roteiro", "Orçamento").index("Explorar"))).click().run()
            app.segmented_control(key="ux_section").set_value("Passeios").run()
        self.assertFalse(app.exception,[e.message for e in app.exception])
        self.assertFalse(FIVE.intersection(observed))
        self.assertEqual(app.session_state["advisor_plan"],initial)
        self.assertFalse(app.session_state.get("advisor_autosave_pending",False))


if __name__=="__main__":
    unittest.main()
