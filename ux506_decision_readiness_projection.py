"""Read-only decision readiness, never an automatic city-base recommendation.

Optional research overlays are consumed when separately approved PRs land.
Until then the output explicitly identifies its limited legacy-catalog scope.
A rail/return/access identity match is NOT a timetable match or an outing.
"""
from __future__ import annotations

from importlib import import_module
from urllib.parse import urlparse

from attractions_model import load_attractions
from base_research_expanded_model import load_research
from ux501_destination_discovery_model import build_destination_discovery


def _optional_research(module_name, function_name):
    """Load an approved independent overlay if installed; no hidden fallback data."""
    try:
        module = import_module(module_name)
    except ModuleNotFoundError as exc:
        if exc.name == module_name:
            return None
        raise
    return getattr(module, function_name)()


def _https(value):
    parsed = urlparse(value or "")
    return parsed.scheme == "https" and bool(parsed.netloc)


def build_decision_readiness(comparison: dict, *, discovery=None,
                             catalog=None, research=None,
                             tourism_overlay=None, housing_overlay=None,
                             access_overlay=None) -> dict:
    """Enhance the same manually selected basket with versioned research coverage.

    Explicit injections allow integration tests without merging all branches.
    No overlay is authoritative over the canonical catalog or user interests.
    """
    discovery = discovery if discovery is not None else build_destination_discovery()
    catalog = catalog if catalog is not None else load_attractions()
    research = research if research is not None else load_research()
    if tourism_overlay is None:
        tourism_overlay = _optional_research(
            "tourism_visit_evidence_model", "load_visit_evidence")
    if housing_overlay is None:
        housing_overlay = _optional_research(
            "housing_short_stay_research_model", "housing_research_overview")
    if access_overlay is None:
        access_overlay = _optional_research(
            "attraction_last_mile_model", "load_access_pilot")

    attrs = {x["id"]: x for x in catalog["attractions"]}
    destinations = {x["id"]: x for x in discovery["destinations"]}
    attr_to_destination = {
        a["id"]: d["id"] for d in discovery["destinations"] for a in d["attractions"]
    }
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

    enriched = {}
    if tourism_overlay is not None:
        for entry in tourism_overlay.get("entries", []):
            aid = entry.get("attraction_id")
            if (aid in enriched or aid not in attr_to_destination or
                    entry.get("destination_id") != attr_to_destination.get(aid)):
                raise ValueError("Overlay turístico com identidade duplicada/inválida")
            if (entry.get("opening_state") != "verified_current_rule" or
                    not entry.get("opening_rule") or
                    not _https(entry.get("source_url")) or
                    entry.get("valid_for_2027") is not False):
                raise ValueError("Overlay turístico sem fonte/estado temporal")
            enriched[aid] = entry

    housing_lookup = {}
    if housing_overlay is not None:
        for row in housing_overlay.get("bases", []):
            key = row.get("base_id")
            if key in housing_lookup or key not in bases:
                raise ValueError("Overlay de moradia duplicado ou cidade não cadastrada")
            housing_lookup[key] = row

    access_by_attraction = {}
    for record in (access_overlay or {}).get("observations", []):
        aid = record.get("attraction_id")
        if attr_to_destination.get(aid) != record.get("destination_id"):
            raise ValueError("Acesso não corresponde à atração canônica")
        access_by_attraction.setdefault(aid, []).append(record)
    attraction_details = []
    tourism = []
    for dest in selected_destinations:
        d = destinations[dest]
        observed = [attrs[a["id"]] for a in d["attractions"] if a["id"] in attrs]
        enriched_here = [enriched[a["id"]] for a in d["attractions"] if a["id"] in enriched]
        legacy_hours_ids = {x["id"] for x in observed if x.get("opening_hours")}
        current_rule_ids = {x["attraction_id"] for x in enriched_here}
        for attraction in d["attractions"]:
            canonical = attrs.get(attraction["id"], {})
            extra = enriched.get(attraction["id"], {})
            attraction_details.append({
                "attraction_id": attraction["id"], "destination_id": dest,
                "name": attraction["name"], "category": attraction.get("category"),
                "description": canonical.get("summary"),
                "why_visit": extra.get("experience_reason"),
                "opening_rule": extra.get("opening_rule"),
                "opening_schedule": extra.get("opening_schedule"),
                "opening_source_url": extra.get("source_url"),
                "opening_checked_at": extra.get("checked_at"),
                "opening_verified_for_2027": False,
                "ticket_main": extra.get("entry_ticket", canonical.get("ticket")),
                "additional_activity": extra.get("additional_activity"),
                "visit_minutes": canonical.get("visit_minutes"),
                "visit_duration_status": canonical.get("visit_minutes_status", "unknown"),
                "last_mile_observations": access_by_attraction.get(attraction["id"], []),
                "station_access_time": None,
                "decision_ready": False,
            })
        tourism.append({
            "destination_id": dest, "destination_name": d["name"],
            "catalog_attraction_count": len(d["attractions"]),
            "legacy_attractions_with_description": sum(bool(x.get("summary")) for x in observed),
            "published_ticket_amounts_historical": sum(
                x.get("ticket", {}).get("status") == "operator_published"
                and x.get("ticket", {}).get("amount") is not None for x in observed),
            "published_opening_hours": len(legacy_hours_ids | current_rule_ids),
            "enriched_current_opening_rules": len(current_rule_ids),
            "enrichment_checked_at": sorted({
                x["checked_at"] for x in enriched_here if x.get("checked_at")
            }),
            "editorial_visit_durations": sum(
                x.get("visit_minutes_status") == "editorial_assumption" for x in observed),
            "visit_ready_for_2027": False,
            "research_status": "historical_or_current_rules_not_2027_confirmed"
                if current_rule_ids else "missing_date_specific_opening_evidence",
        })
    housing = []
    for base_id in comparison["base_ids"]:
        city = bases[base_id]
        offers = city["housing_offers"]
        overlay = housing_lookup.get(base_id)
        housing.append({
            "base_id": base_id, "base_name": city["name"],
            "historical_offer_count": len(offers),
            "verified_56_to_60_night_quotes_2027": city["eligible_2027_quotes"],
            "remote_work_internet_verified_count": sum(
                x.get("internet_verified") is True for x in offers),
            "total_stay_price_2027": None,
            "cleaning_fee_2027": None,
            "refundable_deposit_2027": None,
            "work_space_verified": False,
            "station_access_verified": False,
            "decision_ready": False,
            "housing_contract_loaded": overlay is not None,
            "live_listing_recheck_pending": True,
        })
    journeys = []
    for row in comparison["rows"]:
        observations = row.get("observations", [])
        primary = next((x for x in observations
                        if x.get("source_url") == row.get("source_url")), {})
        association = compatible_evidence_association(
            row.get("outbound_service"), row.get("return_service"),
            row.get("bidirectional_last_mile"),
            attraction_window=row.get("attraction_window"))
        journeys.append({
            "base_id": row["base_id"], "destination_id": row["destination_id"],
            "historical_rail_oneway_min": row["minimum_oneway_min"],
            "origin_station_id": primary.get("origin_station"),
            "destination_station_id": primary.get("destination_station"),
            "transfers": row.get("transfers"),
            "weekend_return_verified": False,
            "last_mile_verified": False,
            "temporal_association_status": association["temporal_status"],
            "association_reasons": association["reasons"],
            "full_door_to_door_min": None,
            "couple_2027_outing_total": None,
            "complete_trip_ready": False,
        })
    return {
        "destinations": tourism, "attraction_details": attraction_details,
        "base_housing": housing, "journeys": journeys,
        "base_ids": list(comparison["base_ids"]),
        "basket_ids": selected_destinations, "winner_id": None,
        "tourism_source_scope": "pilot_overlay_and_legacy_catalog"
            if tourism_overlay is not None else "legacy_catalog_only",
        "housing_source_scope": "housing_research_contract_and_legacy"
            if housing_overlay is not None else "legacy_housing_only",
        "ranking_available": False, "official_plan_modified": False,
        "wishlist_modified": False,
    }


