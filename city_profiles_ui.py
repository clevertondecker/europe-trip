"""Temporary UX123 research entry; renders the same UX124 profile, not a second dossier."""
from __future__ import annotations
import streamlit as st
from ux124_city_profile_ui import render_city_profile
from base_research_expanded_model import load_research

def render_enriched_city_profiles(*,only_finalists:bool)->None:
    research=load_research(include_candidates=True)
    choices={c["id"]:c["name"] for c in research["cities"]
             if not only_finalists or c["shortlist"]}
    st.markdown("### Conheça as cidades-base")
    st.caption("Mesma ficha de Conhecer cidade; entrada temporária até a migração do inventário.")
    selected=st.selectbox("Cidade para conhecer",list(choices),
                          key="ux_city_profile_detail",format_func=lambda key:choices[key])
    if selected:
        render_city_profile(selected,research=research,key_prefix="ux124_inventory")
