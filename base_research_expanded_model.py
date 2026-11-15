"""Evidence-first screening for 30 candidate European home bases.

The score is intentionally NOT published until every criterion has comparable
evidence and 3 truly bookable 2027 furnished private rentals. This prevents a
city with missing costs appearing cheaper or winning just for having more data.
"""
from __future__ import annotations
from collections import Counter
from pathlib import Path
from statistics import median
import json
import math

DATA=Path(__file__).resolve().parent/"data"/"base_city_research_expanded_2026_11.json"
RAIL=Path(__file__).resolve().parent/"data"/"base_city_rail_evidence_expanded_2026_11.json"

CRITERIA=("temporary_housing","rail_connectivity","viable_destinations",
          "outing_cost","daily_life_remote_work","practical_country_diversity")
PRESETS={
    "general":(30,25,20,10,10,5),
    "economy":(40,20,15,15,7,3),
    "explorer":(20,30,25,8,7,10),
}
COUNTRY_FLAGS={"França":"🇫🇷","Alemanha":"🇩🇪","Bélgica":"🇧🇪",
               "Luxemburgo":"🇱🇺"}


def load_research(path:Path=DATA)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    cities=data["cities"]
    if data["schema_version"]!=1 or len(cities)<25 or data["travelers"]!=2:
        raise ValueError("Pesquisa de cidades-base incompleta")
    ids=[x["id"] for x in cities]
    if len(ids)!=len(set(ids)):raise ValueError("Cidade-base duplicada")
    if not 10<=sum(x["shortlist"] for x in cities)<=12:
        raise ValueError("Triagem precisa de 10 a 12 finalistas")
    for city in cities:
        if not city["name"] or not city["country"] or not city["corridor"]:
            raise ValueError("Cidade sem informações básicas")
        if city["eligible_2027_quotes"]<0:
            raise ValueError("Cotações verificadas negativas")
        seen=set()
        for item in city["housing_offers"]:
            if item["listing_ref"] in seen:raise ValueError("Anúncio repetido")
            seen.add(item["listing_ref"])
            if (not 0<float(item["monthly_eur"])<15000 or
                    not 0<float(item["size_m2"])<1000 or
                    not item["catalogue_url"].startswith("https://")):
                raise ValueError("Anúncio sem preço/unidade/fonte")
            if item["available_for_autumn_2027"]:
                raise ValueError("Dados históricos não podem alegar disponibilidade em 2027")
            if item["short_stay_56_to_60_nights_confirmed"]:
                raise ValueError("Não validar 60 noites com índice sem datas")
        if city["ranking_status"]=="decision_ready" and city["eligible_2027_quotes"]<3:
            raise ValueError("Não declarar cidade pronta sem cotações")
    return data


def load_rail(path:Path=RAIL)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data["schema_version"]!=1 or not data.get("basis_date"):
        raise ValueError("Matriz ferroviária inválida")
    seen=set()
    for r in data["segments"]:
        pair=(r["from"],r["to"])
        if pair in seen:raise ValueError("Rota duplicada")
        seen.add(pair)
        if (r["fastest_minutes"]<=0 or
                r["average_minutes"]<r["fastest_minutes"] or
                r["services_on_sample_day"]<1 or
                r.get("return_verified_2027",False) is not False):
            raise ValueError("Dado ferroviário inválido")
        if not r["source_url"].startswith("https://"):
            raise ValueError("Fonte ferroviária ausente")
    return data


def observed_housing(city:dict)->dict:
    rows=city["housing_offers"]
    if not rows:
        return {"count":0,"minimum_eur_month":None,
                "median_eur_month":None,"maximum_eur_month":None,
                "two_adult_listings_documented":0,
                "total_for_56_to_60_nights_eur":None,
                "status":"not_researched"}
    prices=[float(x["monthly_eur"]) for x in rows]
    return {"count":len(rows),
            "minimum_eur_month":min(prices),
            "median_eur_month":median(prices),
            "maximum_eur_month":max(prices),
            "two_adult_listings_documented":sum(
                x["two_adults_confirmed"] is True for x in rows),
            "total_for_56_to_60_nights_eur":None,
            "status":"not_date_verified_noncomparable_2026"}


def normalized_score(criteria:dict,profile:str)->dict:
    """Document reproducible score using verified 0–100 criterion inputs only.

    No denominator shrinking: missing criterion does not make others stronger.
    """
    if profile not in PRESETS:raise ValueError("Perfil não cadastrado")
    unknown=set(criteria)-set(CRITERIA)
    if unknown:raise ValueError("Critérios desconhecidos")
    weights=dict(zip(CRITERIA,PRESETS[profile]))
    total=0.
    known_weight=0
    for key,weight in weights.items():
        value=criteria.get(key)
        if value is None:continue
        if (not isinstance(value,(int,float)) or
                not math.isfinite(value) or not 0<=value<=100):
            raise ValueError("Pontuação deve estar entre 0 e 100")
        total+=weight*value/100
        known_weight+=weight
    return {"profile":profile,"score_0_100":round(total,2) if known_weight==100
            else None,"evidence_weight":known_weight,
            "lower_bound":round(total,2),
            "upper_bound":round(total+100-known_weight,2),
            "missing_criteria":[k for k in CRITERIA if criteria.get(k) is None]}


def decision_readiness(city:dict)->dict:
    housing=observed_housing(city)
    missing=[]
    if city["eligible_2027_quotes"]<3:
        missing.append("Três anúncios privados para dois adultos, 56–60 noites com taxas, disponibilidade e condições confirmadas para 2027")
    if housing["count"]<3:
        missing.append("Três anúncios observados distintos para triagem inicial")
    missing.extend([
        "15 destinos com conexões de ida/volta e tempo porta a porta verificados",
        "Custos normais de transporte do casal para conjunto de passeios fixo",
        "Comida, internet, lavanderia e transporte urbano comparáveis",
        "Requisitos legais de aluguel, estadia e trabalho remoto confirmados"
    ])
    return {"city_id":city["id"],"eligible_for_final_ranking":False,
            "reasons":missing,
            "housing":housing}


def research_overview(data:dict)->dict:
    cities=data["cities"]
    return {
        "candidate_count":len(cities),
        "shortlist_count":sum(c["shortlist"] for c in cities),
        "housing_offer_count":sum(len(c["housing_offers"]) for c in cities),
        "three_observed_offers":sum(len(c["housing_offers"])>=3 for c in cities),
        "three_eligible_2027_quotes":sum(c["eligible_2027_quotes"]>=3 for c in cities),
        "country_counts":dict(Counter(c["country"] for c in cities)),
        "ranking_ready_count":sum(decision_readiness(c)["eligible_for_final_ranking"] for c in cities)
    }


def find_city(data:dict,id:str)->dict:
    matches=[c for c in data["cities"] if c["id"]==id]
    if len(matches)!=1:raise ValueError("Cidade-base não encontrada")
    return matches[0]
