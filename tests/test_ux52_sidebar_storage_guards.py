"""Regression tests: sidebar visibility never grants remote storage access."""
import unittest
from unittest.mock import patch

import travel_advisor_ui as advisor
import continuity_ui as continuity


class SidebarStorageAuthorizationTests(unittest.TestCase):
    def test_save_denied_without_verified_owner(self):
        cfg={"token":"fake-token","owner_email":"owner@example.com","google_configured":True}
        with patch.object(advisor,"_owner_config",return_value=cfg),\
             patch.object(advisor,"_owner_signed_in",return_value=False),\
             patch.object(advisor.st,"session_state",{}),\
             patch.object(advisor,"GitHubPlanRepository") as repository:
            with self.assertRaises(PermissionError):
                advisor._secure_save({"plan_id":"untouched"})
            repository.assert_not_called()

    def test_remote_restore_skipped_without_verified_owner(self):
        cfg={"token":"fake-token","owner_email":"owner@example.com","google_configured":True}
        with patch.object(advisor,"_owner_config",return_value=cfg),\
             patch.object(advisor,"_owner_signed_in",return_value=False),\
             patch.object(advisor.st,"session_state",{}),\
             patch.object(advisor,"GitHubPlanRepository") as repository:
            advisor._recover_saved_plan()
            repository.assert_not_called()

    def test_private_storage_denied_without_verified_owner(self):
        with patch("travel_advisor_ui._owner_signed_in",return_value=False),\
             patch.object(continuity,"PrivateArchiveStore") as private:
            self.assertIsNone(continuity._private_store())
            private.assert_not_called()


if __name__=="__main__":
    unittest.main()
