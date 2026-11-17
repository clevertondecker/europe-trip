"""UX 4.8: lightweight weekend group sidecar; never duplicates TripPlan choices.

It remains an explicitly exported/imported draft, NOT a new canonical plan,
booking, budget component, or auto-saved remote document.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date,timedelta
import json
from uuid import uuid4
from calendar_model import calendar_plan
from itinerary_flow_model import selected_rows,FRANCE_STAGE
from trip_plan_model import validate_plan,BASES

SCHEMA=1
STATUS=("estudo","planejado")
PERIODS=("Ainda não definido","Instalação na França","Férias restantes",
         "Trabalho remoto · fim de semana","A definir")
MAX_GROUPS=24

def _selected(plan,catalog):
    return {r["id"]:r for r in selected_rows(plan,catalog)
            if r["stage"]==FRANCE_STAGE}

def _season_days(plan):
    return {r["date"]:r for r in calendar_plan(
        date.fromisoformat(plan["departure_date"]),plan["total_days"],
        plan["italy_days"],plan["vacation_days"],plan["setup_days"])}

def _trip_days(start, nights):
    """Saturday/Sunday minimum; additional nights extend the occupied interval."""
    first=date.fromisoformat(start)
    return [(first+timedelta(days=n)).isoformat()
            for n in range(max(2,nights+1))]

def _rest_days(start):
    return _trip_days(start,1)

def empty_groups(plan):
    validate_plan(plan)
    return {"schema_version":SCHEMA,"plan_id":plan["plan_id"],
            "groups":[],"rest_weekends":[]}

def validate_groups(state,plan,catalog):
    validate_plan(plan)
    if not isinstance(state,dict) or set(state)!={"schema_version","plan_id","groups","rest_weekends"}:
        raise ValueError("Formato de fins de semana inválido")
    if state["schema_version"]!=SCHEMA or state["plan_id"]!=plan["plan_id"]:
        raise ValueError("Rascunho pertence a outro planejamento")
    groups=state["groups"]
    if not isinstance(groups,list) or len(groups)>MAX_GROUPS:
        raise ValueError("Quantidade de viagens inválida")
    chosen=_selected(plan,catalog)
    season=_season_days(plan)
    occupied={}
    used=set()
    assigned_to_group=set()
    for group in groups:
        keys={"id","name","destinations","period","start_date","nights",
              "base_city","notes","status"}
        if not isinstance(group,dict) or set(group)!=keys:
            raise ValueError("Grupo possui campos incompatíveis")
        gid=group["id"]
        if not isinstance(gid,str) or not gid.startswith("weekend-") or gid in used:
            raise ValueError("Identificador do grupo inválido")
        used.add(gid)
        dests=group["destinations"]
        if (not isinstance(dests,list) or not 1<=len(dests)<=6 or
            len(dests)!=len(set(dests)) or any(d not in chosen for d in dests)):
            raise ValueError("Grupo contém destino não escolhido")
        if assigned_to_group.intersection(dests):
            raise ValueError("Passeio já associado a outra viagem")
        assigned_to_group.update(dests)
        if not isinstance(group["name"],str) or not 1<=len(group["name"].strip())<=100:
            raise ValueError("Nome de viagem inválido")
        if (group["period"] not in PERIODS or group["status"] not in STATUS or
            group["base_city"] not in BASES or
            type(group["nights"]) is not int or not 0<=group["nights"]<=3 or
            not isinstance(group["notes"],str) or len(group["notes"])>700):
            raise ValueError("Premissas inválidas do grupo")
        start=group["start_date"]
        if start is None:continue
        if not isinstance(start,str) or start not in season or date.fromisoformat(start).weekday()!=5:
            raise ValueError("Fim de semana inválido ou fora da temporada")
        days=_trip_days(start,group["nights"])
        if any(day not in season or season[day]["stage"]!=FRANCE_STAGE or
               season[day]["activity"]=="Instalação" for day in days):
            raise ValueError("Fim de semana coincide com Itália ou instalação")
        for day in days:
            if day in occupied:
                raise ValueError("Dois grupos ocupam o mesmo fim de semana")
            occupied[day]=gid
            assignment=plan["assignments"].get(day)
            if assignment is not None and assignment not in dests:
                raise ValueError("Data já atribuída a outro passeio no TripPlan")
        # A destination already committed elsewhere cannot be silently moved.
        for dest in dests:
            chosen_dates=chosen[dest]["exact_dates"]
            if chosen_dates and any(d not in days for d in chosen_dates):
                raise ValueError("Passeio possui data definida fora deste fim de semana")
    rests=state["rest_weekends"]
    if not isinstance(rests,list) or len(rests)!=len(set(rests)):
        raise ValueError("Descansos duplicados")
    for start in rests:
        if not isinstance(start,str) or start not in season or date.fromisoformat(start).weekday()!=5:
            raise ValueError("Descanso fora da temporada europeia")
        days=_rest_days(start)
        if any(day not in season or season[day]["stage"]!=FRANCE_STAGE
               or season[day]["activity"]=="Instalação" for day in days):
            raise ValueError("Descanso fora da temporada europeia")
        if any(day in occupied or day in plan["assignments"] for day in days):
            raise ValueError("Descanso conflita com passeio ou compromisso oficial")
    return deepcopy(state)

def create_group(state,plan,catalog,*,name,destinations,period="Ainda não definido",
                 start_date=None,nights=0,notes="",status="estudo"):
    draft=deepcopy(state)
    draft["groups"].append({"id":"weekend-"+uuid4().hex[:12],"name":name,
        "destinations":list(destinations),"period":period,"start_date":start_date,
        "nights":nights,"base_city":plan["base_city"],"notes":notes,"status":status})
    return validate_groups(draft,plan,catalog)

def update_group(state,plan,catalog,group_id,**changes):
    draft=deepcopy(state)
    group=next((x for x in draft["groups"] if x["id"]==group_id),None)
    if group is None:raise ValueError("Grupo não encontrado")
    if set(changes)-{"name","destinations","period","start_date","nights","notes","status"}:
        raise ValueError("Campos de grupo imutáveis")
    group.update(changes)
    return validate_groups(draft,plan,catalog)

def remove_group(state,plan,catalog,group_id):
    draft=deepcopy(state)
    draft["groups"]=[x for x in draft["groups"] if x["id"]!=group_id]
    if len(draft["groups"])==len(state["groups"]):raise ValueError("Grupo não encontrado")
    return validate_groups(draft,plan,catalog)

def reconcile_removed_outings(state,plan,catalog):
    """Keep all valid groups; clear outdated dates instead of losing itineraries."""
    if state["plan_id"]!=plan["plan_id"]:return empty_groups(plan)
    result=deepcopy(state)
    choices=_selected(plan,catalog)
    season=_season_days(plan)
    kept=[]
    for group in result["groups"]:
        group["destinations"]=[x for x in group["destinations"] if x in choices]
        if group["destinations"]:kept.append(group)
    result["groups"]=kept
    result["rest_weekends"]=[start for start in result["rest_weekends"]
         if isinstance(start,str) and start in season and
         date.fromisoformat(start).weekday()==5 and
         all(day in season and season[day]["stage"]==FRANCE_STAGE and
             season[day]["activity"]!="Instalação" and
             day not in plan["assignments"] for day in _rest_days(start))]
    # Validate the aggregate after each reconciliation so overlaps are resolved
    # deterministically; all destinations/notes remain intact.
    accepted=[]
    for group in kept:
        candidate=deepcopy(group)
        partial={**result,"groups":accepted+[candidate]}
        try:
            validate_groups(partial,plan,catalog)
        except ValueError:
            candidate["start_date"]=None
            validate_groups({**result,"groups":accepted+[candidate]},plan,catalog)
        accepted.append(candidate)
    result["groups"]=accepted
    return validate_groups(result,plan,catalog)

def ungrouped_outings(state,plan,catalog):
    taken={d for g in state["groups"] for d in g["destinations"]}
    return [r for r in _selected(plan,catalog).values() if r["id"] not in taken]

def available_weekends(state,plan,catalog):
    validate_groups(state,plan,catalog)
    days=_season_days(plan)
    scheduled={day:g for g in state["groups"] if g["start_date"]
               for day in _trip_days(g["start_date"],g["nights"])}
    slots=[]
    for day,row in sorted(days.items()):
        dt=date.fromisoformat(day)
        if dt.weekday()!=5 or row["stage"]!=FRANCE_STAGE:continue
        sunday=(dt+timedelta(days=1)).isoformat()
        if sunday not in days or days[sunday]["stage"]!=FRANCE_STAGE:continue
        if day in scheduled or sunday in scheduled:
            trip=scheduled.get(day) or scheduled[sunday]
            status="pernoite possível" if trip["nights"] else "viagem planejada"
        elif day in state["rest_weekends"]:status="descanso escolhido"
        elif row["activity"]=="Instalação" or days[sunday]["activity"]=="Instalação":
            status="indisponível · instalação"
        elif day in plan["assignments"] or sunday in plan["assignments"]:
            status="passeio com data no TripPlan"
        else:status="livre · não reservado"
        slots.append({"start":day,"end":sunday,"status":status,
                      "group":(scheduled.get(day) or scheduled.get(sunday) or {}).get("name")})
    return slots

def set_rest_weekend(state,plan,catalog,start,rest:bool):
    draft=deepcopy(state)
    value=set(draft["rest_weekends"])
    if rest:value.add(start)
    else:value.discard(start)
    draft["rest_weekends"]=sorted(value)
    return validate_groups(draft,plan,catalog)

def export_groups(state,plan,catalog):
    return json.dumps(validate_groups(state,plan,catalog),ensure_ascii=False,indent=2)

def import_groups(text,plan,catalog):
    if not isinstance(text,str) or len(text)>100_000:
        raise ValueError("Arquivo inválido ou grande demais")
    return validate_groups(json.loads(text),plan,catalog)


def eligible_weekends(state, plan, catalog, *, destinations, nights=0,
                      period="Ainda não definido", group_id=None):
    """Preview dates through the same validator used by saves, without mutation."""
    season = _season_days(plan)
    results = []
    for start, row in sorted(season.items()):
        if date.fromisoformat(start).weekday() != 5 or row["stage"] != FRANCE_STAGE:
            continue
        changes = dict(name="Prévia", destinations=destinations, nights=nights,
                       period=period, start_date=start)
        reason = None
        try:
            if group_id is None:
                create_group(state, plan, catalog, **changes)
            else:
                update_group(state, plan, catalog, group_id, **changes)
            activities = [season[day]["activity"] for day in _trip_days(start, nights)]
            if period == "Férias restantes" and any(
                    activity != "Férias · excursões possíveis" for activity in activities):
                reason = "A viagem ultrapassa o período de férias escolhido."
            if period == "Trabalho remoto · fim de semana" and any(
                    activity == "Férias · excursões possíveis" for activity in activities):
                reason = "A viagem começa antes do período de trabalho remoto."
            if period == "Instalação na França":
                reason = "Os dias de instalação estão protegidos no calendário."
        except ValueError as exc:
            reason = str(exc)
        results.append({"start": start, "end": _trip_days(start, nights)[-1],
                        "eligible": reason is None, "reason": reason})
    return results
