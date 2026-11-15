"""Editable, session-only scenario board with explicit cost accounting.

The board is never an authoritative TripPlan until the owner approves it.
Its finance projection deliberately uses the existing excursions allowance.
"""
from __future__ import annotations
from copy import deepcopy
from decimal import Decimal
from attractions_model import package_cost,route_for
from advisor_finance import advisor_projection
from travel_optimizer import propose_schedule

def new_board(plan:dict,scenario:dict)->dict:
    return {"profile":scenario["profile"],"plan_id":plan["plan_id"],
            "base_revision":plan["revision"],"base_city":plan["base_city"],
            "budget_scenario":plan["budget_scenario"],
            "packages":deepcopy(scenario["proposal_packages"]),
            "original_packages":deepcopy(scenario["proposal_packages"]),
            "official_packages":deepcopy(plan["packages"]),
            "official_dates":deepcopy(plan["assignments"]),
            "status":"draft","undo":[]}

def is_stale(board:dict,plan:dict)->bool:
    return any((board["plan_id"]!=plan["plan_id"],
                board["base_revision"]!=plan["revision"],
                board["base_city"]!=plan["base_city"],
                board["budget_scenario"]!=plan["budget_scenario"]))

def change_board(board:dict,catalog:dict,destination:str,ids:list[str]|None)->dict:
    """One draft mutation: add/remove destination or edit its selected attractions."""
    by_dest={d["id"] for d in catalog["destinations"]}
    ids=ids or []
    if destination not in by_dest:raise ValueError("Destino desconhecido")
    valid={a["id"] for a in catalog["attractions"] if a["destination_id"]==destination}
    if len(ids)>5 or len(ids)!=len(set(ids)) or not set(ids)<=valid:
        raise ValueError("Escolha até cinco atrações distintas do destino")
    official=board["official_packages"].get(destination)
    if official is not None and ids!=official:
        raise ValueError("Este passeio já foi aprovado no plano oficial; altere-o em Explorar atrações")
    next_board=deepcopy(board)
    current=next_board["packages"].get(destination,[])
    if (ids==current or not ids and destination not in next_board["packages"]):
        return next_board
    next_board["undo"].append(deepcopy(board["packages"]))
    next_board["undo"]=next_board["undo"][-10:]
    if ids:next_board["packages"][destination]=list(ids)
    else:next_board["packages"].pop(destination,None)
    next_board["status"]="draft"
    return next_board

def undo_board(board:dict)->dict:
    next_board=deepcopy(board)
    if next_board["undo"]:
        next_board["packages"]=next_board["undo"].pop()
    return next_board

def cost_details(board:dict,catalog:dict,routes:dict)->dict:
    index={a["id"]:a for a in catalog["attractions"]}
    destinations={d["id"]:d for d in catalog["destinations"]}
    rows=[]
    for dest,ids in board["packages"].items():
        one=package_cost(catalog,routes,board["base_city"],ids)
        route=route_for(routes,board["base_city"],dest)
        components=[]
        for line in one["breakdown"]:
            components.append({"name":line["item"],"currency":line["currency"],
                               "value":Decimal(str(line["known_eur"])),
                               "condition":line["condition"]})
        rows.append({"destination_id":dest,"destination":destinations[dest],
                     "attractions":[index[x] for x in ids],
                     "components":components,"missing":one["missing"],
                     "conditional":one["conditional"],"known":one["known_by_currency"],
                     "route":route,"locked":dest in board["official_packages"]})
    all_ids=[a for ids in board["packages"].values() for a in ids]
    total=package_cost(catalog,routes,board["base_city"],all_ids)
    return {"rows":rows,"total":total}

def reprice_board(board:dict,plan:dict,catalog:dict,routes:dict,
                  trip_data:dict,source_live:bool,eurfx:float,chffx:float,
                  use_city_rent:bool=True)->dict:
    detail=cost_details(board,catalog,routes)
    candidate=deepcopy(plan)
    candidate["packages"]=deepcopy(board["packages"])
    candidate["profile"]=board["profile"]
    finance=advisor_projection(trip_data,source_live,candidate,detail["total"],
                               eurfx,chffx,use_city_rent)
    available=propose_schedule(candidate,catalog,routes,board["profile"],1)
    calendar=available[0]["assignments"] if available else deepcopy(plan["assignments"])
    unresolved=available[0]["unresolved"] if available else []
    before=cost_details({**board,"packages":board["original_packages"]},catalog,routes)
    delta={
        cur:round(detail["total"]["known_by_currency"][cur]-
                  before["total"]["known_by_currency"][cur],2)
        for cur in ("EUR","CHF")}
    converted=Decimal(str(delta["EUR"]))*Decimal(str(eurfx))+Decimal(str(delta["CHF"]))*Decimal(str(chffx))
    return {"detail":detail,"finance":finance,"calendar":calendar,"unresolved":unresolved,
            "known_delta":delta,"known_delta_brl":round(float(converted),2),
            "changed":board["packages"]!=board["original_packages"],
            "attractions_count":sum(map(len,board["packages"].values()))}

def board_to_approval(board:dict,plan:dict,simulation:dict)->dict:
    if is_stale(board,plan):raise ValueError("Roteiro desatualizado; atualize as propostas")
    return {"plan_id":plan["plan_id"],"base_revision":plan["revision"],
            "base_city":plan["base_city"],"profile":board["profile"],
            "proposal_packages":deepcopy(board["packages"]),
            "preview_assignments":deepcopy(simulation["calendar"])}
