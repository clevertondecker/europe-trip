"""UX132C1: attraction documentary coverage, with no planning writes."""
import logging
from time import perf_counter
import streamlit as st

from ux132c1_attraction_coverage_model import (
    build_attraction_view, indicator_rows, filter_destinations, detail_rows,
    attraction_gaps, gap_count, GAP_OPTIONS, SORT_OPTIONS,
)
from ux132_research_coverage_ui import _widget_state

_LOG = logging.getLogger(__name__)
GAP_LABELS = {key: label for label, key in GAP_OPTIONS.items()}


def _load(discovery):
    start = perf_counter()
    view = build_attraction_view(discovery=discovery)
    _LOG.debug("UX132C1 attraction projection: %.3fs", perf_counter() - start)
    return view


def _ratio(value, total):
    return f"{value}/{total}" if total else "N/A (0/0)"


def _link(label, url):
    if isinstance(url, str) and url.startswith("https://"):
        st.link_button(label, url)
    else:
        st.caption(label + ": fonte específica não documentada.")


def render_attraction_overview_summary(discovery=None):
    """Compact cross-domain overview; isolate a failure from the rail screen."""
    try:
        view = _load(discovery)
    except Exception:
        _LOG.exception("UX132C1 attraction summary unavailable")
        st.warning("Cobertura de atrações temporariamente indisponível.")
        return
    c = view["counts"]
    st.markdown("#### Atrações turísticas")
    st.write(f'{_ratio(c["destinations_with_attractions"], c["destinations"])} destinos '
             f'com atrações catalogadas · {c["attractions"]} atrações únicas.')
    st.caption("Selecione Atrações turísticas para consultar cobertura por campo e pendências.")


def _render_indicators(counts):
    table = []
    for metric in indicator_rows(counts):
        table.append({
            "Indicador": metric["label"],
            "Documentado / total": _ratio(metric["documented"], metric["total"]),
            "Percentual": metric["fraction"] * 100 if metric["fraction"] is not None else None,
            "Pendências": (
                counts["ticket_unknown"] if metric["key"] == "ticket_published"
                else None if metric["key"] in ("ticket_not_applicable", "ticket_unknown") or not metric["total"]
                else metric["total"] - metric["documented"]
            ),
        })
    st.dataframe(table, hide_index=True, width="stretch",
                 column_config={"Percentual": st.column_config.ProgressColumn(
                     "Percentual", min_value=0, max_value=100, format="%.1f%%")},
                 key="ux132c1_indicators")
    st.caption("Denominadores: destinos do catálogo ou atrações únicas, conforme o indicador. "
               "Ingresso publicado, não aplicável e desconhecido são estados distintos. "
               "N/A indica denominador zero. Horários de abertura: não medidos pelo inventário atual.")


def _destination_table(rows, gap):
    return [{
        "Destino": r["name"],
        "Atrações": c["attractions"],
        "Foto contextual": "Atribuída" if c["destinations_with_attributed_photo"] else "Não documentada",
        "Descrição": _ratio(c["described"], c["attractions"]),
        "Duração editorial": _ratio(c["editorial_duration"], c["attractions"]),
        "Ingresso desconhecido": c["ticket_unknown"] if c["attractions"] else None,
        "Foto própria": _ratio(c["attraction_photo_attributed"], c["attractions"]),
        "Acesso de estação": _ratio(c["station_access_documented"], c["attractions"]),
        "Pendências no filtro": gap_count(r, gap),
    } for r in rows for c in (r["counts"],)]


def _ticket_label(row):
    status = row["ticket_status"]
    if status == "operator_published":
        t = row["ticket"]
        return f'{t["amount"]} {t["currency"]} / {t["per"]}'
    if status == "not_applicable":
        return "Não aplicável"
    return "Desconhecido"


def _photo_detail(photo):
    st.write(f'Autor: {photo["author"]} · Licença: {photo["license"]}')
    _link("Página da fotografia", photo["source_page"])
    _link("Licença da fotografia", photo["license_url"])
    st.caption("Atribuição registrada; disponibilidade online não verificada.")


def _render_source_detail(row):
    st.markdown("**Registro geral da atração**")
    _link("Fonte geral", row["source_url"])
    st.caption("Data do registro geral: " + str(row["checked_at"] or "Não informada")
               + ". Não é necessariamente a data de cada campo.")
    if row["description"]:
        st.write(row["description"])
    if row["editorial_duration_min"] is not None:
        st.caption(f'Duração editorial: {row["editorial_duration_min"]} min (estimativa, não verificada).')
    st.markdown("**Ingresso**")
    st.write(_ticket_label(row))
    ticket = row["ticket"]
    if ticket.get("validity"):
        st.caption(str(ticket["validity"]))
    if ticket.get("notes"):
        st.caption(str(ticket["notes"]))
    if row["ticket_status"] == "operator_published":
        _link("Fonte específica do ingresso", ticket.get("source_url"))
        if ticket.get("checked_at"):
            st.caption("Consulta do ingresso: " + str(ticket["checked_at"]))
    if row["ticket_status"] == "not_applicable":
        st.caption("Não aplicável não confirma gratuidade de todos os acessos.")
    if row["photo_attributed"]:
        st.markdown("**Foto própria da atração**")
        _photo_detail(row["photo"])
    if row["station_access"]:
        st.markdown("**Acesso a partir de estação**")
        st.dataframe([{
            "Estação (ID)": a["origin_id"], "Duração (min)": a["duration_min"],
            "Registro": a.get("status"), "Data": a.get("checked_at"),
            "Fonte": a.get("source_url"), "Observação": a.get("notes"),
        } for a in row["station_access"]], hide_index=True, width="stretch",
            column_config={"Fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir fonte")},
            key="ux132c1_access")
        st.caption("Trecho documentado; não confirma deslocamento porta a porta.")
    if row["additional_sources"]:
        st.markdown("**Referências adicionais do catálogo**")
        for index, source in enumerate(row["additional_sources"], 1):
            url = source if isinstance(source, str) else source.get("source_url") if isinstance(source, dict) else None
            if isinstance(url, str) and url.startswith("https://"):
                st.link_button(f"Referência adicional {index}", url)


