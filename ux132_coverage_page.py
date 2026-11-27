"""Composition of documentary coverage; domains remain independent."""
import logging
from time import perf_counter

import streamlit as st

from data24_coverage_model import rail_coverage
from trip01_supplemental_discovery import build_exploration_discovery
from ux_shared_ui_presentation import section_heading
from ux_widget_state import widget_state
from ux132_research_coverage_ui import render_rail_coverage
from ux132c1_attraction_coverage_ui import render_attraction_coverage, render_attraction_indicators
from ux132c1_attraction_coverage_model import build_attraction_inventory
from ux132c2_living_coverage_ui import render_living_summary, render_living_coverage

_LOG = logging.getLogger(__name__)
DOMAINS = ("Visão geral", "Transporte ferroviário", "Atrações turísticas", "Morar e trabalhar")


def _open_domain(domain):
    st.session_state["ux132_domain_shadow"] = domain
    st.session_state["ux132_domain"] = domain


def _render_overview(discovery, research):
    # No presentation-level detail projection or duplicate inventory build.
    started = perf_counter()
    discovery = build_exploration_discovery() if discovery is None else discovery
    with st.container(border=True):
        st.markdown("#### Transporte ferroviário")
        try:
            counts = rail_coverage(discovery=discovery, research=research)["global"]
            rate = counts["fraction"]
            st.metric("Cobertura ferroviária", "N/A" if rate is None else f"{rate:.1%}".replace(".", ","))
            if rate is not None:
                st.progress(rate)
            st.caption(f'{counts["timed"]}/{counts["eligible"]} conexões não locais com tempo · '
                       f'{counts["missing"]} sem tempo documentado.')
        except Exception:
            _LOG.exception("Coverage overview rail unavailable")
            st.warning("Resumo ferroviário indisponível.")
        st.button("Ver cobertura ferroviária", key="ux132_open_rail", on_click=_open_domain, args=(DOMAINS[1],))
    with st.container(border=True):
        st.markdown("#### Atrações turísticas")
        try:
            counts = build_attraction_inventory(discovery=discovery)["counts"]
            a, b = st.columns(2)
            a.metric("Atrações únicas", counts["attractions"])
            b.metric("Destinos com atrações", f'{counts["destinations_with_attractions"]}/{counts["destinations"]}' if counts["destinations"] else "N/A")
            st.caption(f'{counts["destinations"] - counts["destinations_with_attractions"]} destinos sem atrações catalogadas.')
            render_attraction_indicators(counts, compact=True)
        except Exception:
            _LOG.exception("Coverage overview attractions unavailable")
            st.warning("Resumo de atrações indisponível.")
        st.button("Ver cobertura das atrações", key="ux132_open_attractions",
                  on_click=_open_domain, args=(DOMAINS[2],))
    with st.container(border=True):
        st.markdown("#### Morar e trabalhar")
        render_living_summary(research=research)
        st.button("Ver cobertura de moradia e trabalho", key="ux132_open_living",
                  on_click=_open_domain, args=(DOMAINS[3],))
    st.caption("Cada domínio possui seus próprios indicadores. Cobertura não equivale à qualidade turística ou à viabilidade de 2027; não há nota global.")
    _LOG.debug("UX132 overview: %.3fs", perf_counter() - started)


def render_research_coverage(*, discovery=None, research=None):
    st.markdown(section_heading(
        "COBERTURA DOCUMENTAL", "Cobertura dos dados",
        "Veja o que já sabemos e quais pesquisas ainda faltam para escolher a base e organizar as visitas.",
        variant="compact",
    ), unsafe_allow_html=True)
    domain = st.segmented_control("Área da cobertura", DOMAINS,
                                  **widget_state("ux132_domain", DOMAINS[0], lambda v: v in DOMAINS)) or DOMAINS[0]
    if domain == DOMAINS[1]:
        render_rail_coverage(discovery=discovery, research=research)
    elif domain == DOMAINS[2]:
        render_attraction_coverage(discovery=discovery)
    elif domain == DOMAINS[3]:
        render_living_coverage(research=research)
    else:
        _render_overview(discovery, research)
