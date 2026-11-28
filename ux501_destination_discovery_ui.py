"""UX 5.0.1 — browse European places before choosing a city-base.

The interest basket lives only in transient session state in this PR.
Persisted destination priorities and comparison are intentionally deferred
to UX 5.0.2 / 5.0.3, avoiding a second source of truth.
"""
from __future__ import annotations

import streamlit as st
from html import escape
from ux501_destination_photo_service import lookup_destination_photos, curated_destination_photo
from destination_photo_assets import (local_destination_photo, preferred_destination_photo,
                                      display_photo_url)

from ux501_destination_discovery_model import (
    build_destination_discovery, filter_destinations,
)
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_ui import render_wishlist,add_destination
from ux_shared_ui_presentation import page_header, section_heading
from data8_tourism_ui import render_data8_destination_preview



@st.cache_data(show_spinner=False)
def _cached_discovery():
    return build_exploration_discovery()




from time import monotonic
from commons_client import NEGATIVE_TTL

_visible_photo_cache = {}

def _cached_visible_photos(identity: tuple[tuple[str, str], ...]) -> dict:
    now = monotonic()
    pending = [(i, n) for i, n in identity
               if (i, n) not in _visible_photo_cache or _visible_photo_cache[i, n][1] <= now]
    if pending:
        found = lookup_destination_photos([{"id": i, "name": n} for i, n in pending])
        for i, n in pending:
            result = found.get(i)
            _visible_photo_cache[i, n] = (result, float("inf") if result else monotonic() + NEGATIVE_TTL)
    return {i: _visible_photo_cache[i, n][0] for i, n in identity
            if _visible_photo_cache[i, n][0] is not None}


def _render_destination_media(destination: dict, photo: dict | None) -> None:
    """Same size for every card, licensed provenance or honest fallback."""
    if photo and photo.get("local_path"):
        st.image(photo["local_path"], caption=None, width="stretch")
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
    resolved_url = display_photo_url(photo["url"]) if photo and photo.get("url") else None
    if resolved_url:
        url = escape(resolved_url, quote=True)
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


def _destination_wishlist_state(interests: dict | None, destination_id: str) -> str:
    """Read the existing UX502 priority without treating discarded as active."""
    for row in (interests or {}).get("items", []):
        from destination_identity import canonical_destination_id
        if canonical_destination_id(row["destination_id"]) == canonical_destination_id(destination_id):
            return "discarded" if row["priority"] == "discarded" else "saved"
    return "new"


def _result_caption(matches):
    n=len(matches)
    return "Nenhum destino" if not n else "1 destino" if n==1 else f"{n} destinos"


_FILTER_DEFAULTS = {"ux501_country": "Todos os países", "ux501_categories": [],
                    "ux501_search": "", "ux501_page": 1}


def _remember_filters():
    state = st.session_state
    saved=state.get("ux502_discovery_filters", {})
    snapshot = {key:saved.get(key,value) for key,value in _FILTER_DEFAULTS.items()}
    state.pop("ux126_eligibility_filter",None)
    for key in _FILTER_DEFAULTS:
        if key != "ux501_page" and key in state:
            snapshot[key] = state[key]
    snapshot["ux501_page"] = 1
    state["ux502_discovery_filters"] = snapshot
    state["ux501_page"] = 1


def _turn_page(delta):
    state = st.session_state
    snapshot = dict(state["ux502_discovery_filters"])
    snapshot["ux501_page"] += delta
    state["ux502_discovery_filters"] = snapshot
    state["ux501_page"] = snapshot["ux501_page"]


def _render_pagination(page, pages, *, bottom=False):
    if pages <= 1:
        return
    suffix = "_bottom" if bottom else ""
    prev, label, nxt = st.columns([1, 2, 1])
    prev.button("Anterior", key="ux126b_previous"+suffix, disabled=page == 1,
                on_click=_turn_page, args=(-1,))
    label.caption(f"Página {page} de {pages}")
    nxt.button("Próxima", key="ux126b_next"+suffix, disabled=page == pages,
               on_click=_turn_page, args=(1,))


def _restore_filters(discovery):
    state = st.session_state
    saved=state.get("ux502_discovery_filters", {})
    snapshot = {key:saved.get(key,value) for key,value in _FILTER_DEFAULTS.items()}
    state.pop("ux126_eligibility_filter",None)
    # Explicit navigation and filter callbacks update the stable snapshot.
    # Widget keys may be stale after a handoff; bootstrap them only once.
    if "ux502_discovery_filters" not in state:
        snapshot.update({key: state[key] for key in _FILTER_DEFAULTS if key in state})
    if snapshot["ux501_country"] not in ["Todos os países", *discovery["countries"]]:
        snapshot["ux501_country"] = "Todos os países"
        snapshot["ux501_page"] = 1
    snapshot["ux501_categories"] = [x for x in snapshot["ux501_categories"] if x in discovery["categories"]]
    for key in _FILTER_DEFAULTS:
        if key != "ux501_page":
            state[key] = snapshot[key]
    state["ux502_discovery_filters"] = snapshot
    return snapshot


