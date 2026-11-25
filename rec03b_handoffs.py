"""REC03B: validated one-shot handoffs across existing areas, session only.

Keys use REC03A's namespace so its account/restore invalidation also clears
all REC03B context. The wishlist and TripPlan remain authoritative.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite
from recommendation_scope_model import reconcile_scope
from ux64_navigation_model import select_public_task
from ux_navigation import set_task

PENDING = "rec03a_handoff_pending"
CONTEXT = "rec03a_handoff_context"
ERROR = "rec03a_handoff_error"
PREVIOUS = "rec03a_handoff_previous_manual"
CHOICE = "rec03a_handoff_base_selection"
SCOPE = "rec03a_scope"
MANUAL_KEYS = (
    ("ux503_bases", "ux504_bases_shadow"),
    ("ux503_visible_destinations", "ux504_visible_destinations_shadow"),
)


def _ids(value, allowed, *, minimum=1, maximum=None):
    if (not isinstance(value, list) or len(value) < minimum
            or (maximum is not None and len(value) > maximum)
            or any(not isinstance(x, str) or x not in allowed for x in value)
            or len(set(value)) != len(value)):
        raise ValueError("Seleção inválida ou desatualizada.")
    return list(value)


def validate_handoff(scope, interests, discovery, research, bases, kind):
    """Do not infer stages, include new interests or truncate a confirmed scope."""
    # manual is a read-only compatibility token for pre-UX128 pending requests.
    if kind not in ("manual", "profile", "map", "planning"):
        raise ValueError("Destino do encaminhamento inválido.")
    checked = reconcile_scope(interests, scope, discovery)
    if checked["state"] != "ready" or checked["scope"] != scope:
        raise ValueError("A lista mudou. Revise o escopo antes de continuar.")
    ids = {c["id"] for c in research["cities"]}
    if kind=="planning":
        if bases!=[]:
            raise ValueError("Planejamento não seleciona uma base.")
        chosen=[]
    else:
        chosen = _ids(bases, ids, minimum=2 if kind=="manual" else 1,
                      maximum=5 if kind=="manual" else 1)
    return {"kind":kind, "base_ids":chosen, "scope":deepcopy(scope)}


def planning_handoff_projection(context, plan, interests, discovery, catalog):
    """Use #195 eligibility, limited to the confirmed REC02 stage and scope."""
    from itinerary_flow_model import FRANCE_STAGE
    from ux_planning_journey_model import project_planning
    view=project_planning(plan,interests,discovery,catalog)
    wanted=set(context["scope"]["destination_ids"])
    eligible=[r["id"] for r in view["batches"][FRANCE_STAGE]["eligible"] if r["id"] in wanted]
    unsupported=[r["id"] for r in view["unsupported"] if r["id"] in wanted]
    included=[r["id"] for r in view["rows"] if r["id"] in wanted]
    other_stage=sorted(wanted-set(eligible)-set(unsupported)-set(included))
    return {"eligible":eligible,"unsupported":unsupported,"included":included,
            "other_stage":other_stage,
            "action":"build" if eligible else "review" if view["rows"] else "wishlist"}


def queue_handoff(state, kind, bases):
    """Only button callbacks request a transition; no widget writes here."""
    state[PENDING] = {"kind":kind,"base_ids":deepcopy(bases),
                      "scope":deepcopy(state.get(SCOPE))}


def queue_restore_manual(state):
    state[PENDING] = {"kind":"restore_manual"}


