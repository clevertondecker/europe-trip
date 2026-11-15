"""Versioned travel plan domain and explicit proposal application.

No UI state, network or LLM dependencies; all operations are pure.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import date
from uuid import uuid4

BASES={"mulhouse","strasbourg","metz","nancy"}
PROFILES={"balanced","economy","experience"}
SCHEMA_VERSION=1

def new_plan(base="mulhouse",departure="2027-09-09",profile="balanced")->dict:
    plan={"schema_version":SCHEMA_VERSION,"plan_id":"trip-"+uuid4().hex[:12],
          "revision":0,"base_city":base,"departure_date":departure,
          "total_days":70,"italy_days":10,"vacation_days":25,"setup_days":4,
          "budget_scenario":"70k","profile":profile,"mandatory_destinations":[],
          "excluded_destinations":[],"packages":{},"assignments":{},
          "preferences":{},"flexible_visits":[],
          "accepted_recommendations":[],"rejected_recommendations":[],
          "source_versions":{"attractions":"2026-11-14","routes":"2026-11-14"}}
    validate_plan(plan)
    return plan

def validate_plan(plan:dict,known_attractions:set[str]|None=None)->None:
    if plan.get("schema_version")!=SCHEMA_VERSION:raise ValueError("Versão de plano incompatível")
    if not isinstance(plan.get("plan_id"),str) or not plan["plan_id"].startswith("trip-"):
        raise ValueError("ID inválido")
    if plan.get("base_city") not in BASES or plan.get("profile") not in PROFILES:
        raise ValueError("Base/perfil inválido")
    if plan.get("budget_scenario") not in {"60k","70k"}:raise ValueError("Cenário inválido")
    if type(plan.get("revision")) is not int or plan["revision"]<0:
        raise ValueError("Revisão inválida")
    if date.fromisoformat(plan["departure_date"])<=date(2027,9,4):
        raise ValueError("Viagem anterior ao casamento")
    if not 65<=plan["total_days"]<=75 or not 8<=plan["italy_days"]<=12:
        raise ValueError("Duração inválida")
    if not 20<=plan["vacation_days"]<=30 or not 1<=plan["setup_days"]<=5:
        raise ValueError("Férias/instalação inválidas")
    if plan["vacation_days"]<=plan["italy_days"]+plan["setup_days"]:
        raise ValueError("Férias insuficientes")
    preferences=plan.get("preferences",{})
    if not isinstance(preferences,dict) or any(
        not isinstance(k,str) or v not in {"Quero visitar","Opcional","Descartar"}
        for k,v in preferences.items()):
        raise ValueError("Preferências de atrações inválidas")
    packages=plan.get("packages")
    if not isinstance(packages,dict) or not all(isinstance(v,list) for v in packages.values()):
        raise ValueError("Passeios inválidos")
    chosen=[x for group in packages.values() for x in group]
    if len(chosen)!=len(set(chosen)):raise ValueError("Atrações duplicadas")
    if known_attractions is not None and not set(chosen)<=known_attractions:
        raise ValueError("Atração desconhecida")
    if set(plan.get("mandatory_destinations",[])) & set(plan.get("excluded_destinations",[])):
        raise ValueError("Destino obrigatório e excluído")
    if not isinstance(plan.get("assignments"),dict):raise ValueError("Datas inválidas")
    for k,v in plan["assignments"].items():
        date.fromisoformat(k)
        if not isinstance(v,str):raise ValueError("Destino inválido no calendário")
    # Optional v1 extension: older saved plans remain readable unchanged.
    flexible=plan.get("flexible_visits",[])
    if not isinstance(flexible,list) or len(flexible)>80:
        raise ValueError("Visitas flexíveis inválidas")
    seen=set()
    for visit in flexible:
        if not isinstance(visit,dict) or set(visit)!={
                "destination_id","stage","attractions","period"}:
            raise ValueError("Formato de visita flexível inválido")
        destination=visit["destination_id"]
        stage=visit["stage"]
        choices=visit["attractions"]
        period=visit["period"]
        if (not isinstance(destination,str) or len(destination)>80 or
            not destination.replace("_","").replace("-","").isalnum() or
            destination in seen or stage not in ("Itália","França") or
            not isinstance(choices,list) or not 1<=len(choices)<=5 or
            not all(isinstance(a,str) and 0<len(a)<=100 for a in choices) or
            len(set(choices))!=len(choices) or
            not isinstance(period,str) or len(period)>80):
            raise ValueError("Visita flexível inválida ou duplicada")
        if stage=="Itália" and not destination.startswith("italy_"):
            raise ValueError("Destino não pertence à Itália")
        if stage=="França" and destination.startswith("italy_"):
            raise ValueError("Passeio não pertence à França")
        seen.add(destination)

def with_revision(plan:dict,updates:dict)->dict:
    result=deepcopy(plan)
    result.update(deepcopy(updates))
    result["revision"]=plan["revision"]+1
    validate_plan(result)
    return result

def apply_proposal(plan:dict,proposal:dict,approved:bool=False)->dict:
    """Preview is immutable. Approval is the sole way to modify assignments."""
    if not approved: return deepcopy(plan)
    if proposal.get("base_revision")!=plan["revision"]:
        raise ValueError("Proposta obsoleta; recalcular")
    if proposal.get("base_city")!=plan["base_city"]:
        raise ValueError("Cidade-base foi alterada")
    if proposal.get("plan_id") not in (None,plan["plan_id"]):
        raise ValueError("A proposta pertence a outro plano")
    if any(proposal.get("assignments",{}).get(day)!=dest
           for day,dest in plan["assignments"].items()):
        raise ValueError("A proposta altera visitas anteriormente confirmadas")
    from calendar_assignment_validation import validate_new_assignments
    validate_new_assignments(plan,proposal["assignments"],
                             previously_approved=plan["assignments"])
    result=with_revision(plan,{"assignments":proposal["assignments"],
                                "accepted_recommendations":plan["accepted_recommendations"]+
                                    [proposal["proposal_id"]]})
    return result
