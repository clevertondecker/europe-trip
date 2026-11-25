"""Timeline-first view; existing canonical organizers remain the only writers."""
from __future__ import annotations
import streamlit as st
from ux63_timeline_model import project_timeline, timeline_metrics


def render_timeline(plan, catalog, stage, *, on_organize=None, pending_first=False,
                    focused_id=None,render_editor=None,render_photo=None,places=None):
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
    from ux129_visit_focus import visible_visits,stable_visit_order
    from ux97_comparison_visual_ui import destination_country_label
    if render_editor is not None:
        rows=stable_visit_order(rows,st.session_state,stage,focused_id)
    from itinerary_flow_model import get_choice,selected_rows_for_stage,ITALY_STAGE
    from destination_identity import canonical_destination_id
    visits={r["id"]:r for r in selected_rows_for_stage(plan,catalog,stage)}
    visible=visible_visits(rows,limit,focused_id)
    for row in visible:
        key=row["id"]
        selected=focused_id==key and render_editor is not None
        with st.container(border=True,key=("ux129_focused_" if selected else "ux129_visit_")+key):
            if render_photo is not None:
                photo_col,top,status=st.columns([1,3,2],vertical_alignment="top")
                with photo_col:
                    render_photo(row)
            else:
                top,status=st.columns([3,2],vertical_alignment="center")
            place=(places or {}).get(canonical_destination_id(key),{})
            country=place.get("country") or ("Itália" if stage==ITALY_STAGE else "")
            top.markdown("**"+destination_country_label(row["name"],country)+"**")
            if country:
                top.caption(country)
            if selected:
                top.caption("● Em edição")
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
            if render_editor is not None:
                names={a["id"]:a["name"] for a in get_choice(catalog,key)["attractions"]}
                picked=visits[key]["attractions"]
                st.write(" · ".join(names.get(a,a) for a in picked) or "Atrações a escolher")
            else:
                st.caption(str(row["attractions_count"])+" atração(ões) escolhida(s)")
            if selected:
                st.divider()
                render_editor(row)
            elif on_organize is not None:
                st.button("Organizar visita",key="ux120_visit_"+row["id"],
                          on_click=on_organize,args=(row["id"],))
    if len(rows)>limit:
        if pending_first:
            key="ux120_timeline_limit_"+stage
            st.button("Mostrar mais visitas",key="ux120_timeline_more_"+stage,
                      on_click=lambda:st.session_state.update({key:limit+14}))
        st.caption(f"Mostrando {len(visible)} de {len(rows)} visitas.")
    st.info("O calendário atual aceita um passeio francês principal por dia. "
            "Várias cidades podem compor uma viagem de fim de semana, "
            "mas não criam várias reservas ou agendamentos no mesmo dia.")
