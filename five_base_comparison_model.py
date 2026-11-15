"""Strict five-base comparison: documented rail evidence and housing samples.

No 2027 bookability, complete fares, weekend return, or door-to-door access
is inferred from one weekday's operator schedule. Unknown != zero.
"""
from __future__ import annotations
from collections import Counter
from copy import deepcopy
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from statistics import median
import json

DATA=Path(__file__).resolve().parent/"data"/"five_base_comparison_evidence_2026_11.json"
BASE_IDS=("offenburg","trier","mulhouse","strasbourg","lille")
COUNTRY_FLAGS={"França":"🇫🇷","Alemanha":"🇩🇪","Bélgica":"🇧🇪","Luxemburgo":"🇱🇺",
               "Suíça":"🇨🇭","Países Baixos":"🇳🇱"}
UNKNOWN="Sem pesquisa suficiente"


def load_five_base_evidence(path:Path=DATA)->dict:
    dataset=json.loads(path.read_text(encoding="utf-8"))
    names=dataset["base_ids"]
    destinations=dataset["common_destinations"]
    bases=dataset["housing"]
    if (dataset.get("schema_version")!=1 or tuple(names)!=BASE_IDS or
            len(destinations)!=15 or len(bases)!=5 or
            not dataset.get("checked_at")):
        raise ValueError("Matriz de pesquisa incompleta")
    if (len({d["id"] for d in destinations})!=15 or
            {b["id"] for b in bases}!=set(BASE_IDS)):
        raise ValueError("Cidades e destinos devem ser únicos")
    days=(date.fromisoformat(dataset["research_window"]["departure_2027_assumption"])-
          date.fromisoformat(dataset["research_window"]["arrival_2027_assumption"])).days
    if days!=60 or dataset["research_window"]["status"]!="comparison_hypothesis_not_official_plan_date":
        raise ValueError("Janela precisa ser exatamente 60 noites hipotéticas")
    seen=set()
    for b in bases:
        if len(b["listings"])<3:
            raise ValueError("Toda finalista precisa de 3 referências históricas")
        refs=set()
        for x in b["listings"]:
            if x["id"] in refs:raise ValueError("Oferta duplicada")
            refs.add(x["id"])
            if not x["source_url"].startswith("https://"):
                raise ValueError("Fonte de anúncio ausente")
            if any(x[y] is not None for y in (
                "date_specific_2027_availability","stay_60_night_total_eur",
                "cleaning_fees_eur","internet_speed_verified",
                "walk_to_station_minutes")):
                raise ValueError("Não transformar observação antiga em cotação 2027")
            if x["monthly_eur"]<=0 or x["size_m2"]<=0:
                raise ValueError("Anúncio inválido")
    for row in dataset["verified_time_routes"]:
        key=(row["base_id"],row["destination_id"])
        if (key in seen or row["base_id"] not in BASE_IDS or
                row["destination_id"] not in {d["id"] for d in destinations}):
            raise ValueError("Rota duplicada ou inválida")
        seen.add(key)
        minute=row["fastest_train_oneway_min"]
        if minute is None or not isinstance(minute,int) or minute<=0:
            raise ValueError("Uma rota não verificada não deve virar tempo zero")
        region=row["regional_example_min"]
        if region is not None and (not isinstance(region,int) or region<=0):
            raise ValueError("Tempo regional inválido")
        fare=row["advertised_from_eur_person_oneway"]
        if fare is not None and fare<=0:raise ValueError("Tarifa inválida")
        if (row["weekend_return_confirmed"] or row["first_last_mile_confirmed"] or
                row["fare_is_normal_verified"]):
            raise ValueError("Não afirmar verificação 2027 sem dados de ambas as pontas")
        if not row["source_url"].startswith("https://"):
            raise ValueError("Fonte oficial ou secundária deve ser rastreável")
    return dataset


def _indices(data:dict)->tuple[dict,dict,dict]:
    return ({b["id"]:b for b in data["housing"]},
            {d["id"]:d for d in data["common_destinations"]},
            {(r["base_id"],r["destination_id"]):r
             for r in data["verified_time_routes"]})


