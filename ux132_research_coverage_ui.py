"""UX132: documentary coverage without itinerary or wishlist dependencies."""
import logging
from time import perf_counter
import streamlit as st

from ux132_research_coverage_model import (
    build_coverage_view, connection_rows, filter_coverage_rows,
    SORT_OPTIONS, STATUS_OPTIONS,
)
from rail_reference_projection_model import format_minutes
from ux_shared_ui_presentation import section_heading
from rec03a_suggestions_ui import _restore_widget, _remember

_LOG = logging.getLogger(__name__)


def _pct(counts):
    value = counts["fraction"]
    return "Não aplicável" if value is None else f"{value:.1%}".replace(".", ",")


def _table(rows):
    return [{
        "Cidade": r["name"],
        "Cobertura": r["fraction"] * 100 if r["fraction"] is not None else None,
        "Com tempo": r["timed"],
        "Elegíveis": r["eligible"],
        "Históricos": r["historical"],
        "Indicativos": r["indicative"],
        "Locais": r["local"],
        "Sem tempo": r["missing"],
    } for r in rows]


def _widget_state(key, default, valid):
    """Keep ephemeral coverage filters when Streamlit removes hidden widgets."""
    shadow = key + "_shadow"
    _restore_widget(key, shadow, default, valid)
    return {"key": key, "on_change": _remember, "args": (key, shadow)}


