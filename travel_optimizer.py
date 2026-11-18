"""Bounded, deterministic draft calendar optimization; never commits a proposal."""
from __future__ import annotations
from datetime import date
from calendar_model import calendar_plan
from attractions_model import route_for
from trip_plan_model import validate_plan

def available_days(plan):
    days=calendar_plan(date.fromisoformat(plan["departure_date"]),plan["total_days"],
                       plan["italy_days"],plan["vacation_days"],plan["setup_days"])
    return [d for d in days if d["stage"]=="França" and d["activity"]!="Instalação"
            and "Trabalho remoto" not in d["activity"]]

def propose_schedule(plan,attractions,routes,profile="balanced",max_variants=3):
    """Heuristic: prioritize verified short rail, vacation for long/Alps.

    Unknown connections remain unresolved rather than placed optimistically.
    """
    validate_plan(plan)
    if profile not in {"balanced","economy","experience"}:raise ValueError("profile")
    if not plan["packages"]:
        return []
    by_dest={d["id"]:d for d in attractions["destinations"]}
    days=available_days(plan)
    taken=set(plan.get("assignments",{}))
    eligible=[x for x in days if x["date"] not in taken]
    jobs=[]
    unresolved=[]
    for dest, ids in plan["packages"].items():
        if dest in plan["assignments"].values():continue
        if dest not in by_dest:
            unresolved.append({"destination":dest,"reason":"Destino desconhecido"})
            continue
        if by_dest[dest]["kind"]=="overnight":
            unresolved.append({"destination":dest,"reason":"Pernoite e conexões não verificados"})
            continue
        route=route_for(routes,plan["base_city"],dest)
        oneway=route["train_minutes_one_way"]
        if dest!=plan["base_city"] and (type(oneway) is not int or oneway<=0):
            unresolved.append({"destination":dest,"reason":"Tempo de deslocamento não verificado"})
            continue
        length=sum(a["visit_minutes"] for a in attractions["attractions"] if a["id"] in ids)
        if length>7*60:
            unresolved.append({"destination":dest,"reason":"Tempo dentro das atrações superior a 7h"})
            continue
        # A zero here is strictly a rail sorting penalty for a local outing,
        # never an estimate of walking / urban travel.
        jobs.append((dest,oneway if dest!=plan["base_city"] else 0))
    # Stable deterministic sort; optional priorities cannot remove mandatory selections.
    if profile=="economy": jobs.sort(key=lambda x:(x[1],x[0]))
    elif profile=="experience":jobs.sort(key=lambda x:(-x[1],x[0]))
    else:jobs.sort(key=lambda x:(x[1]>70,x[1],x[0]))
    proposals=[]
    for variant in range(min(max_variants,3)):
        mapping=dict(plan.get("assignments",{}))
        reserved=set(mapping)
        placed=[]
        for dest,minutes in jobs:
            # Early vacation for longer outings, weekend otherwise, never a workday.
            options=sorted([d for d in eligible if d["date"] not in reserved],
                key=lambda d: (0 if (minutes>70 and "Férias" in d["activity"]) or
                         (minutes<=70 and "Fim de semana" in d["activity"]) else 1,
                         d["date"]))
            if variant==1:options=list(reversed(options))
            if variant==2:options=sorted(options,key=lambda d:(abs(d["day"]-30),d["date"]))
            if not options:
                unresolved.append({"destination":dest,"reason":"Sem dia livre suficiente"})
                continue
            selected=options[0]
            mapping[selected["date"]]=dest
            reserved.add(selected["date"])
            placed.append(dest)
        proposals.append({
           "proposal_id":f"{plan['plan_id']}:r{plan['revision']}:{profile}:{variant}",
           "base_revision":plan["revision"],"base_city":plan["base_city"],
           "assignments":mapping,"placed":placed,
           "unresolved":list(unresolved),"profile":profile,
           "status":"draft_unapproved",
           "note":"Sugestão heurística, sem horários de abertura/retorno confirmados. Nenhuma reserva."
        })
    for candidate in proposals:
        candidate["score"]=score_proposal(candidate,plan,routes,profile)
    proposals.sort(key=lambda x:(-x["score"]["relative_score"],x["proposal_id"]))
    distinct=[]
    seen=set()
    for candidate in proposals:
        if candidate["assignments"]==plan["assignments"]:
            continue
        signature=tuple(sorted(candidate["assignments"].items()))
        if signature in seen:
            continue
        seen.add(signature)
        distinct.append(candidate)
    return distinct

def score_proposal(proposal,plan,routes,profile):
    """Relative draft ordering only; not an itinerary feasibility assessment."""
    count=len(proposal["placed"])
    # Historical one-way times are not verified return journeys.
    # Preserve the old relative score by using the symmetric value ONLY as
    # an explicit heuristic penalty, not as a known duration.
    outbound_mins = 0
    for dest in proposal["placed"]:
        if dest == plan["base_city"]:
            # A local destination needs no intercity train; local transit is unknown.
            continue
        minutes = route_for(routes, plan["base_city"], dest)["train_minutes_one_way"]
        if type(minutes) is not int or minutes <= 0:
            raise ValueError("Cannot score a proposed outing with unknown outbound rail time")
        outbound_mins += minutes
    symmetric_proxy_mins = outbound_mins * 2
    holidays=sum(1 for day,dest in proposal["assignments"].items()
        if day not in plan["assignments"] and date.fromisoformat(day).weekday()<5)
    unfinished=len(proposal["unresolved"])
    if profile=="economy":
        raw= count*70-symmetric_proxy_mins/12-unfinished*30
    elif profile=="experience":
        raw=count*95-symmetric_proxy_mins/35-unfinished*40+holidays*2
    else:
        raw=count*85-symmetric_proxy_mins/20-unfinished*35
    return {"relative_score":round(raw,2),"scheduled":count,
            # Retained legacy field is deliberately null, never an inferred route.
            "known_roundtrip_train_minutes":None,
            "known_outbound_train_minutes":outbound_mins,
            "symmetric_train_proxy_minutes":symmetric_proxy_mins,
            "return_train_minutes":None,
            "local_access_minutes":None,
            "return_2027_verified":False,
            "score_time_basis":"outbound_twice_editorial_proxy_not_verified_return",
            "logistical_feasibility":None,
            "confirmed_2027":False,
            "unscheduled":unfinished,
            "method":"Relative draft-ordering heuristic; twice the known outbound is only a penalty proxy. Return, access, openings and 2027 availability are NOT verified."}
