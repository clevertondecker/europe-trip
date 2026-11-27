"""UX132A: documentary coverage without itinerary or wishlist dependencies."""
import logging
import streamlit as st

from ux132_research_coverage_model import build_coverage_view
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
        "QUALIDADE DA PESQUISA", "Cobertura dos dados",
        "Acompanhe os dados documentados e as lacunas de pesquisa.",
        variant="compact",
    ), unsafe_allow_html=True)
    try:
        view = build_coverage_view(discovery=discovery, research=research)
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
    st.caption("Ordem alfabética; cobertura não indica a melhor cidade.")
    if not rows:
        st.info("Nenhum registro neste recorte.")
        return
    st.dataframe(_table(rows), hide_index=True, width="stretch",
                 column_config={"Cobertura": st.column_config.ProgressColumn(
                     "Cobertura", min_value=0, max_value=100, format="%.1f%%")},
                 key="ux132_coverage_table_" + section)
    st.markdown("#### O que falta pesquisar")
    selected = st.selectbox("Escolha uma cidade para detalhar", [r["id"] for r in rows],
                            format_func=lambda ident: next(r["name"] for r in rows if r["id"] == ident),
                            key="ux132_detail_" + section)
    row = next(r for r in rows if r["id"] == selected)
    st.write(f'{row["name"]}: {_pct(row)} · {row["timed"]}/{row["eligible"]} pares não locais.')
    if row["missing_names"]:
        label = "Destinos" if section == "Cidades-base" else "Origens"
        st.write(f'{label} sem tempo pesquisado ({row["missing"]}):')
        st.write(", ".join(row["missing_names"]))
    else:
        st.caption("Nenhuma lacuna de tempo neste recorte; retorno e acesso ainda exigem verificação.")
    st.caption("Sem tempo pesquisado não significa ausência de conexão.")