def route_observation(data:dict,base:str,destination:str)->dict:
    bases,destinations,route_map=_indices(data)
    if base not in bases or destination not in destinations:
        raise ValueError("Base ou destino não cadastrado")
    if base==destination:
        # Local access still needs walking/public transport and any admissions.
        return {"base":base,"destination":destination,"train_min":0,
                "regional_min":None,"fare_from_eur_person_oneway":None,
                "status":"local_no_intercity_train","source_url":None,
                "source_status":"local_only","weekend_return_verified":True,
                "door_to_door_verified":False,
                "notes":"Destino local; custo e duração urbana até atrações NÃO verificados"}
    r=route_map.get((base,destination))
    if r is None:
        return {"base":base,"destination":destination,"train_min":None,
                "regional_min":None,"fare_from_eur_person_oneway":None,
                "status":"unresearched","source_url":None,
                "source_status":"not_researched","weekend_return_verified":False,
                "door_to_door_verified":False,
                "notes":"Não há horário/custo documentado para essa combinação"}
    return {"base":base,"destination":destination,
            "train_min":r["fastest_train_oneway_min"],
            "regional_min":r["regional_example_min"],
            "fare_from_eur_person_oneway":r["advertised_from_eur_person_oneway"],
            "source_url":r["source_url"],"status":"historical_2026_reference",
            "source_status":r["source_status"],"weekend_return_verified":False,
            "door_to_door_verified":False,"notes":r["notes"]}


def housing_sample(base:dict)->dict:
    offers=base["listings"]
    prices=[x["monthly_eur"] for x in offers]
    comparable=[x for x in offers if 30<=x["size_m2"]<=60]
    return {"base_id":base["id"],"sample_count":len(offers),
            "min_eur_month":min(prices),"max_eur_month":max(prices),
            "sample_median_eur_month":median(prices),
            "size_30_to_60_count":len(comparable),
            "verified_for_same_60_nights":0,
            "total_60_nights_eur":None,
            "needs_quote":True}


def base_comparison(data:dict,destination_ids:list[str]|None=None)->list[dict]:
    bases,places,_=_indices(data)
    ids=destination_ids if destination_ids is not None else list(places)
    if not ids or len(set(ids))!=len(ids) or not set(ids)<=set(places):
        raise ValueError("Destinos distintos e cadastrados são necessários")
    output=[]
    for base in BASE_IDS:
        rows=[route_observation(data,base,destination) for destination in ids]
        documented=[r for r in rows if r["train_min"] is not None]
        rail=[r for r in documented if r["train_min"]>0]
        local=[r for r in documented if r["train_min"]==0]
        advertised=[r for r in rail if r["fare_from_eur_person_oneway"] is not None]
        # Preserve conservative lower bound: missing routes cannot be free.
        known_minutes=sum(r["train_min"] for r in rail)
        countries={places[r["destination"]]["country"] for r in documented}
        output.append({
            "base_id":base,"name":bases[base]["name"],"country":bases[base]["country"],
            "rows":rows,"destinations_count":len(rows),
            "with_station_times":len(documented),
            "without_station_times":len(rows)-len(documented),
            "with_fare_samples":len(advertised),
            "local_destinations":len(local),
            "minimum_train_oneway_minutes_known":known_minutes if rail else None,
            "within_60_station":sum(0<r["train_min"]<=60 for r in rail),
            "within_90_station":sum(0<r["train_min"]<=90 for r in rail),
            "within_150_station":sum(0<r["train_min"]<=150 for r in rail),
            "countries_with_some_train_evidence":sorted(countries),
            "country_count_lower_bound":len(countries),
            "full_return_date_verified":False,
            "fare_2027_coverage":0,
            "housing":housing_sample(bases[base]),
            "can_rank_final":False})
    return output


def illustrative_cashflow(inputs:dict,eur_brl:float)->dict:
    """Separate 60-night hypothetical total, never the global trip budget.

    Zero means pending, not automatically free. Refundable deposits are
    cash needed but not part of expenditure.
    """
    def positive(x,strict:bool=False)->Decimal:
        try:
            v=Decimal(str(x))
        except (InvalidOperation,TypeError,ValueError) as e:
            raise ValueError("Hipótese financeira inválida") from e
        if not v.is_finite() or v<0 or (strict and v==0):
            raise ValueError("Hipótese financeira deve ser válida e positiva")
        return v
    fx=positive(eur_brl,strict=True)
    sections=("housing","groceries","restaurants","urban","excursions","extras")
    out={}
    missing=[]
    for key in sections:
        v=inputs.get(key)
        if v is None:
            out[key]=None
            missing.append(key)
        else:
            out[key]=positive(v,strict=True)
    deposit=positive(inputs.get("refundable_deposit",0))
    total=sum((v for v in out.values() if v is not None),Decimal(0))
    done=not missing
    return {"inputs_eur":{k:float(v) if v is not None else None for k,v in out.items()},
            "known_input_subtotal_eur":round(float(total),2) if total else None,
            "full_six_category_hypothesis_eur":round(float(total),2) if done else None,
            "full_six_category_hypothesis_brl":round(float(total*fx),2) if done else None,
            "missing_categories":missing,
            "deposit_cash_eur":float(deposit),
            "all_values_user_supplied":True,"complete_trip_cost":False,
            "official_budget_changed":False}
