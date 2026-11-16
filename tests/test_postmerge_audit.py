"""Post-merge smoke regressions for PRs 48-50. No real GCS writes."""
import unittest
from copy import deepcopy
from unittest.mock import Mock,patch

from private_continuity_store import StorageConflict,StorageUnavailable
from private_city_studies import empty_collection,add_study,cloud_commit
from continuity_ui import autosave_private_if_requested
import continuity_ui as ui
from base_change_model import known_route
from trip_plan_model import new_plan


class PostMergeAuditTests(unittest.TestCase):
    def test_gcs_autosave_failure_does_not_clear_dirty(self):
        state={"advisor_plan":new_plan(),"ux36_private_autosave":True,
               "ux36_cloud_dirty":True}
        with patch.object(ui.st,"session_state",state),patch.object(
                ui,"_private_archive",return_value={"kind":"test"}),patch.object(
                ui,"save_private_now",side_effect=StorageUnavailable("network")) as save:
            autosave_private_if_requested({})
            autosave_private_if_requested({})
            self.assertTrue(state["ux36_cloud_dirty"])
            self.assertEqual(save.call_count,1)

    def test_studies_conflict_preserves_original(self):
        original=empty_collection()
        store=Mock()
        store.save.side_effect=StorageConflict("changed")
        with self.assertRaises(StorageConflict):
            cloud_commit(store,original,5)
        self.assertEqual(original,empty_collection())

    def test_rail_additions_cannot_produce_fares(self):
        for base,dest in (("nancy","luxembourg"),("nancy","brussels"),
                          ("metz","brussels"),("lille","luxembourg")):
            route=known_route(base,dest)
            self.assertIsInstance(route["minutes"],int)
            self.assertIsNone(route["fare"])
            self.assertFalse(route["return_verified"])

    def test_trip_plan_never_mutated_by_research(self):
        plan=new_plan()
        before=deepcopy(plan)
        for base,dest in (("nancy","brussels"),("lille","luxembourg")):
            known_route(base,dest)
        self.assertEqual(plan,before)


if __name__=="__main__":
    unittest.main()
