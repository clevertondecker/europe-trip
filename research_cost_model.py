"""Auditable Nov 2026 price evidence and conditional travel-day examples.

No external data fetching at runtime. A menu observation is not a city average.
Unknown routes and costs are never zeroed to claim a complete travel price.
"""
from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from statistics import median

DATA=Path(__file__).resolve().parent/"data"/"researched_prices_2026_11.json"
CURRENCIES={"EUR","CHF"}
VALID_BASES={"mulhouse","strasbourg","metz","nancy"}


def load_research(path:Path=DATA)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not data.get("checked_at"):
        raise ValueError("Research schema not supported")
    if not isinstance(data.get("food"),list) or not isinstance(data.get("rail"),list):
        raise ValueError("Missing research sections")
    keys=set()
    for item in data["food"]:
        if item["currency"] not in CURRENCIES or not item["city"] or not item["venue"]:
            raise ValueError("Food evidence invalid")
        value=Decimal(str(item["price_per_person"]))
        if not value.is_finite() or value<=0:
            raise ValueError("Food price invalid")
        if not item["source_url"].startswith("https://") or not item["checked_at"]:
            raise ValueError("Food source missing")
        key=(item["city"],item["venue"])
        if key in keys:raise ValueError("Duplicate food venue")
        keys.add(key)
    routes=set()
    for item in data["rail"]:
        key=(item["base_id"],item["destination_id"])
        if key in routes or item["base_id"] not in VALID_BASES:
            raise ValueError("Invalid or duplicated route")
        routes.add(key)
        if not item["source_url"].startswith("https://"):
            raise ValueError("Route source missing")
        if item["regular_fare_status"]=="operator_explicit" and item["regular_eur_person_oneway"] is None:
            raise ValueError("Operator fare missing")
    for item in data["urban"]:
        if (item["currency"] not in CURRENCIES or item["amount"]<=0 or
                not item["source_url"].startswith("https://")):
            raise ValueError("Transit evidence invalid")
    return data


def menu_examples(city:str,data:dict|None=None)->dict:
    research=data if data is not None else load_research()
    items=sorted((x for x in research["food"] if x["city"]==city),
                 key=lambda x:x["price_per_person"])
    if not items:
        return {"city":city,"items":[],"currency":None,"count":0,"low":None,
                "median":None,"high":None,"status":"unknown"}
    currencies={item["currency"] for item in items}
    if len(currencies)!=1:raise ValueError("Mixed food sample currencies")
    values=[float(item["price_per_person"]) for item in items]
    return {"city":city,"items":items,"currency":items[0]["currency"],
            "count":len(items),"low":min(values),"median":median(values),
            "high":max(values),"status":"small_convenience_sample",
            "representativeness":"not_statistically_representative"}


def transit_examples(city:str,data:dict|None=None)->list[dict]:
    source=data if data is not None else load_research()
    return [x for x in source["urban"] if x["city"]==city]


def rail_cost_options(base:str,destination:str,travelers:int=2,
                      data:dict|None=None)->dict:
    """Card fare charged once, not on every segment or every outing.

    Weekend Fluo example is conditional on two people traveling together on
    an eligible TER journey. No weekday companion discount is inferred.
    """
    research=data if data is not None else load_research()
    route=next((r for r in research["rail"]
                if r["base_id"]==base and r["destination_id"]==destination),None)
    if route is None or base==destination:
        return {"route":route,"regular_roundtrip_eur":None,
                "discounted_roundtrip_without_card_eur":None,
                "weekend_with_new_card_eur":None,
                "status":"no_verified_fare"}
    regular=route["regular_eur_person_oneway"]
    discounted=route["discounted_eur_person_oneway"]
    card_price=float(research["cards"][0]["price_eur"])
    return {"route":route,
            "regular_roundtrip_eur":round(regular*travelers*2,2) if regular is not None else None,
            "discounted_roundtrip_without_card_eur":round(discounted*travelers*2,2),
            "weekend_with_new_card_eur":round(discounted*travelers*2+card_price,2)
                         if travelers==2 and destination!="basel" else None,
            "card_eur":card_price,"status":"conditional_2026_reference",
            "regular_status":route["regular_fare_status"]}


