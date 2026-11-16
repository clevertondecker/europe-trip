"""UX 3.4 — honest, comparable home-base decision snapshots.

One reference TripPlan, one fixed set of selected outings, equal stay length
and FX, at most two alternative bases. Unknown journeys and 2027 rental
quotes remain UNKNOWN; historical one-way fares are never added to a
supposedly complete trip budget.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite

from base_change_model import (
    _canonical_destination,destination_catalog,destination_impact,impact_summary,
    comparable_rent_whatif,known_route,planned_destinations,
)
from base_scenario_model import base_options
from attractions_model import load_attractions
from base_explorer_model import load_exploration
from planning_workflow_model import preview_settings
from trip_plan_model import BASES

MAX_DESTINATIONS=8
MAX_ALTERNATIVES=2


def names_and_bases()->dict:
    return {b["id"]:b for b in base_options()}


def shared_destinations(plan:dict)->list[str]:
    """Use selected actual outings first; suggest examples only if none selected."""
    return planned_destinations(plan)


def _validate_inputs(plan:dict,alternatives:list[str],destinations:list[str],
                     rents:dict,french_days:int,eur_fx:float)->tuple:
    bases=names_and_bases()
    if (not isinstance(alternatives,list) or
        not 1<=len(alternatives)<=MAX_ALTERNATIVES or
        len(set(alternatives))!=len(alternatives) or
        plan["base_city"] in alternatives or
        any(a not in bases for a in alternatives)):
        raise ValueError("Escolha uma ou duas bases alternativas distintas da oficial")
    known=destination_catalog()
    if (not isinstance(destinations,list) or not 1<=len(destinations)<=MAX_DESTINATIONS
        or len(set(destinations))!=len(destinations) or
        any(d not in known for d in destinations)):
        raise ValueError("Escolha de um a oito destinos conhecidos, sem repetição")
    if type(french_days) is not int or not 40<=french_days<=80:
        raise ValueError("Dias na temporada europeia fora do intervalo estudado")
    if (not isinstance(eur_fx,(float,int)) or isinstance(eur_fx,bool) or
        not isfinite(eur_fx) or eur_fx<=0):
        raise ValueError("Câmbio inválido")
    if not isinstance(rents,dict) or not set(rents)<=set(alternatives+[plan["base_city"]]):
        raise ValueError("Aluguéis devem corresponder às bases comparadas")
    for rent in rents.values():
        if rent is not None and (
            not isinstance(rent,(float,int)) or isinstance(rent,bool) or
            not isfinite(rent) or not 0<rent<=20000
        ):
            raise ValueError("Provisão mensal de aluguel inválida")
    return bases,known


def _country_catalog()->dict:
    """Existing attraction/exploration labels, not inferred countries."""
    places={d["id"]:d.get("country") for d in load_attractions()["destinations"]}
    for d in load_exploration()["destinations"]:
        places.setdefault(d["id"],d.get("country"))
    return places


def _base_route_summary(base_id:str, destinations:list[str],countries:dict)->dict:
    routes=[{"destination_id":dest,**known_route(base_id,dest)} for dest in destinations]
    timed=[r for r in routes if r["minutes"] is not None]
    priced=[r for r in routes if r["fare"] is not None]
    country_set=sorted({countries[r["destination_id"]] for r in timed
                        if countries.get(r["destination_id"]) and
                        countries[r["destination_id"]] not in
                        (None,names_and_bases()[base_id]["country"])})
    return {
        "base_id":base_id,"selected_count":len(destinations),
        "route_time_count":len(timed),"fare_from_count":len(priced),
        "country_time_references":country_set,
        "routes":routes,"has_verified_2027_return":False,
    }


def compare_city_decisions(plan:dict,alternatives:list[str],destinations:list[str],
                           rents:dict,trip_data:dict,finance_live:bool,
                           french_days:int,eur_fx:float)->dict:
    """Source-aware what-if. Never writes the user's official plan."""
    destinations=[_canonical_destination(d) for d in destinations]
    bases,places=_validate_inputs(plan,alternatives,destinations,
                                   rents,french_days,eur_fx)
    reference=plan["base_city"]
    countries=_country_catalog()
    profiles={}
    for city in [reference]+alternatives:
        profiles[city]=_base_route_summary(city,destinations,countries)
    candidates=[]
    for city in alternatives:
        rows=destination_impact(plan,city,destinations)
        groups=impact_summary(rows)
        paired=sum(r["delta_minutes"] is not None for r in rows)
        # Missing rent is not zero; absent tickets aren't added to trip totals.
        housing=comparable_rent_whatif(
            plan,trip_data,finance_live,rents.get(reference),rents.get(city),
            french_days,eur_fx)
        candidates.append({
            "id":city,"name":bases[city]["name"],
            "official_supported":bool(bases[city]["official_supported"]),
            "changes":groups,"paired_route_times":paired,
            "candidate_only_researched":sum(
                r["candidate_minutes"] is not None and
                r["official_minutes"] is None for r in rows),
            "official_only_researched":sum(
                r["official_minutes"] is not None and
                r["candidate_minutes"] is None for r in rows),
            "routes":rows,"housing_whatif":housing,
            "financial_delta_brl":housing["delta_brl"],
            "financial_delta_scope":"Somente diferença de provisão mensal de moradia, "
                 "mantendo demais parcelas constantes; não é economia total.",
            "total_difference_known":False,
            "lost_destinations":[],"new_destinations_confirmed":[],
            "return_or_hotel_verified":False,
            "missing":["Ida e volta real para os mesmos passeios",
                       "Última milha, transferências e horários compatíveis",
                       "Apartamentos equivalentes para 56–60 noites em 2027",
                       "Impostos, caução e taxas de hospedagem",
                       "Custos de novos passeios e ingressos",
                       "Transporte Itália → base europeia"],
        })
    return {
        "plan_id":plan["plan_id"],"plan_revision":plan["revision"],
        "official_base":reference,"official_name":bases[reference]["name"],
        "alternatives":alternatives[:],"destinations":destinations[:],
        "destination_names":{d:places[d] for d in destinations},
        "french_days":french_days,"eur_fx":eur_fx,
        "rents_eur_month":deepcopy(rents),
        "profiles":profiles,"candidates":candidates,
        "comparable_2027_totals":False,"winner":None,
        "unmodified":["Cidade-base oficial","Datas e períodos",
                      "Passeios escolhidos","Estilo e cenário do orçamento",
                      "Decisões do Drive","Reservas (não confirmadas)"],
        "methodology":"Mesma lista de passeios, duração, casal e cenário financeiro; "
            "tempos históricos de ida: típicos quando disponíveis em ambas as bases, "
            "mínimos somente como referência subsidiária; sem conclusão sobre volta; "
            "provisões de moradia são hipóteses inseridas pelo usuário.",
    }


def review_base_application(plan:dict,comparison:dict,candidate:str)->dict:
    """Two-step reviewed application; only four supported official bases."""
    if comparison["plan_id"]!=plan["plan_id"] or comparison["plan_revision"]!=plan["revision"]:
        raise ValueError("Comparação antiga: o plano mudou")
    entry=next((x for x in comparison["candidates"] if x["id"]==candidate),None)
    if entry is None:
        raise ValueError("Cidade não está na comparação")
    if candidate not in BASES or not entry["official_supported"]:
        raise ValueError("Cidade ainda não integra o modelo oficial")
    return preview_settings(plan,{"base_city":candidate})
