"""UX 5.0.1 — browse European places before choosing a city-base.

The interest basket lives only in transient session state in this PR.
Persisted destination priorities and comparison are intentionally deferred
to UX 5.0.2 / 5.0.3, avoiding a second source of truth.
"""
from __future__ import annotations

import streamlit as st

from ux501_destination_discovery_model import (
    build_destination_discovery, filter_destinations,
)


@st.cache_data(show_spinner=False)
def _cached_discovery():
    return build_destination_discovery()


def render_independent_destination_discovery(*, discovery=None) -> None:
    discovery = discovery if discovery is not None else _cached_discovery()
    destinations = discovery["destinations"]
    by_id = {item["id"]: item for item in destinations}

    st.markdown("### O que gostaríamos de conhecer?")
    st.write(
        "Comece pelos lugares e experiências que interessam a vocês. "
        "**Não é necessário escolher uma cidade-base agora.**"
    )
    st.caption(
        "A cidade-base atual permanece no planejamento oficial como referência "
        "provisória. Esta descoberta não altera o TripPlan, não cria reservas "
        "e não confirma a viabilidade de passeios."
    )
    a, b, c = st.columns(3)
    a.metric("Destinos para descobrir", discovery["destination_count"])
    b.metric("Atrações únicas identificadas", discovery["unique_attractions_count"])
    c.metric("Países no catálogo", len(discovery["countries"]))
    st.caption(
        "Atrações provenientes do catálogo histórico e da pesquisa DQ 3.2; "
        "equivalências semânticas são contadas uma única vez. "
        "Destinos sem atrações detalhadas continuam exploráveis."
    )

    valid = list(by_id)
    selected = [key for key in st.session_state.get("ux501_interest_session", [])
                if key in by_id]
    # Do not sync to TripPlan, favorites, cloud storage or autosave.
    if "ux501_interest_session" not in st.session_state:
        st.session_state["ux501_interest_session"] = selected
    elif selected != st.session_state["ux501_interest_session"]:
        st.session_state["ux501_interest_session"] = selected

    st.multiselect(
        "Lugares que despertaram interesse nesta exploração",
        options=valid,
        format_func=lambda key: by_id[key]["name"]+" · "+by_id[key]["country"],
        key="ux501_interest_session",
        help="Seleção apenas nesta sessão; não é o roteiro oficial nem uma lista salva.",
    )
    selected = st.session_state["ux501_interest_session"]
    if selected:
        st.info(
            f"{len(selected)} lugar(es) em observação nesta sessão. "
            "A classificação e persistência dos destinos desejados serão "
            "introduzidas na etapa UX 5.0.2."
        )

    col1, col2, col3 = st.columns([2, 2, 3])
    with col1:
        country = st.selectbox(
            "País", ["Todos os países", *discovery["countries"]],
            key="ux501_country")
    with col2:
        categories = st.multiselect(
            "Experiências", discovery["categories"],
            key="ux501_categories")
    with col3:
        query = st.text_input(
            "Buscar cidade ou atração", placeholder="Ex.: Colmar, museu, catedral",
            key="ux501_search")
    matches = filter_destinations(
        discovery,
        country=None if country == "Todos os países" else country,
        categories=categories,
        query=query,
        selected=selected,
    )
    st.caption(f"{len(matches)} destino(s) encontrados — resultados do catálogo, "
               "não uma lista de viagens ferroviárias confirmadas.")
    if not matches:
        st.info("Nenhum destino corresponde aos filtros. Experimente outra busca.")
        return

    page_size = 12
    pages = (len(matches)+page_size-1)//page_size
    page = st.selectbox(
        "Página de destinos", list(range(1, pages+1)),
        key="ux501_page", format_func=lambda p: f"{p} de {pages}")
    subset = matches[(page-1)*page_size:page*page_size]
    for idx in range(0, len(subset), 3):
        columns = st.columns(3)
        for column, item in zip(columns, subset[idx:idx+3]):
            with column:
                with st.container(border=True):
                    photo = item.get("photo")
                    if photo and photo.get("url"):
                        st.image(photo["url"], use_container_width=True)
                        st.caption("Foto: "+photo["author"]+" · "+
                                   photo["license"])
                    st.markdown("**"+item["name"]+"** · "+item["country"])
                    if item["attraction_count"]:
                        names = [attr["name"] for attr in item["attractions"][:3]]
                        st.write(" · ".join(names))
                        if item["attraction_count"] > 3:
                            st.caption(
                                f"+ {item['attraction_count']-3} atrações catalogadas")
                    else:
                        st.caption(
                            "Destino conhecido; atrações individuais ainda "
                            "não cadastradas nesta pesquisa.")
                    if item["categories"]:
                        st.caption("Experiências: "+", ".join(item["categories"][:3]))
                    st.caption(
                        "Pesquisa de atrações disponível" if item["attraction_count"]
                        else "Pesquisa local a aprofundar")
                    if item.get("source_url"):
                        st.link_button("Consultar fonte turística", item["source_url"])
                    with st.expander("Ver atrações e fontes"):
                        if not item["attractions"]:
                            st.caption("Nenhuma atração individual documentada.")
                        for attraction in item["attractions"]:
                            st.markdown(
                                "- ["+attraction["name"]+"]("+
                                attraction["source_url"]+") · "+
                                attraction["category"])
                    label = ("Retirar do interesse" if item["id"] in selected
                             else "Tenho interesse")
                    if st.button(label, key="ux501_interest_"+item["id"],
                                 use_container_width=True):
                        next_selection = list(st.session_state["ux501_interest_session"])
                        if item["id"] in next_selection:
                            next_selection.remove(item["id"])
                        else:
                            next_selection.append(item["id"])
                        st.session_state["ux501_interest_session"] = next_selection
                        st.rerun()
    st.caption(
        "Acesso ferroviário, retorno de fim de semana, última milha e custo "
        "total não foram determinados por esta visualização. "
        "Continue a pesquisa de passeios por cidade-base abaixo, se desejar."
    )
