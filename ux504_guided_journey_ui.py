"""UX 5.0.4 — compact, coherent journey UI using existing navigation."""
from __future__ import annotations

import streamlit as st
from ux504_guided_journey_model import project_journey, navigation_request


def request_step(step_id: str) -> None:
    """Queue only; widget keys are updated by app.py before sidebar renders."""
    # Preserve ephemeral discovery inputs before their widgets unmount.
    # Streamlit removes widget-owned session keys when switching pages.
    if st.session_state.get("ux502_view") == "Descobrir lugares":
        keys = ("ux501_country","ux501_categories","ux501_search","ux501_page")
        snapshot = dict(st.session_state.get("ux502_discovery_filters", {}))
        snapshot.update({key:st.session_state[key] for key in keys
                         if key in st.session_state})
        st.session_state["ux502_discovery_filters"] = snapshot
    st.session_state["_ux504_navigation_request"] = navigation_request(step_id)


def render_guided_home(plan: dict, interests: dict | None = None) -> None:
    view = project_journey(plan, interests)
    st.markdown("## Vamos planejar nossa viagem")
    st.caption("Dos lugares que queremos conhecer até nosso roteiro na Europa.")
    st.markdown("#### Próxima ação útil")
    st.button(view["next"]["label"] + " →", type="primary",
              key="ux504_next_step", on_click=request_step,
              args=(view["next"]["id"],))
    for alternative in view["alternatives"]:
        st.button(alternative["label"] + " →",
                  key="ux504_next_alternative_"+alternative["id"],
                  on_click=request_step,args=(alternative["id"],))
    if isinstance(interests,dict) and any(isinstance(x,dict) and x.get("priority")!="discarded"
            for x in interests.get("items",[])):
        from rec03a_session import request_navigation
        st.button("Encontrar cidades-base para minha lista",key="rec03a_handoff_home",
                  on_click=request_navigation,args=(st.session_state,"suggestions"))
    st.caption("A base oficial permanece como referência de trabalho; "
               "comparar alternativas não significa decidir onde morar.")
    st.markdown("#### Nosso caminho")
    for idx, step in enumerate(view["steps"], start=1):
        with st.container(border=True):
            title, action = st.columns([3, 1])
            with title:
                st.markdown(f"**{idx}. {step['title']}**")
                st.caption(step["description"])
                st.write(step["status"])
            with action:
                st.button("Abrir",key="ux504_step_"+step["id"],
                          on_click=request_step,args=(step["id"],),
                          use_container_width=True)
    st.caption("Esta jornada apresenta o que já registramos; não indica reservas, "
               "comparação concluída ou custos verificados.")


def render_contextual_shortcuts(place: str) -> None:
    """Use secondary actions without creating another router or persistence."""
    if place == "discovery":
        st.button("Abrir Minha lista →",key="ux504_discovery_to_wishlist",
                  on_click=request_step,args=("wishlist",))
    elif place == "comparison":
        st.button("Continuar para Montar roteiro →",
                  key="ux504_compare_to_itinerary",on_click=request_step,
                  args=("itinerary",))
    elif place == "itinerary":
        left,right = st.columns(2)
        with left:
            st.button("Organizar datas →",key="ux504_itinerary_to_dates",
                      on_click=request_dates)
        with right:
            st.button("Revisar orçamento →",key="ux504_itinerary_to_budget",
                      on_click=request_step,args=("budget",))


def request_dates() -> None:
    st.session_state["_ux504_navigation_request"] = {
        "area":"Meu roteiro","section":"Organizar viagem","view":None,
    }
