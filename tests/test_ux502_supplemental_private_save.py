"""UX502: supplemental destinations persist through the same versioned private archive."""
import unittest
from copy import deepcopy
from unittest.mock import Mock, patch

import continuity_ui
from attractions_model import load_attractions
from continuity_archive_model import make_archive, export_archive, import_archive
from trip_plan_model import new_plan
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import (
    empty_interests, set_interest, validate_interests, import_interests,
    export_interests,
)


class SupplementalWishlistPersistenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.discovery = build_exploration_discovery()

    @staticmethod
    def wishlist():
        data = empty_interests()
        for key in ("colmar", "obernai", "paris", "basel", "strasbourg"):
            data = set_interest(data, key, "interested")
        return data

    def test_export_import_and_full_archive_accept_obernai(self):
        wishes = self.wishlist()
        self.assertEqual(validate_interests(wishes), wishes)
        self.assertEqual(import_interests(export_interests(wishes)), wishes)
        catalog = load_attractions()
        archived = make_archive(new_plan(), catalog, destination_interests=wishes)
        restored = import_archive(export_archive(archived, catalog), catalog)
        self.assertEqual(restored["destination_interests"], wishes)
        self.assertEqual(
            [x["destination_id"] for x in restored["destination_interests"]["items"]],
            ["colmar", "obernai", "paris", "basel", "strasbourg"],
        )

    def test_private_save_round_trip_confirms_only_after_storage_success(self):
        wishes, plan, catalog = self.wishlist(), new_plan(), load_attractions()
        state = {
            "advisor_plan": deepcopy(plan),
            "ux502_interests": deepcopy(wishes),
            "ux36_cloud_generation": 4,
            "ux36_cloud_dirty": True,
        }
        storage = Mock()
        storage.save.return_value = 5
        with (patch.object(continuity_ui.st, "session_state", state),
              patch.object(continuity_ui, "_private_store", return_value=storage)):
            continuity_ui.save_private_now(plan, catalog)
        body, expected = storage.save.call_args.args
        self.assertEqual(expected, 4)
        self.assertEqual(import_archive(body, catalog)["destination_interests"], wishes)
        self.assertEqual(state["ux36_cloud_generation"], 5)
        self.assertEqual(state["ux502_private_saved_revision"], wishes["revision"])
        self.assertFalse(state["ux36_cloud_dirty"])

    def test_old_catalog_injection_does_not_silently_drop_obernai(self):
        from ux501_destination_discovery_model import build_destination_discovery
        with self.assertRaises(ValueError):
            validate_interests(self.wishlist(), build_destination_discovery())


if __name__ == "__main__":
    unittest.main()
