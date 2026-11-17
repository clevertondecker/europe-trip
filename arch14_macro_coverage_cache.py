"""ARCH 1.4 — cached read-only macro coverage for repeated Streamlit reruns.

The underlying dataset lives in Git; TTL limits stale research after an
external dataset refresh. No cache of user selections or official TripPlan.
"""
from __future__ import annotations

import streamlit as st


def macro_coverage_rows(base_ids):
    """Compute a deterministic snapshot with each source loaded once."""
    from dq32_macro_opportunities_model import (
        load_macro_tourism, opportunity_overview,
    )
    from attractions_model import load_attractions
    from base_explorer_model import load_exploration
    from base_research_expanded_model import load_research
    from base_scenario_model import base_options
    from rail_evidence_unified_model import load_rail_evidence

    if not isinstance(base_ids,tuple) or not base_ids or (
            len(base_ids)!=len(set(base_ids))):
        raise ValueError("Pass a nonempty tuple of distinct base IDs")
    macro=load_macro_tourism()
    catalog=load_attractions()
    exploration=load_exploration()
    research=load_research()
    options=base_options()
    rail=load_rail_evidence()
    results=[]
    for base_id in base_ids:
        result=opportunity_overview(
            base_id,macro=macro,catalog=catalog,exploration=exploration,
            research=research,options=options,rail=rail)
        results.append({
            "Cidade-base":result["base_name"],
            "Atrações canônicas locais":result["canonical_local_attractions"],
            "Novas atrações locais":result["new_local_attractions"],
            "Destinos com trem histórico":result["rail_time_documented_count"],
            "Destinos sem tempo de trem":result["unresearched_count"],
            "Passeios viáveis comprovados":"Não avaliados",
        })
    return results


@st.cache_data(ttl=300, show_spinner=False)
def cached_macro_coverage_rows(base_ids: tuple[str,...]):
    """Safe across reruns; no personally identifiable or mutable plan data."""
    return macro_coverage_rows(base_ids)
