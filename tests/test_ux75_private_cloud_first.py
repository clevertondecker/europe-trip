"""UX75: the main Save action must target private storage only."""
import unittest
from unittest.mock import patch

from private_continuity_store import StorageConflict, StorageUnavailable


class PrimaryPrivateSaveTests(unittest.TestCase):
    @patch("continuity_ui._private_store", return_value=None)
    @patch("continuity_ui.st")
    def test_unconfigured_cloud_never_claims_saved_or_attempts_write(self, st, store):
        from continuity_ui import render_primary_private_save
        with patch("continuity_ui.save_private_now") as write:
            self.assertFalse(render_primary_private_save({}, {}))
        st.warning.assert_called_once()
        st.success.assert_not_called()
        write.assert_not_called()

    @patch("continuity_ui._private_store", return_value=object())
    @patch("continuity_ui._current_decisions_fingerprint", return_value="same")
    @patch("continuity_ui.st")
    def test_confirmed_identical_snapshot_disables_repeat_save(self, st, fp, store):
        from continuity_ui import render_primary_private_save
        st.session_state = {
            "ux36_cloud_status": "Salvo em espaço privado",
            "ux36_saved_decisions_fingerprint": "same",
            "ux36_cloud_generation": 7,
        }
        st.button.return_value = False
        with patch("continuity_ui.save_private_now") as write:
            self.assertTrue(render_primary_private_save({}, {}))
        st.button.assert_not_called()
        st.success.assert_called()
        write.assert_not_called()

    @patch("continuity_ui._private_store", return_value=object())
    @patch("continuity_ui._current_decisions_fingerprint", return_value="new")
    @patch("continuity_ui.st")
    def test_click_saves_private_once_without_github(self, st, fp, store):
        from continuity_ui import render_primary_private_save
        st.session_state = {"ux36_saved_decisions_fingerprint": "previous"}
        st.button.return_value = True
        with patch("continuity_ui.save_private_now") as save, patch(
                "travel_advisor_ui._secure_save") as public_write:
            self.assertTrue(render_primary_private_save({"plan_id": "test"}, {}))
        save.assert_called_once()
        public_write.assert_not_called()

    @patch("continuity_ui._private_store", return_value=object())
    @patch("continuity_ui._current_decisions_fingerprint", return_value="new")
    @patch("continuity_ui.st")
    def test_conflict_does_not_mark_saved(self, st, fp, store):
        from continuity_ui import render_primary_private_save
        st.session_state = {"ux36_saved_decisions_fingerprint": "previous"}
        st.button.return_value = True
        with patch("continuity_ui.save_private_now", side_effect=StorageConflict()):
            self.assertTrue(render_primary_private_save({}, {}))
        self.assertTrue(st.session_state["ux36_cloud_dirty"])
        self.assertTrue(st.session_state["ux36_cloud_status"].startswith("Conflito"))
        st.rerun.assert_called_once()

    @patch("continuity_ui._private_store", return_value=object())
    @patch("continuity_ui._current_decisions_fingerprint", return_value="new")
    @patch("continuity_ui.st")
    def test_unavailable_storage_does_not_mark_saved(self, st, fp, store):
        from continuity_ui import render_primary_private_save
        st.session_state = {}
        st.button.return_value = True
        with patch("continuity_ui.save_private_now", side_effect=StorageUnavailable()):
            self.assertTrue(render_primary_private_save({}, {}))
        self.assertTrue(st.session_state["ux36_cloud_status"].startswith("Erro"))
        st.success.assert_not_called()

    @patch("continuity_ui.st")
    def test_autosave_requires_opt_in(self, st):
        from continuity_ui import _ux75_private_autosave_changed
        st.session_state = {"ux75_private_autosave_toggle": False}
        _ux75_private_autosave_changed()
        self.assertFalse(st.session_state["ux36_private_autosave"])
        st.session_state["ux75_private_autosave_toggle"] = True
        _ux75_private_autosave_changed()
        self.assertTrue(st.session_state["ux36_private_autosave"])


class PublicAutosaveSafetyTests(unittest.TestCase):
    @patch("planning_session.bootstrap")
    @patch("planning_session.sync_legacy_view")
    @patch("planning_session.st")
    def test_local_change_never_queues_public_autosave(self, st, sync, bootstrap):
        from planning_session import _commit
        st.session_state = {
            "advisor_autosave_optin": True,
            "advisor_public_repo_ack": True,
            "advisor_autosave_pending": True,
        }
        from trip_plan_model import new_plan, with_revision
        previous = new_plan()
        bootstrap.return_value = previous
        next_plan = with_revision(previous, {"profile": "economy"})
        self.assertEqual(_commit(next_plan), next_plan)
        self.assertFalse(st.session_state["advisor_autosave_pending"])
        self.assertTrue(st.session_state["ux36_cloud_dirty"])


if __name__ == "__main__":
    unittest.main()
