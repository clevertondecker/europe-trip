"""Shared exploratory city widget state, independent of presentation modules.

Keep this module dependency-light: it must import without loading the finance
engine, maps, Streamlit page, or advisor UI.  Streamlit callbacks run before
new widgets are instantiated.
"""
from __future__ import annotations
import streamlit as st
from base_scenario_model import base_options, choose_exploratory_base


def sync_city_widget(widget_key: str, choices: list[str]) -> None:
    """Set a local widget's candidate before it renders if context changed."""
    candidate = st.session_state.get("scenario_base_selected")
    if candidate in choices and st.session_state.get(widget_key) != candidate:
        st.session_state[widget_key] = candidate


def set_city_from_widget(widget_key: str) -> None:
    """Propagate a candidate to the shared context without changing TripPlan."""
    candidate = choose_exploratory_base(
        st.session_state[widget_key], base_options(include_candidates=True))
    st.session_state["scenario_base_selected"] = candidate
    st.session_state["scenario_sidebar"] = candidate
    st.session_state["ux_last_candidate"] = candidate
    # Avoid assigning to a widget key from a callback registered on a
    # different widget *after* the global mode control was instantiated.
    # Instead, stage the mode switch for the next script run.
    st.session_state["ux_pending_mode"] = "Simulação"
