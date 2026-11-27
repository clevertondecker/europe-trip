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
    st.caption("Universo global: pares dirigidos. Pares locais ficam fora do denominador; "
               "tempos de ida não confirmam retorno, viabilidade ou horários de 2027.")
    priority = view["priority"]
    st.caption(f'Cinco bases prioritárias: {_pct(priority)} '
               f'({priority["timed"]}/{priority["eligible"]} pares não locais).')
    sections = ("Visão geral", "Cidades-base", "Destinos")
    section = st.segmented_control("Detalhamento da cobertura", sections,
                                   default=sections[0], key="ux132_coverage_section") or sections[0]
    if section == "Visão geral":
        st.markdown("#### Transporte ferroviário")
        st.write(f'{counts["historical"]} históricos · {counts["indicative"]} indicativos · '
                 f'{counts["missing"]} sem tempo · {counts["local"]} locais')
        st.caption("Os demais domínios terão indicadores próprios; não há nota geral de qualidade.")
        return
    rows = view["bases"] if section == "Cidades-base" else view["destinations"]
    if section == "Cidades-base":
        scope = st.selectbox("Recorte de bases", ("Cinco bases prioritárias", "Todas as bases"),
                             key="ux132_base_scope")
        if scope == "Cinco bases prioritárias":
            rows = [r for r in rows if r["id"] in view["priority_ids"]]
    axis = "bases" if section == "Cidades-base" else "destinations"
    left, right = st.columns(2)
    query = left.text_input("Pesquisar cidade", placeholder="Digite o nome",
                            key="ux132_search_" + axis)
    order = right.selectbox("Ordenar por", SORT_OPTIONS, key="ux132_sort_" + axis)
    gaps_only = st.checkbox("Somente cidades com lacunas de tempo",
                            key="ux132_only_gaps_" + axis)
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
    if st.session_state.get(detail_key) not in names:
        st.session_state[detail_key] = next(iter(names))
    selected = st.selectbox("Escolha uma cidade para detalhar", list(names),
                            format_func=names.__getitem__, key=detail_key)
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
                              key="ux132_status_" + axis)
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
                table = [{label: c[counterpart], "Pendência": "Sem referência de tempo"}
                         for c in connections]
                config = None
            else:
                table = [{
                    label: c[counterpart], "Evidência": c["label"],
                    "Mínimo de ida": format_minutes(c["minimum"]) if c["minimum"] is not None else None,
                    "Data registrada": c["source_date"], "Fonte": c["source_url"],
                } for c in connections]
                config = {"Fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir fonte")}
            st.dataframe(table, hide_index=True, width="stretch",
                         column_config=config, key="ux132_gaps_" + section)
            timed = { (c["destination_id"] if axis == "bases" else c["base_id"]): c
                      for c in connections if c["category"] in ("historical", "reference_only") }
            if timed:
                with st.expander("Consultar fonte e ressalvas"):
                    key = "ux132_connection_" + axis
                    if st.session_state.get(key) not in timed:
                        st.session_state[key] = next(iter(timed))
                    chosen = st.selectbox("Conexão documentada", list(timed),
                                          format_func=lambda k: timed[k][counterpart], key=key)
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
                    st.caption("Referência de ida; retorno, última milha e horários de 2027 não confirmados.")
        st.caption("Sem tempo pesquisado não significa ausência de conexão. "
                   "Local indica acesso urbano a verificar, não lacuna ferroviária.")
