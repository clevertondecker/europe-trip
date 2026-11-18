"""UX 5.2: sidebar account discoverability and fail-closed OIDC status."""
import unittest
from pathlib import Path
from time import time
from streamlit.testing.v1 import AppTest

from sidebar_account_ui import account_view_state

ROOT = Path(__file__).resolve().parents[1]


class SidebarGoogleAccountStateTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "google_configured": True, "owner_email": "owner@example.com",
            "token": "not-used-by-sidebar",
        }
        self.user = {
            "is_logged_in": True,
            "iss": "https://accounts.google.com",
            "email": "owner@example.com",
            "email_verified": True,
            "exp": int(time()) + 3600,
        }

    def test_states_fail_closed(self):
        self.assertEqual(account_view_state(
            {"google_configured": False, "owner_email": "owner@example.com"},
            self.user), "unconfigured")
        self.assertEqual(account_view_state(
            {"google_configured": True, "owner_email": ""},
            self.user), "unconfigured")
        self.assertEqual(account_view_state(self.config, {}),
                         "signed_out")
        self.assertEqual(account_view_state(self.config, None),
                         "signed_out")
        self.assertEqual(account_view_state(self.config, self.user),
                         "owner")
        self.assertEqual(account_view_state(
            self.config, {**self.user, "email": "someoneelse@example.com"}),
            "other_account")
        self.assertEqual(account_view_state(
            self.config, {**self.user, "exp": 1}), "other_account")
        self.assertEqual(account_view_state(
            self.config, {**self.user, "iss": "https://example.com"}),
            "other_account")

    def test_sidebar_renders_without_provider_secrets_and_navigation_stays_working(self):
        app = AppTest.from_file(str(ROOT / "app.py"),
                                default_timeout=120).run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertTrue(any("Conta Google" in x.value
                            for x in app.markdown))
        self.assertTrue(any("Login Google ainda não configurado" in x.value
                            for x in app.caption))
        self.assertEqual(len(app.button(key="ux52_google_login")), 0)
        self.assertEqual(len(app.button(key="ux52_google_logout")), 0)
        self.assertEqual(len(app.button(key="ux52_google_logout_other")), 0)
        plan = app.session_state["advisor_plan"].copy()
        app.button(key="ux_sidebar_nav_1").click().run()
        self.assertFalse(app.exception, [x.message for x in app.exception])
        self.assertEqual(app.session_state["ux_area"], "Explorar")
        self.assertEqual(app.session_state["advisor_plan"], plan)


if __name__ == "__main__":
    unittest.main()
