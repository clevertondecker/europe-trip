"""UX132C1: attraction documentary coverage, with no planning writes."""
import logging
from time import perf_counter
import streamlit as st

from ux132c1_attraction_coverage_model import (
    build_attraction_view, indicator_rows, filter_destinations, detail_rows,
    attraction_gaps, gap_count, GAP_OPTIONS, SORT_OPTIONS,
)
from ux_widget_state import widget_state

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


def render_attraction_indicators(counts, *, compact=False):
    if compact:
        # Same canonical counts; no additional projection or composite score.
        for metric in indicator_rows(counts):
            if metric["key"] in ("destinations_with_attractions", "ticket_published",
                                  "ticket_not_applicable", "ticket_unknown"):
                continue
            st.caption(metric["label"] + " · " + _ratio(metric["documented"], metric["total"]))
            if metric["fraction"] is not None:
                st.progress(metric["fraction"])
        st.caption(f'Ingressos: {counts["ticket_published"]} com preço publicado · '
                   f'{counts["ticket_not_applicable"]} não aplicáveis · '
                   f'{counts["ticket_unknown"]} desconhecidos / {counts["attractions"]} atrações.')
        st.caption("Horários de abertura: não medidos. Consulte Atrações turísticas para ver pendências por destino.")
        return
    table = []
    for metric in indicator_rows(counts):
        if metric["key"] == "destinations_with_attractions":
            # Already shown as the destination count in the overview card.
            continue
        table.append({
            "Indicador": metric["label"],
            "Quantidade / total": _ratio(metric["documented"], metric["total"]),
            "Percentual": metric["fraction"] * 100 if metric["fraction"] is not None else None,
            "Pendências": (
                None if not metric["total"]
                else counts["ticket_unknown"] if metric["key"] == "ticket_published"
                else None if metric["key"] in ("ticket_not_applicable", "ticket_unknown")
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
        "Pendências do destino": gap_count(r, "catalog") + gap_count(r, "context_photo"),
        "Campos de atrações pendentes": (
            gap_count(r, "all") - gap_count(r, "catalog") - gap_count(r, "context_photo")
            if c["attractions"] else None),
        **({"Pendências no filtro": gap_count(r, gap)} if gap != "all" else {}),
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
    for field, record in row.get("field_records", {}).items():
        if record and record["record_id"] != row["id"]:
            st.caption(f'Registro complementar ({field}): {record["record_id"]} · '
                       f'data do registro: {record["record_date"] or "não informada"}')
            for index, url in enumerate(record["record_sources"], 1):
                _link(f"Registro complementar {field} {index}", url)
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
                              **widget_state("ux132c1_search", "", lambda v: isinstance(v, str)))
    gap_label = cols[1].selectbox("Campo de pesquisa", list(GAP_OPTIONS),
                                  **widget_state("ux132c1_gap", next(iter(GAP_OPTIONS)), lambda v: v in GAP_OPTIONS))
    order = cols[2].selectbox("Ordenar por", SORT_OPTIONS,
                             **widget_state("ux132c1_sort", SORT_OPTIONS[0], lambda v: v in SORT_OPTIONS))
    gaps_only = st.checkbox("Somente destinos com pendências",
                            **widget_state("ux132c1_only_gaps", False, lambda v: isinstance(v, bool)))
    gap = GAP_OPTIONS[gap_label]
    rows = filter_destinations(view, query=query, gap=gap, gaps_only=gaps_only, sort=order)
    st.caption(f'{len(rows)} de {len(view["destinations"])} destinos. Pendências são campos de pesquisa, não nota de qualidade.')
    if not rows:
        st.info("Nenhum destino corresponde aos filtros.")
        return
    st.dataframe(_destination_table(rows, gap), hide_index=True, width="stretch", key="ux132c1_destinations")
    names = {r["id"]: r["name"] for r in rows}
    chosen = st.selectbox("Destino para detalhar", list(names), format_func=names.__getitem__,
                          **widget_state("ux132c1_destination", next(iter(names)), lambda v: v in names))
    dest = next(r for r in rows if r["id"] == chosen)
    c = dest["counts"]
    with st.container(border=True):
        st.markdown(f'#### {dest["name"]}')
        a, b = st.columns(2)
        a.metric("Atrações catalogadas", c["attractions"])
        b.metric("Campos de atrações pendentes", gap_count(dest, "all") -
                 gap_count(dest, "catalog") - gap_count(dest, "context_photo") if c["attractions"] else "N/A")
        st.caption(f'Pendências do destino: {gap_count(dest, "catalog") + gap_count(dest, "context_photo")}.')
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
                                   **widget_state("ux132c1_attraction", next(iter(attr_names)), lambda v: v in attr_names))
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
    _render_destinations(view)
