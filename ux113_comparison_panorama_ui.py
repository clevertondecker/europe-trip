"""UX113: non-redundant housing, daily-life and pilot context for UX87 selection.

The canonical UX87 matrix already owns travel-time evidence. This panel adds
only researched dimensions that are not in the matrix; missing values remain
unknown and no research-only city is silently promoted into the official plan.
"""
from __future__ import annotations

import streamlit as st

from base_research_expanded_model import observed_housing
from city_research_round2 import load_round2


PILOT_BASES = frozenset({"mulhouse", "strasbourg", "freiburg"})


def coworking_night_status(coworking: dict | None) -> str:
    """Three-valued 2026 observation, NEVER a promise of access in 2027."""
    if not coworking:
        return "Não pesquisado"
    observed=coworking.get("late_work_compatible")
    if observed is True:
        return "Compatibilidade observada em 2026 · confirmar acesso em 2027"
    if observed is False:
        return "Horário publicado não cobre todo o turno · verificar condições"
    return "Compatibilidade ainda não confirmada"


def project_comparison_panorama(projection: dict, research: dict, round2: dict) -> dict:
    """Project the SAME selected cities without inventing cost or viability.

    Historical offers are heterogeneous rental advertisements, not verified
    comparable furnished 2027 stays. Residential €/m² is a separate indicator.
    """
    cities = {city["id"]: city for city in research["cities"]}
    costs = {city["id"]: city for city in round2["cities"]}
    bases = projection["base_ids"]
    total = len(projection["destinations"])
    logistics, living, routine, sources, housing_sources = [], [], [], [], []
    for base in bases:
        city = cities[base]
        evidence = projection["counts"][base]
        timed = evidence.get("historical", 0) + evidence.get("reference_only", 0)
        # Retained for backward-compatible research projections; intentionally
        # NOT rendered as a second logistics table beside the UX97 matrix.
        logistics.append({
            "Cidade-base": city["name"],
            "Idas com tempo documentado": f"{timed}/{total}",
            "Acesso local a verificar": evidence.get("local", 0),
            "Sem tempo pesquisado": evidence.get("no_time", 0),
            "Retorno e última milha": "Não validados",
        })
        housing = observed_housing(city)
        for offer in city["housing_offers"]:
            housing_sources.append((
                city["name"] + " · anúncio histórico " + str(offer["listing_ref"]),
                offer["catalogue_url"],
            ))
        specific = costs.get(base)
        coworking = specific["coworking"] if specific else None
        living.append({
            "Cidade-base": city["name"],
            "Amostra de anúncios (2026)": housing["count"],
            "Mínimo observado (€ / mês)": housing["minimum_eur_month"],
            "Mediana observada (€ / mês)": housing["median_eur_month"],
            "Máximo observado (€ / mês)": housing["maximum_eur_month"],
            "Anúncios para dois adultos": housing["two_adult_listings_documented"],
            "Aluguel residencial (€/m²/mês)": (
                specific["residential_rent_eur_sqm_month"] if specific else None
            ),
            "Jantar para dois (€)": (
                specific["restaurant_two_midrange_eur"] if specific else None
            ),
        })
        routine.append({
            "Cidade-base": city["name"],
            "Coworking pesquisado": coworking["name"] if coworking else None,
            "Preço de referência (€)": coworking["price_eur"] if coworking else None,
            "Modalidade": coworking["price_basis"] if coworking else None,
            "Horário publicado": coworking["schedule"] if coworking else None,
            "Expediente noturno (ref. 2026)": coworking_night_status(coworking),
            "Ressalva sobre acesso": coworking["note"] if coworking else None,
        })
        if specific:
            sources.append((city["name"] + " · alimentação",
                            specific["restaurant_source_url"]))
            sources.append((city["name"] + " · coworking",
                            coworking["source_url"]))
    return {
        "base_ids": list(bases),
        "logistics": logistics,
        "living": living,
        "routine": routine,
        "living_sources": sources,
        "housing_sources": housing_sources,
        "residential_source": round2["common_sources"][0]["url"],
        "pilot_bases": [base for base in bases if base in PILOT_BASES],
        "covered_living_count": sum(base in costs for base in bases),
        "comparison_has_full_trip_logistics": False,
        "cost_of_stay_2027_quoted": False,
        "selected_base_for_itinerary": None,
    }


