"""Single versioned itinerary state; Streamlit-free domain selectors and actions.

Legacy keys are a compatibility cache during migration, never authoritative
once a TripPlan is loaded. No network or persistence side effects.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from trip_plan_model import new_plan,validate_plan,with_revision,BASES
from calendar_assignment_validation import validate_new_assignments

def create_from_legacy(values:dict)->dict:
    """Create *one* plan from older session keys, without mutating the source."""
    p=new_plan()
    p["packages"]=deepcopy(values.get("explore_packages") or {})
    p["assignments"]=deepcopy(values.get("explore_calendar") or {})
    base=values.get("explore_base")
    if base in BASES:p["base_city"]=base
    dt=values.get("itinerary_departure")
    if isinstance(dt,date):p["departure_date"]=dt.isoformat()
    elif isinstance(dt,str):p["departure_date"]=dt
    for key,widget in (("total_days","itinerary_total_days"),
                       ("italy_days","itinerary_italy_days"),
                       ("vacation_days","itinerary_vacation_days"),
                       ("setup_days","itinerary_setup_days")):
        if widget in values:p[key]=values[widget]
    if values.get("unified_scenario") in {"60k","70k"}:
        p["budget_scenario"]=values["unified_scenario"]
    validate_plan(p)
    return p

def change_plan(plan:dict,changes:dict)->dict:
    """One canonical mutation, no redundant revision for an identical value."""
    permitted={"packages","assignments","base_city","profile","budget_scenario",
               "departure_date","total_days","italy_days","vacation_days","setup_days",
               "preferences","excluded_destinations","flexible_visits","italy_proposal"}
    if not changes or not set(changes)<=permitted:
        raise ValueError("Unsupported plan change")
    delta={k:deepcopy(v) for k,v in changes.items() if plan.get(k)!=v}
    if "assignments" in delta:
        candidate={**plan,**delta}
        validate_new_assignments(candidate,candidate["assignments"],
                                 previously_approved=plan["assignments"])
    return with_revision(plan,delta) if delta else deepcopy(plan)

def set_package(plan:dict,destination:str,attractions:list[str],
                valid_destinations:set[str]|None=None,
                valid_attractions:set[str]|None=None)->dict:
    if valid_destinations is not None and destination not in valid_destinations:
        raise ValueError("Destino desconhecido")
    if not attractions or len(attractions)>5 or len(attractions)!=len(set(attractions)):
        raise ValueError("Escolha uma a cinco atrações distintas")
    if valid_attractions is not None and not set(attractions)<=valid_attractions:
        raise ValueError("Atração desconhecida")
    packages=deepcopy(plan["packages"])
    packages[destination]=list(attractions)
    updates={"packages":packages}
    if any(v["destination_id"]==destination for v in plan.get("flexible_visits",[])):
        visits=deepcopy(plan["flexible_visits"])
        for item in visits:
            if item["destination_id"]==destination:
                item["attractions"]=list(attractions)
        updates["flexible_visits"]=visits
    return change_plan(plan,updates)

def remove_package(plan:dict,destination:str)->dict:
    packages=deepcopy(plan["packages"])
    if destination not in packages:return deepcopy(plan)
    del packages[destination]
    dates={day:dest for day,dest in plan["assignments"].items() if dest!=destination}
    visits=[v for v in plan.get("flexible_visits",[])
            if v["destination_id"]!=destination]
    return change_plan(plan,{"packages":packages,"assignments":dates,
                              "flexible_visits":visits})

def add_assignment(plan:dict,day:str,destination:str)->dict:
    if destination not in plan["packages"]:
        raise ValueError("Selecione atrações desse destino antes de agendar")
    date.fromisoformat(day)
    if day in plan["assignments"] and plan["assignments"][day]!=destination:
        raise ValueError("Já existe outro passeio neste dia")
    dates={**plan["assignments"],day:destination}
    return change_plan(plan,{"assignments":dates})

def remove_assignment(plan:dict,day:str)->dict:
    if day not in plan["assignments"]:return deepcopy(plan)
    dates=dict(plan["assignments"])
    del dates[day]
    return change_plan(plan,{"assignments":dates})

def summary(plan:dict)->dict:
    return {"destinations":len(plan["packages"]),
            "attractions":sum(len(x) for x in plan["packages"].values()),
            "scheduled_days":len(plan["assignments"]),
            "budget_scenario":plan["budget_scenario"],
            "base_city":plan["base_city"],"revision":plan["revision"]}

def is_dirty(plan:dict,persisted_plan:dict|None)->bool:
    if persisted_plan is None:return True
    validate_plan(plan)
    return plan!=persisted_plan

def sync_legacy_view(plan:dict,values:dict,*,include_controls:bool=False)->None:
    """Compatibility bridge: canonical -> legacy, never legacy -> canonical."""
    values["explore_packages"]=deepcopy(plan["packages"])
    values["explore_calendar"]=deepcopy(plan["assignments"])
    if include_controls:
        # Caller must invoke before those Streamlit widgets are instantiated.
        values["explore_base"]=plan["base_city"]
