"""Read-only view projections for UX 4.0 Research: no model/score changes."""
from __future__ import annotations

from base_research_expanded_model import observed_housing
from five_base_comparison_model import BASE_IDS,base_comparison,housing_sample


ACTIVITIES=("Comparar cidades","Explorar uma cidade","Todas as candidatas")


def five_base_cards(study:dict,five:dict,destinations:list[str]|None=None)->list[dict]:
    """Preexisting comparison evidence displayed without quality ranking."""
    canonical={city["id"]:city for city in study["cities"]}
    housing={b["id"]:b for b in five["housing"]}
    summaries={row["base_id"]:row for row in base_comparison(five,destinations)}
    cards=[]
    for key in BASE_IDS:
        base=canonical[key]
        h=housing_sample(housing[key])
        comparison=summaries[key]
        cards.append({
            "id":key,"name":base["name"],"country":base["country"],
            "housing_count":h["sample_count"],
            "size_comparable_count":h["size_30_to_60_count"],
            "with_station_times":comparison["with_station_times"],
            "total_destinations":comparison["destinations_count"],
            "shortlist":base["shortlist"],
            "status":"Pesquisa parcial",
            "confirmed_2027_quotes":0,
            "limitation":"Sem cotação para 2027 nem retorno de fim de semana validado.",
        })
    return cards


def filter_candidates(study:dict,*,country:str="Todos",only_finalists:bool=False,
                      corridor:str="Todos",evidence:str="Todas")->list[dict]:
    """Filter canonical cities; missing research never means the city is unsuitable."""
    rows=[]
    for city in study["cities"]:
        if country!="Todos" and city["country"]!=country:continue
        if only_finalists and not city["shortlist"]:continue
        if corridor!="Todos" and city["corridor"]!=corridor:continue
        h=observed_housing(city)
        if evidence=="Com amostras de moradia" and not h["count"]:continue
        if evidence=="Sem amostras de moradia" and h["count"]:continue
        rows.append(city)
    return rows


def evidence_state(city:dict)->str:
    return "Amostras históricas" if observed_housing(city)["count"] else "Moradia não pesquisada"