def _pilot_context(projection: dict, research: dict, pilot: list[str]) -> None:
    """Only expose pilot observations overlapping the user's actual destinations."""
    from dq21_decision_model import decision_research

    names = {city["id"]: city["name"] for city in research["cities"]}
    with st.expander("Pesquisa histórica do piloto · detalhes opcionais", expanded=False):
        st.caption("Estudo independente de Mulhouse, Strasbourg e Freiburg. "
                   "Apenas destinos em comum com a sua seleção aparecem aqui; "
                   "nenhum horário, retorno ou aeroporto é uma reserva para 2027.")
        data = decision_research(pilot)
        if data["status"] != "available":
            st.info("Pacote piloto adicional indisponível; a comparação principal permanece válida.")
            return
        selected_destinations = {d["id"] for d in projection["destinations"]}
        matched = [r for r in data["routes"] if r["destination_id"] in selected_destinations]
        if not matched:
            st.info("O piloto não pesquisou os destinos deste escopo. "
                    "Não usamos tempos de outras viagens como evidência pessoal.")
        else:
            rows = []
            names_dest = {d["id"]: d["name"] for d in projection["destinations"]}
            for item in matched:
                rows.append({
                    "Cidade-base": names[item["base_id"]],
                    "Destino do seu escopo": names_dest[item["destination_id"]],
                    "Mínimo histórico (min)": item.get("minimum_rail_minutes_2026"),
                    "Volta em 2027": "Não validada",
                })
            st.dataframe(rows, hide_index=True, width="stretch")
            st.caption("Observações históricas, sem confirmação de estações, frequência, "
                       "retornos, última milha ou disponibilidade em 2027.")
        with st.expander("Aeroportos e vida urbana · pesquisa geral",expanded=False):
            st.caption("Estas informações descrevem as cidades pesquisadas em 2026; "
                       "não pertencem necessariamente aos destinos do seu escopo.")
            for record in data["airports"]:
                options=record.get("airport_options",[])
                names_airport=list(dict.fromkeys(
                    str(a.get("airport_code")) for a in options if a.get("airport_code")
                ))
                st.markdown("**"+names[record["base_id"]]+"** · aeroportos investigados: "+
                            (", ".join(names_airport) or "sem pesquisa"))
                st.caption("Acesso completo porta a porta, conexões aéreas e tarifas "
                           "do casal para 2027 não verificados.")
            for record in data["urban"]:
                st.markdown("**"+names[record["city_id"]]+"** · rotina e mobilidade")
                link=record.get("late_transit_service")
                if isinstance(link,str) and link.startswith("https://"):
                    st.link_button("Referência de transporte urbano · "+
                                   names[record["city_id"]],link)
                st.caption("Internet do imóvel, segurança na vizinhança, "
                           "horário do coworking para o seu contrato e última milha "
                           "exigem confirmação individual.")
            st.caption("Hipóteses de fins de semana e roteiro combinado belga "
                       "permanecem no estudo histórico DQ20/DQ21 da área de "
                       "cidades favoritas; não são passeios confirmados de 2027.")


def render_comparison_panorama(projection: dict, research: dict) -> None:
    """Add decision-relevant dimensions below, never duplicate UX97's counts."""
    try:
        panorama = project_comparison_panorama(projection, research, load_round2())
    except (KeyError, ValueError, TypeError, OSError):
        st.info("Moradia e rotina indisponíveis nesta pesquisa. A matriz ferroviária permanece válida.")
        return
    st.markdown("#### Moradia, alimentação e trabalho remoto")
    st.caption("Referências pesquisadas em 2026, não cotações de hospedagem ou custos confirmados de 2027.")
    housing_tab, routine_tab = st.tabs(["Moradia e alimentação", "Trabalho e rotina"])
    with housing_tab:
        st.dataframe(panorama["living"], hide_index=True, width="stretch")
        st.caption(f'{panorama["covered_living_count"]} de {len(panorama["base_ids"])} '
                   "cidades têm indicadores locais de alimentação e aluguel residencial. "
                   "Campos vazios significam pesquisa ausente. "
                   "As amostras de anúncios são heterogêneas; não equivalem a "
                   "hospedagem mobiliada para duas pessoas por 56–60 noites.")
    with routine_tab:
        st.dataframe(panorama["routine"], hide_index=True, width="stretch")
        st.caption("Coworking e horários são referências dos provedores. "
                   "Internet no imóvel, acesso ao turno noturno e condições para 2027 não confirmados.")
    with st.expander("Fontes e limitações de custos", expanded=False):
        st.link_button("Indicador de aluguel residencial (2026)", panorama["residential_source"])
        for label, url in panorama["living_sources"]:
            st.link_button(label, url)
        with st.expander("Anúncios históricos consultados", expanded=False):
            if not panorama["housing_sources"]:
                st.caption("Não há anúncios pesquisados para essas cidades.")
            for label,url in panorama["housing_sources"]:
                st.link_button(label,url)
            st.caption("Anúncios observados em 2026; preço, duração e "
                       "disponibilidade em 2027 não confirmados.")
        st.caption("Preço residencial por metro quadrado, jantar para dois e anúncio "
                   "histórico usam metodologias distintas; não some como orçamento real.")
    pilot = panorama["pilot_bases"]
    if len(pilot) >= 2:
        _pilot_context(projection, research, pilot)
