"""Independent, source-aware exploration of alternate French home bases.

No writes to TripPlan, no market-rent proxy used as a short-let quote.
Fares labelled 'desde' are conditional per traveler/leg, not 2027 quotes.
"""
from __future__ import annotations

import json
from pathlib import Path
from math import isfinite

from data_model import get_scenario
from unified_budget import resolve_french_budget,scenario_total

DATA=Path(__file__).resolve().parent/"data"/"exploration_bases_2027.json"


def load_exploration(path:Path=DATA)->dict:
    data=json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version")!=1 or not data.get("checked_at"):
        raise ValueError("Catálogo exploratório incompatível")
    bases=data.get("bases",[])
    destinations=data.get("destinations",[])
    routes=data.get("routes",[])
    base_ids={b["id"] for b in bases}
    destination_ids={d["id"] for d in destinations}
    if len(base_ids)!=len(bases) or len(destination_ids)!=len(destinations):
        raise ValueError("Base ou destino duplicado")
    if not {"lille","arras","dijon","reims","mulhouse","strasbourg","metz","nancy"}<=base_ids:
        raise ValueError("Cidades-base essenciais ausentes")
    for b in bases:
        if b["country"]!="França" or not b.get("name"):
            raise ValueError("Base inválida")
        rent=b["rent_market_eur_m2"]
        if rent is not None and (not isfinite(float(rent)) or rent<=0
                                 or not str(b.get("rent_source_url") or "").startswith("https://")):
            raise ValueError("Aluguel não fundamentado")
    for p in bases+destinations:
        if not -90<=p["lat"]<=90 or not -180<=p["lon"]<=180:
            raise ValueError("Local sem coordenadas válidas")
    pairs=set()
    for r in routes:
        key=(r["base_id"],r["destination_id"])
        if key in pairs or key[0] not in base_ids or key[1] not in destination_ids:
            raise ValueError("Rota duplicada ou inválida")
        pairs.add(key)
        minutes=r["train_minutes_oneway_min"]
        fare=r["fare_from_eur_person_oneway"]
        if (minutes is not None and (type(minutes) is not int or minutes<=0)) or (
            fare is not None and (not isfinite(float(fare)) or fare<=0)
        ):
            raise ValueError("Tempo ou tarifa inválidos")
        if not r["source_url"].startswith("https://") or r["return_verified_2027"] is not False:
            raise ValueError("Rota sem origem ou declarada como confirmada para 2027")
    return data


def classify_travel(minutes:int|None)->str:
    """Editorial only, based on *fastest one-way* station time."""
    if minutes is None:return "Sem dados suficientes"
    if minutes<=90:return "Candidato a bate-volta"
    if minutes<=240:return "Melhor avaliar fim de semana"
    return "Viagem de 2–3 noites a avaliar"


def route_detail(data:dict,base_id:str,destination_id:str,travelers:int=2)->dict:
    bases={b["id"]:b for b in data["bases"]}
    places={d["id"]:d for d in data["destinations"]}
    if base_id not in bases or destination_id not in places:
        raise ValueError("Base ou destino inválido")
    if type(travelers) is not int or travelers<1:
        raise ValueError("Número de viajantes inválido")
    row=next((x for x in data["routes"] if x["base_id"]==base_id
             and x["destination_id"]==destination_id),None)
    if row is None:
        return {"base_id":base_id,"destination_id":destination_id,"minutes":None,
                "roundtrip_train_minimum_minutes":None,"fare_from":None,
                "all_legs_at_from_fare_eur":None,"status":"not_researched",
                "source_url":None,"notes":"Trajeto ainda não pesquisado.",
                "classification":"Sem dados suficientes","return_verified_2027":False}
    minutes=row["train_minutes_oneway_min"]
    fare=row["fare_from_eur_person_oneway"]
    return {"base_id":base_id,"destination_id":destination_id,
            "minutes":minutes,
            "roundtrip_train_minimum_minutes":minutes*2 if minutes is not None else None,
            "fare_from":fare,
            "all_legs_at_from_fare_eur":round(fare*travelers*2,2) if fare is not None else None,
            "status":row["reference_status"],"source_url":row["source_url"],
            "notes":row["notes"],
            "classification":classify_travel(minutes),"return_verified_2027":False}


