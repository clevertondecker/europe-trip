"""Cloud-first save: identical GitHub plans sync session references without PUT."""
import copy
import unittest
from unittest.mock import patch

from trip_plan_model import new_plan
from plan_reconciliation import same_persisted_plan
from trip_plan_repository import PlanConflictError


class IdenticalPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = new_plan()

    def test_identical_including_revision(self):
        self.assertTrue(same_persisted_plan(self.plan, copy.deepcopy(self.plan)))

    def test_revision_only_difference_is_not_noop(self):
        remote = copy.deepcopy(self.plan)
        remote["revision"] += 1
        self.assertFalse(same_persisted_plan(self.plan, remote))

    def test_plan_data_difference_is_not_noop(self):
        remote = copy.deepcopy(self.plan)
        remote["preferences"]["colmar_venise"] = "Quero visitar"
        self.assertFalse(same_persisted_plan(self.plan, remote))


class CloudNoWriteTests(unittest.TestCase):
    def setUp(self):
        self.local = new_plan()

    @patch("travel_advisor_ui._owner_config", return_value={"token": "fake"})
    @patch("travel_advisor_ui._owner_signed_in", return_value=True)
    @patch("travel_advisor_ui.GitHubPlanRepository")
    def test_verified_identical_plan_only_updates_session_metadata(self, repo_cls, owner, config):
        import streamlit as st
        from plan_reconciliation import plan_digest
        from travel_advisor_ui import sync_identical_remote_plan
        remote = copy.deepcopy(self.local)
        repo_cls.return_value.load.return_value = (remote, "sha-1")
        session = {}
        with patch.object(st, "session_state", session):
            sync_identical_remote_plan(self.local, "sha-1", plan_digest(self.local))
        repo_cls.return_value.save.assert_not_called()
        self.assertEqual(session["advisor_github_sha"], "sha-1")
        self.assertEqual(session["advisor_saved_snapshot"], self.local)

    @patch("travel_advisor_ui._owner_config", return_value={"token": "fake"})
    @patch("travel_advisor_ui._owner_signed_in", return_value=True)
    @patch("travel_advisor_ui.GitHubPlanRepository")
    def test_remote_sha_changed_fails_closed(self, repo_cls, owner, config):
        import streamlit as st
        from plan_reconciliation import plan_digest
        from travel_advisor_ui import sync_identical_remote_plan
        repo_cls.return_value.load.return_value = (copy.deepcopy(self.local), "sha-2")
        session = {}
        with patch.object(st, "session_state", session):
            with self.assertRaises(PlanConflictError):
                sync_identical_remote_plan(self.local, "sha-1", plan_digest(self.local))
        self.assertNotIn("advisor_github_sha", session)
        repo_cls.return_value.save.assert_not_called()

    @patch("travel_advisor_ui._owner_config", return_value={"token": "fake"})
    @patch("travel_advisor_ui._owner_signed_in", return_value=True)
    @patch("travel_advisor_ui.GitHubPlanRepository")
    def test_local_changed_after_preview_fails_without_read(self, repo_cls, owner, config):
        from plan_reconciliation import plan_digest
        from travel_advisor_ui import sync_identical_remote_plan
        digest = plan_digest(self.local)
        self.local["preferences"] = {"colmar_venise": "Quero visitar"}
        with self.assertRaises(PlanConflictError):
            sync_identical_remote_plan(self.local, "sha-1", digest)
        repo_cls.return_value.load.assert_not_called()

    @patch("travel_advisor_ui._owner_config", return_value={"token": "fake"})
    @patch("travel_advisor_ui._owner_signed_in", return_value=False)
    @patch("travel_advisor_ui.GitHubPlanRepository")
    def test_owner_required_even_for_metadata_sync(self, repo_cls, owner, config):
        from plan_reconciliation import plan_digest
        from travel_advisor_ui import sync_identical_remote_plan
        with self.assertRaises(PermissionError):
            sync_identical_remote_plan(self.local, "sha-1", plan_digest(self.local))
        repo_cls.assert_not_called()


if __name__ == "__main__":
    unittest.main()
