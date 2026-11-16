"""Evidence-aware base-change impact, never a TripPlan modification.

Only compare like-for-like fastest station-to-station time observations.
Missing destinations are NOT lost destinations; missing fares are NOT free.
The housing what-if uses two explicit manual assumptions, same duration,
budget and exchange rate on each side. Local outings and transport remain
unchanged and therefore a complete saving is never claimed.
"""
from __future__ import annotations

from math import isfinite

from attractions_model import load_attractions, load_base_routes
from base_explorer_model import load_exploration
from five_base_comparison_model import load_five_base_evidence
from base_research_expanded_model import load_rail
from base_scenario_model import base_options
from data_model import get_scenario
from unified_budget import resolve_french_budget, scenario_total


# Canonical aliases refer to the SAME city; never merge generic names by proximity.
DESTINATION_ALIASES={"luxembourg_city":"luxembourg"}
EVIDENCE_ALIASES={"luxembourg":"luxembourg_city"}


def _canonical_destination(destination:str)->str:
    return DESTINATION_ALIASES.get(destination,destination)


def destination_catalog() -> dict[str, str]:
    choices={row["id"]:row["name"] for row in load_attractions()["destinations"]}
    for row in load_exploration()["destinations"]:
        choices.setdefault(row["id"],row["name"])
    for row in load_rail()["segments"]:
        choices.setdefault(_canonical_destination(row["to"]),row["destination"])
    choices.pop("luxembourg_city",None)
    return choices


def planned_destinations(plan:dict)->list[str]:
    """Show selected destinations first, then clearly-marked research examples."""
    names=destination_catalog()
    selected=[_canonical_destination(city) for city in plan.get("packages",{})
              if _canonical_destination(city) in names]
    selected=list(dict.fromkeys(selected))
    if selected:
        return selected[:8]
    return [city for city in ("strasbourg","colmar","basel","freiburg","luxembourg")
            if city in names]


def known_route(base_id:str,dest_id:str)->dict:
    """Use documented 2026 sources only; don't fabricate transitive rail routes."""
    dest_id=_canonical_destination(dest_id)
    if base_id in {"mulhouse","strasbourg","metz","nancy"}:
        data=load_base_routes()
        route=next((r for r in data["routes"] if
                    r["base_id"]==base_id and r["destination_id"]==dest_id),None)
        if route is not None and route["train_minutes_one_way"] is not None:
            return {"minutes":route["train_minutes_one_way"],
                    "fare":route["fare_eur_person_oneway"],
                    "source":route["source_url"],
                    "fare_condition":route["fare_type"],
                    "basis":route.get("retrieved_at","2026"),
                    "note":route["notes"],"return_verified":False}
    # Five-base study has dated operator evidence for routes absent from the
    # original four-base itinerary matrix. Prefer an observed station time
    # over a legacy placeholder with None, never infer a train connection.
    study=load_five_base_evidence()
    evidence_id=EVIDENCE_ALIASES.get(dest_id,dest_id)
    verified=next((r for r in study["verified_time_routes"]
                   if r["base_id"]==base_id and r["destination_id"]==evidence_id),None)
    if verified is not None:
        return {"minutes":verified["fastest_train_oneway_min"],
                "fare":verified.get("advertised_from_eur_person_oneway"),
                "source":verified["source_url"],
                "fare_condition":"advertised_from_not_normal_verified",
                "basis":verified["checked_at"],"note":verified["notes"],
                "return_verified":False,
                "representative_minutes":verified.get("representative_minutes"),
                "transfers":verified.get("transfers"),
                "operator":verified.get("operator"),
                "origin_station":verified.get("origin_station"),
                "destination_station":verified.get("destination_station"),
                "frequency_reference":verified.get("frequency_reference"),
                "provenance":"five_base_operator_2026",
                "missing":verified.get("missing",[])}
    rail=load_rail()
    sample=next((r for r in rail["segments"] if
                 r["from"]==base_id and r["to"]==dest_id),None)
    if sample:
        return {"minutes":sample["fastest_minutes"],
                "fare":sample["advertised_fare_from_eur_person_oneway"],
                "source":sample["source_url"],"fare_condition":"announced_from",
                "basis":rail["basis_date"],"note":sample["notes"],
                "return_verified":False}
    explore=load_exploration()
    route=next((r for r in explore["routes"] if
                r["base_id"]==base_id and r["destination_id"]==dest_id),None)
    if route:
        return {"minutes":route["train_minutes_oneway_min"],
                "fare":route["fare_from_eur_person_oneway"],
                "source":route["source_url"],"fare_condition":route["reference_status"],
                "basis":route["retrieved_at"],"note":route["notes"],
                "return_verified":False}
    return {"minutes":None,"fare":None,"source":None,"fare_condition":None,
            "basis":None,"note":"Ainda não pesquisado", "return_verified":False}


