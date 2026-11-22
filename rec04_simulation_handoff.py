"""REC04 nonpersisted and explicitly-confirmed simulation navigation.

No scenario selection mutates TripPlan, wishlist, favorites or private decisions.
Pending intents are consumed once, before Streamlit widgets initialize.
"""
from __future__ import annotations
from copy import deepcopy

PENDING="rec03a_rec04_pending"
CONTEXT="rec03a_rec04_context"
ERROR="rec03a_rec04_error"
SOURCE_OPTIONS=("suggestions","profile")


def request_simulation(state,city_id,source="suggestions"):
    if source not in SOURCE_OPTIONS or not isinstance(city_id,str):
        raise ValueError("Origem ou cidade inválida")
    state[PENDING]={
        "city_id":city_id, "source":source,
        "identity":state.get("rec03a_identity"),
        "plan_id":state.get("advisor_plan",{}).get("plan_id"),
        "scope":deepcopy(state.get("rec03a_scope")),
    }


def apply_simulation_request(state,*,options=None,research=None):
    pending=state.pop(PENDING,None)
    if pending is None:
        return False
    try:
        if (not isinstance(pending,dict)
                or pending.get("source") not in SOURCE_OPTIONS
                or pending.get("identity")!=state.get("rec03a_identity")
                or pending.get("plan_id")!=state.get("advisor_plan",{}).get("plan_id")
                or pending.get("scope")!=state.get("rec03a_scope")):
            raise ValueError("Contexto da recomendação alterado")
        from rec04_candidate_capabilities import capability_for
        row=capability_for(pending.get("city_id"),options=options,research=research)
        if not row["scenario_selectable"]:
            raise ValueError("Simulação não suportada")
        from ux64_navigation_model import select_public_task
        select_public_task(state,"Orçamento","Simulações")
        city=row["id"]
        state["scenario_base_selected"]=city
        state["scenario_sidebar"]=city
        state["ux_last_candidate"]=city
        state["ux_mode"]="Simulação"
        state["ux_mode_value"]="Simulação"
        # A previous city's manual rent must never follow the new candidate.
        state["unified_override_rent"]=False
        state[CONTEXT]=deepcopy(pending)
        state.pop(ERROR,None)
        return True
    except (ValueError,TypeError,KeyError):
        state[ERROR]="Não foi possível abrir a simulação; a cidade ou o escopo mudou."
        return False


def valid_context(state):
    ctx=state.get(CONTEXT)
    if not isinstance(ctx,dict):
        return None
    if (ctx.get("identity")!=state.get("rec03a_identity")
            or ctx.get("plan_id")!=state.get("advisor_plan",{}).get("plan_id")
            or ctx.get("scope")!=state.get("rec03a_scope")
            or ctx.get("city_id")!=state.get("scenario_base_selected")
            or state.get("ux_mode")!="Simulação"):
        state.pop(CONTEXT,None)
        return None
    return ctx


def return_to_source(state):
    ctx=valid_context(state)
    if ctx is None:
        return
    state.pop(CONTEXT,None)
    if ctx["source"]=="profile" and (state.get("rec03a_handoff_context") or {}).get("kind")=="profile":
        from ux_navigation import set_task
        set_task(state,"Explorar","Cidades-base")
    else:
        from rec03a_session import request_navigation
        request_navigation(state,"suggestions")


def return_to_official(state):
    official=state["advisor_plan"]["base_city"]
    last=state.get("scenario_base_selected",official)
    if last!=official:
        state["ux_last_candidate"]=last
    state["scenario_base_selected"]=official
    state["scenario_sidebar"]=official
    state["ux_mode"]="Oficial"
    state["ux_mode_value"]="Oficial"
    state.pop(CONTEXT,None)
    from ux64_navigation_model import select_public_task
    select_public_task(state,"Orçamento","Visão financeira")
