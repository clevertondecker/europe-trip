"""Destination card photographs: identity, Commons license and UX fallbacks."""
from copy import deepcopy
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ux501_destination_photo_service import (
    ARTICLE_TITLES, COMMONS_API, WIKIPEDIA_API, _image_metadata,
    lookup_destination_photos,
)
from ux501_destination_discovery_model import build_destination_discovery

ROOT = Path(__file__).resolve().parents[1]


def _image_info(name, *, license="CC BY-SA 4.0", author="<a>Jane Photographer</a>"):
    return {
        "title": "File:" + name,
        "imageinfo": [{
            "thumburl": "https://upload.wikimedia.org/wikipedia/commons/thumb/"
                        "a/ab/" + name + "/720px-" + name,
            "extmetadata": {
                "LicenseShortName": {"value": license},
                "Artist": {"value": author},
                "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
            },
        }],
    }


class DestinationPhotosTests(TestCase):
    def test_visible_cities_receive_distinct_photos_and_attribution(self):
        requested = [
            {"id":"aachen","name":"Aachen","photo":None},
            {"id":"baden_baden","name":"Baden-Baden","photo":None},
            {"id":"cologne","name":"Colônia","photo":None},
            {"id":"karlsruhe","name":"Karlsruhe","photo":None},
            {"id":"kehl","name":"Kehl","photo":None},
            {"id":"freiburg","name":"Freiburg im Breisgau",
             "photo":{"url":"https://commons.wikimedia.org/wiki/Special:FilePath/existing.jpg"}},
        ]
        calls=[]
        def fake(api, params):
            calls.append((api, params))
            if api == WIKIPEDIA_API:
                return {"query":{"pages":[
                    {"title":title, "pageimage":title.replace(" ","_") + ".jpg"}
                    for title in ("Aachen","Baden-Baden","Cologne","Karlsruhe","Kehl")
                ]}}
            if api == COMMONS_API:
                return {"query":{"pages":[
                    _image_info(title.replace(" ","_") + ".jpg")
                    for title in ("Aachen","Baden-Baden","Cologne","Karlsruhe","Kehl")
                ]}}
            raise AssertionError(api)
        before=deepcopy(requested)
        photos=lookup_destination_photos(requested,fetch_json=fake)
        self.assertEqual(set(photos),
                         {"aachen","baden_baden","cologne","karlsruhe","kehl"})
        self.assertEqual(len({v["url"] for v in photos.values()}),5)
        self.assertTrue(all(v["license"]=="CC BY-SA 4.0" for v in photos.values()))
        self.assertTrue(all(v["author"]=="Jane Photographer" for v in photos.values()))
        self.assertTrue(all(v["source_page"].startswith(
            "https://commons.wikimedia.org/wiki/File:") for v in photos.values()))
        self.assertEqual(requested,before)
        self.assertEqual(len(calls),2)
        self.assertIn("Cologne",calls[0][1]["titles"])
        self.assertNotIn("Freiburg im Breisgau",calls[0][1]["titles"])

    def test_no_unlicensed_or_unattributed_images(self):
        for lic,author in (("All rights reserved","John"),
                           ("CC BY-SA 4.0",""),("Unknown","John")):
            with self.subTest(license=lic,author=author):
                self.assertIsNone(_image_metadata(_image_info(
                    "Aachen.jpg",license=lic,author=author)))

    def test_no_unverified_fallback_in_failure_or_missing_picture(self):
        destination=[{"id":"kehl","name":"Kehl","photo":None}]
        def broken(api,params):
            raise OSError("API not available")
        self.assertEqual(lookup_destination_photos(destination,broken),{})
        self.assertEqual(lookup_destination_photos(
            destination,lambda api,params:{"query":{"pages":[]}}),{})

    def test_article_title_not_naively_translated_and_catalog_unchanged(self):
        catalog=build_destination_discovery()
        before=deepcopy(catalog)
        self.assertEqual(ARTICLE_TITLES["baden_baden"],"Baden-Baden")
        self.assertEqual(ARTICLE_TITLES["brussels"],"Brussels")
        self.assertEqual(catalog,before)
        self.assertGreaterEqual(len(catalog["destinations"]),30)


class DestinationPhotoAppTests(TestCase):
    def test_cards_render_uniform_images_provenance_and_unavailable_state(self):
        photo = {
            "url":"https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Aachen.jpg/720px-Aachen.jpg",
            "author":"Jane Photographer", "license":"CC BY-SA 4.0",
            "source_page":"https://commons.wikimedia.org/wiki/File:Aachen.jpg",
        }
        # UI is exercised with stable external I/O mocks, so tests never
        # depend on availability of Wikimedia or live article thumbnails.
        with patch("ux501_destination_discovery_ui._cached_visible_photos",
                   return_value={"aachen":photo}):
            app=AppTest.from_file(str(ROOT/"app.py"),default_timeout=120).run()
            initial=deepcopy(app.session_state["advisor_plan"])
            app.radio(key="ux_area").set_value("Explorar").run()
            app.segmented_control(key="ux_section").set_value("Passeios").run()
            self.assertFalse(app.exception,[x.message for x in app.exception])
            markup=" ".join(x.value for x in app.markdown)
            self.assertIn('alt="Fotografia de Aachen"',markup)
            self.assertIn("Jane Photographer",markup)
            self.assertIn("Foto a pesquisar",markup)
            self.assertIn("aspect-ratio:16/9",markup)
            self.assertEqual(app.session_state["advisor_plan"],initial)
            self.assertFalse(app.session_state.get("advisor_autosave_pending",False))
