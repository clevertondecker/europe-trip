"""Timeline-first view; existing canonical organizers remain the only writers."""
from __future__ import annotations
import streamlit as st
from ux63_timeline_model import project_timeline, timeline_metrics


def render_timeline(plan, catalog, stage, *, on_organize=None, pending_first=False):
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
    if pending_first:
        rows.sort(key=lambda row:row["organized"])
    limit=st.session_state.get("ux120_timeline_limit_"+stage,14) if pending_first else 14
    for row in rows[:limit]:
        with st.container(border=True):
            top, status = st.columns([3,2], vertical_alignment="center")
            top.markdown("**"+row["name"]+"**")
            if row["group_name"]:
                top.caption("Viagem: "+row["group_name"])
            status.caption(row["status"])
            if row["dates"]:
                st.caption("Data individual: "+", ".join(row["dates"]))
            if row["period"]:
                st.caption("Período individual: "+row["period"])
            if row["group_dates"]:
                st.caption("Intervalo da viagem: "+row["group_dates"][0]+" a "+row["group_dates"][-1])
            if row["group_period"]:
                st.caption("Período da viagem: "+row["group_period"])
            if row["grouped"] and not row["dated"]:
                st.caption("Dia individual a definir")
            st.caption(str(row["attractions_count"])+" atração(ões) escolhida(s)")
            if on_organize is not None:
                st.button("Organizar visita",key="ux120_visit_"+row["id"],
                          on_click=on_organize,args=(row["id"],))
    if len(rows)>limit:
        if pending_first:
            key="ux120_timeline_limit_"+stage
            st.button("Mostrar mais visitas",key="ux120_timeline_more_"+stage,
                      on_click=lambda:st.session_state.update({key:limit+14}))
        st.caption(f"Mostrando {limit} de {len(rows)} visitas.")
    st.info("O calendário atual aceita um passeio francês principal por dia. "
            "Várias cidades podem compor uma viagem de fim de semana, "
            "mas não criam várias reservas ou agendamentos no mesmo dia.")
