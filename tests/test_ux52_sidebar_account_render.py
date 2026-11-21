"""Render-integration tests for the existing Streamlit/OIDC sidebar controls."""
import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import sidebar_account_ui as ui


class SidebarAccountRenderIntegration(unittest.TestCase):
    def setUp(self):
        self.config={"google_configured":True,"owner_email":"owner@example.com"}
        self.owner={"is_logged_in":True,"iss":"https://accounts.google.com",
                    "email":"owner@example.com","email_verified":True,
                    "exp":int(datetime.now(timezone.utc).timestamp())+3600}
        self.session={"advisor_plan":{"plan_id":"unchanged"},
                      "ux502_interests":["metz"],"main_navigation":"Roteiro",
                      "budget_scenario":"70k","advisor_saved_snapshot":None}

    def _render(self,user,config=None):
        messages=[]
        buttons=[]
        def button(label,**props):
            buttons.append((label,props))
            return False
        with patch.object(ui,"_owner_config",return_value=self.config if config is None else config),\
             patch.object(ui,"_logged_in_user",return_value=user),\
             patch.object(ui.st,"button",side_effect=button),\
             patch.object(ui.st,"caption",side_effect=lambda x:messages.append(str(x))),\
             patch.object(ui.st,"markdown",side_effect=lambda x:messages.append(str(x))),\
             patch.object(ui.st,"warning",side_effect=lambda x:messages.append(str(x))),\
             patch.object(ui.st,"login") as login,\
             patch.object(ui.st,"logout") as logout,\
             patch.object(ui.st,"session_state",dict(self.session)):
            with patch.object(ui,"_saving_status",return_value="Ainda não salvo"):
                ui.render_sidebar_account()
            login.assert_not_called()
            logout.assert_not_called()
            self.assertEqual(ui.st.session_state,self.session)
            mapped={p["key"]:p for _,p in buttons}
            if "ux52_google_login" in mapped:
                self.assertIs(mapped["ux52_google_login"]["on_click"],login)
                mapped["ux52_google_login"]["on_click"](*mapped["ux52_google_login"]["args"])
                login.assert_called_once_with("google")
                logout.assert_not_called()
            elif "ux52_google_logout" in mapped or "ux52_google_logout_other" in mapped:
                key="ux52_google_logout" if "ux52_google_logout" in mapped else "ux52_google_logout_other"
                self.assertIs(mapped[key]["on_click"],logout)
                mapped[key]["on_click"]()
                logout.assert_called_once_with()
                login.assert_not_called()
            return set(mapped),messages

    def test_unconfigured(self):
        keys,_=self._render(None,{"google_configured":False,"owner_email":"owner@example.com"})
        self.assertFalse(keys)
    def test_signed_out(self):
        keys,_=self._render(None)
        self.assertEqual(keys,{"ux52_google_login"})
    def test_owner(self):
        keys,messages=self._render(self.owner)
        self.assertEqual(keys,{"ux52_google_logout"})
        self.assertTrue(any("Ainda não salvo" in x for x in messages))
        self.assertFalse(any("Salvo no Drive" in x for x in messages))
    def test_other_account(self):
        keys,messages=self._render({**self.owner,"email":"other@example.com"})
        self.assertEqual(keys,{"ux52_google_logout_other"})
        self.assertTrue(any("não autorizada" in x for x in messages))
    def test_expired(self):
        keys,messages=self._render({**self.owner,"exp":1})
        self.assertEqual(keys,{"ux52_google_logout_other"})
        self.assertTrue(any("expirou" in x for x in messages))
    def test_authorization_fail_closed(self):
        for change in ({"email_verified":False},{"iss":"evil"},{"exp":"invalid"}):
            with self.subTest(change=change):
                self.assertNotEqual(ui.account_view_state(self.config,{**self.owner,**change}),"owner")
    def test_saved_states_reuse_canonical_helpers(self):
        cases=(("Ainda não salvo","Ainda não salvo"),
               ("Planejamento salvo","Planejamento salvo"),
               ("Alterações não salvas","Alterações não salvas"),
               ("Ainda não salvo","Salvo em espaço privado"))
        for fallback,shown in cases:
            with self.subTest(shown=shown),\
                 patch("planning_status.save_label",return_value=(fallback,"detail")) as legacy_save,\
                 patch("continuity_ui.private_status_label",return_value=(shown,"detail")) as private,\
                 patch.object(ui.st,"session_state",dict(self.session)):
                self.assertEqual(ui._saving_status(),shown)
                legacy_save.assert_not_called()
                private.assert_called_once_with((
                    "Apenas nesta sessão",
                    "O GitHub público não confirma salvamento na nuvem privada"))
    def test_save_status_logs_only_safe_error_type(self):
        with patch("continuity_ui.private_status_label",
                   side_effect=RuntimeError("TOKEN_MUST_NOT_LOG")),\
             self.assertLogs("sidebar_account_ui","WARNING") as lines:
            result=ui._saving_status()
        self.assertEqual(result,"Status de salvamento indisponível")
        self.assertFalse(any("TOKEN_MUST_NOT_LOG" in line for line in lines.output))


if __name__=="__main__":
    unittest.main()
