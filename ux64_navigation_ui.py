"""Three-area task selector while preserving legacy callback/backup compatibility."""
from __future__ import annotations
import streamlit as st
from ux64_navigation_model import PUBLIC_TASKS,public_area,public_task,select_public_task


def _changed():
    area=public_area(st.session_state.get("ux_area"))
    selected=st.session_state["ux64_public_task"]
    select_public_task(st.session_state,area,selected)


def render_public_task_tabs():
    area=public_area(st.session_state.get("ux_area"))
    current=public_task(st.session_state.get("ux_area"),
                        st.session_state.get("ux_section"),
                        st.session_state.get("ux502_view"))
    # The public widget callback synchronizes the canonical route and view.
    # A queued handoff can change that view before the widget renders; never
    # allow an old widget value to override the requested destination.
    if st.session_state.get("ux64_public_task")!=current:
        st.session_state["ux64_public_task"]=current
    st.segmented_control("Atividade",list(PUBLIC_TASKS[area]),
                         key="ux64_public_task",selection_mode="single",
                         on_change=_changed)