def render_independent_destination_discovery(*, discovery=None, focused_destination=None) -> None:
    discovery = discovery if discovery is not None else _cached_discovery()
    from attractions_model import load_attractions
    from itinerary_eligibility import itinerary_eligibility, eligibility_index, availability_label
    from destination_identity import canonical_destination_id
    from planning_session import active_plan
    catalog = load_attractions()
    destinations = discovery["destinations"]
    index = eligibility_index(catalog)
    eligibility = {item["id"]: itinerary_eligibility(item["id"], catalog, index=index) for item in destinations}
    by_id = {item["id"]: item for item in destinations}
    focused = by_id.get(canonical_destination_id(focused_destination)) if isinstance(focused_destination, str) and focused_destination.strip() else None
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
    selected = [key for key in st.session_state.get("ux501_interest_session", [])
                if key in by_id]
    if "ux501_interest_session" not in st.session_state or (
            st.session_state["ux501_interest_session"] != selected):
        st.session_state["ux501_interest_session"] = selected

    if focused is not None:
        st.caption("Destino escolhido na ficha da cidade-base: "+focused["name"])
        subset = [focused]
    else:
        snapshot = _restore_filters(discovery)
        st.markdown(section_heading("ENCONTRE SEU DESTINO","Filtre as opções",
                                    "Pesquise por país, experiência ou atração.",
                                    variant="compact"),unsafe_allow_html=True)
        col1, col2, col3 = st.columns([2, 2, 3])
        with col1:
            country = st.selectbox(
                "País", ["Todos os países", *discovery["countries"]],
                key="ux501_country", on_change=_remember_filters)
        with col2:
            categories = st.multiselect(
                "Experiências", discovery["categories"],
                key="ux501_categories", placeholder="Escolha uma ou mais experiências", on_change=_remember_filters)
        with col3:
            query = st.text_input(
                "Buscar cidade ou atração", placeholder="Ex.: Colmar, museu, catedral",
                key="ux501_search", on_change=_remember_filters)
        matches = filter_destinations(
            discovery,
            country=None if country == "Todos os países" else country,
            categories=categories,
            query=query,
            selected=selected,
        )
        st.caption(_result_caption(matches))
        st.caption("Resultados do catálogo; não é uma lista de viagens ferroviárias confirmadas.")
        page_size = 12
        pages = max(1, (len(matches)+page_size-1)//page_size)
        page = snapshot["ux501_page"]
        if not isinstance(page, int) or not 1 <= page <= pages:
            page = 1
        snapshot["ux501_page"] = page
        st.session_state["ux502_discovery_filters"] = snapshot
        st.session_state["ux501_page"] = page
        if not matches:
            st.info("Nenhum destino corresponde aos filtros. Experimente outra busca.")
            return
        _render_pagination(page, pages)
        subset = matches[(page-1)*page_size:page*page_size]
    plan = active_plan()
    # Bundled images require no HTTP request. Query Wikimedia only when
    # neither editorial nor local files cover a destination on this page.
    local_photos = {item["id"]: local_destination_photo(item["id"])
                    for item in subset if not item.get("photo")}
    missing_on_page = tuple((item["id"],item["name"]) for item in subset
                            if not item.get("photo") and
                            not local_photos.get(item["id"]) and
                            not curated_destination_photo(item["id"]) and
                            item.get("research_status") != "supplemental_attractions_documented")
    fallback_photos = (_cached_visible_photos(missing_on_page)
                       if missing_on_page else {})
    for row_index, row_items in enumerate(_destination_rows(subset)):
        with st.container(key=f"ux53_row_destinations_{row_index * 3}"):
            # Avoid empty bordered cards for searches returning 1 or 2 places.
            columns = st.columns(len(row_items), border=True)
            for column, item in zip(columns, row_items):
                with column:
                    photo = preferred_destination_photo(item, curated_destination_photo(item["id"]) or fallback_photos.get(item["id"]))
                    _render_destination_media(item,photo)
                    st.markdown("**"+item["name"]+"** · "+item["country"])
                    # A short, sourced reason to explore: only catalogued
                    # attractions and categories, not invented editorial text.
                    st.caption(_destination_teaser(item))
                    st.caption(availability_label(eligibility[item["id"]], plan))
                    state = _destination_wishlist_state(
                        st.session_state.get("ux502_interests"), item["id"])
                    if state == "saved":
                        st.caption("✓ Na minha lista")
                    elif state == "discarded":
                        st.caption("Destino descartado anteriormente")
                        st.button("Reconsiderar destino",
                                  key="ux502_restore_"+item["id"], type="primary",
                                  width="stretch",
                                  on_click=add_destination, args=(item["id"], discovery))
                    else:
                        st.button("Quero conhecer",
                                  key="ux502_add_"+item["id"], type="primary",
                                  width="stretch",
                                  on_click=add_destination, args=(item["id"], discovery))
                    with st.container(key=f"ux53_footer_destination_{item['id']}"):
                        with st.expander("Ver atrações e fontes · detalhes", expanded=focused is not None):
                            if photo and photo.get("subject"):
                                st.caption("Na foto: "+photo["subject"])
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
    if focused is None:
        _render_pagination(page, pages, bottom=True)
