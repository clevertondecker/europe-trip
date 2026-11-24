"""Single versioned itinerary state; Streamlit-free domain selectors and actions.

Legacy keys are a compatibility cache during migration, never authoritative
once a TripPlan is loaded. No network or persistence side effects.
"""
from __future__ import annotations
from copy import deepcopy
from destination_identity import stored_outing_id, outing_destination_id
from datetime import date
from trip_plan_model import new_plan,validate_plan,with_revision,BASES
from plan_read_models import legacy_plan_projection
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
               "preferences","mandatory_destinations","excluded_destinations",
                "flexible_visits","italy_proposal"}
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
    destination = stored_outing_id(plan, destination)
    identity = outing_destination_id(destination)
    if valid_destinations is not None and identity not in {outing_destination_id(d) for d in valid_destinations}:
        raise ValueError("Destino desconhecido")
    if not attractions or len(attractions)>5 or len(attractions)!=len(set(attractions)):
        raise ValueError("Escolha uma a cinco atrações distintas")
    if valid_attractions is not None and not set(attractions)<=valid_attractions:
        raise ValueError("Atração desconhecida")
    packages=deepcopy(plan["packages"])
    packages[destination]=list(attractions)
    updates={"packages":packages}
    if any(outing_destination_id(v["destination_id"])==identity for v in plan.get("flexible_visits",[])):
        visits=deepcopy(plan["flexible_visits"])
        for item in visits:
            if outing_destination_id(item["destination_id"])==identity:
                item["attractions"]=list(attractions)
        updates["flexible_visits"]=visits
    return change_plan(plan,updates)

def remove_package(plan:dict,destination:str)->dict:
    destination = stored_outing_id(plan, destination)
    identity = outing_destination_id(destination)
    packages=deepcopy(plan["packages"])
    if destination not in packages:return deepcopy(plan)
    del packages[destination]
    dates={day:dest for day,dest in plan["assignments"].items() if outing_destination_id(dest)!=identity}
    visits=[v for v in plan.get("flexible_visits",[])
            if outing_destination_id(v["destination_id"])!=identity]
    return change_plan(plan,{"packages":packages,"assignments":dates,
                              "flexible_visits":visits})

def add_assignment(plan:dict,day:str,destination:str)->dict:
    destination = stored_outing_id(plan, destination)
    identity = outing_destination_id(destination)
    chosen = destination in plan["packages"] or any(
        outing_destination_id(v["destination_id"]) == identity and v["stage"] == "França"
        for v in plan.get("flexible_visits", []))
    if not chosen:
        raise ValueError("Inclua a cidade no roteiro antes de agendar")
    date.fromisoformat(day)
    if day in plan["assignments"] and outing_destination_id(plan["assignments"][day])!=identity:
        raise ValueError("Já existe outro passeio neste dia")
    if day in plan["assignments"]:
        return deepcopy(plan)
    dates={**plan["assignments"],day:destination}
    return change_plan(plan,{"assignments":dates})

def remove_assignment(plan:dict,day:str)->dict:
    if day not in plan["assignments"]:return deepcopy(plan)
    dates=dict(plan["assignments"])
    del dates[day]
    return change_plan(plan,{"assignments":dates})

def summary(plan:dict)->dict:
    return {"destinations":len(set(plan["packages"]) | {
                v["destination_id"] for v in plan.get("flexible_visits", [])}),
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
    projection=legacy_plan_projection(plan)
    values["explore_packages"]=projection["explore_packages"]
    values["explore_calendar"]=projection["explore_calendar"]
    if include_controls:
        # Caller must invoke before those Streamlit widgets are instantiated.
        values["explore_base"]=projection["explore_base"]
