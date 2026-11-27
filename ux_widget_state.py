"""Session-only widget restoration shared by navigation and research views."""
import streamlit as st


def remember(widget, shadow):
    st.session_state[shadow] = st.session_state[widget]


def restore_widget(widget, shadow, default, valid=None):
    state = st.session_state
    value = state.get(shadow, default)
    if valid is not None and not valid(value):
        value = default
    if state.get(widget) != value:
        state[widget] = value
    state[shadow] = value
    return value


def widget_state(key, default, valid):
    shadow = key + "_shadow"
    restore_widget(key, shadow, default, valid)
    return {"key": key, "on_change": remember, "args": (key, shadow)}


def _remember_navigation(widget, shadow, options):
    """Only valid navigation choices replace the last valid choice."""
    value = st.session_state[widget]
    if value in options:
        st.session_state[shadow] = value


def navigation_widget_state(key, options):
    """Deselect is a no-op for single-choice navigation, not generic inputs."""
    shadow = key + "_shadow"
    restore_widget(key, shadow, options[0], lambda v: v in options)
    return {"key": key, "on_change": _remember_navigation,
            "args": (key, shadow, tuple(options))}
