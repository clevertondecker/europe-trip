"""One planning journey for Italy and France, with flexible periods.

`packages` remains the canonical source for France outings and financial
projections; `assignments` remains the precise-date schedule. Optional
`flexible_visits` stores *metadata* about choice and period and does not
represent a reservation or incur an additional transport fare.
"""
from __future__ import annotations

from copy import deepcopy
from planning_store import change_plan
from catalog_plan_validation import allowed_attractions

ITALY_STAGE="Itália"
FRANCE_STAGE="França"
UNASSIGNED="Ainda não definido"
ITALY_PERIODS=(UNASSIGNED,"Durante Roma","Durante a Costa Amalfitana",
               "Férias na Itália")
FRANCE_PERIODS=(UNASSIGNED,"Instalação na França","Férias restantes",
                "Primeiro fim de semana na França",
                "Fim de semana a definir","Durante a estadia na França")

# These are planning choices derived from the documented Italy honeymoon
# research, NOT confirmed tickets, packages or travel bookings.
ITALIAN_PLACES={
    "italy_rome":("Roma",("Coliseu e Fórum Romano","Vaticano e São Pedro",
                          "Centro histórico, Panteão e Trevi","Trastevere")),
    "italy_amalfi":("Amalfi",("Centro histórico e Duomo","Litoral e passeios a pé",
                             "Vista da costa")),
    "italy_ravello":("Ravello",("Mirantes e jardins","Centro histórico")),
    "italy_positano":("Positano",("Centro e mirantes","Praia e passeio costeiro")),
    "italy_capri":("Capri",("Passeio pela ilha","Vistas da costa")),
    "italy_pompeii":("Pompeia",("Sítio arqueológico")),
    "italy_maiori":("Maiori",("Passeio à beira-mar","Praia")),
    "italy_minori":("Minori",("Centro e orla","Praia")),
    "italy_salerno":("Salerno",("Centro histórico","Orla")),
    "italy_naples":("Nápoles",("Centro histórico","Passeios urbanos")),
}
ITALY_ATTRACTIONS={
    city:[{"id":city+"__"+str(i),"name":a} for i,a in enumerate(details[1],1)]
    for city,details in ITALIAN_PLACES.items()
}


def period_options(stage:str)->tuple[str,...]:
    if stage==ITALY_STAGE:return ITALY_PERIODS
    if stage==FRANCE_STAGE:return FRANCE_PERIODS
    raise ValueError("Etapa desconhecida")


def destinations(catalog:dict)->list[dict]:
    italy=[{"id":cid,"name":details[0],"stage":ITALY_STAGE,
            "attractions":deepcopy(ITALY_ATTRACTIONS[cid]),"research":"Proposta Itália"}
           for cid,details in ITALIAN_PLACES.items()]
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
                   "exact_dates":rows.get(key,{}).get("exact_dates",[])}
    return sorted(rows.values(),key=lambda x:(x["stage"]!=ITALY_STAGE,x["name"]))


def choice_counts(plan:dict,catalog:dict)->dict:
    rows=selected_rows(plan,catalog)
    return {"destinations":len(rows),
            "organized":sum(x["period"]!=UNASSIGNED or x["exact_dates"] for x in rows),
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


def italy_starter_preview(plan:dict,catalog:dict,variant:str)->dict:
    if variant not in ("balanced","economy","experience"):
        raise ValueError("Proposta italiana desconhecida")
    # The three published scenarios all require Rome and the Amalfi coast,
    # but disagree on the overnight base. Overnight base is NOT adopted here.
    starter=[
        ("italy_rome",["italy_rome__1","italy_rome__2","italy_rome__3"],"Durante Roma"),
        ("italy_amalfi",["italy_amalfi__1","italy_amalfi__2"],
         "Durante a Costa Amalfitana"),
    ]
    added=[x for x in starter if not is_selected(plan,x[0])]
    unchanged=[x[0] for x in starter if is_selected(plan,x[0])]
    return {"variant":variant,"to_add":added,"unchanged":unchanged,
            "requires_confirmation":True,"does_not_set_dates":True,
            "hotel_base_approved":False,"reservations":False}


def adopt_italy_starter(plan:dict,catalog:dict,variant:str,
                        *,confirmed:bool=False)->dict:
    if not confirmed:return deepcopy(plan)
    preview=italy_starter_preview(plan,catalog,variant)
    if not preview["to_add"]:
        return deepcopy(plan)
    visits=deepcopy(plan.get("flexible_visits",[]))
    for dest_id,ids,period in preview["to_add"]:
        visits.append(_validated_choice(catalog,dest_id,ids,period))
    return change_plan(plan,{"flexible_visits":visits})
