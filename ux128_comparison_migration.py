"""UX128: migrate the retired manual comparison into REC03A, never persisted."""
from rec03a_session import ACTIVITY, SUGGESTED, MANUAL, SCOPE, DRAFT
from rec03b_handoffs import CHOICE, CONTEXT, PREVIOUS
from recommendation_scope_model import reconcile_scope
from ux502_destination_interests_model import selected_destinations_for_comparison

LEGACY_KEYS = ("ux503_bases", "ux504_bases_shadow",
               "ux503_visible_destinations", "ux504_visible_destinations_shadow",
               "ux503_detail_destination", PREVIOUS)


def _valid_ids(value, allowed):
    return list(dict.fromkeys(x for x in value if isinstance(x,str) and x in allowed)) if isinstance(value,list) else []


def migrate_legacy_comparison(state, interests, discovery, research):
    """Canonical choices win (even empty). Legacy basket becomes a draft, not approval."""
    had_manual = state.get(ACTIVITY)==MANUAL
    cities = {c["id"] for c in research["cities"]}
    active = set(selected_destinations_for_comparison(interests,discovery))
    previous=state.get(PREVIOUS) if isinstance(state.get(PREVIOUS),dict) else {}
    old_bases = state.get("ux504_bases_shadow",state.get("ux503_bases",previous.get("ux504_bases_shadow")))
    old_destinations = state.get("ux504_visible_destinations_shadow",state.get("ux503_visible_destinations",previous.get("ux504_visible_destinations_shadow")))
    modern = state.get(CHOICE)
    if not isinstance(modern,list) or any(not isinstance(x,str) or x not in cities for x in modern) or len(set(modern))!=len(modern):
        if isinstance(old_bases,list):
            state[CHOICE]=_valid_ids(old_bases,cities)
    checked = reconcile_scope(interests,state.get(SCOPE),discovery)
    if checked["scope"] is None and DRAFT not in state and isinstance(old_destinations,list):
        state[DRAFT]=_valid_ids(old_destinations,active)
    if had_manual or (isinstance(old_bases,list) and "ux112_active_view_shadow" not in state):
        state["ux112_active_view"]="Minha comparação"
        state["ux112_active_view_shadow"]="Minha comparação"
    for key in LEGACY_KEYS:
        state.pop(key,None)
    context=state.get(CONTEXT)
    if isinstance(context,dict) and context.get("kind")=="manual":
        state.pop(CONTEXT,None)
    state[ACTIVITY]=SUGGESTED


def migrate_restored_comparison(state):
    """Bootstrap hook: no catalog loads or session writes for modern sessions."""
    context=state.get(CONTEXT)
    if not (state.get(ACTIVITY)==MANUAL or any(key in state for key in LEGACY_KEYS)
            or (isinstance(context,dict) and context.get("kind")=="manual")):
        return False
    from base_research_expanded_model import load_research
    from trip01_supplemental_discovery import build_exploration_discovery
    from ux502_destination_interests_model import empty_interests
    try:
        migrate_legacy_comparison(state,state.get("ux502_interests",empty_interests()),
                                  build_exploration_discovery(),load_research(include_candidates=True))
    except (ValueError,KeyError,TypeError,ImportError,OSError):
        # Fail closed: leave canonical selections untouched; do not retry a
        # malformed restored payload on every rerun.
        for key in LEGACY_KEYS:
            state.pop(key,None)
        if isinstance(context,dict) and context.get("kind")=="manual":
            state.pop(CONTEXT,None)
        state[ACTIVITY]=SUGGESTED
        state["rec03a_handoff_error"]="Filtros antigos incompatíveis; revise sua comparação."
    return True
