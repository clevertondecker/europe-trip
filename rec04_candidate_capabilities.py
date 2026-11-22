"""REC04 read-only capabilities from the existing research/plan contracts.

An explorative scenario is NOT a city-specific budget quote. Capability flags
never imply that 2027 housing, last mile, or return trains are verified.
"""
from __future__ import annotations

from base_scenario_model import base_options
from base_research_expanded_model import load_research
from trip_plan_model import BASES
from base_scenario_impact import SUPPORTED_ROUTE_BASES


def candidate_capabilities(*, options=None, research=None):
    choices=base_options(include_candidates=True) if options is None else options
    study=load_research(include_candidates=True) if research is None else research
    ids={city["id"] for city in study["cities"]}
    result={}
    for row in choices:
        city=row["id"]
        if city in result:
            raise ValueError("Cidade duplicada nas opções exploratórias")
        supported=city in BASES
        detailed=city in SUPPORTED_ROUTE_BASES
        profile=city in ids
        result[city]={
            "id":city, "name":row["name"], "country":row["country"],
            "researchable":True,
            "recommendable":profile,
            "has_profile":profile,
            "comparable":profile,  # Matrix eligibility, NOT verified like-for-like coverage
            "scenario_selectable":True,
            "detailed_budget_supported":detailed,
            "official_plan_supported":supported,
            "rental_quote_2027_available":False,
            "missing":(
                ["Cesta detalhada de passeios e tarifas por base não disponível"]
                if not detailed else [])+
                ["Aluguel mobiliado e caução para 2027 não cotados",
                 "Retorno ferroviário, frequência e última milha a confirmar"],
            "budget_note":(
                "Referência parcial do roteiro e custos históricos, não cotação local de 2027"
                if detailed else
                "Somente cenário hipotético com provisões gerais; custo local não pesquisado"),
        }
    return result


def capability_for(city_id, *, options=None, research=None):
    caps=candidate_capabilities(options=options,research=research)
    if not isinstance(city_id,str) or city_id not in caps:
        raise ValueError("Cidade não está no catálogo de pesquisa atual")
    return caps[city_id]
