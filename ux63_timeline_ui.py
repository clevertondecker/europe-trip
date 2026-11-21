"""Timeline-first view; existing canonical organizers remain the only writers."""
from __future__ import annotations
import streamlit as st
from ux63_timeline_model import project_timeline, timeline_metrics


def render_timeline(plan, catalog, stage):
    rows = project_timeline(plan, catalog,
                            st.session_state.get("ux48_weekend_groups"),
                            stage=stage)
    stats = timeline_metrics(rows)
    st.markdown("#### Organização da temporada")
    a,b,c=st.columns(3)
    a.metric("Visitas no roteiro",stats["visits"])
    b.metric("Em viagens agrupadas",stats["grouped"])
    c.metric("Com período ou data",stats["organized"])
    st.caption("Você pode deixar uma visita sem data. Pertencer a uma viagem "
               "sem período definido não significa estar agendada.")
    if not rows:
        st.info("Adicione uma cidade ao roteiro antes de organizar seu calendário.")
        return
    for row in rows[:14]:
        with st.container(border=True):
            top, status = st.columns([3,2], vertical_alignment="center")
            top.markdown("**"+row["name"]+"**")
            if row["group_name"]:
                top.caption("Viagem: "+row["group_name"])
            status.caption(row["status"])
            if row["dates"]:
                st.caption("Data de referência: "+", ".join(row["dates"]))
            elif row["period"]:
                st.caption("Período: "+row["period"])
            st.caption(str(row["attractions_count"])+" atração(ões) escolhida(s)")
    if len(rows)>14:
        st.caption("Mostrando 14 visitas; use o organizador abaixo para outras datas.")
    st.info("O calendário atual aceita um passeio francês principal por dia. "
            "Várias cidades podem compor uma viagem de fim de semana, "
            "mas não criam várias reservas ou agendamentos no mesmo dia.")
