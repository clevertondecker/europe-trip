"""Central Streamlit-session adapter to one canonical, versioned TripPlan.

No API writes happen here. A user interaction creates one revision and copies
read-only compatibility projections for older UI components.
"""
from __future__ import annotations
from copy import deepcopy
import streamlit as st
from planning_store import (create_from_legacy,change_plan,set_package,
                            remove_package,add_assignment,remove_assignment,
                            sync_legacy_view,summary)
from trip_plan_model import new_plan

def bootstrap()->dict:
    """Initialize early, before navigation/widgets are rendered."""
    if "advisor_plan" not in st.session_state:
        try:
            plan=create_from_legacy(st.session_state)
        except (ValueError,KeyError,TypeError):
            plan=new_plan()
        st.session_state["advisor_plan"]=plan
    plan=st.session_state["advisor_plan"]
    # Missing keys only; canonical always wins for loaded session state.
    if "explore_packages" not in st.session_state:
        st.session_state["explore_packages"]=deepcopy(plan["packages"])
    if "explore_calendar" not in st.session_state:
        st.session_state["explore_calendar"]=deepcopy(plan["assignments"])
    if "explore_base" not in st.session_state:
        st.session_state["explore_base"]=plan["base_city"]
    if "unified_city" not in st.session_state:
        st.session_state["unified_city"]=plan["base_city"].capitalize()
    if "unified_scenario" not in st.session_state:
        st.session_state["unified_scenario"]=plan["budget_scenario"]
    return plan

def active_plan()->dict:
    return bootstrap()

def _commit(next_plan:dict)->dict:
    before=bootstrap()
    if next_plan==before:return before
    st.session_state["advisor_plan"]=next_plan
    sync_legacy_view(next_plan,st.session_state)
    if before["base_city"]!=next_plan["base_city"]:
        new_base=next_plan["base_city"]
        # Do not mutate an instantiated widget; only set a different value
        # when changed in another page or before the control is rendered.
        if st.session_state.get("explore_base")!=new_base:
            st.session_state["explore_base"]=new_base
        city_name=new_base.capitalize()
        if st.session_state.get("unified_city")!=city_name:
            st.session_state["unified_city"]=city_name
    if before["budget_scenario"]!=next_plan["budget_scenario"]:
        if st.session_state.get("unified_scenario")!=next_plan["budget_scenario"]:
            st.session_state["unified_scenario"]=next_plan["budget_scenario"]
    st.session_state.pop("advisor_proposals",None)
    st.session_state["advisor_local_changed"]=True
    if st.session_state.get("advisor_autosave_optin") and st.session_state.get(
        "advisor_public_repo_ack"):
        st.session_state["advisor_autosave_pending"]=True
    return next_plan

def accept_approved_plan(next_plan:dict)->dict:
    """Adopt a reviewed optimizer proposal; may queue opt-in persistence."""
    return _commit(next_plan)

def update_fields(**changes)->dict:
    return _commit(change_plan(bootstrap(),changes))

def select_package(destination:str,items:list[str])->dict:
    return _commit(set_package(bootstrap(),destination,items))

def delete_package(destination:str)->dict:
    return _commit(remove_package(bootstrap(),destination))

def schedule_package(day:str,destination:str)->dict:
    return _commit(add_assignment(bootstrap(),day,destination))

def unschedule_package(day:str)->dict:
    return _commit(remove_assignment(bootstrap(),day))

def update_interest(attraction_id:str,preference:str)->dict:
    if preference not in {"Quero visitar","Opcional","Descartar"}:
        raise ValueError("Interesse inválido")
    plan=bootstrap()
    marks=dict(plan.get("preferences") or {})
    marks[attraction_id]=preference
    return update_fields(preferences=marks)

def statistics()->dict:
    return summary(bootstrap())
