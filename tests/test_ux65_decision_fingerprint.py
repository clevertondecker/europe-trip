"""Regression: cloud save status ignores navigation and restore shows wishlist differences."""
import unittest
from copy import deepcopy

from attractions_model import load_attractions
from trip_plan_model import new_plan
from continuity_archive_model import (
    make_archive, preview_restore, confirm_restore, persisted_data_fingerprint,
)
from ux502_destination_interests_model import empty_interests


class ContinuityDecisionTests(unittest.TestCase):
    def setUp(self):
        self.plan = new_plan()
        self.catalog = load_attractions()
        self.wishes = empty_interests()
        self.wishes["items"].append(
            {"destination_id": "obernai", "priority": "interested"})

    def test_navigation_does_not_mark_decisions_dirty(self):
        old = make_archive(self.plan, self.catalog,
                           context={"area": "Meu roteiro", "section": "Meu planejamento"},
                           destination_interests=self.wishes)
        other = make_archive(self.plan, self.catalog,
                             context={"area": "Explorar", "section": "Passeios",
                                      "search": "Obernai"},
                             destination_interests=self.wishes)
        self.assertEqual(persisted_data_fingerprint(old),
                         persisted_data_fingerprint(other))

    def test_restore_preview_lists_wishlist_change(self):
        current = make_archive(self.plan, self.catalog,
                               destination_interests=self.wishes)
        changed = deepcopy(self.wishes)
        changed["items"][0]["priority"] = "must_visit"
        incoming = make_archive(self.plan, self.catalog,
                                destination_interests=changed)
        preview = preview_restore(self.plan, incoming, self.catalog,
                                  current_archive=current)
        self.assertEqual(preview["wishlist_changes"]["priority_changed"], 1)
        self.assertIn("destination_interests", preview["auxiliary_changed_fields"])
        self.assertEqual(preview["relation"], "same_plan_same_revision_conflict")

    def test_changed_wishlist_after_preview_blocks_restore(self):
        current = make_archive(self.plan, self.catalog,
                               destination_interests=self.wishes)
        incoming = make_archive(self.plan, self.catalog)
        preview = preview_restore(self.plan, incoming, self.catalog,
                                  current_archive=current)
        changed = deepcopy(current)
        changed["destination_interests"]["items"][0]["priority"] = "maybe"
        with self.assertRaisesRegex(ValueError, "Destinos ou outros dados"):
            confirm_restore(self.plan, incoming, preview, self.catalog,
                            confirmed=True, current_archive=changed)


if __name__ == "__main__":
    unittest.main()
