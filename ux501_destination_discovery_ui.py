"""UX 5.0.1 — browse European places before choosing a city-base.

The interest basket lives only in transient session state in this PR.
Persisted destination priorities and comparison are intentionally deferred
to UX 5.0.2 / 5.0.3, avoiding a second source of truth.
"""
from __future__ import annotations

import streamlit as st
from html import escape
from ux501_destination_photo_service import lookup_destination_photos
from destination_photo_assets import (local_destination_photo, preferred_destination_photo,
                                      display_photo_url)

from ux501_destination_discovery_model import (
    build_destination_discovery, filter_destinations,
)
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_ui import render_wishlist,add_destination
from ux_shared_ui_presentation import page_header, kpi_cards, section_heading
from data8_tourism_ui import render_data8_destination_preview



@st.cache_data(show_spinner=False)
def _cached_discovery():
    return build_exploration_discovery()




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
        url = escape(display_photo_url(photo["url"]), quote=True)
        name = escape(photo.get("subject") or destination["name"], quote=True)
        # CSS backgrounds do not produce broken-image glyphs. When the
        # resource fails, the visible placeholder remains deterministic.
        st.markdown(
            '<div role="img" aria-label="Fotografia de '+name+'" '
            'style="position:relative;width:100%;aspect-ratio:16/9;'
            'overflow:hidden;border-radius:9px;background:#e7ebe9;'
            'display:flex;align-items:center;justify-content:center;'
            'color:#586e70;text-align:center">'
            '<span>Foto indisponível no momento</span>'
            '<div aria-hidden="true" style="position:absolute;inset:0;'
            'background-size:cover;background-position:center;'
            'background-repeat:no-repeat;'
            'background-image:url(&quot;'+url+'&quot;)"></div>'
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


def _destination_rows(items: list[dict], size: int = 3) -> list[list[dict]]:
    """Return only populated destination rows, keeping the catalog order."""
    return [items[i:i+size] for i in range(0, len(items), size)]


def _destination_teaser(item: dict) -> str:
    """Concise evidence-backed card copy; never invent visit duration or routes."""
    attractions = [row["name"] for row in item.get("attractions", [])[:2]
                   if row.get("name")]
    if attractions:
        return "Destaques: " + " · ".join(attractions)
    categories = item.get("categories") or []
    if categories:
        return "Experiências: " + " · ".join(categories[:2])
    return "Conheça este destino; atrações individuais ainda não pesquisadas."


def render_independent_destination_discovery(*, discovery=None) -> None:
    discovery = discovery if discovery is not None else _cached_discovery()
    destinations = discovery["destinations"]
    by_id = {item["id"]: item for item in destinations}
    # Keep the page header ahead of filters and wishlist save tools.
    if st.session_state.get("ux502_view","Descobrir lugares")!="Minha lista":
        st.markdown(page_header(
            "Descobrir destinos", "NOSSA EUROPA 2027 · EXPLORAR",
            "Explore lugares e experiências antes de decidir a cidade-base da viagem.",
            tag="Pesquisar e escolher", variant="compact",
        ),unsafe_allow_html=True)
    show_list = render_wishlist(discovery)
    if show_list:
        return
    # Keep existing transient interests recoverable, without putting their
    # old editor ahead of the destination gallery.
    valid = list(by_id)
    selected = [key for key in st.session_state.get("ux501_interest_session", [])
                if key in by_id]
    if "ux501_interest_session" not in st.session_state or (
            st.session_state["ux501_interest_session"] != selected):
        st.session_state["ux501_interest_session"] = selected

    st.markdown(section_heading("ENCONTRE SEU DESTINO","Filtre as opções",
                                "Pesquise por país, experiência ou atração.",
                                variant="compact"),unsafe_allow_html=True)
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
                            not local_photos.get(item["id"]) and
                            item.get("research_status") != "supplemental_attractions_documented")
    fallback_photos = (_cached_visible_photos(missing_on_page)
                       if missing_on_page else {})
    for row_index, row_items in enumerate(_destination_rows(subset)):
        with st.container(key=f"ux53_row_destinations_{row_index * 3}"):
            # Avoid empty bordered cards for searches returning 1 or 2 places.
            columns = st.columns(len(row_items), border=True)
            for column, item in zip(columns, row_items):
                with column:
                    photo = preferred_destination_photo(item, fallback_photos.get(item["id"]))
                    _render_destination_media(item,photo)
                    st.markdown("**"+item["name"]+"** · "+item["country"])
                    # A short, sourced reason to explore: only catalogued
                    # attractions and categories, not invented editorial text.
                    st.caption(_destination_teaser(item))
                    saved = {r["destination_id"]: r["priority"] for r in
                             st.session_state.get("ux502_interests",{}).get("items",[])}
                    if item["id"] in saved:
                        st.caption("✓ Na minha lista")
                    else:
                        st.button("Adicionar à minha lista",
                                  key="ux502_add_"+item["id"],
                                  use_container_width=True,
                                  on_click=add_destination, args=(item["id"], discovery))
                    with st.container(key=f"ux53_footer_destination_{item['id']}"):
                        with st.expander("Ver detalhes, atrações e fontes"):
                            if photo and photo.get("subject"):
                                st.caption("Na foto: "+photo["subject"])
                            if item.get("planning_support") == "exploration_only":
                                st.info("Disponível para pesquisar e comparar; ainda não pode ser incluído no roteiro.")
                            if item["attractions"]:
                                for attraction in item["attractions"]:
                                    st.markdown("- ["+attraction["name"]+"]("+
                                                attraction["source_url"]+") · "+
                                                attraction["category"])
                            else:
                                st.caption("Atrações individuais ainda não cadastradas.")
                            if item.get("source_url"):
                                st.link_button("Consultar fonte turística",item["source_url"])
                            render_data8_destination_preview(
                                item["id"], attraction_names={
                                    a["id"]:a["name"] for a in item["attractions"]})

    with st.expander("Pesquisa do catálogo e seleção anterior · avançado", expanded=False):
        st.caption("Os destinos ainda não representam reservas nem trajetos "
                   "ou custos confirmados para 2027.")
        cards = kpi_cards([
            {"name":"Destinos","value":discovery["destination_count"],"icon":"◎",
             "hint":"Catálogo de pesquisa"},
            {"name":"Atrações","value":discovery["unique_attractions_count"],
             "icon":"◇","hint":"Sem duplicatas semânticas"},
            {"name":"Países","value":len(discovery["countries"]),
             "icon":"◉","hint":"Locais pesquisados"},
        ])
        with st.container(key="ux82_discovery_metrics"):
            for column,markup in zip(st.columns(3,gap="small"),cards):
                column.markdown(markup,unsafe_allow_html=True)
        st.caption("Seleções temporárias anteriores não são a wishlist salva. "
                   "Você pode reconciliá-las em Minha lista sem perder os dados.")
        st.multiselect(
            "Lugares que despertaram interesse nesta exploração",
            options=valid,
            format_func=lambda key: by_id[key]["name"]+" · "+by_id[key]["country"],
            key="ux501_interest_session",
            help="Somente nesta sessão. Não altera o roteiro oficial.",
        )

