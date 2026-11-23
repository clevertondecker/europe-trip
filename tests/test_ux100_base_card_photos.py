"""UX100: photo provenance and fallback; never guess city images."""
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from ux100_base_card_photos import base_card_photo_record


class VerifiedBasePhotosTests(unittest.TestCase):
    def test_local_provenance_for_bundled_city(self):
        result=base_card_photo_record("lille")
        self.assertIsNotNone(result)
        self.assertTrue(result.get("local_path"))
        self.assertIn("commons.wikimedia.org",result["source_page"])
        self.assertTrue(result["author"])
        self.assertTrue(result["license"])

    def test_catalog_photo_fallback_is_city_specific_and_licensed(self):
        for city in ("mulhouse", "strasbourg", "metz", "nancy", "colmar"):
            with self.subTest(city=city):
                record=base_card_photo_record(city)
                self.assertIsNotNone(record)
                self.assertTrue(record["source_page"].startswith(
                    "https://commons.wikimedia.org/wiki/File:"))
                self.assertTrue(record["license_url"].startswith(
                    "https://creativecommons.org/licenses/"))
                self.assertTrue(record["author"])

    def test_local_image_passes_verified_alt_to_native_image(self):
        from ux100_base_card_photos import render_base_card_photo
        photo={"local_path":"test.webp", "alt":"Centro histórico de Lille",
               "source_page":"https://commons.wikimedia.org/wiki/File:Lille.jpg",
               "author":"Autor", "license":"CC BY-SA 4.0",
               "license_url":"https://creativecommons.org/licenses/by-sa/4.0/"}
        with patch("ux100_base_card_photos.base_card_photo_record",return_value=photo):
            with patch("ux100_base_card_photos.st.container"):
                with patch("ux100_base_card_photos.st.image") as image:
                    with patch("ux100_base_card_photos.st.markdown"):
                        render_base_card_photo("lille","Lille")
        image.assert_called_once_with("test.webp",width="stretch",
                                     alt="Centro histórico de Lille")

    def test_unknown_city_does_not_fetch_unrelated_photo(self):
        self.assertIsNone(base_card_photo_record("ux100_nonexistent_city"))

    def test_fallback_does_not_raise_or_change_state(self):
        code = """
from ux100_base_card_photos import render_base_card_photo
render_base_card_photo("ux100_nonexistent_city", "<Example>")
"""
        app=AppTest.from_string(code,default_timeout=30).run()
        self.assertFalse(app.exception,[x.message for x in app.exception])
        self.assertTrue(any("Foto de &lt;Example&gt;" in x.value
                            for x in app.markdown))

    def test_local_selection_precedes_curated_external(self):
        with patch("ux100_base_card_photos.local_destination_photo",
                   return_value={"local_path":"a.webp"}) as local:
            with patch("ux100_base_card_photos.curated_destination_photo") as curated:
                self.assertEqual(base_card_photo_record("lille"),{"local_path":"a.webp"})
                curated.assert_not_called()
                local.assert_called_once_with("lille")

if __name__=="__main__":
    unittest.main()
