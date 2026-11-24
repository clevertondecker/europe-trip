"""UX 4.5: a single semantic contract for confirmed outing changes.

Presentation may differ between Explorer, Discover and My planning. Only
itinerary_flow_model writes canonical TripPlan structures (no second editor).
"""
from __future__ import annotations
from dataclasses import dataclass
from destination_identity import outing_destination_id as canonical_destination_id
from itinerary_flow_model import (get_choice,selected_rows,upsert_choice,
                                  remove_choice,UNASSIGNED,FRANCE_STAGE)

@dataclass(frozen=True)
class OutingResult:
    action: str
    destination_id: str
    name: str
    attraction_count: int
    period: str
    dates: tuple[str,...]
    transport_pending: bool
    storage: str = "session_only"

def existing_choice(plan:dict,catalog:dict,destination_id:str)->dict|None:
    return next((r for r in selected_rows(plan,catalog)
                 if canonical_destination_id(r["id"])==canonical_destination_id(destination_id)),None)

def preview_outing(plan:dict,catalog:dict,destination_id:str,
                   attractions:list[str]|None=None,period:str|None=None)->dict:
    item=get_choice(catalog,destination_id)
    existing=existing_choice(plan,catalog,destination_id)
    selected=list(attractions if attractions is not None else
                  (existing["attractions"] if existing else []))
    from itinerary_flow_model import period_options
    chosen=(period if period is not None else
            (existing["period"] if existing else UNASSIGNED))
    if chosen not in period_options(item["stage"]):
        raise ValueError("Período não pertence a esta etapa")
    allowed={a["id"] for a in item["attractions"]}
    if (len(selected)>5 or len(selected)!=len(set(selected)) or
        not set(selected)<=allowed):
        raise ValueError("Atrações inválidas ou duplicadas")
    return {"destination_id":destination_id,"name":item["name"],
            "stage":item["stage"],"selected_attractions":selected,
            "period":chosen,"dates":list(existing["exact_dates"]) if existing else [],
            "already_exists":existing is not None,
            "action":"update" if existing else "add",
            "requires_confirmation":True,
            "transport_pending":item["stage"]==FRANCE_STAGE}

def apply_outing(plan:dict,catalog:dict,destination_id:str,attractions:list[str],
                 period:str|None=None,*,confirmed:bool=False)->tuple[dict,OutingResult]:
    if not confirmed:
        raise ValueError("Confirme a inclusão ou atualização antes de aplicar")
    info=preview_outing(plan,catalog,destination_id,attractions,period)
    if (info["already_exists"] and
        existing_choice(plan,catalog,destination_id)["attractions"]==info["selected_attractions"] and
        existing_choice(plan,catalog,destination_id)["period"]==info["period"]):
        updated=plan
    else:
        updated=upsert_choice(plan,catalog,destination_id,
                              info["selected_attractions"],info["period"])
    row=existing_choice(updated,catalog,destination_id)
    return updated,OutingResult(
        action="updated" if info["already_exists"] else "added",
        destination_id=destination_id,name=info["name"],
        attraction_count=len(row["attractions"]),period=row["period"],
        dates=tuple(row["exact_dates"]),
        transport_pending=info["transport_pending"])

def remove_outing(plan:dict,catalog:dict,destination_id:str,*,
                  confirmed:bool=False)->tuple[dict,OutingResult]:
    if not confirmed:
        raise ValueError("Confirme a remoção e o impacto sobre as datas")
    previous=existing_choice(plan,catalog,destination_id)
    if previous is None:
        raise ValueError("Destino não está no roteiro")
    updated=remove_choice(plan,catalog,destination_id)
    return updated,OutingResult(
        action="removed",destination_id=destination_id,name=previous["name"],
        attraction_count=0,period=UNASSIGNED,dates=(),
        transport_pending=previous["stage"]==FRANCE_STAGE)