def destination_impact(plan:dict,candidate:str,dest_ids:list[str])->list[dict]:
    all_bases={row["id"] for row in base_options()}
    official=plan["base_city"]
    if official not in all_bases or candidate not in all_bases:
        raise ValueError("Cidade-base desconhecida")
    names=destination_catalog()
    if (len(dest_ids)>25 or len({_canonical_destination(d) for d in dest_ids})!=len(dest_ids)
            or any(_canonical_destination(d) not in names for d in dest_ids)):
        raise ValueError("Destinos inválidos ou duplicados")
    rows=[]
    for supplied in dest_ids:
        dest=_canonical_destination(supplied)
        before,after=known_route(official,dest),known_route(candidate,dest)
        a,b=before["minutes"],after["minutes"]
        if a is None or b is None:
            status="Não pesquisado"
            delta=None
        else:
            delta=b-a
            status=("Melhorou" if delta<=-15 else
                    "Piorou" if delta>=15 else "Semelhante")
        rows.append({"destination_id":dest,"destination":names[dest],
                     "official_minutes":a,"candidate_minutes":b,
                     "delta_minutes":delta,"status":status,
                     "official_fare":before["fare"],
                     "candidate_fare":after["fare"],
                     "official_source":before["source"],
                     "candidate_source":after["source"],
                     "official_fare_condition":before["fare_condition"],
                     "candidate_fare_condition":after["fare_condition"],
                     "official_note":before["note"],
                     "candidate_note":after["note"],
                     "official_basis":before["basis"],
                     "candidate_basis":after["basis"],
                     "official_representative_minutes":before.get("representative_minutes"),
                     "candidate_representative_minutes":after.get("representative_minutes"),
                     "official_transfers":before.get("transfers"),
                     "candidate_transfers":after.get("transfers")})
    return rows


def impact_summary(rows:list[dict])->dict:
    keys={"Melhorou","Piorou","Semelhante","Não pesquisado"}
    return {key:sum(r["status"]==key for r in rows) for key in keys}


def comparable_rent_whatif(plan:dict,trip_data:dict,finance_live:bool,
                           official_eur_month:float|None,
                           candidate_eur_month:float|None,
                           french_days:int,fx:float)->dict:
    """Same assumptions, only two manual housing provisions vary.

    Return no delta when either rent quote is missing. Even with both, travel
    times, tickets, deposits and relocation remain unquoted. The result is
    NOT a defensible complete-trip cost comparison.
    """
    if (type(french_days) is not int or not 40<=french_days<=80 or
        not isinstance(fx,(int,float)) or not isfinite(fx) or fx<=0):
        raise ValueError("Premissas financeiras inválidas")
    if official_eur_month is None or candidate_eur_month is None:
        return {"known":False,"delta_brl":None,"official_total_brl":None,
                "candidate_total_brl":None,"provisional":True}
    if any(not isinstance(v,(int,float)) or not isfinite(v) or v<=0
           for v in (official_eur_month,candidate_eur_month)):
        raise ValueError("Os dois aluguéis devem ser positivos")
    scenario=get_scenario(trip_data,plan["budget_scenario"])
    french=resolve_french_budget(scenario,finance_live)
    params={"french_days":french_days,"outings_weekly":2,
            "outing_couple_eur":60,"fx_brl_per_eur":fx}
    original=scenario_total(scenario,french,**params,
                            rent_override_eur_month=official_eur_month)
    test=scenario_total(scenario,french,**params,
                        rent_override_eur_month=candidate_eur_month)
    return {"known":True,"delta_brl":round(test["total"]-original["total"],2),
            "official_total_brl":original["total"],
            "candidate_total_brl":test["total"],
            "provisional":True,
            "missing":["Bilhetes completos de ida/volta para 2027",
                       "Transporte inicial da Itália e retorno ao Brasil",
                       "Caução, taxas, limpeza e contrato",
                       "Diferenças reais na alimentação e passeios"]}
