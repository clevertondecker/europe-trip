"""Explicit multi-visit model, separate from legacy assignments.

A repeated destination on another day is a second visit. Cost model consumers
must count one intercity round-trip per distinct visit, not per attraction.
"""
from __future__ import annotations
from datetime import date
from copy import deepcopy
from calendar_model import calendar_plan
from attractions_model import route_for

def legacy_to_visits(assignments:dict,packages:dict)->list[dict]:
    return [{"visit_id":day+"-"+dest,"date":day,"destination_id":dest,
             "attraction_ids":list(packages.get(dest,[]))}
            for day,dest in sorted(assignments.items())]

def validate_repeat_visits(plan:dict,visits:list[dict],catalog:dict|None=None)->list[dict]:
    if not isinstance(visits,list):raise ValueError("Visitas inválidas")
    availability={x["date"]:x for x in calendar_plan(
        date.fromisoformat(plan["departure_date"]),plan["total_days"],
        plan["italy_days"],plan["vacation_days"],plan["setup_days"])}
    known=None if catalog is None else {
        d["id"]:{a["id"] for a in catalog["attractions"] if a["destination_id"]==d["id"]}
        for d in catalog["destinations"]}
    days=set();ids=set();verified=[]
    for visit in visits:
        day=visit["date"];dest=visit["destination_id"];vid=visit["visit_id"]
        if day not in availability or day in days or vid in ids:
            raise ValueError("Data duplicada, inválida ou ID de visita repetido")
        row=availability[day]
        if row["stage"]!="França" or row["activity"]=="Instalação" or "Trabalho remoto" in row["activity"]:
            raise ValueError("Visita de dia inteiro conflita com trabalho, Itália ou instalação")
        selected=visit["attraction_ids"]
        if not isinstance(selected,list) or not selected or len(selected)!=len(set(selected)):
            raise ValueError("Visita sem atrações válidas")
        if known is not None and (dest not in known or not set(selected)<=known[dest]):
            raise ValueError("Atração não pertence ao destino")
        days.add(day);ids.add(vid);verified.append(deepcopy(visit))
    return verified

def intercity_trip_count(visits:list[dict],base_city:str)->dict[str,int]:
    result={}
    for v in visits:
        if v["destination_id"]!=base_city:
            d=v["destination_id"];result[d]=result.get(d,0)+1
    return result

def travel_fares_by_visit(visits:list[dict],routes:dict,base_city:str,travelers:int=2)->dict:
    """Price only known intercity fares; return unknown visits as pending."""
    if travelers<1:raise ValueError("Invalid travelers")
    total=0.0;unknown=[]
    for v in visits:
        if v["destination_id"]==base_city:continue
        route=route_for(routes,base_city,v["destination_id"])
        fare=route["fare_eur_person_oneway"]
        if fare is None:unknown.append(v["visit_id"])
        else:total+=fare*2*travelers
    return {"known_eur":round(total,2),"unknown_visit_ids":unknown}
