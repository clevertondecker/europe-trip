"""Single source of planning configuration and safe what-if comparisons.

All functions are pure. No Streamlit, Drive, authentication or persistence is
performed here; only a confirmed action may enter the canonical session API.
"""
from __future__ import annotations

from copy import deepcopy
from trip_plan_model import BASES, PROFILES,validate_plan
from planning_store import change_plan

EDITABLE=("total_days","italy_days","vacation_days","setup_days",
          "base_city","profile","budget_scenario","preferences")
TRIP_STYLES={"balanced":"Equilibrado","economy":"Econômico",
             "experience":"Lua de mel e experiências"}
BUDGET_LABELS={"60k":"R$ 60 mil","70k":"R$ 70 mil"}


def settings(plan:dict)->dict:
    """Supported plan fields only; never derive official state from widgets."""
    return {key:deepcopy(plan[key]) for key in EDITABLE}


def preview_settings(plan:dict,changes:dict)->dict:
    """Review the full delta; refuse unsupported official cities and bad dates."""
    if not changes or not set(changes)<=set(EDITABLE):
        raise ValueError("Configuração não permitida")
    proposed=deepcopy(plan)
    proposed.update(deepcopy(changes))
    validate_plan(proposed)
    delta={key:{"current":deepcopy(plan[key]),"proposed":deepcopy(proposed[key])}
           for key in EDITABLE if proposed[key]!=plan[key]}
    return {"original_revision":plan["revision"],
            "plan_id":plan["plan_id"],"changes":delta,
            "same_choice":not bool(delta),"proposed_plan":proposed,
            "untouched":["packages","assignments","flexible_visits",
                         "italy_proposal","accepted_recommendations",
                         "rejected_recommendations","source_versions"]}


def approve_settings(plan:dict,preview:dict,*,confirmed:bool=False)->dict:
    if not confirmed:return deepcopy(plan)
    if plan["plan_id"]!=preview["plan_id"] or plan["revision"]!=preview["original_revision"]:
        raise ValueError("O planejamento mudou; revise novamente")
    changes={key:d["proposed"] for key,d in preview["changes"].items()}
    return change_plan(plan,changes) if changes else deepcopy(plan)


def compare_alternative(plan:dict,candidate:dict)->dict:
    """Non-mutating what-if; bases not supported officially stay hypothetical."""
    permitted={"base_city","total_days","italy_days","profile","budget_scenario"}
    if not set(candidate)<=permitted:
        raise ValueError("Critério de comparação desconhecido")
    alternative=deepcopy(plan)
    alternative.update(candidate)
    # Research catalog includes bases that cannot yet become official.
    unsupported=alternative["base_city"] not in BASES
    for key in ("total_days","italy_days"):
        if type(alternative[key]) is not int:
            raise ValueError("Duração inválida")
    if not 65<=alternative["total_days"]<=75 or not 8<=alternative["italy_days"]<=12:
        raise ValueError("Duração hipotética fora dos limites estudados")
    if alternative["profile"] not in PROFILES or alternative["budget_scenario"] not in BUDGET_LABELS:
        raise ValueError("Premissa hipotética inválida")
    if unsupported:
        if not isinstance(alternative["base_city"],str):
            raise ValueError("Base inválida")
        alternative["base_city"]="mulhouse" # validate unrelated fields only
    validate_plan(alternative)
    alternative["base_city"]=candidate.get("base_city",plan["base_city"])
    differences={key:(plan[key],alternative[key]) for key in permitted
                 if plan[key]!=alternative[key]}
    return {"official":deepcopy(plan),"alternative":alternative,
            "differences":differences,
            "unchanged":["passeios escolhidos","datas e períodos planejados",
                         "propostas italianas","reservas (não confirmadas)",
                         "fontes e decisões do Drive"],
            "official_base_supported":not unsupported,
            "can_apply_official":not unsupported,
            "not_quoted":["hospedagem de 2027","transporte entre etapas",
                          "viagens e bilhetes sem pesquisa equivalente"]}


def resume_target(plan:dict)->dict:
    """Reconstruct useful continuation from recovered persisted plan, no tracking."""
    visits=plan.get("flexible_visits",[])
    if visits:
        last=visits[-1]
        return {"area":"Meu roteiro","task":"Meu planejamento",
                "stage":last["stage"],"destination_id":last["destination_id"],
                "why":"Continuar pelas escolhas recuperadas"}
    if plan["packages"]:
        last=next(reversed(plan["packages"]))
        return {"area":"Meu roteiro","task":"Meu planejamento",
                "stage":"França","destination_id":last,
                "why":"Retomar os passeios do roteiro"}
    return {"area":"Meu roteiro","task":"Meu planejamento",
            "stage":"Itália","destination_id":None,
            "why":"Começar pelos lugares da lua de mel"}


def breadcrumb(stage:str|None=None,city:str|None=None)->tuple[str,...]:
    parts=["Meu roteiro","Meu planejamento"]
    if stage:
        parts.append("Temporada europeia" if stage=="França" else stage)
    if city:
        parts.append(city)
    return tuple(parts)
