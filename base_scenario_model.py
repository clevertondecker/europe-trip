"""Shared, read-only selection of exploratory home bases.

The hypothetical base is intentionally independent of TripPlan.base_city.
Never treat missing quotations as zero or market rent as a furnished short stay.
"""
from __future__ import annotations

from base_explorer_model import load_exploration
from base_research_expanded_model import load_research,load_rail


def base_options(data: dict | None = None) -> list[dict]:
    """One source for explored French bases; labels reflect evidence coverage."""
    source = data if data is not None else load_exploration()
    routes = source["routes"]
    output = []
    for item in source["bases"]:
        rows = [r for r in routes if r["base_id"] == item["id"]]
        with_time = sum(r["train_minutes_oneway_min"] is not None for r in rows)
        with_fare = sum(r["fare_from_eur_person_oneway"] is not None for r in rows)
        output.append({
            "id": item["id"], "name": item["name"], "country": item["country"],
            "official_supported": bool(item["official_base"]),
            "routes": len(rows), "time_coverage": with_time,
            "fare_coverage": with_fare,
            # These are research coverage labels, never booking readiness.
            "research_status": ("Rotas pesquisadas" if rows and
                                with_time == len(rows) and with_fare == len(rows)
                                else "Pesquisa parcial" if rows else "Sem rotas pesquisadas"),
        })
    seen={row["id"] for row in output}
    rail=load_rail()
    for item in load_research(include_candidates=True)["cities"]:
        if item["id"] in seen:
            continue
        segments=[line for line in rail["segments"] if line["from"]==item["id"]]
        output.append({
            "id":item["id"],"name":item["name"],"country":item["country"],
            "official_supported":False,
            "routes":len(segments),
            "time_coverage":sum(x.get("fastest_minutes") is not None for x in segments),
            "fare_coverage":sum(x.get("advertised_fare_from_eur_person_oneway") is not None for x in segments),
            "research_status":("Amostra ferroviária parcial" if segments
                               else "Pesquisa ampliada · rotas não catalogadas"),
        })
    return output


def choose_exploratory_base(candidate: str, options: list[dict]) -> str:
    """Validate selection without touching an official plan."""
    if candidate not in {item["id"] for item in options}:
        raise ValueError("Cidade-base exploratória inválida")
    return candidate


def hypothetical_city_name(base_id: str, options: list[dict]) -> str:
    return next(item["name"] for item in options if item["id"] == choose_exploratory_base(base_id, options))

def expanded_rail_routes(city_id:str)->list[dict]:
    """Verified source excerpts only; never infer a connection or a return fare."""
    choose_exploratory_base(city_id,base_options())
    from data23_france_candidates_model import base_routes as candidate_base_routes
    candidate_rows=candidate_base_routes(city_id)
    if candidate_rows:
        return [{
            "destination_id":r["destination_id"],
            "destination_name":r["destination_id"].replace("_"," ").title(),
            "oneway_minutes":r["minimum_oneway_min"],
            "fare_eur_person_oneway":None,
            "source_url":r["source_url"],
            "fare_source_url":None,
            "basis_date":r["checked_at"],
            "return_verified_2027":False,
            "notes":r["notes"],
        } for r in candidate_rows]
    return [
        {
            "destination_id":x["to"],
            "destination_name":x["destination"],
            "oneway_minutes":x["fastest_minutes"],
            "fare_eur_person_oneway":x["advertised_fare_from_eur_person_oneway"],
            "source_url":x["source_url"],
            "fare_source_url":x.get("fare_source_url"),
            "basis_date":load_rail()["basis_date"],
            "return_verified_2027":False,
            "notes":x["notes"],
        }
        for x in load_rail()["segments"] if x["from"]==city_id
    ]
