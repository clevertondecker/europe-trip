"""UX 4.5: bounded navigation handoff, without a second planning state.

Snapshots only ephemeral exploration filters that Streamlit can discard when a
widget disappears. Does not persist passwords, plans, or unapproved scenarios.
"""
from __future__ import annotations
from copy import deepcopy

EXPLORER_KEYS=("scenario_base_selected","explore_countries","explore_categories",
               "explore_route_filter","explore_ticket_filter",
               "explore_interest_filter","explore_max_minutes",
               "attractions_scenario_base","ux_mode")
DISCOVERY_KEYS=("workspace_destination_search","workspace_destination_country",
                "workspace_destination_category","workspace_discovery_sort",
                "workspace_discovery_count","advisor_discovery_max",
                "advisor_discovery_overnight","advisor_discovery_unverified")

def handoff(state,*,area:str,section:str,destination_id:str)->None:
    if (area,section) not in (("Explorar","Passeios"),
                               ("Meu roteiro","Melhorar meu roteiro")):
        raise ValueError("Origem de navegação não reconhecida")
    from ux_navigation import set_task
    keys=EXPLORER_KEYS if area=="Explorar" else DISCOVERY_KEYS
    state["ux45_origin"]={"area":area,"section":section,
                           "destination_id":destination_id,
                           "snapshot":{k:deepcopy(state[k]) for k in keys if k in state}}
    state["flow_active_stage"]="França"
    state["flow_stage"]="França"
    state["flow_active_destination"]=destination_id
    state["flow_add_open"]=False
    state["flow_edit_target"]=destination_id
    set_task(state,"Meu roteiro","Meu planejamento")

def return_to_origin(state)->bool:
    from ux_navigation import set_task
    origin=state.pop("ux45_origin",None)
    if not isinstance(origin,dict):
        return False
    if (origin.get("area"),origin.get("section")) not in (
        ("Explorar","Passeios"),("Meu roteiro","Melhorar meu roteiro")):
        return False
    for key,value in origin.get("snapshot",{}).items():
        state[key]=deepcopy(value)
    state.pop("flow_edit_target",None)
    state.pop("explore_selected_destination",None)
    if (origin["area"],origin["section"])==("Explorar","Passeios"):
        # The base-specific explorer moved to a specialist guide. Old handoffs
        # retain their filter snapshots and return to that actual renderer.
        state["ux_improve_view"]="Guias especializados"
        state["ux_guide_view"]="Explorar atrações"
        set_task(state,"Meu roteiro","Melhorar meu roteiro")
    else:
        set_task(state,origin["area"],origin["section"])
    return True
