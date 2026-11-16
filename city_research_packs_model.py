"""Conservative, reusable public research for city packages 1–3.

A legacy listing or advertised railway fare is not a 2027 booking or a
comparable cost. No write APIs; all functions are pure.
"""
from __future__ import annotations
import json
from copy import deepcopy
from pathlib import Path
from base_research_expanded_model import load_research

PATH=Path(__file__).resolve().parent/"data"/"city_research_packs_2026_11.json"
DEPARTURE_MIN_DATE="2027-09-04"


def validate_city_packs(data:dict,canonical:dict|None=None)->dict:
    canonical=load_research() if canonical is None else canonical
    originals={c["id"]:c for c in canonical["cities"] if c["shortlist"]}
    if data.get("schema_version")!=1 or len(data.get("cities",[]))!=len(originals):
        raise ValueError("Pesquisa incompleta ou schema desconhecido")
    seen=set()
    for row in data["cities"]:
        key=row["city_id"]
        if key in seen or key not in originals:
            raise ValueError("Cidade ausente, duplicada ou fora das finalistas")
        seen.add(key)
        d=row["daily_life"]
        amount=d["restaurant_two_midrange_eur_2026"]
        if amount is not None:
            if not isinstance(amount,(float,int)) or amount<=0 or not str(d.get("restaurant_source_url","")).startswith("https://"):
                raise ValueError("Despesa sem referência válida")
        if d.get("complete_comparable_basket_eur") is not None:
            raise ValueError("Não declarar cesta completa sem auditoria")
        if d.get("grocery_basket_eur") is not None or d.get("transport_monthly_pass_eur") is not None:
            raise ValueError("Não completar cesta parcial com preço não verificado")
        cowork=row["remote_work"].get("coworking_reference")
        if cowork and (not str(cowork.get("source_url","")).startswith("https://") or not cowork.get("limitations")):
            raise ValueError("Coworking sem condições identificadas")
        if row["remote_work"].get("internet_in_rental_verified") is not False:
            raise ValueError("Internet de imóvel não comprovada")
        clim=row["climate"]
        if clim["months_9_10_11"] is not None:
            raise ValueError("Normal climática deve ser carregada de fonte compatível validada")
        if clim["normal_period"]!="1991–2020":
            raise ValueError("Período climático de referência alterado")
        h=row["housing"]
        if h["verified_for_trip_dates"]!=0:
            raise ValueError("Imóveis para setembro 2027 não confirmados")
        orig={item["listing_ref"] for item in originals[key]["housing_offers"]}
        offers=h["historical_listings"]
        if {x["listing_ref"] for x in offers}!=orig or len(offers)!=len(orig):
            raise ValueError("Histórico de anúncios alterado")
        if h["individual_listing_urls_count"]!=sum(x["source_is_direct_listing"] for x in offers):
            raise ValueError("Contagem de anúncios diretos inválida")
        for x in offers:
            if not str(x["source_url"]).startswith("https://") or not (x["monthly_eur_2026"]>0 and x["size_m2"]>0):
                raise ValueError("Amostra histórica sem fonte ou unidade")
            if x["confirmed_56_to_60_nights"] or x["available_after_2027_09_04"]:
                raise ValueError("Reserva histórica marcada como válida para 2027")
        for n in row["neighborhoods"]:
            if not n["name"] or not str(n.get("source_url","")).startswith("https://") or n["validated_rental_in_area"]:
                raise ValueError("Bairro sem fonte ou declarado como imóvel garantido")
        for line in row["weekend_rail_references"]:
            if not str(line.get("source_url","")).startswith("https://"):
                raise ValueError("Rota sem operador")
            if not (type(line["duration_minutes_oneway"]) is int and line["duration_minutes_oneway"]>0):
                raise ValueError("Tempo de trem inválido")
            if any(line.get(attr) for attr in ("weekend_return_confirmed","return_timetable_verified","last_mile_verified","valid_for_2027")):
                raise ValueError("Rota histórica não pode afirmar retorno confirmado")
            fare=line["fare_eur_oneway_with_condition"]
            if fare is not None and (fare<=0 or not line.get("fare_condition")):
                raise ValueError("Tarifa condicional deve manter condições")
    return deepcopy(data)


def load_city_packs(path:Path=PATH,canonical:dict|None=None)->dict:
    return validate_city_packs(json.loads(path.read_text(encoding="utf-8")),canonical)


def pack_for_city(data:dict,city_id:str)->dict|None:
    return deepcopy(next((c for c in data["cities"] if c["city_id"]==city_id),None))


def pack_summary(data:dict)->dict:
    c=data["cities"]
    return {
        "finalists":len(c),
        "restaurant_city_count":sum(r["daily_life"]["restaurant_two_midrange_eur_2026"] is not None for r in c),
        "coworking_city_count":sum(r["remote_work"]["coworking_reference"] is not None for r in c),
        "neighborhood_references":sum(len(r["neighborhoods"]) for r in c),
        "rail_operator_references":sum(len(r["weekend_rail_references"]) for r in c),
        "historical_housing_observations":sum(len(r["housing"]["historical_listings"]) for r in c),
        "housing_confirmed_2027":sum(r["housing"]["verified_for_trip_dates"] for r in c),
        "comparable_climate_cities":sum(r["climate"]["months_9_10_11"] is not None for r in c),
    }
