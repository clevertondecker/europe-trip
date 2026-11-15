"""One planning journey for Italy and France, with flexible periods.

`packages` remains the canonical source for France outings and financial
projections; `assignments` remains the precise-date schedule. Optional
`flexible_visits` stores *metadata* about choice and period and does not
represent a reservation or incur an additional transport fare.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date,timedelta
from planning_store import change_plan
from catalog_plan_validation import allowed_attractions
from italy_honeymoon_model import load_honeymoon, italy_itinerary_places, proposal_snapshot

ITALY_STAGE="Itália"
FRANCE_STAGE="França"  # compatibility ID for preexisting plans
EUROPE_STAGE_LABEL="Temporada europeia"
UNASSIGNED="Ainda não definido"
ITALY_PERIODS=(UNASSIGNED,"Durante Roma","Durante a Costa Amalfitana",
               "Férias na Itália")
FRANCE_PERIODS=(UNASSIGNED,"Instalação na França","Férias restantes",
                "Primeiro fim de semana na França",
                "Fim de semana a definir","Durante a estadia na França")

# The only authoritative Italian catalog is embedded with the honeymoon
# proposals in data/italy_honeymoon_research_2027.json. Do not copy it here.
def italian_catalog()->list[dict]:
    return italy_itinerary_places()



def period_options(stage:str)->tuple[str,...]:
    if stage==ITALY_STAGE:return ITALY_PERIODS
    if stage==FRANCE_STAGE:return FRANCE_PERIODS
    raise ValueError("Etapa desconhecida")


def destinations(catalog:dict)->list[dict]:
    italy=[{"id":d["id"],"name":d["name"],"stage":ITALY_STAGE,
            "attractions":deepcopy(d["attractions"]),
            "research":"Pesquisa Itália e propostas de lua de mel"}
           for d in italian_catalog()]
    france=[{"id":d["id"],"name":d["name"],"stage":FRANCE_STAGE,
             "attractions":[{"id":a["id"],"name":a["name"]}
                            for a in catalog["attractions"]
                            if a["destination_id"]==d["id"]],
             "research":"Pesquisa de atrações"}
            for d in catalog["destinations"]]
    return italy+france


def get_choice(catalog:dict,dest_id:str)->dict:
    item=next((d for d in destinations(catalog) if d["id"]==dest_id),None)
    if item is None:raise ValueError("Destino desconhecido")
    return item


def selected_rows(plan:dict,catalog:dict)->list[dict]:
    lookup={d["id"]:d for d in destinations(catalog)}
    rows={}
    for key,picked in plan.get("packages",{}).items():
        if key in lookup:
            rows[key]={"id":key,"name":lookup[key]["name"],
                       "stage":FRANCE_STAGE,"attractions":picked,
                       "period":UNASSIGNED,"exact_dates":[
                           day for day,d in plan.get("assignments",{}).items() if d==key]}
    for item in plan.get("flexible_visits",[]):
        key=item["destination_id"]
        if key not in lookup:continue
        if item["stage"]==FRANCE_STAGE and key not in plan.get("packages",{}):
            continue  # The existing canonical outing editor removed this destination.
        attractions=(plan["packages"][key] if item["stage"]==FRANCE_STAGE
                     else item["attractions"])
        rows[key]={"id":key,"name":lookup[key]["name"],"stage":item["stage"],
                   "attractions":attractions,"period":item["period"],
                   "exact_dates":([item["exact_date"]]
                                  if item.get("exact_date") else
                                  rows.get(key,{}).get("exact_dates",[]))}
    return sorted(rows.values(),key=lambda x:(x["stage"]!=ITALY_STAGE,x["name"]))


def choice_counts(plan:dict,catalog:dict)->dict:
    rows=selected_rows(plan,catalog)
    return {"destinations":len(rows),
            "organized":sum(bool(x["period"]!=UNASSIGNED or x["exact_dates"]) for x in rows),
            "italy":sum(x["stage"]==ITALY_STAGE for x in rows),
            "france":sum(x["stage"]==FRANCE_STAGE for x in rows)}


def is_selected(plan:dict,dest_id:str)->bool:
    return dest_id in plan.get("packages",{}) or any(
        v["destination_id"]==dest_id for v in plan.get("flexible_visits",[]))


def _validated_choice(catalog:dict,dest_id:str,attractions:list[str],period:str)->dict:
    item=get_choice(catalog,dest_id)
    allowed={a["id"] for a in item["attractions"]}
    if (not isinstance(attractions,list) or not 1<=len(attractions)<=5
        or len(attractions)!=len(set(attractions)) or not set(attractions)<=allowed):
        raise ValueError("Selecione de uma a cinco atrações válidas e distintas")
    if period not in period_options(item["stage"]):
        raise ValueError("Período inválido para esta etapa")
    return {"destination_id":dest_id,"stage":item["stage"],
            "attractions":list(attractions),"period":period}


def upsert_choice(plan:dict,catalog:dict,dest_id:str,
                  attractions:list[str],period:str=UNASSIGNED)->dict:
    """One atomic canonical revision, including France `packages` when needed."""
    item=_validated_choice(catalog,dest_id,attractions,period)
    visits=deepcopy(plan.get("flexible_visits",[]))
    old=next((v for v in visits if v["destination_id"]==dest_id),None)
    if old and old.get("exact_date") and item["stage"]==ITALY_STAGE:
        item["exact_date"]=old["exact_date"]
    visits=[v for v in visits if v["destination_id"]!=dest_id]+[item]
    updates={"flexible_visits":visits}
    if item["stage"]==FRANCE_STAGE:
        allowed=allowed_attractions(catalog,dest_id)
        if not set(attractions)<=allowed:
            raise ValueError("Atrações não pertencem ao destino")
        packages=deepcopy(plan["packages"])
        packages[dest_id]=list(attractions)
        updates["packages"]=packages
    return change_plan(plan,updates)


def remove_choice(plan:dict,catalog:dict,dest_id:str)->dict:
    stage=get_choice(catalog,dest_id)["stage"]
    visits=[v for v in plan.get("flexible_visits",[]) if v["destination_id"]!=dest_id]
    changes={"flexible_visits":visits}
    if stage==FRANCE_STAGE:
        packages=deepcopy(plan["packages"])
        packages.pop(dest_id,None)
        changes["packages"]=packages
        changes["assignments"]={day:dest for day,dest in plan.get("assignments",{}).items()
                                 if dest!=dest_id}
    return change_plan(plan,changes)


def schedule_italy_day(plan:dict,catalog:dict,dest_id:str,
                       chosen_day:str|None)->dict:
    """Organize an Italian visit by day without changing French assignments."""
    item=get_choice(catalog,dest_id)
    if item["stage"]!=ITALY_STAGE:
        raise ValueError("Datas francesas pertencem ao calendário do roteiro")
    visits=deepcopy(plan.get("flexible_visits",[]))
    target=next((v for v in visits if v["destination_id"]==dest_id),None)
    if target is None:
        raise ValueError("Inclua o lugar no roteiro antes de organizar o dia")
    if chosen_day is not None:
        try: picked=date.fromisoformat(chosen_day)
        except (TypeError,ValueError) as exc:
            raise ValueError("Dia inválido") from exc
        departure=date.fromisoformat(plan["departure_date"])
        if not departure<=picked<departure+timedelta(days=plan["italy_days"]):
            raise ValueError("Dia fora da etapa italiana")
        target["exact_date"]=chosen_day
    else:
        target.pop("exact_date",None)
    return change_plan(plan,{"flexible_visits":visits})


def italy_starter_preview(plan:dict,catalog:dict,variant:str)->dict:
    """Preview a *complete, distinct* proposal before a single atomic adoption."""
    data=load_honeymoon()
    snapshot=proposal_snapshot(data,variant)
    lookup={d["id"]:d for d in destinations(catalog)}
    starter=[]
    for dest_id in snapshot["itinerary_place_ids"]:
        available=lookup[dest_id]["attractions"]
        # Rome's three major research clusters and Amalfi's first two,
        # plus at least one attraction per other research-backed stop.
        count=3 if dest_id=="italy_rome" else 2 if dest_id=="italy_amalfi" else 1
        chosen=[a["id"] for a in available[:count]]
        period=("Durante Roma" if dest_id=="italy_rome"
                else "Durante a Costa Amalfitana")
        starter.append((dest_id,chosen,period))
    added=[x for x in starter if not is_selected(plan,x[0])]
    unchanged=[x[0] for x in starter if is_selected(plan,x[0])]
    return {"variant":variant,"snapshot":snapshot,"to_add":added,
            "unchanged":unchanged,"requires_confirmation":True,
            "does_not_set_dates":True,"hotel_base_approved":False,
            "reservations":False}


def adopt_italy_starter(plan:dict,catalog:dict,variant:str,
                        *,confirmed:bool=False)->dict:
    if not confirmed:return deepcopy(plan)
    preview=italy_starter_preview(plan,catalog,variant)
    visits=deepcopy(plan.get("flexible_visits",[]))
    for dest_id,ids,period in preview["to_add"]:
        visits.append(_validated_choice(catalog,dest_id,ids,period))
    # A single revision contains the full proposal (day by day, coast base,
    # and 4/4/1 vs. 4/5/0 nights), preserving existing individual selections.
    return change_plan(plan,{"flexible_visits":visits,
                             "italy_proposal":preview["snapshot"]})


def validate_flow_backup(plan:dict,catalog:dict)->None:
    """Review every imported flexible choice before it can enter this session."""
    from trip_plan_model import validate_plan
    from catalog_plan_validation import validate_catalog_packages
    validate_plan(plan)
    validate_catalog_packages(plan,catalog)
    if plan.get("italy_proposal") is not None:
        stored=plan["italy_proposal"]
        original=proposal_snapshot(load_honeymoon(),stored["variant"])
        if set(stored)!=set(original):
            raise ValueError("Formato da proposta italiana não reconhecido")
        if stored["status"]!="proposta exploratória" or stored["reserved"] or stored["hotel_confirmed"]:
            raise ValueError("Backup não pode afirmar reserva italiana")
    for row in plan.get("flexible_visits",[]):
        clean=_validated_choice(catalog,row["destination_id"],
                                row["attractions"],row["period"])
        if {k:row[k] for k in clean}!=clean:
            raise ValueError("Etapa ou atração divergente do catálogo")
        if row["stage"]==FRANCE_STAGE and plan["packages"].get(
                row["destination_id"])!=row["attractions"]:
            raise ValueError("Passeio francês divergente entre calendário e roteiro")
