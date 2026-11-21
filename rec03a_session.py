"""REC03A session-only view state; canonical navigation and REC02 scope."""
from __future__ import annotations

from hashlib import sha256
from ux64_navigation_model import select_public_task
from recommendation_scope_model import reconcile_scope

SCOPE = "rec03a_scope"
DRAFT = "rec03a_draft"
ACTIVITY = "rec03a_activity"
INTENT = "rec03a_navigation_intent"
IDENTITY = "rec03a_identity"
SUGGESTED = "Cidades sugeridas"
MANUAL = "Comparação personalizada"
ACTIVITIES = (MANUAL, SUGGESTED)


def clear_recommendation_context(state):
    """Only ephemeral REC03A state, never a persisted planning document."""
    for key in list(state.keys()):
        if isinstance(key, str) and key.startswith("rec03a_") and key != IDENTITY:
            state.pop(key, None)


def identity_token(account_state, user=None):
    """Opaque ephemeral token; no email or identity claims stored in scope."""
    if account_state not in ("owner", "other_account"):
        return account_state
    subject = user.get("sub") or user.get("email") if user is not None else None
    if not isinstance(subject, str) or not subject:
        return account_state + ":unknown"
    return account_state + ":" + sha256(subject.encode("utf-8")).hexdigest()


def sync_identity(state, token):
    if state.get(IDENTITY) != token:
        clear_recommendation_context(state)
        state[IDENTITY] = token


def request_navigation(state, target):
    if target not in ("suggestions", "manual", "wishlist"):
        raise ValueError("Destino de navegação inválido")
    state[INTENT] = target


def apply_navigation(state):
    target = state.pop(INTENT, None)
    if "rec03a_handoff_pending" in state:
        from rec03b_handoffs import apply_handoff
        apply_handoff(state)
    if target == "wishlist":
        select_public_task(state, "Explorar", "Minha lista")
    elif target in ("suggestions", "manual"):
        select_public_task(state, "Explorar", "Comparar bases")
        state[ACTIVITY] = SUGGESTED if target == "suggestions" else MANUAL
    return target


def reconcile_session_scope(state, interests, discovery):
    checked = reconcile_scope(interests, state.get(SCOPE), discovery)
    previous=state.get(SCOPE)
    state[SCOPE] = checked["scope"]
    if previous is not None and checked["scope"] is None:
        # Stale document identity: do not carry even unconfirmed draft IDs over.
        state.pop(DRAFT,None)
        state.pop("rec03a_edit_scope",None)
        state.pop("rec03a_scope_widget",None)
    return checked
