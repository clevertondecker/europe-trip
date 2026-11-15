"""Portable drafts for itinerary proposals. No unapproved GitHub writes.

Exports are user-controlled JSON; loading is schema-checked against one plan
and real catalog attractions. Persistence between devices requires a private
backend and is intentionally not claimed by this module.
"""
from __future__ import annotations
import json
from copy import deepcopy
SCHEMA=1
PROFILES={"economy","balanced","experience"}

def validate_draft(draft:dict,plan:dict,catalog:dict)->dict:
    if draft.get("schema_version")!=SCHEMA or draft.get("plan_id")!=plan["plan_id"]:
        raise ValueError("Arquivo de rascunho incompatível com este planejamento")
    if draft.get("profile") not in PROFILES:
        raise ValueError("Perfil de rascunho desconhecido")
    if type(draft.get("base_revision")) is not int or draft["base_revision"]!=plan["revision"]:
        raise ValueError("O planejamento mudou desde o backup. Revise as propostas antes de importar")
    if draft.get("base_city")!=plan["base_city"]:
        raise ValueError("Cidade-base diferente; recalcule os custos")
    packs=draft.get("packages")
    if not isinstance(packs,dict):raise ValueError("Passeios inválidos")
    bydest={x["id"] for x in catalog["destinations"]}
    attractions={x["id"]:x["destination_id"] for x in catalog["attractions"]}
    for dest,ids in packs.items():
        if dest not in bydest or not isinstance(ids,list) or not 1<=len(ids)<=5:
            raise ValueError("Destino ou seleção inválidos")
        if len(set(ids))!=len(ids) or any(attractions.get(id)!=dest for id in ids):
            raise ValueError("Atração fora do destino")
    if any(packs.get(dest)!=ids for dest,ids in plan["packages"].items()):
        raise ValueError("Rascunho não pode remover passeios já aprovados")
    if any(dest in plan.get("excluded_destinations",[]) for dest in packs):
        raise ValueError("Destino descartado no planejamento")
    return deepcopy(draft)

def export_draft(board:dict)->str:
    clean={k:deepcopy(board[k]) for k in ("plan_id","profile","base_revision","base_city","packages")}
    clean["schema_version"]=SCHEMA
    return json.dumps(clean,ensure_ascii=False,indent=2)

def import_draft(serialized:str,plan:dict,catalog:dict)->dict:
    if len(serialized)>100_000:raise ValueError("Backup de rascunho grande demais")
    draft=validate_draft(json.loads(serialized),plan,catalog)
    return {"profile":draft["profile"],"plan_id":draft["plan_id"],
            "base_revision":draft["base_revision"],"base_city":draft["base_city"],
            "budget_scenario":plan["budget_scenario"],
            "packages":draft["packages"],"original_packages":deepcopy(draft["packages"]),
            "official_packages":deepcopy(plan["packages"]),
            "official_dates":deepcopy(plan["assignments"]),
            "status":"draft","undo":[]}

def save_draft(store:dict,board:dict)->dict:
    """Copy a draft to the current session's namespaced store; no network I/O."""
    key=(board["plan_id"],board["profile"])
    store[key]=deepcopy(board)
    return store[key]

def get_draft(store:dict,plan_id:str,profile:str)->dict|None:
    item=store.get((plan_id,profile))
    return deepcopy(item) if item is not None else None

def list_drafts(store:dict,plan_id:str)->list[str]:
    return sorted(profile for (pid,profile) in store if pid==plan_id)