def render_research_coverage(*, discovery=None, research=None):
    st.markdown(section_heading(
        "COBERTURA DOCUMENTAL", "Cobertura dos dados",
        "Acompanhe os dados documentados e as lacunas de pesquisa.",
        variant="compact",
    ), unsafe_allow_html=True)
    try:
        started = perf_counter()
        view = build_coverage_view(discovery=discovery, research=research)
        _LOG.debug("UX132 coverage projection: %.3fs", perf_counter() - started)
    except Exception:
        _LOG.exception("UX132 coverage unavailable")
        st.error("Não foi possível carregar a cobertura. Seu roteiro e suas escolhas permanecem intactos.")
        return

    counts = view["global"]
    cols = st.columns(4)
    cols[0].metric("Cidades-base", view["base_count"])
    cols[1].metric("Destinos no catálogo", view["destination_count"])
    cols[2].metric("Conexões com tempo", f'{counts["timed"]}/{counts["eligible"]}')
    cols[3].metric("Cobertura ferroviária", _pct(counts))
    st.caption("Universo global: pares dirigidos. Pares locais ficam fora do denominador.")
    st.info("Cobertura documental mede disponibilidade de referências, não viabilidade logística. "
            "Retorno, última milha e horários de 2027 não estão confirmados.")
    priority = view["priority"]
    st.caption(f'Cinco bases prioritárias: {_pct(priority)} '
               f'({priority["timed"]}/{priority["eligible"]} pares não locais).')
    sections = ("Visão geral", "Cidades-base", "Destinos")
    section = st.segmented_control(
        "Detalhamento da cobertura", sections,
        **_widget_state("ux132_coverage_section", sections[0], lambda v: v in sections),
    ) or sections[0]
    if section == "Visão geral":
        st.markdown("#### Transporte ferroviário")
        st.write(f'{counts["historical"]} históricos · {counts["indicative"]} indicativos · '
                 f'{counts["missing"]} sem tempo · {counts["local"]} locais')
        st.caption("Os demais domínios terão indicadores próprios; não há nota geral de qualidade.")
        return
    rows = view["bases"] if section == "Cidades-base" else view["destinations"]
    axis = "bases" if section == "Cidades-base" else "destinations"
    cols = st.columns(3 if axis == "bases" else 2)
    query = cols[0].text_input("Pesquisar cidade", placeholder="Digite o nome",
                              **_widget_state("ux132_search_" + axis, "", lambda v: isinstance(v, str)))
    order = cols[1].selectbox("Ordenar por", SORT_OPTIONS,
                             **_widget_state("ux132_sort_" + axis, SORT_OPTIONS[0], lambda v: v in SORT_OPTIONS))
    if axis == "bases":
        scopes = ("Cinco bases prioritárias", "Todas as bases")
        scope = cols[2].selectbox("Recorte de bases", scopes,
                                  **_widget_state("ux132_base_scope", scopes[0], lambda v: v in scopes))
        if scope == scopes[0]:
            rows = [r for r in rows if r["id"] in view["priority_ids"]]
    gaps_only = st.checkbox("Somente cidades com lacunas de tempo",
                            **_widget_state("ux132_only_gaps_" + axis, False, lambda v: isinstance(v, bool)))
    total = len(rows)
    rows = filter_coverage_rows(rows, query=query, gaps_only=gaps_only, sort=order)
    st.caption(f'{len(rows)} de {total} cidades no recorte. Os filtros não alteram os '
               "indicadores globais. Cobertura não indica a melhor cidade.")
    if not rows:
        st.info("Nenhuma cidade corresponde aos filtros. Altere a busca ou o recorte.")
        return
    st.dataframe(_table(rows), hide_index=True, width="stretch",
                 column_config={"Cobertura": st.column_config.ProgressColumn(
                     "Cobertura", min_value=0, max_value=100, format="%.1f%%")},
                 key="ux132_coverage_table_" + section)
    st.markdown("#### Detalhamento da cidade")
    detail_key = "ux132_detail_" + section
    names = {r["id"]: r["name"] for r in rows}
    # A stable-ID selectbox supports keyboard access, restores state across pages
    # and avoids coupling the detail to ephemeral dataframe row positions.
    selected = st.selectbox("Escolha uma cidade para detalhar", list(names),
                            format_func=names.__getitem__,
                            **_widget_state(detail_key, next(iter(names)), lambda v: v in names))
    row = next(r for r in rows if r["id"] == selected)
    with st.container(border=True):
        a, b = st.columns(2)
        a.metric(f'{row["name"]} — cobertura ferroviária', _pct(row))
        if row["fraction"] is not None:
            a.progress(row["fraction"])
        a.caption(f'{row["timed"]} de {row["eligible"]} conexões documentadas')
        b.metric("Lacunas de pesquisa", row["missing"])
        b.caption("Conexões sem tempo documentado")
        st.divider()
        st.markdown("#### Conexões e lacunas de pesquisa")
        status = st.selectbox("Tipo de evidência", list(STATUS_OPTIONS),
                              **_widget_state("ux132_status_" + axis, next(iter(STATUS_OPTIONS)),
                                              lambda v: v in STATUS_OPTIONS))
        connections = connection_rows(view, axis, row["id"], status)
        st.caption(f'{len(connections)} conexões no filtro · os indicadores acima consideram '
                   "todos os pares não locais desta cidade.")
        if not connections:
            st.info("Nenhuma conexão neste filtro.")
        else:
            counterpart = "destination" if axis == "bases" else "origin"
            label = "Destino" if axis == "bases" else "Origem"
            if status == "Sem tempo pesquisado":
                # Keep the original compact gap table as the default.
                table = [{label: c[counterpart], "Pendência": c["label"]}
                         for c in connections]
                config = None
            else:
                table = [{
                    label: c[counterpart], "Evidência": c["label"],
                    "Fonte": c["source_url"],
                } for c in connections]
                config = {"Fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir fonte")}
            st.dataframe(table, hide_index=True, width="stretch",
                         column_config=config, key="ux132_gaps_" + section)
            timed = { (c["destination_id"] if axis == "bases" else c["base_id"]): c
                      for c in connections if c["category"] in ("historical", "reference_only") }
            if timed:
                with st.expander("Consultar fonte e ressalvas"):
                    key = "ux132_connection_" + axis
                    chosen = st.selectbox(
                        "Conexão documentada", list(timed),
                        format_func=lambda k: timed[k][counterpart],
                        **_widget_state(key, next(iter(timed)), lambda v: v in timed),
                    )
                    c = timed[chosen]
                    st.write(f'**{c["origin"]} → {c["destination"]}**')
                    st.write(c["label"])
                    st.caption("Data registrada: " + str(c["source_date"] or "Não informada"))
                    if c["source_url"]:
                        st.link_button("Abrir fonte do mínimo exibido", c["source_url"])
                    else:
                        st.caption("Fonte do mínimo não informada.")
                    if c["station_caveat"]:
                        st.caption(c["station_caveat"])
                    if c["notes"]:
                        st.caption(str(c["notes"]))
                    if c["variation"]:
                        st.caption("Há variação entre referências; não implica contradição confirmada.")
                    if c["alternative"]:
                        alt = c["alternative"]
                        st.markdown("**Referência indicativa alternativa (não substitui o histórico)**")
                        st.write(format_minutes(alt["minimum"]))
                        st.caption("Data registrada: " + str(alt["source_date"]))
                        st.link_button("Abrir fonte alternativa", alt["source_url"])
                        if alt["station_caveat"]:
                            st.caption(alt["station_caveat"])
                        if alt["notes"]:
                            st.caption(str(alt["notes"]))
                    if c["observations"]:
                        st.markdown("**Outras observações históricas catalogadas**")
                        observations = []
                        for obs in c["observations"]:
                            minutes = obs.get("minimum_oneway_min")
                            url = obs.get("source_url")
                            observations.append({
                                "Mínimo registrado": format_minutes(minutes) if type(minutes) is int and minutes > 0 else None,
                                "Data": obs.get("evidence_date"),
                                "Estação de origem": obs.get("origin_station"),
                                "Estação de destino": obs.get("destination_station"),
                                "Observação": obs.get("notes"),
                                "Fonte": url if isinstance(url, str) and url.startswith("https://") else None,
                            })
                        st.dataframe(observations, hide_index=True, width="stretch",
                                     column_config={"Fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir fonte")},
                                     key="ux132_observations_" + axis)
                    st.caption("Referência de ida; retorno, última milha e horários de 2027 não confirmados.")
        st.caption("Sem tempo pesquisado não significa ausência de conexão. "
                   "Local indica acesso urbano a verificar, não lacuna ferroviária.")