def apply_handoff(state, *, interests=None, discovery=None, research=None):
    """Consume BEFORE relevant Streamlit widgets. No changes if validation fails."""
    request=state.pop(PENDING,None)
    if request is None:
        return None
    from ux502_destination_interests_model import empty_interests
    from trip01_supplemental_discovery import build_exploration_discovery
    from base_research_expanded_model import load_research
    try:
        if not isinstance(request,dict):
            raise ValueError("Encaminhamento inválido.")
        if interests is None:
            interests=state.get("ux502_interests",empty_interests())
        if discovery is None:
            discovery=build_exploration_discovery()
        if research is None:
            research=load_research(include_candidates=True)
        kind=request.get("kind")
        if kind=="restore_manual":
            # Old queued restore cannot replace a newer canonical selection.
            from ux128_comparison_migration import migrate_legacy_comparison
            migrate_legacy_comparison(state,interests,discovery,research)
            select_public_task(state,"Explorar","Comparar bases")
            state["ux112_active_view"]="Minha comparação"
            state["ux112_active_view_shadow"]="Minha comparação"
            state.pop(ERROR,None)
            return kind
        if request.get("scope")!=state.get(SCOPE):
            raise ValueError("O escopo mudou. Revise as sugestões.")
        from comparison_destinations_model import from_state
        projected=from_state(state,discovery) if "advisor_plan" in state and "plan_id" in (request.get("scope") or {}).get("snapshot",{}) else interests
        context=validate_handoff(request.get("scope"),projected,discovery,research,
                                 request.get("base_ids"),kind)
        if kind=="manual":
            # Validated old handoff opens the existing modern comparison.
            # Do not overwrite a newer explicit canonical selection.
            if CHOICE not in state:
                state[CHOICE]=list(context["base_ids"])
            select_public_task(state,"Explorar","Comparar bases")
            state["ux112_active_view"]="Minha comparação"
            state["ux112_active_view_shadow"]="Minha comparação"
        elif kind=="profile":
            set_task(state,"Explorar","Cidades-base")
            state["ux40_selected_city"]=context["base_ids"][0]
            state["expanded_bases_detail_city"]=context["base_ids"][0]
        elif kind=="planning":
            from attractions_model import load_attractions
            from itinerary_flow_model import FRANCE_STAGE
            from ux_planning_journey_ui import request_planning
            plan=state["advisor_plan"]
            projected=planning_handoff_projection(context,plan,interests,discovery,load_attractions())
            if projected["action"]=="wishlist":
                select_public_task(state,"Explorar","Minha lista")
            else:
                request_planning(state,projected["action"],FRANCE_STAGE)
        else:
            select_public_task(state,"Explorar","Mapa")
        if kind=="manual":
            state.pop(CONTEXT,None)
        else:
            state[CONTEXT]=context
        state.pop(ERROR,None)
        return kind
    except (ValueError,KeyError,TypeError,ImportError,OSError):
        state[ERROR]="Não foi possível abrir esta seleção. Revise as cidades e o escopo."
        return None


def current_context(state, kind, *, interests, discovery, research):
    context=state.get(CONTEXT)
    if not isinstance(context,dict) or context.get("kind")!=kind:
        return None
    if context.get("scope")!=state.get(SCOPE):
        return None
    try:
        from comparison_destinations_model import from_state
        projected=from_state(state,discovery) if "plan_id" in context["scope"].get("snapshot",{}) else interests
        return validate_handoff(context["scope"],projected,discovery,research,
                                context["base_ids"],kind)
    except (ValueError,KeyError,TypeError):
        return None


def contextual_points(context, plan, *, discovery, research, exploration, catalog):
    """Only existing catalog coordinates. No geocoding, no straight-line routes."""
    from rail_evidence_unified_model import canonical_place
    from itinerary_flow_model import selected_rows
    wanted=set(context["scope"]["destination_ids"])
    candidate=context["base_ids"][0]
    official=plan["base_city"]
    planned={canonical_place(row["id"]) for row in selected_rows(plan,catalog)}
    names={c["id"]:c for c in discovery["destinations"]}
    names.update({c["id"]:c for c in research["cities"]})
    indexed={}
    for rows in (catalog["destinations"],exploration["destinations"],
                 exploration["bases"],research["cities"]):
        for row in rows:
            lat,lon=row.get("lat"),row.get("lon")
            if (type(lat) in (int,float) and type(lon) in (int,float)
                    and isfinite(lat) and isfinite(lon)
                    and -90<=lat<=90 and -180<=lon<=180
                    and (lat,lon)!=(0,0)):
                indexed.setdefault(canonical_place(row["id"]),(row,lat,lon))
    points=[]
    missing=[]
    for key in sorted(wanted|{candidate,official}):
        roles=[]
        if key==candidate: roles.append("Base candidata")
        if key==official: roles.append("Base oficial")
        if key in wanted: roles.append("Destino desejado no escopo")
        if key in planned: roles.append("Destino já no roteiro")
        if key not in indexed:
            missing.append(names.get(key,{}).get("name",key))
            continue
        row,lat,lon=indexed[key]
        meta=names.get(key,row)
        status="roteiro_proposto" if key==official or key in planned else (
            "candidata" if key==candidate else "opcional")
        points.append({"id":key,"name":meta["name"],"country":meta["country"],
                       "lat":lat,"lon":lon,"status":status,"role":" · ".join(roles)})
    return points,missing