def outing_research_snapshot(guide:dict,eur_fx:float=6.3,chf_fx:float=7.1,
                             data:dict|None=None,meal_band:str="median")->dict:
    """Reference for one documented lunch; not an additional charge to global budget."""
    if min(eur_fx,chf_fx)<=0:raise ValueError("Invalid FX")
    if meal_band not in {"low","median","high"}:
        raise ValueError("Invalid observed meal option")
    source=data if data is not None else load_research()
    city=guide["destination_id"]
    meals=menu_examples(city,source)
    rail=rail_cost_options(guide["base_id"],city,guide["travelers"],source)
    transit=transit_examples(city,source)
    tickets=guide["known_admission"]
    # Only print a combined meal+rail example when regular rail fare is
    # directly published or this is a local outing. Never assume Fluo eligibility.
    rail_complete=guide["local"] or rail["regular_roundtrip_eur"] is not None
    rail_regular=0. if guide["local"] else rail["regular_roundtrip_eur"]
    fare_eur=rail_regular if rail_complete else None
    meal_bands_brl={}
    for kind in ("low","median","high"):
        value=meals[kind]
        if value is None:
            meal_bands_brl[kind]=None
        else:
            fx=eur_fx if meals["currency"]=="EUR" else chf_fx
            meal_bands_brl[kind]=round(value*guide["travelers"]*fx,2)
    sample_total=None
    if fare_eur is not None and meals["median"] is not None:
        price=guide["known_admission"]["EUR"]*eur_fx+guide["known_admission"]["CHF"]*chf_fx
        price+=fare_eur*eur_fx+meal_bands_brl[meal_band]
        sample_total=round(price,2)
    warnings=[
        "Amostra não aleatória: preços de restaurantes específicos, não média do destino.",
        "Menus podem ser restritos a dias úteis; não foram cotados para a data de 2027.",
        "Comida fora pode substituir uma refeição já provisionada no orçamento: não somar duas vezes.",
        "Custo do cartão Fluo deve ser cobrado uma vez por titular, não por passeio.",
        "Tarifas de volta, transporte urbano, bebidas, outras refeições e atrasos podem estar pendentes."
    ]
    if not rail_complete and not guide["local"]:
        warnings.append("Preço regular para 2 adultos não comprovado; só desconto condicionado publicado.")
    if not meals["items"]:
        warnings.append("Sem cardápio pesquisado para este destino.")
    return {"destination":city,"base":guide["base_id"],"meal":meals,"rail":rail,
            "transit":transit,"meal_bands_brl":meal_bands_brl,
            "regular_fare_eur_couple":fare_eur,
            "lunch_plus_rail_and_known_tickets_brl":sample_total,
            "meal_band":meal_band,
            "scenario_status":"illustrative_partial" if sample_total is not None
                              else "insufficient_data",
            "warnings":warnings,"checked_at":source["checked_at"],
            "exchange_rates_hypothetical":True,
            "quote_complete_for_2027":False}


def selected_trip_research(plan:dict,catalog:dict,routes:dict,
                           eur_fx:float,chf_fx:float,
                           data:dict|None=None)->dict:
    """One lunch for each selected destination; never write into total budget.

    Missing meal or regular rail prevents a reliable all-outings sum.
    """
    from outing_guide_model import build_outing_guide
    source=data if data is not None else load_research()
    band={"economy":"low","balanced":"median","experience":"high"}.get(
        plan.get("profile","balanced"),"median")
    parts=[];subtotal=Decimal("0");unpriced=[]
    for destination,ids in plan["packages"].items():
        guide=build_outing_guide(plan,catalog,routes,destination,ids)
        snapshot=outing_research_snapshot(guide,eur_fx,chf_fx,source,
                                          meal_band=band)
        parts.append(snapshot)
        number=snapshot["lunch_plus_rail_and_known_tickets_brl"]
        if number is None:unpriced.append(destination)
        else:subtotal+=Decimal(str(number))
    return {"parts":parts,"meal_band":band,
            "priced_count":len(parts)-len(unpriced),
            "total_count":len(parts),"unpriced_destinations":unpriced,
            "priced_subtotal_brl":round(float(subtotal),2),
            "full_coverage":bool(parts) and not unpriced,
            "not_comparable_to_global_budget_directly":True}


def compare_city_bases(plan:dict,catalog:dict,routes:dict,
                       eur_fx:float,chf_fx:float,
                       data:dict|None=None)->list[dict]:
    """Compare unchanged official outings across four bases, preserving unknowns."""
    from attractions_model import route_for
    source=data if data is not None else load_research()
    result=[]
    for base in ("mulhouse","strasbourg","metz","nancy"):
        draft={**plan,"base_city":base}
        budget=selected_trip_research(draft,catalog,routes,eur_fx,chf_fx,source)
        minutes=0;missing_routes=[]
        for destination in draft["packages"]:
            if destination==base:continue
            travel=route_for(routes,base,destination)
            one_way=travel["train_minutes_one_way"]
            if one_way is None:missing_routes.append(destination)
            else:minutes+=one_way*2
        result.append({
            "base":base,"known_train_roundtrip_minutes":minutes,
            "unknown_duration_destinations":missing_routes,
            "researched_partial_brl":budget["priced_subtotal_brl"],
            "priced_outings":budget["priced_count"],
            "total_outings":budget["total_count"],
            "unpriced_outings":budget["unpriced_destinations"],
            "not_full_cost":True
        })
    return result
