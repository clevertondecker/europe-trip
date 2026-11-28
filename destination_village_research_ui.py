"""Sourced destination detail without changing the plan or budget."""
import streamlit as st
from destination_village_research_model import DESTINATION_IDS, load_village_research

NAMES = {"mulhouse":"Mulhouse","strasbourg":"Strasbourg","metz":"Metz","nancy":"Nancy","lille":"Lille"}

def _duration(n):
    return f"{n // 60}h{n % 60:02d}"

def render_village_research(destination_id):
    if destination_id not in DESTINATION_IDS:
        return
    data = load_village_research()
    st.markdown("**Conexões das cinco cidades-base**")
    for row in data["connections"]:
        if row["destination_id"] != destination_id:
            continue
        if row["minimum_oneway_min"] is not None:
            duration = _duration(row["minimum_oneway_min"]) + " mínimo publicado; média " + _duration(row["typical_oneway_min"])
        else:
            duration = _duration(row["segment_sum_min"]) + " soma indicativa sem espera; não é itinerário"
        st.markdown(f"**{NAMES[row['base_id']]}** · {duration} · {row['scenario']}")
        for segment in row["segments"]:
            st.markdown(f"- [{segment['from']} → {segment['to']}]({segment['source_url']}) · {_duration(segment['minimum_min'])}")
    st.caption(next(r["route_note"] for r in data["connections"] if r["destination_id"] == destination_id))
    st.markdown("**Custos locais publicados em 2026 · casal**")
    for cost in data["local_costs"][destination_id]:
        st.markdown(f"- [{cost['label']}]({cost['source_url']}) — {cost['currency']} {cost['amount']}. {cost['conditions']}")
    st.markdown("**Cenários a avaliar**")
    for scenario in data["scenarios"][destination_id]:
        st.markdown("- " + scenario)
    st.caption("Ainda sem cotação integral: " + "; ".join(data["missing"]) + ".")
