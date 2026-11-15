"""Pure, read-only selectors for comparing genuine profile scenario proposals.

No fake savings, future quotes or implicit TripPlan mutations.
"""
from __future__ import annotations

from collections import Counter
from decimal import Decimal

PROFILE_WEIGHTS={
    "economy":{"interest":20,"cost":45,"comfort":20,"schedule":15},
    "balanced":{"interest":35,"cost":25,"comfort":25,"schedule":15},
    "experience":{"interest":50,"cost":15,"comfort":15,"schedule":20},
}
PROFILE_EXPLANATIONS={
    "economy":"Prioriza despesas documentadas e destinos mais econômicos; custos desconhecidos não valem zero.",
    "balanced":"Equilibra experiências, custos, conforto e agenda, com passeios adicionais quando viáveis.",
    "experience":"Valoriza variedade de experiências; pode exigir mais deslocamentos e verificações.",
}


def scenario_comparison(plan:dict,scenarios:list[dict],eurfx:float,chffx:float,
                        destination_names:dict|None=None)->dict:
    """Build a concrete comparison from canonical plan and existing scenario outputs."""
    names=destination_names or {}
    canonical=set(plan["packages"])
    membership=Counter(key for option in scenarios for key in option["proposal_packages"])
    rows=[]
    by_profile={}
    for option in scenarios:
        packages=option["proposal_packages"]
        selected=set(packages)
        new=selected-canonical
        known=option["known_cost_by_currency"]
        known_brl=(Decimal(str(known.get("EUR",0)))*Decimal(str(eurfx))
                   +Decimal(str(known.get("CHF",0)))*Decimal(str(chffx)))
        finance=option["financial"]
        projection=finance["result"]
        row={
            "profile":option["profile"],"label":option["label"],
            "destinations":len(packages),"new_destinations":len(new),
            "attractions":sum(len(group) for group in packages.values()),
            "scheduled_days":len(option["preview_assignments"]),
            "known_brl":round(float(known_brl),2),
            "pending_count":len(option["missing_costs"]),
            "total_brl":float(projection["total"]),
            "margin_brl":float(projection["margin"]),
            "allowance_brl":float(finance["budget_excursions_allowance_brl"]),
            "overage_brl":float(finance["known_excursions_overage_brl"]),
            "existing":sorted(canonical&selected),
            "new":sorted(new),
            "proposal_destinations":sorted(selected),
            "unique":sorted(key for key in selected if membership[key]==1),
            "shared":sorted(key for key in selected if membership[key]>1),
            "unresolved":len(option["unresolved"]),
            "weights":PROFILE_WEIGHTS[option["profile"]],
            "explanation":PROFILE_EXPLANATIONS[option["profile"]],
        }
        rows.append(row)
        by_profile[row["profile"]]=row
    return {"rows":rows,"by_profile":by_profile,
            "shared":sorted(key for key,count in membership.items() if count>1),
            "unique_by_profile":{row["profile"]:row["unique"] for row in rows},
            "names":names}


def comparison_table(model:dict)->list[dict]:
    return [{
        "Estilo":row["label"],
        "Destinos":row["destinations"],
        "Novos":row["new_destinations"],
        "Atrações":row["attractions"],
        "Dias com passeio (proposta)":row["scheduled_days"],
        "Bilhetes conhecidos (R$)":row["known_brl"],
        "Sem preço completo":row["pending_count"],
        "Projeção total (R$)":row["total_brl"],
        "Margem (R$)":row["margin_brl"],
    } for row in model["rows"]]


def approval_diff(plan:dict,board:dict,simulation:dict,eurfx:float,chffx:float,
                  catalog:dict,routes:dict)->dict:
    """Compare a personalized draft with the current canonical plan."""
    from attractions_model import package_cost
    official_ids=[a for picks in plan["packages"].values() for a in picks]
    before=package_cost(catalog,routes,plan["base_city"],official_ids)
    after=simulation["detail"]["total"]
    def known_brl(cost):
        k=cost["known_by_currency"]
        return round(float(Decimal(str(k["EUR"]))*Decimal(str(eurfx))
                           +Decimal(str(k["CHF"]))*Decimal(str(chffx))),2)
    return {
        "new":sorted(set(board["packages"])-set(plan["packages"])),
        "existing":sorted(set(board["packages"])&set(plan["packages"])),
        "attractions_before":len(official_ids),
        "attractions_after":sum(len(x) for x in board["packages"].values()),
        "scheduled_before":len(plan["assignments"]),
        "scheduled_after":len(simulation["calendar"]),
        "known_before":known_brl(before),"known_after":known_brl(after),
        "pending_before":len(before["missing"]),
        "pending_after":len(after["missing"]),
        "total_after":float(simulation["finance"]["result"]["total"]),
        "margin_after":float(simulation["finance"]["result"]["margin"]),
    }