def _render_destinations(view):
    cols = st.columns(3)
    query = cols[0].text_input("Pesquisar destino", placeholder="Ex.: Colmar",
                              **_widget_state("ux132c1_search", "", lambda v: isinstance(v, str)))
    gap_label = cols[1].selectbox("Campo de pesquisa", list(GAP_OPTIONS),
                                  **_widget_state("ux132c1_gap", next(iter(GAP_OPTIONS)), lambda v: v in GAP_OPTIONS))
    order = cols[2].selectbox("Ordenar por", SORT_OPTIONS,
                             **_widget_state("ux132c1_sort", SORT_OPTIONS[0], lambda v: v in SORT_OPTIONS))
    gaps_only = st.checkbox("Somente destinos com pendências",
                            **_widget_state("ux132c1_only_gaps", False, lambda v: isinstance(v, bool)))
    gap = GAP_OPTIONS[gap_label]
    rows = filter_destinations(view, query=query, gap=gap, gaps_only=gaps_only, sort=order)
    st.caption(f'{len(rows)} de {len(view["destinations"])} destinos. Pendências são campos de pesquisa, não nota de qualidade.')
    if not rows:
        st.info("Nenhum destino corresponde aos filtros.")
        return
    st.dataframe(_destination_table(rows, gap), hide_index=True, width="stretch", key="ux132c1_destinations")
    names = {r["id"]: r["name"] for r in rows}
    chosen = st.selectbox("Destino para detalhar", list(names), format_func=names.__getitem__,
                          **_widget_state("ux132c1_destination", next(iter(names)), lambda v: v in names))
    dest = next(r for r in rows if r["id"] == chosen)
    c = dest["counts"]
    with st.container(border=True):
        st.markdown(f'#### {dest["name"]}')
        a, b = st.columns(2)
        a.metric("Atrações catalogadas", c["attractions"])
        b.metric("Pendências no filtro", gap_count(dest, gap))
        st.caption("Foto contextual: " + ("atribuição documentada" if dest["destination"]["photo_attributed"] else "não documentada"))
        if dest["destination"]["photo_attributed"]:
            with st.expander("Fonte e licença da foto contextual"):
                _photo_detail(dest["destination"]["photo"])
        if not c["attractions"]:
            st.info("Nenhuma atração catalogada para este destino. Isso não significa ausência de atrações; indicadores por atração são N/A.")
            return
        attrs = detail_rows(dest, gap=gap, gaps_only=gaps_only)
        if not attrs:
            st.info("Nenhuma atração com a pendência selecionada.")
            return
        st.dataframe([{
            "Atração": r["name"], "Ingresso": _ticket_label(r),
            "Duração editorial": f'{r["editorial_duration_min"]} min' if r["editorial_duration_min"] is not None else None,
            "Pendências": " · ".join(GAP_LABELS[g] for g in attraction_gaps(r)) or "Nenhuma neste inventário",
        } for r in attrs], hide_index=True, width="stretch", key="ux132c1_attractions")
        with st.expander("Consultar fontes e ressalvas"):
            attr_names = {r["id"]: r["name"] for r in attrs}
            attr_id = st.selectbox("Atração", list(attr_names), format_func=attr_names.__getitem__,
                                   **_widget_state("ux132c1_attraction", next(iter(attr_names)), lambda v: v in attr_names))
            _render_source_detail(next(r for r in attrs if r["id"] == attr_id))


def render_attraction_coverage(*, discovery=None):
    try:
        view = _load(discovery)
    except Exception:
        _LOG.exception("UX132C1 attraction coverage unavailable")
        st.error("Não foi possível carregar a cobertura de atrações. Seu roteiro permanece intacto.")
        return
    counts = view["counts"]
    a, b, c = st.columns(3)
    a.metric("Destinos no catálogo", counts["destinations"])
    b.metric("Atrações únicas", counts["attractions"])
    c.metric("Destinos com atrações", _ratio(counts["destinations_with_attractions"], counts["destinations"]))
    st.info("Cobertura documental mede registros disponíveis, não qualidade turística ou viabilidade de 2027.")
    sections = ("Visão geral", "Destinos")
    section = st.segmented_control("Detalhamento das atrações", sections,
                                   **_widget_state("ux132c1_section", sections[0], lambda v: v in sections)) or sections[0]
    if section == "Visão geral":
        _render_indicators(counts)
    else:
        _render_destinations(view)
