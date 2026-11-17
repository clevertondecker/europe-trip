"""Safe UX projection of readiness to *decide*, not a base recommendation.

Read-only: all decision states are sourced from existing public research data.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from urllib.parse import urlparse

from attractions_model import load_attractions
from base_research_expanded_model import load_research
from ux501_destination_discovery_model import build_destination_discovery


def build_decision_readiness(comparison: dict, *, discovery=None,
                             catalog=None, research=None) -> dict:
    """Decorate current UX5 comparison with honest gaps for visits and housing."""
    discovery = discovery if discovery is not None else build_destination_discovery()
    catalog = catalog if catalog is not None else load_attractions()
    research = research if research is not None else load_research()
    attrs = {x["id"]: x for x in catalog["attractions"]}
    destinations = {x["id"]: x for x in discovery["destinations"]}
    bases = {x["id"]: x for x in research["cities"]}
    if not set(comparison["base_ids"]) <= set(bases):
        raise ValueError("Cidade-base não cadastrada")
    selected_destinations = [x["id"] for x in comparison["destinations"]]
    if len(set(selected_destinations)) != len(selected_destinations):
        raise ValueError("Destinos duplicados")
    if not set(selected_destinations) <= set(destinations):
        raise ValueError("Destino não cadastrado")
    expected = {(b, d) for b in comparison["base_ids"] for d in selected_destinations}
    found = {(x["base_id"], x["destination_id"]) for x in comparison["rows"]}
    if expected != found or len(found) != len(comparison["rows"]):
        raise ValueError("Matriz não corresponde à mesma cesta fixa")
    tourism = []
    for dest in selected_destinations:
        d = destinations[dest]
        observed = [attrs[a["id"]] for a in d["attractions"] if a["id"] in attrs]
        tourism.append({
            "destination_id": dest, "destination_name": d["name"],
            "catalog_attraction_count": len(d["attractions"]),
            "legacy_attractions_with_description": sum(bool(x.get("summary")) for x in observed),
            "published_ticket_amounts_historical": sum(
                x.get("ticket", {}).get("status") == "operator_published"
                and x.get("ticket", {}).get("amount") is not None for x in observed),
            "published_opening_hours": sum(bool(x.get("opening_hours")) for x in observed),
            "editorial_visit_durations": sum(
                x.get("visit_minutes_status") == "editorial_assumption" for x in observed),
            "visit_ready_for_2027": False,
            "research_status": "missing_opening_seasonality_and_date_specific_costs",
        })
    housing = []
    for base_id in comparison["base_ids"]:
        city = bases[base_id]
        offers = city["housing_offers"]
        housing.append({
            "base_id": base_id, "base_name": city["name"],
            "historical_offer_count": len(offers),
            "verified_56_to_60_night_quotes_2027": city["eligible_2027_quotes"],
            "remote_work_internet_verified_count": sum(
                x.get("internet_verified") is True for x in offers),
            "total_stay_price_2027": None,
            "decision_ready": False,
        })
    train = []
    for row in comparison["rows"]:
        train.append({
            "base_id": row["base_id"], "destination_id": row["destination_id"],
            "historical_rail_oneway_min": row["minimum_oneway_min"],
            "weekend_return_verified": bool(row["return_weekend_verified"]),
            "last_mile_verified": bool(row["local_access_verified"]),
            "full_door_to_door_min": None,
            "couple_2027_outing_total": None,
            "complete_trip_ready": False,
        })
    return {
        "destinations": tourism, "base_housing": housing,
        "journeys": train, "base_ids": list(comparison["base_ids"]),
        "basket_ids": selected_destinations, "winner_id": None,
        "ranking_available": False, "official_plan_modified": False,
        "wishlist_modified": False,
    }


def compatible_evidence_association(rail: dict | None, return_leg: dict | None,
                                    access: dict | None) -> dict:
    """Do not sum incomplete or disjoint historical rail and last-mile records."""
    reasons = []
    if not rail or not return_leg or not access:
        reasons.append("missing_component")
    else:
        if rail.get("destination_station_id") is None:
            reasons.append("rail_arrival_station_unknown")
        if (rail.get("destination_station_id") != access.get("arrival_station_id")
                or return_leg.get("origin_station_id") != access.get("return_station_id")):
            reasons.append("station_mismatch")
        if (rail.get("destination_id") != return_leg.get("origin_id")
                or rail.get("origin_id") != return_leg.get("destination_id")):
            reasons.append("direction_mismatch")
        if (rail.get("travel_date") is None or
                rail.get("travel_date") != return_leg.get("travel_date")):
            reasons.append("travel_date_mismatch")
        if any(not (urlparse((part or {}).get("source_url") or "").scheme == "https")
               for part in (rail, return_leg, access)):
            reasons.append("source_missing")
        if any((part or {}).get("duration_min") is None
               for part in (rail, return_leg, access)):
            reasons.append("duration_missing")
    return {
        "association_status": "compatible_components_only" if not reasons else "not_composable",
        "reasons": sorted(set(reasons)),
        # Full duration additionally requires lodging-to-station, schedules,
        # opening window and verified conditions. It is NEVER inferred here.
        "full_door_to_door_min": None,
        "outing_feasible_2027": False,
    }
