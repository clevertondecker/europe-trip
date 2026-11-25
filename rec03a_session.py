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
ACTIVITIES = (SUGGESTED,)
# MANUAL is retained solely as a historical session compatibility token.


def clear_recommendation_context(state):
    """Only ephemeral REC03A state, never a persisted planning document."""
    # An identity change must also discard any UX34 inputs borrowed by a
    # contextual UX114 review, rather than leaking the previous account's
    # candidate/destinations into the advanced workspace.
    if "ux114_review_context" in state:
        for key in ("ux34_candidates","ux34_destinations","ux34_apply_candidate",
                    "ux34_review","ux34_review_candidate",
                    "ux34_review_signature","ux34_apply_ack"):
            state.pop(key,None)
    # UX111/112 and contextual UX114 are short-lived REC03A presentation
    # state, even though their keys do not use the historical rec03a prefix.
    for key in list(state.keys()):
        if isinstance(key, str) and (
            (key.startswith("rec03a_") and key != IDENTITY)
            or key.startswith(("ux111_", "ux112_", "ux114_"))
        ):
            state.pop(key, None)
    # Never migrate another account's legacy comparison filters.
    for key in ("ux503_bases", "ux504_bases_shadow", "ux503_visible_destinations",
                "ux504_visible_destinations_shadow", "ux503_detail_destination",
                "ux503_pending_return_to_wishlist"):
        state.pop(key, None)
    # An open contextual review must not outlive an account change.
    for key in ("ux34_review", "ux34_review_candidate",
                "ux34_review_signature", "ux34_apply_ack"):
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
    if target not in ("suggestions", "manual", "wishlist", "discovery"):
        raise ValueError("Destino de navegação inválido")
    state[INTENT] = target


def apply_navigation(state):
    target = state.pop(INTENT, None)
    if "rec03a_handoff_pending" in state:
        from rec03b_handoffs import apply_handoff
        apply_handoff(state)
    if target == "discovery":
        select_public_task(state, "Explorar", "Descobrir")
    elif target == "wishlist":
        select_public_task(state, "Explorar", "Minha lista")
    elif target in ("suggestions", "manual"):
        select_public_task(state, "Explorar", "Comparar bases")
        state[ACTIVITY] = SUGGESTED
        if target == "manual":
            state["ux112_active_view"] = "Minha comparação"
            state["ux112_active_view_shadow"] = "Minha comparação"
    return target


def reconcile_session_scope(state, interests, discovery):
    checked = reconcile_scope(interests, state.get(SCOPE), discovery)
    previous=state.get(SCOPE)
    state[SCOPE] = checked["scope"]
    if previous is not None and previous != checked["scope"]:
        # Restore previous advanced filters, but NEVER an old approval.
        saved=state.get("ux114_saved_workspace")
        if isinstance(saved,dict):
            from copy import deepcopy
            for key in ("ux34_candidates","ux34_destinations","ux34_apply_candidate",
                        "ux34_review","ux34_review_candidate",
                        "ux34_review_signature","ux34_apply_ack"):
                state.pop(key,None)
            for key,value in saved.items():
                if key in ("ux34_candidates","ux34_destinations","ux34_apply_candidate"):
                    state[key]=deepcopy(value)
        # A contextual official-base review belongs to exactly one confirmed
        # scope; never let it survive edits to destinations or priorities.
        for key in list(state.keys()):
            if isinstance(key,str) and key.startswith("ux114_"):
                state.pop(key,None)
        state.pop("ux34_review",None)
        state.pop("ux34_review_signature",None)
        state.pop("ux34_apply_ack",None)
    if previous is not None and checked["scope"] is None:
        # Stale document identity: do not carry even unconfirmed draft IDs over.
        state.pop(DRAFT,None)
        state.pop("rec03a_edit_scope",None)
        state.pop("rec03a_scope_widget",None)
    return checked
