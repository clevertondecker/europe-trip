"""Deterministic destination discovery from the verified editorial catalog.

Unknown fares are never interpreted as free. Scores are relative editorial
ranking aids, NOT reliability, trip availability or financial quotations.
"""
from __future__ import annotations
from collections import defaultdict
from attractions_model import route_for,package_cost
from travel_advisor import objective_weights

CATEGORY_INTEREST={"natureza","foto/paisagem","história","arquitetura","museu","gastronomia"}
def recommend_destinations(plan:dict,catalog:dict,routes:dict,profile:str|None=None,
                           max_travel_minutes:int=180,allow_overnight:bool=False,
                           limit:int=11,
                           include_unverified_routes:bool=True)->list[dict]:
    profile=profile or plan["profile"]
    weights=objective_weights(profile)
    base=plan["base_city"]
    selected=set(plan["packages"])
    excluded=set(plan.get("excluded_destinations",[]))
    prefs=plan.get("preferences",{})
    by_destination=defaultdict(list)
    for a in catalog["attractions"]:
        if prefs.get(a["id"])!="Descartar":
            by_destination[a["destination_id"]].append(a)
    results=[]
    for d in catalog["destinations"]:
        dest=d["id"]
        if dest in selected or dest in excluded or not by_destination[dest]:
            continue
        route=route_for(routes,base,dest)
        mins=route["train_minutes_one_way"]
        overnight=d["kind"]=="overnight"
        if overnight and not allow_overnight:
            continue
        if mins is not None and mins>max_travel_minutes:
            continue
        # An unknown duration cannot pass a numeric maximum by assumption.
        # Retain historical behavior for other callers unless explicitly filtered.
        if mins is None and dest!=base and not include_unverified_routes:
            continue
        ordered=sorted(by_destination[dest],
            key=lambda a:(0 if prefs.get(a["id"])=="Quero visitar" else 1,
                          0 if a["category"] in CATEGORY_INTEREST else 1,
                          a["visit_minutes"],a["id"]))
        picks=ordered[:min(2,len(ordered))]
        cost=package_cost(catalog,routes,base,[a["id"] for a in picks])
        preferred=sum(prefs.get(a["id"])=="Quero visitar" for a in ordered)
        interest=min(100,45+preferred*22+len(ordered)*3)
        comfort=(100 if dest==base else max(10,100-(mins or 125)*.42)) if mins is not None or dest==base else 20
        schedule=95 if dest==base else (max(10,95-(mins or 140)*.3) if not overnight else 15)
        known=sum(cost["known_by_currency"].values())
        # The absence of a fare cannot improve cost benefit.
        cost_score=max(10,100-known*.25) if cost["complete"] else 35
        score=round((interest*weights["interest"]+cost_score*weights["cost"]+
                     comfort*weights["comfort"]+schedule*weights["schedule"])/100,2)
        evidence_missing=list(cost["missing"])
        if mins is None and dest!=base:evidence_missing.append("Tempo ferroviário sem verificação")
        if not route["weekend_return_verified"] and dest!=base:
            evidence_missing.append("Último retorno e operação de fim de semana")
        if overnight:evidence_missing.append("Custo e logística de hospedagem")
        trip_type=("Pernoite a investigar" if overnight else
                   "Passeio local" if dest==base else
                   "Bate-volta a verificar" if mins is not None and mins<=70 else
                   "Dia inteiro a verificar")
        results.append({
          "destination_id":dest,"name":d["name"],"country":d["country"],
          "photo":d.get("photo"),"source_url":d["source_url"],
          "kind":d["kind"],"score":score,"train_minutes_one_way":mins,
          "minutes_scope":"estação a estação" if mins is not None else None,
          "trip_type":trip_type,"selected_attractions":[a["id"] for a in picks],
          "attraction_names":[a["name"] for a in picks],"attractions_available":len(ordered),
          "known_costs":cost["known_by_currency"],
          "missing":sorted(set(evidence_missing)),
          "conditional":cost["conditional"],"complete":not evidence_missing,
          "route_source":route["source_url"],
          "base_city":base,
          "fare_type":route["fare_type"],
          "fare_eur_person_oneway":route["fare_eur_person_oneway"],
          "route_verified_minutes":mins is not None or dest==base,
          "reasons":[
              f"{len(ordered)} atrações cadastradas para conhecer",
              "Algumas atrações combinam com seus interesses" if preferred else
              "Opção baseada no catálogo de atrações pesquisado",
              f"Trem histórico: {mins} min por trecho (estação a estação)" if mins is not None
                else "Tempo ferroviário ainda não verificado"],
          "confidence":"parcial" if evidence_missing else "histórico",
          "priority":"Quero visitar" if preferred else "Sugestão",
        })
    return sorted(results,key=lambda x:(-x["score"],x["name"]))[:limit]
