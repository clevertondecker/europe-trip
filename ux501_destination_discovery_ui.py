"""UX 5.0.1 — browse European places before choosing a city-base.

The interest basket lives only in transient session state in this PR.
Persisted destination priorities and comparison are intentionally deferred
to UX 5.0.2 / 5.0.3, avoiding a second source of truth.
"""
from __future__ import annotations

import streamlit as st
from html import escape
from ux501_destination_photo_service import lookup_destination_photos
from destination_photo_assets import local_destination_photo, preferred_destination_photo

from ux501_destination_discovery_model import (
    build_destination_discovery, filter_destinations,
)
from ux502_destination_interests_ui import render_wishlist,add_destination
from data8_tourism_ui import render_data8_destination_preview



@st.cache_data(show_spinner=False)
def _cached_discovery():
    return build_destination_discovery()




@st.cache_data(ttl=21600, show_spinner=False)
def _cached_visible_photos(identity: tuple[tuple[str, str], ...]) -> dict:
    # Fetch only the current page, once per cache TTL. No catalog writes.
    return lookup_destination_photos(
        [{"id":destination_id,"name":name} for destination_id,name in identity])


def _render_destination_media(destination: dict, photo: dict | None) -> None:
    """Same size for every card, licensed provenance or honest fallback."""
    if photo and photo.get("local_path"):
        st.image(photo["local_path"], caption=None, use_container_width=True)
        author = escape(photo["author"])
        license_label = escape(photo["license"])
        source = escape(photo["source_page"], quote=True)
        license_url = escape(photo["license_url"], quote=True)
        st.markdown(
            '<div style="font-size:0.75rem;opacity:0.78;margin-top:5px">'
            f'Foto: {author} · <a href="{license_url}" target="_blank" '
            f'rel="noopener noreferrer">{license_label}</a> · '
            f'<a href="{source}" target="_blank" rel="noopener noreferrer">'
            'Fonte original</a> · recortada para 16:9</div>',
            unsafe_allow_html=True)
        return
    if photo and photo.get("url"):
        url = escape(photo["url"], quote=True)
        name = escape(destination["name"], quote=True)
        st.markdown(
            '<div style="width:100%;aspect-ratio:16/9;overflow:hidden;'
            'border-radius:9px;background:#e7ebe9">'
            f'<img src="{url}" alt="Fotografia de {name}" loading="lazy" '
            'style="width:100%;height:100%;object-fit:cover;display:block">'
            '</div>',unsafe_allow_html=True)
        author = escape(photo.get("author") or "Autor não identificado")
        license_label = escape(photo.get("license") or "Licença não identificada")
        source_page = photo.get("source_page", "")
        if source_page.startswith("https://commons.wikimedia.org/"):
            st.markdown(
                '<div style="font-size:0.75rem;opacity:0.78;margin-top:5px">'
                f'Foto: {author} · {license_label} · '
                f'<a href="{escape(source_page,quote=True)}" target="_blank" '
                'rel="noopener noreferrer">Fonte e licença</a></div>',
                unsafe_allow_html=True)
        else:
            st.caption(f"Foto: {author} · {license_label}")
    else:
        name = escape(destination["name"])
        st.markdown(
            '<div role="img" aria-label="Foto deste destino ainda não disponível" '
            'style="aspect-ratio:16/9;border-radius:9px;background:#eef2ef;'
            'border:1px solid #dce5e1;display:flex;flex-direction:column;'
            'align-items:center;justify-content:center;text-align:center;'
            'padding:12px;color:#586e70">'
            '<span style="font-size:1.8rem" aria-hidden="true">⌖</span>'
            f'<span style="font-weight:600">{name}</span>'
            '<small>Foto a pesquisar</small></div>',unsafe_allow_html=True)


def render_independent_destination_discovery(*, discovery=None) -> None:
    discovery = discovery if discovery is not None else _cached_discovery()
    destinations = discovery["destinations"]
    by_id = {item["id"]: item for item in destinations}
    show_list = render_wishlist(discovery)
    if show_list:
        return

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

    st.caption("A seleção temporária da versão anterior pode ser incorporada "
               "explicitamente em Minha lista; ela não é salva automaticamente.")
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
    if st.session_state.get("ux501_page") not in range(1, pages+1):
        st.session_state["ux501_page"] = 1
    page = st.selectbox(
        "Página de destinos", list(range(1, pages+1)),
        key="ux501_page", format_func=lambda p: f"{p} de {pages}")
    subset = matches[(page-1)*page_size:page*page_size]
    # Bundled images require no HTTP request. Query Wikimedia only when
    # neither editorial nor local files cover a destination on this page.
    local_photos = {item["id"]: local_destination_photo(item["id"])
                    for item in subset if not item.get("photo")}
    missing_on_page = tuple((item["id"],item["name"]) for item in subset
                            if not item.get("photo") and
                            not local_photos.get(item["id"]))
    fallback_photos = (_cached_visible_photos(missing_on_page)
                       if missing_on_page else {})
    for idx in range(0, len(subset), 3):
        with st.container(key=f"ux53_row_destinations_{idx}"):
            columns = st.columns(3, border=True)
            for column, item in zip(columns, subset[idx:idx+3]):
                with column:
                    photo = preferred_destination_photo(item, fallback_photos.get(item["id"]))
                    _render_destination_media(item,photo)
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
                    with st.container(key=f"ux53_footer_destination_{item['id']}"):
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
                            render_data8_destination_preview(
                                item["id"], attraction_names={
                                    a["id"]: a["name"] for a in item["attractions"]})
                        saved = {r["destination_id"]: r["priority"] for r in
                                 st.session_state.get("ux502_interests",{}).get("items",[])}
                        if item["id"] in saved:
                            st.caption("Na minha lista: " + saved[item["id"]].replace("_"," "))
                        else:
                            st.button("Adicionar à minha lista",
                                      key="ux502_add_"+item["id"],
                                      use_container_width=True,
                                      on_click=add_destination, args=(item["id"], discovery))

    st.caption(
        "Acesso ferroviário, retorno de fim de semana, última milha e custo "
        "total não foram determinados por esta visualização. "
        "Continue a pesquisa de passeios por cidade-base abaixo, se desejar."
    )
