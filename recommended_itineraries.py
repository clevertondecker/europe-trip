"""Safe proposal acceptance; all candidate and date changes require explicit approval."""
from __future__ import annotations
from copy import deepcopy
from planning_store import change_plan
from trip_plan_model import validate_plan

def approve_destination(plan:dict,recommendation:dict,approved:bool=False)->dict:
    if not approved:return deepcopy(plan)
    dest=recommendation["destination_id"]
    if dest in plan["packages"] or dest in plan.get("excluded_destinations",[]):
        raise ValueError("Destino indisponível ou já selecionado")
    ids=recommendation["selected_attractions"]
    if not ids or len(ids)>5 or len(ids)!=len(set(ids)):
        raise ValueError("Seleção inválida")
    packs=deepcopy(plan["packages"])
    packs[dest]=list(ids)
    next_plan=change_plan(plan,{"packages":packs})
    validate_plan(next_plan)
    return next_plan

def reject_destination(plan:dict,destination_id:str,approved:bool=False)->dict:
    if not approved:return deepcopy(plan)
    if destination_id in plan["packages"] or destination_id in plan.get("mandatory_destinations",[]):
        raise ValueError("Não descartar destino obrigatório ou já escolhido")
    rejected=list(plan.get("excluded_destinations",[]))
    if destination_id not in rejected:rejected.append(destination_id)
    return change_plan(plan,{"excluded_destinations":rejected})

def approve_profile_scenario(plan:dict,scenario:dict,approved:bool=False)->dict:
    """Atomic acceptance of reviewed new outings and evidence-backed dates."""
    if not approved:return deepcopy(plan)
    if (scenario["base_revision"]!=plan["revision"]
        or scenario["plan_id"]!=plan["plan_id"]
        or scenario["base_city"]!=plan["base_city"]):
        raise ValueError("Proposta desatualizada: gere novamente")
    proposed=scenario["proposal_packages"]
    if any(proposed.get(dest)!=picks for dest,picks in plan["packages"].items()):
        raise ValueError("Proposta remove ou altera passeios já aprovados")
    if any(dest in plan.get("excluded_destinations",[]) for dest in proposed):
        raise ValueError("Proposta contém destinos descartados")
    proposed_dates=scenario["preview_assignments"]
    if any(proposed_dates.get(day)!=dest for day,dest in plan["assignments"].items()):
        raise ValueError("Proposta altera datas já aprovadas")
    if not set(proposed_dates.values())<=set(proposed):
        raise ValueError("Datas de destino não selecionado")
    out=change_plan(plan,{
        "packages":deepcopy(proposed),
        "assignments":deepcopy(proposed_dates),
        "profile":scenario["profile"]})
    if out==plan:raise ValueError("Proposta sem alterações")
    return out
