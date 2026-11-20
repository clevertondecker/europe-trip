"""Ensure Metz displays a direct, licensed image instead of failed Commons redirects."""
import unittest
from unittest.mock import patch

from attractions_model import load_attractions
from destination_photo_assets import preferred_destination_photo, display_photo_url


class MetzPhotoRegressionTests(unittest.TestCase):
    def test_metz_photo_uses_direct_wikimedia_media_and_preserves_attribution(self):
        destination = next(x for x in load_attractions()["destinations"]
                           if x["id"] == "metz")
        original = dict(destination["photo"])
        photo = preferred_destination_photo(destination)
        self.assertEqual(
            photo["url"],
            "https://upload.wikimedia.org/wikipedia/commons/0/00/Centre_Pompidou_%C3%A0_Metz.jpg"
        )
        for key in ("author", "license", "license_url", "source_page"):
            self.assertEqual(photo[key], original[key])
        self.assertEqual(destination["photo"], original)
        with patch("urllib.request.urlopen", side_effect=AssertionError("Unexpected API request")):
            self.assertEqual(display_photo_url(photo["url"]), photo["url"])

    def test_other_editorial_destination_photos_are_not_rewritten(self):
        destination = next(x for x in load_attractions()["destinations"]
                           if x["id"] == "strasbourg")
        self.assertEqual(preferred_destination_photo(destination), destination["photo"])


if __name__ == "__main__":
    unittest.main()