def compare_bases(data:dict,base_ids:list[str],destinations:list[str],
                  travelers:int=2)->list[dict]:
    """Identical destination set for fair coverage; NEVER rank unknowns as free."""
    if not destinations or len(set(destinations))!=len(destinations):
        raise ValueError("Escolha destinos distintos para comparar")
    if not base_ids or len(set(base_ids))!=len(base_ids):
        raise ValueError("Escolha bases distintas para comparar")
    output=[]
    for base in base_ids:
        rows=[route_detail(data,base,dest,travelers) for dest in destinations]
        known_times=[r["roundtrip_train_minimum_minutes"] for r in rows
                     if r["roundtrip_train_minimum_minutes"] is not None]
        known_fares=[r["all_legs_at_from_fare_eur"] for r in rows
                     if r["all_legs_at_from_fare_eur"] is not None]
        output.append({
            "base_id":base,"routes":rows,
            "known_time_minutes":sum(known_times) if known_times else None,
            "time_coverage":len(known_times),
            "illustrative_fare_if_all_min_eur":round(sum(known_fares),2) if known_fares else None,
            "fare_coverage":len(known_fares),
            "destination_count":len(destinations),
            "fully_priced":len(known_fares)==len(destinations),
            "verified_2027":False,
        })
    return output


def base_opportunities(data:dict,base_id:str)->list[dict]:
    if base_id not in {b["id"] for b in data["bases"]}:
        raise ValueError("Cidade-base não cadastrada")
    names={d["id"]:d for d in data["destinations"]}
    rows=[route_detail(data,base_id,r["destination_id"]) for r in data["routes"]
          if r["base_id"]==base_id]
    return [{**r,"destination":names[r["destination_id"]]} for r in
            sorted(rows,key=lambda r:(r["minutes"] is None,
                                      r["minutes"] or 99999,r["destination_id"]))]


def stay_projection(plan:dict,trip_data:dict,source_live:bool,eurfx:float,
                    base_a:str,base_b:str,days_first:int,
                    rent_a_eur_month:float,rent_b_eur_month:float,
                    moving_eur:float=0,deposit_a_eur:float=0,
                    deposit_b_eur:float=0)->dict:
    """Three comparable user-input *what-if* budgets with baseline components.

    Housing quotes here are user hypotheticals for a furnished apartment for
    the couple, not market €/m². Only housing and a one-off move change.
    No intercity or outing fares are automatically included or assumed free.
    """
    if base_a==base_b:raise ValueError("Escolha bases diferentes")
    days=plan["total_days"]-plan["italy_days"]
    if not 1<=days_first<days:raise ValueError("Divisão dos dias inválida")
    nums=(eurfx,rent_a_eur_month,rent_b_eur_month,moving_eur,
          deposit_a_eur,deposit_b_eur)
    if not all(isinstance(x,(float,int)) and isfinite(float(x)) for x in nums):
        raise ValueError("Valores precisam ser números finitos")
    if eurfx<=0 or min(nums[1:])<0:raise ValueError("Valores/câmbio inválidos")
    # Compatible with the official single-base finance engine: housing
    # replaces its already budgeted rent, so it is NOT added twice.
    scenario=get_scenario(trip_data,plan["budget_scenario"])
    french=resolve_french_budget(scenario,source_live)
    days_second=days-days_first
    weighted_rent=(rent_a_eur_month*days_first+rent_b_eur_month*days_second)/days
    def run(monthly:float,move:float):
        return scenario_total(scenario,french,french_days=days,outings_weekly=2,
                              outing_couple_eur=60,fx_brl_per_eur=eurfx,
                              rent_override_eur_month=monthly,
                              local_transport_delta_brl=move*eurfx)
    first=run(rent_a_eur_month,0)
    second=run(rent_b_eur_month,0)
    split=run(weighted_rent,moving_eur)
    return {
        "days_france":days,"days_first":days_first,"days_second":days_second,
        "housing_single_a_eur":round(rent_a_eur_month*days/30,2),
        "housing_single_b_eur":round(rent_b_eur_month*days/30,2),
        "housing_split_eur":round((rent_a_eur_month*days_first+
                                  rent_b_eur_month*days_second)/30,2),
        "move_eur":moving_eur,
        "cash_deposit_single_a_eur":deposit_a_eur,
        "cash_deposit_single_b_eur":deposit_b_eur,
        "cash_deposit_split_eur":deposit_a_eur+deposit_b_eur,
        "single_a_total_brl":first["total"],
        "single_b_total_brl":second["total"],
        "split_total_brl":split["total"],
        "split_delta_vs_a_brl":round(split["total"]-first["total"],2),
        "split_delta_vs_b_brl":round(split["total"]-second["total"],2),
        "budget_cap_brl":scenario["cap_brl"],
        "hypothetical":True,"quoted_for_2027":False,
        "intercity_trains_included":False,
        "lifestyle_same_across_scenarios":True,
        "deposits_are_expense":False,
    }
