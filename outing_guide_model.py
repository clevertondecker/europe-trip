"""One source-of-truth, base-aware guide for each selected or suggested outing.

All amounts come from the existing 2026 sourced catalog/route matrix.
Station-to-station time is *not* door-to-door time; unknown costs stay unknown.
"""
from __future__ import annotations

from attractions_model import (package_cost, route_for,
                               approximate_feasibility, line_of_sight_km)

def build_outing_guide(plan:dict,catalog:dict,routes:dict,destination_id:str,
                       attraction_ids:list[str],*,travelers:int=2)->dict:
    destinations={d["id"]:d for d in catalog["destinations"]}
    attractions={a["id"]:a for a in catalog["attractions"]}
    if destination_id not in destinations:
        raise ValueError("Destino não existe no catálogo")
    if not attraction_ids or len(attraction_ids)>5 or len(set(attraction_ids))!=len(attraction_ids):
        raise ValueError("Passeio deve conter de 1 a 5 atrações diferentes")
    if any(key not in attractions or attractions[key]["destination_id"]!=destination_id
           for key in attraction_ids):
        raise ValueError("Atração não pertence ao destino escolhido")
    base_id=plan["base_city"]
    if base_id not in destinations:
        raise ValueError("Cidade-base não existe no catálogo")
    route=route_for(routes,base_id,destination_id)
    selected=[attractions[key] for key in attraction_ids]
    cost=package_cost(catalog,routes,base_id,attraction_ids,travelers=travelers)
    other=[a for a in catalog["attractions"]
           if a["destination_id"]==destination_id and a["id"] not in attraction_ids
           and plan.get("preferences",{}).get(a["id"])!="Descartar"]
    other.sort(key=lambda a:(0 if a["category"] in {"história","arquitetura","natureza",
                                                       "foto/paisagem"} else 1,a["name"]))
    route_mins=route["train_minutes_one_way"]
    is_local=base_id==destination_id
    visit_mins=sum(a["visit_minutes"] for a in selected)
    known_transport={"EUR":0.,"CHF":0.}
    known_admission={"EUR":0.,"CHF":0.}
    for row in cost["breakdown"]:
        category=known_transport if row["item"].startswith("Transporte ") else known_admission
        category[row["currency"]]+=row["known_eur"]
    for values in (known_transport,known_admission):
        for cur in values:values[cur]=round(values[cur],2)
    required_checks=list(cost["missing"])
    if not is_local:
        if route_mins is None:required_checks.append("Tempo ferroviário entre base e destino")
        if route["transfers"] is None:required_checks.append("Conexões ferroviárias")
        if route["first_last_mile_minutes"] is None:required_checks.append("Deslocamento estação ↔ atrações")
        if not route["weekend_return_verified"]:required_checks.append("Último trem/retorno e horários do dia")
        if route["fare_type"]=="discount_carte_fluo":
            required_checks.append("Elegibilidade e custo do cartão Carte Fluo")
    else:
        required_checks.append("Deslocamento urbano/local a verificar")
    if any(a["opening_hours"] is None for a in selected):
        required_checks.append("Horários de funcionamento das atrações na data escolhida")
    required_checks += ["Alimentação do casal durante o passeio",
                        "Outros gastos pessoais e transporte local"]
    destination=destinations[destination_id]
    distance=route["distance_km"]
    distance_kind=route["distance_kind"]
    return {
        "base_id":base_id,"base_name":destinations[base_id]["name"],
        "base":destinations[base_id],
        "destination_id":destination_id,"destination":destination,
        "route":route,"selected":selected,"optional":other,
        "visit_minutes_editorial":visit_mins,
        "roundtrip_train_minutes_station_only":route_mins*2 if route_mins is not None else None,
        "train_minutes_one_way":route_mins,
        "distance_km_documented":distance if distance_kind!="unknown" else None,
        "distance_kind":distance_kind,
        "distance_straight_km":line_of_sight_km(destinations[base_id],destination),
        "fare_eur_person_oneway":route["fare_eur_person_oneway"],
        "fare_type":route["fare_type"],
        "feasibility":approximate_feasibility(destination,route),
        "known_cost":cost["known_by_currency"],
        "known_transport":known_transport,"known_admission":known_admission,
        "breakdown":cost["breakdown"],
        "missing":sorted(set(required_checks)),
        "cost_missing":cost["missing"],"conditional":cost["conditional"],
        "route_source":route["source_url"],"route_checked_at":route["retrieved_at"],
        "catalog_checked_at":catalog.get("checked_at"),
        "local":is_local,"travelers":travelers,
        "quote_complete_for_2027":False,
    }


def additional_estimate(guide:dict,*,eur_fx:float,chf_fx:float,
                        dining_per_person_eur:float|None=None,
                        local_transport_per_person_eur:float|None=None,
                        extra_for_couple_eur:float|None=None)->dict:
    """User-supplied what-if only; always separate from the official budget."""
    base=guide["known_cost"]["EUR"]*eur_fx+guide["known_cost"]["CHF"]*chf_fx
    if any(x is None for x in (dining_per_person_eur,local_transport_per_person_eur,
                              extra_for_couple_eur)):
        return {"known_brl":round(base,2),"scenario_brl":None}
    inputs=(dining_per_person_eur,local_transport_per_person_eur,extra_for_couple_eur)
    if any(x<0 for x in inputs) or eur_fx<=0 or chf_fx<=0:
        raise ValueError("Hipóteses precisam ser não negativas e câmbio positivo")
    extra_eur=(dining_per_person_eur+local_transport_per_person_eur)*guide["travelers"]+extra_for_couple_eur
    return {"known_brl":round(base,2),
            "scenario_brl":round(base+extra_eur*eur_fx,2),
            "extras_eur":round(extra_eur,2)}
