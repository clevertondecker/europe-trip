"""Metz photo is a real Wikimedia asset with matching author and license."""
import unittest
from unittest.mock import patch
from attractions_model import load_attractions
from destination_photo_assets import preferred_destination_photo, display_photo_url

class MetzPhotoRegressionTests(unittest.TestCase):
    def test_metz_uses_verified_asset_with_matching_credit(self):
        destination = next(d for d in load_attractions()["destinations"] if d["id"] == "metz")
        original = dict(destination["photo"])
        photo = preferred_destination_photo(destination)
        self.assertEqual(photo["url"], "https://upload.wikimedia.org/wikipedia/commons/3/36/Metz_centre_ville_crop.jpg")
        self.assertEqual(photo["author"], "Philippe Gisselbrecht / Ville de Metz")
        self.assertEqual(photo["license"], "CC BY-SA 4.0")
        self.assertEqual(photo["license_url"], "https://creativecommons.org/licenses/by-sa/4.0/")
        self.assertEqual(photo["source_page"], "https://commons.wikimedia.org/wiki/File:Metz_centre_ville_crop.jpg")
        self.assertEqual(destination["photo"], original)
        with patch("urllib.request.urlopen", side_effect=AssertionError("Unexpected API request")):
            self.assertEqual(display_photo_url(photo["url"]), photo["url"])

    def test_other_destination_photos_unchanged(self):
        d = next(d for d in load_attractions()["destinations"] if d["id"] == "strasbourg")
        self.assertEqual(preferred_destination_photo(d), d["photo"])

if __name__ == "__main__":
    unittest.main()
