"""Regression tests: failed private saves must not appear acknowledged."""
import unittest
from unittest.mock import patch

import continuity_ui as ui
from private_continuity_store import StorageConflict, StorageUnavailable


class AutosaveRetryTests(unittest.TestCase):
    def setUp(self):
        self.state={"ux36_private_autosave":True,"ux36_cloud_dirty":True,
                    "advisor_plan":{"revision":7}}
        self.patches=[
            patch.object(ui.st,"session_state",self.state),
            patch.object(ui,"_private_archive",return_value={"schema_version":1}),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()

    def test_failed_remote_save_keeps_dirty_and_blocks_rerun_loop(self):
        with patch.object(ui,"save_private_now",side_effect=StorageUnavailable("network")) as save:
            ui.autosave_private_if_requested({})
            self.assertTrue(self.state["ux36_cloud_dirty"])
            self.assertIn("Erro",self.state["ux36_cloud_status"])
            ui.autosave_private_if_requested({})
            self.assertEqual(save.call_count,1)
            self.assertIsNotNone(self.state["ux36_autosave_failed_fingerprint"])

    def test_conflict_keeps_local_work(self):
        with patch.object(ui,"save_private_now",side_effect=StorageConflict("generation")):
            ui.autosave_private_if_requested({})
        self.assertTrue(self.state["ux36_cloud_dirty"])
        self.assertIn("Conflito",self.state["ux36_cloud_status"])

    def test_changed_snapshot_retries(self):
        with patch.object(ui,"save_private_now",side_effect=StorageUnavailable("network")) as save:
            ui.autosave_private_if_requested({})
            with patch.object(ui,"_private_archive",return_value={"schema_version":1,"revision":8}):
                ui.autosave_private_if_requested({})
            self.assertEqual(save.call_count,2)

    def test_successful_save_only_clears_after_remote_ack(self):
        def success(plan,catalog):
            self.assertTrue(self.state["ux36_cloud_dirty"])
            self.state["ux36_cloud_dirty"]=False
            self.state["ux36_cloud_status"]="Salvo em espaço privado"
        with patch.object(ui,"save_private_now",side_effect=success) as save:
            ui.autosave_private_if_requested({})
        self.assertEqual(save.call_count,1)
        self.assertFalse(self.state["ux36_cloud_dirty"])
        self.assertNotIn("ux36_autosave_failed_fingerprint",self.state)

    def test_disabled_autosave_does_not_consume_dirty(self):
        self.state["ux36_private_autosave"]=False
        with patch.object(ui,"save_private_now") as save:
            ui.autosave_private_if_requested({})
            save.assert_not_called()
        self.assertTrue(self.state["ux36_cloud_dirty"])


if __name__=="__main__":
    unittest.main()
