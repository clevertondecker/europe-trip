"""UX 5.2: sidebar authentication UI, using the existing OIDC security boundary.

This is deliberately *not* a persistence, Drive OAuth or authorization layer.
All decisions about GitHub writes and private archive access remain in their
existing modules and require their original authorization checks.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from collections.abc import Mapping

import streamlit as st

from travel_advisor_ui import _owner_config
from advisor_auth import is_verified_owner

_LOGGER = logging.getLogger(__name__)


def account_view_state(config: dict, user: Mapping | None) -> str:
    """UI classification only; never a substitute for authorization checks."""
    if not config.get("google_configured") or not config.get("owner_email"):
        return "unconfigured"
    if not isinstance(user, Mapping) or user.get("is_logged_in") is not True:
        return "signed_out"
    if is_verified_owner(user, config["owner_email"]):
        return "owner"
    # Distinguish an expired session only for presentation; authorization
    # remains exclusively in advisor_auth.is_verified_owner (fail closed).
    try:
        expiry = int(user.get("exp"))
        if expiry <= int(datetime.now(timezone.utc).timestamp()) + 30:
            return "expired"
    except (ValueError, TypeError, OverflowError):
        pass
    return "other_account"


def _logged_in_user():
    try:
        return st.user
    except (AttributeError, KeyError, TypeError):
        return None


def _saving_status() -> str:
    """Use the existing canonical storage labels; never infer saved from login."""
    try:
        from continuity_ui import private_status_label
        from planning_status import save_label
        from planning_session import active_plan
        label, _ = private_status_label(save_label(
            active_plan(), st.session_state.get("advisor_saved_snapshot"), True))
        return label
    except (AttributeError, KeyError, TypeError, ValueError, RuntimeError) as exc:
        # Exception class only: provider exceptions may contain sensitive content.
        _LOGGER.warning("Sidebar save-status unavailable: %s", type(exc).__name__)
        return "Status de salvamento indisponível"


def render_sidebar_account() -> None:
    """Show account access on every page, below primary navigation and tools."""
    config = _owner_config()
    # Do not access st.user before OIDC is configured: unauthenticated
    # deployments must still render every navigation area normally.
    user = (_logged_in_user() if config.get("google_configured")
            and config.get("owner_email") else None)
    status = account_view_state(config, user)

    st.markdown("**Conta Google**")
    if status == "unconfigured":
        st.caption("Login Google ainda não configurado neste aplicativo.")
        st.caption("Configure o OAuth nos Secrets do Streamlit para habilitar o acesso.")
        return

    if status == "signed_out":
        st.caption("Desconectado · escolhas locais não são salvas automaticamente.")
        st.button("Entrar com Google", key="ux52_google_login", icon=":material/login:",
                  width="stretch", on_click=st.login, args=["google"])
        return

    if status == "expired":
        st.warning("Sua sessão expirou. Saia e entre novamente para continuar.")
        st.button("Sair do Google", key="ux52_google_logout_other",
                  icon=":material/logout:", width="stretch", on_click=st.logout)
        return

    if status == "other_account":
        st.warning("Conta não autorizada para salvar este planejamento.")
        st.button("Sair do Google", key="ux52_google_logout_other",
                  icon=":material/logout:", width="stretch", on_click=st.logout)
        return

    # The identity displayed below is *only* the already verified owner.
    st.caption("Conectado · conta autorizada")
    st.caption(config["owner_email"])

    # Logging in does not confer Drive write access or imply remote persistence.
    st.caption("Planejamento: " + _saving_status())
    st.caption("Entrar no Google não significa que seus dados foram salvos no Drive.")

    st.button("Sair do Google", key="ux52_google_logout",
              icon=":material/logout:", width="stretch", on_click=st.logout)
