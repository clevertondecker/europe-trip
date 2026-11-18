"""UX 5.2: sidebar authentication UI, using the existing OIDC security boundary.

This is deliberately *not* a persistence, Drive OAuth or authorization layer.
All decisions about GitHub writes and private archive access remain in their
existing modules and require their original authorization checks.
"""
from __future__ import annotations

import streamlit as st

from travel_advisor_ui import _owner_config
from advisor_auth import is_verified_owner


def account_view_state(config: dict, user) -> str:
    """Deterministic UI-only state. An arbitrary Google login is not ownership."""
    if not config.get("google_configured") or not config.get("owner_email"):
        return "unconfigured"
    try:
        if is_verified_owner(user, config["owner_email"]):
            return "owner"
        if user.get("is_logged_in") is True:
            return "other_account"
    except (AttributeError, KeyError, TypeError):
        pass
    return "signed_out"


def _logged_in_user():
    try:
        return st.user
    except (AttributeError, KeyError, TypeError):
        return None


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

    if status == "other_account":
        st.warning("Conta não autorizada ou sessão expirada. Salvamento protegido indisponível.")
        st.button("Sair do Google", key="ux52_google_logout_other",
                  icon=":material/logout:", width="stretch", on_click=st.logout)
        return

    # The identity displayed below is *only* the already verified owner.
    st.caption("Conectado · conta autorizada")
    st.caption(config["owner_email"])

    # Google authentication does not imply Google Drive write authorization.
    # Reuse the existing saved-state contract; never infer successful persistence.
    try:
        from continuity_ui import private_status_label
        from planning_status import save_label
        from planning_session import active_plan
        plan = active_plan()
        label, _ = private_status_label(save_label(
            plan, st.session_state.get("advisor_saved_snapshot"), True))
        st.caption("Planejamento: " + label)
    except (AttributeError, KeyError, TypeError, ValueError):
        st.caption("Planejamento: status de salvamento indisponível")

    st.button("Sair do Google", key="ux52_google_logout",
              icon=":material/logout:", width="stretch", on_click=st.logout)
