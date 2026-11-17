"""Reusable Streamlit map presentation, without App globals.

Retain original pydeck layer/tooltip semantics and status palette.
"""
from __future__ import annotations

import pydeck as pdk
import streamlit as st
from data_model import STATUS_COLORS, STATUS_LABEL


def render_map_view(places: list[dict], height: int = 430, show_labels: bool = True,
             center: tuple[float, float] | None = None, zoom: float = 4.0) -> None:
    points = [dict(p, color=STATUS_COLORS[p["status"]], status_label=STATUS_LABEL[p["status"]]) for p in places]
    if not points:
        st.info("Nenhum destino corresponde aos filtros.")
        return
    scatter = pdk.Layer(
        "ScatterplotLayer", data=points, get_position="[lon, lat]", get_fill_color="color",
        get_radius=25000, radius_min_pixels=6, radius_max_pixels=15, stroked=True,
        get_line_color=[255, 255, 255], line_width_min_pixels=2, pickable=True,
    )
    label = pdk.Layer(
        "TextLayer", data=points, get_position="[lon, lat]", get_text="name",
        get_size=13, size_min_pixels=10, get_color=[27, 53, 64],
        get_pixel_offset=[0, 15], get_text_anchor="'middle'", pickable=True,
    )
    latitude, longitude = center if center is not None else (45.3, 10.1)
    view = pdk.ViewState(latitude=latitude, longitude=longitude, zoom=zoom, min_zoom=2, max_zoom=14)
    deck = pdk.Deck(
        map_style="https://basemaps.cartocdn.com/gl/positron-gl-style/style.json",
        initial_view_state=view, layers=[scatter, label] if show_labels else [scatter],
        tooltip={"html":"<b>{name}</b><br/>{country}<br/>{status_label}<br/>{role}",
                 "style":{"backgroundColor":"#163A4D","color":"white","fontFamily":"sans-serif"}},
    )
    st.pydeck_chart(deck, height=height, width="stretch")


