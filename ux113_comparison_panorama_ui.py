"""UX113: read-only logistics/living panorama for the canonical UX87 selection.

Research snapshots are not fares, schedules, booking quotes or an official
choice. This module introduces no Streamlit selection or persisted plan state.
"""
from __future__ import annotations

import streamlit as st

from base_research_expanded_model import observed_housing
from city_research_round2 import load_round2


PILOT_BASES = frozenset({"mulhouse", "strasbourg", "freiburg"})


def project_comparison_panorama(projection: dict, research: dict, round2: dict) -> dict:
    """Cross-project the same chosen bases without making a synthetic score.

    The 2026 cost snapshot covers four bases only. Missing prices stay missing,
    and unequal rental samples must never be treated as comparable quotes.
    """
    cities = {city["id"]: city for city in research["cities"]}
    costs = {city["id"]: city for city in round2["cities"]}
    bases = projection["base_ids"]
    total = len(projection["destinations"])
    logistics, living = [], []
    sources = []
    for base in bases:
        city = cities[base]
        evidence = projection["counts"][base]
        timed = evidence.get("historical", 0) + evidence.get("reference_only", 0)
        logistics.append({
            "Cidade-base": city["name"],
            "Idas com tempo documentado": f"{timed}/{total}",
            "Acesso local a verificar": evidence.get("local", 0),
            "Sem tempo pesquisado": evidence.get("no_time", 0),
            "Retorno e última milha": "Não validados",
        })
        housing = observed_housing(city)
        specific = costs.get(base)
        living.append({
            "Cidade-base": city["name"],
            "Anúncios históricos (2026)": (
                f'{housing["count"]} · mediana € {housing["median_eur_month"]:,.0f}/mês'
                if housing["count"] else "Sem anúncios pesquisados"
            ),
            "Aluguel residencial (€/m²/mês)": (
                specific["residential_rent_eur_sqm_month"] if specific else None
            ),
            "Jantar para dois (€)": (
                specific["restaurant_two_midrange_eur"] if specific else None
            ),
            "Coworking pesquisado": (
                specific["coworking"]["name"] if specific else "Não pesquisado"
            ),
        })
        if specific:
            sources.append((city["name"] + " · jantar para dois",
                            specific["restaurant_source_url"]))
            sources.append((city["name"] + " · coworking",
                            specific["coworking"]["source_url"]))
    return {
        "base_ids": list(bases),
        "logistics": logistics,
        "living": living,
        "living_sources": sources,
        "residential_source": round2["common_sources"][0]["url"],
        "pilot_bases": [base for base in bases if base in PILOT_BASES],
        "covered_living_count": sum(base in costs for base in bases),
        "comparison_has_full_trip_logistics": False,
        "cost_of_stay_2027_quoted": False,
        "selected_base_for_itinerary": None,
    }


def render_comparison_panorama(projection: dict, research: dict) -> None:
    """Show contextual evidence immediately under UX87's comparison matrix."""
    try:
        panorama = project_comparison_panorama(projection, research, load_round2())
    except (KeyError, ValueError, TypeError, OSError) as exc:
        st.info("O panorama adicional de logística e custo de vida está indisponível. "
                "A matriz principal permanece válida.")
        return
    st.markdown("#### Panorama para decidir o que investigar")
    st.caption("As mesmas cidades da comparação acima, sem segundo seletor. "
               "Referências de 2026 não garantem trajetos, aluguel ou preços em 2027.")
    tab_logistics, tab_living = st.tabs(["Logística e passeios", "Custo de vida e rotina"])
    with tab_logistics:
        st.dataframe(panorama["logistics"], hide_index=True, width="stretch")
        st.caption("O número de idas pesquisadas mede cobertura documental, não menor tempo, "
                   "facilidade de deslocamento nem viabilidade de bate-volta. "
                   "Retorno de fim de semana e última milha continuam pendentes.")
    with tab_living:
        st.dataframe(panorama["living"], hide_index=True, width="stretch",
                     column_config={
                         "Aluguel residencial (€/m²/mês)":
                             st.column_config.NumberColumn(format="€ %.2f"),
                         "Jantar para dois (€)":
                             st.column_config.NumberColumn(format="€ %.2f"),
                     })
        st.caption(f'{panorama["covered_living_count"]} de {len(panorama["base_ids"])} '
                   "cidades têm indicadores locais pontuais da rodada 2026. "
                   "Campos vazios significam pesquisa ausente, não custo zero. "
                   "Anúncios têm amostras desiguais; aluguel residencial não é estadia mobiliada.")
        st.caption("Jantar para dois: referência colaborativa, não orçamento diário. "
                   "Coworking: funcionamento noturno, internet e datas de 2027 não confirmados.")
        with st.expander("Fontes e contexto dos indicadores", expanded=False):
            st.link_button("Fonte do aluguel residencial (2026)",
                           panorama["residential_source"])
            for label, url in panorama["living_sources"]:
                st.link_button(label, url)
    pilot = panorama["pilot_bases"]
    if len(pilot) >= 2:
        names = {city["id"]: city["name"] for city in research["cities"]}
        st.caption("Pesquisas aprofundadas para " + ", ".join(names[base] for base in pilot) +
                   " (subconjunto do piloto de 2026; as demais cidades não foram avaliadas nele):")
        from dq21_comparison_ui import render_dq21_panel
        from dq20_comparison_ui import render_dq20_panel
        render_dq21_panel(pilot)
        render_dq20_panel(pilot)