def compatible_evidence_association(rail: dict | None, return_leg: dict | None,
                                    access: dict | None, *,
                                    schedule_validator=None,
                                    attraction_window=None) -> dict:
    """Identity + optional delegated schedule check, NEVER itinerary synthesis.

    The full temporal/calendar contract belongs to PR #119, which may not
    yet be merged. Do not implement a weaker duplicate validator here.
    """
    reasons = []
    if not rail or not return_leg or not access:
        reasons.append("missing_component")
    else:
        required = (
            "origin_id", "destination_id", "origin_station_id",
            "destination_station_id", "source_url", "duration_min")
        for part in (rail, return_leg):
            if any(part.get(k) is None for k in required):
                reasons.append("incomplete_train_identity")
        if any(access.get(k) is None for k in (
                "arrival_station_id", "return_station_id", "attraction_id",
                "destination_id")):
            reasons.append("incomplete_access_identity")
        if access.get("destination_id") != rail.get("destination_id"):
            reasons.append("attraction_destination_mismatch")
        if (rail.get("destination_station_id") != access.get("arrival_station_id") or
                return_leg.get("origin_station_id") != access.get("return_station_id")):
            reasons.append("station_mismatch")
        if (rail.get("destination_id") != return_leg.get("origin_id") or
                rail.get("origin_id") != return_leg.get("destination_id")):
            reasons.append("direction_mismatch")
        if any(not _https((part or {}).get("source_url"))
               for part in (rail, return_leg, access)):
            reasons.append("source_missing")
        for part in (rail, return_leg, access):
            minutes = part.get("duration_min")
            if type(minutes) is not int or minutes <= 0:
                reasons.append("duration_missing")
        # A Saturday outbound and Sunday return are allowed; the calendar
        # comparison must operate on real instants, not equality of dates.
    if reasons:
        return {"association_status": "not_composable",
                "reasons": sorted(set(reasons)), "temporal_status": "not_checked",
                "full_door_to_door_min": None, "outing_feasible_2027": False}

    if schedule_validator is None:
        try:
            from weekend_return_validation_model import weekend_roundtrip_evidence
            schedule_validator = weekend_roundtrip_evidence
        except ModuleNotFoundError as exc:
            if exc.name != "weekend_return_validation_model":
                raise
    if schedule_validator is None:
        return {"association_status": "identity_match_only",
                "reasons": ["temporal_contract_not_integrated"],
                "temporal_status": "not_checked",
                "full_door_to_door_min": None, "outing_feasible_2027": False}
    try:
        checked = schedule_validator(
            rail, return_leg, attraction_window=attraction_window)
    except ValueError:
        return {"association_status": "not_composable",
                "reasons": ["invalid_temporal_or_service_evidence"],
                "temporal_status": "invalid",
                "full_door_to_door_min": None, "outing_feasible_2027": False}
    allowed = {"documented_legs_only", "historical_schedule_coherent_only"}
    status = checked.get("status")
    if status not in allowed:
        return {"association_status": "not_composable",
                "reasons": [checked.get("reason") or "calendar_or_schedule_incompatible"],
                "temporal_status": status,
                "full_door_to_door_min": None, "outing_feasible_2027": False}
    return {"association_status": "historical_schedule_checked_components_only",
            "reasons": ["missing_full_portal_to_portal_evidence"],
            "temporal_status": status,
            "full_door_to_door_min": None, "outing_feasible_2027": False}
