"""Compact destination board shared conceptually with discovery; no canonical writes."""
from __future__ import annotations
import streamlit as st
from ux61_destination_board_model import build_destination_board, board_metrics
from trip01_supplemental_discovery import build_exploration_discovery


@st.cache_data(show_spinner=False)
def _discovery():
    return build_exploration_discovery()


def _open_research(destination_id, name):
    from ux64_navigation_model import select_public_task
    state = st.session_state
    select_public_task(state, "Explorar", "Descobrir")
    # An explicit target must remain visible even after incompatible filters.
    state["ux502_discovery_filters"] = {
        "ux501_country": "Todos os países", "ux501_categories": [],
        "ux501_search": name, "ux501_page": 1,
    }


def _focus_visit(destination_id, stage):
    state = st.session_state
    state["flow_active_stage"] = stage
    state["flow_stage"] = stage
    state["flow_active_destination"] = destination_id
    state["flow_edit_target"] = destination_id
    state["flow_add_open"] = False


def render_destination_board(plan, catalog):
    """Use projections of the existing wishlist and TripPlan; render no second editor."""
    from ux502_destination_interests_model import empty_interests
    wishes = st.session_state.get("ux502_interests", empty_interests())
    rows = build_destination_board(
        wishes, plan, _discovery(), catalog,
        st.session_state.get("ux48_weekend_groups"))
    counts = board_metrics(rows)
    st.markdown("#### Meus destinos")
    a, b, c = st.columns(3)
    a.metric("Quero conhecer", counts["wished"])
    b.metric("No roteiro", counts["planned"])
    c.metric("Com período ou data", counts["organized"])
    st.caption("Os desejos aparecem automaticamente; só uma confirmação inclui "
               "uma visita no roteiro. Estar em grupo sem data não significa agendado.")
    if not rows:
        st.info("Sua lista ainda está vazia. Descubra lugares e marque os favoritos.")
        st.button("Explorar cidades", key="ux61_find_first",
                  on_click=_open_research, args=("", ""))
        return
    q = st.text_input("Buscar nos meus destinos", key="ux61_search",
                      placeholder="Cidade ou país")
    view = st.radio("Mostrar", ("Todos", "Quero conhecer", "No roteiro", "Organizados"),
                    key="ux61_view", horizontal=True)
    visible = [r for r in rows if (not q or q.casefold() in
               (r["name"] + " " + r["country"]).casefold()) and
               (view == "Todos" or
                (view == "Quero conhecer" and r["wanted"]) or
                (view == "No roteiro" and r["planned"]) or
                (view == "Organizados" and r["organized"]))]
    limit = st.session_state.get("ux61_limit", 10)
    for row in visible[:limit]:
        with st.container(border=True):
            left, center, right = st.columns([3, 3, 2], vertical_alignment="center")
            left.markdown("**" + row["name"] + "**")
            left.caption(row["country"] or "País não informado")
            status = ("No roteiro" if row["planned"] else "Quero conhecer")
            if row["organized"]:
                status += " · Período/data definidos"
            elif row["in_group"]:
                status += " · Em grupo · Data pendente"
            elif row["planned"]:
                status += " · A organizar"
            center.caption(status)
            if not row["planned"] and row["eligibility"]["status"] != "eligible":
                center.caption(row["eligibility"]["reason"])
            if row["planned"]:
                right.button("Revisar passeio", key="ux61_review_" + row["id"],
                             on_click=_focus_visit, args=(row["id"], row["stage"]))
            else:
                right.button("Ver atrações", key="ux61_explore_" + row["id"],
                             on_click=_open_research, args=(row["id"], row["name"]))
    if len(visible) > limit:
        st.button("Mostrar mais destinos", key="ux61_show_more",
                  on_click=lambda: st.session_state.update(
                      {"ux61_limit": st.session_state.get("ux61_limit", 10) + 10}))
    st.caption(f"{min(limit, len(visible))} de {len(visible)} destinos nesta visualização.")
