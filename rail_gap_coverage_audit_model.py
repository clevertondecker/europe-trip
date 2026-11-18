"""DATA 9.1: deterministic, read-only rail research backlog across 30 bases.

The canonical DQ 3.2 view and the main comparison share rail precedence.
This audits coverage, not availability, feasibility, fares or 2027 services.
"""
from __future__ import annotations

from collections import Counter
from copy import deepcopy

from attractions_model import load_attractions
from base_explorer_model import load_exploration
from base_research_expanded_model import load_research
from base_scenario_model import base_options
from dq32_macro_opportunities_model import load_macro_tourism, opportunity_overview
from rail_evidence_unified_model import load_rail_evidence


def build_rail_coverage_inventory(*, bases=None, catalog=None,
                                   exploration=None, research=None,
                                   macro=None, rail=None):
    """Audit the complete existing universe, with stable, reproducible IDs."""
    bases = bases if bases is not None else base_options()
    catalog = catalog if catalog is not None else load_attractions()
    exploration = exploration if exploration is not None else load_exploration()
    research = research if research is not None else load_research()
    macro = macro if macro is not None else load_macro_tourism()
    rail = rail if rail is not None else load_rail_evidence()
    pairs = []
    per_base = []
    expected_destinations = None
    for base in bases:
        view = opportunity_overview(
            base["id"], options=bases, catalog=catalog,
            exploration=exploration, research=research, macro=macro, rail=rail)
        destination_ids = {x["destination_id"] for x in view["destinations"]}
        if expected_destinations is None:
            expected_destinations = destination_ids
        elif destination_ids != expected_destinations:
            raise ValueError("The exploratory universe must be consistent across bases")
        counts = Counter()
        for dest in view["destinations"]:
            state = dest["status"]
            category = {
                "local_access_unresearched":"local",
                "historical_train_time_only":"historical",
                "indicative_rail_reference_only":"indicative",
                "unresearched_from_base":"missing",
            }.get(state)
            if category is None:
                raise ValueError("Unexpected rail evidence category: "+str(state))
            counts[category] += 1
            pairs.append({
                "base_id":view["base_id"],
                "base_name":view["base_name"],
                "destination_id":dest["destination_id"],
                "destination_name":dest["name"],
                "destination_country":dest["country"],
                "category":category,
                "oneway_min":(dest["minimum_train_oneway_min"] if category == "historical"
                              else dest["indicative_train_oneway_min"]
                              if category == "indicative" else None),
                "source_url":(dest["train_source_url"] if category == "historical"
                              else dest["indicative_source_url"]
                              if category == "indicative" else None),
                "source_checked_at":(dest["train_checked_at"] if category == "historical"
                                     else dest["indicative_source_checked_at"]
                                     if category == "indicative" else None),
                "confidence":dest["indicative_confidence"] if category == "indicative"
                             else None,
                "return_2027_verified":False,
                "fare_couple_2027_eur":None,
                "door_to_door_2027_verified":False,
            })
        per_base.append({"base_id":base["id"],"base_name":view["base_name"],
                         **{k:counts[k] for k in ("historical","indicative","local","missing")}})
    count = Counter(x["category"] for x in pairs)
    per_destination = []
    for destination_id in sorted(expected_destinations or ()):
        values = [x for x in pairs if x["destination_id"] == destination_id]
        per_destination.append({
            "destination_id":destination_id,
            "destination_name":values[0]["destination_name"],
            "country":values[0]["destination_country"],
            "missing_bases":sum(x["category"]=="missing" for x in values),
            "historical_bases":sum(x["category"]=="historical" for x in values),
            "indicative_bases":sum(x["category"]=="indicative" for x in values),
            "local_bases":sum(x["category"]=="local" for x in values),
        })
    per_destination.sort(key=lambda row:(-row["missing_bases"],row["destination_id"]))
    return {
        "scope":"read_only_2026_historical_rail_coverage",
        "base_count":len(bases), "destination_count":len(expected_destinations or []),
        "total_pairs":len(pairs),
        "historical_pairs":count["historical"],
        "indicative_pairs":count["indicative"],
        "local_pairs":count["local"],
        "missing_pairs":count["missing"],
        "per_base":per_base,
        "per_destination":per_destination,
        "pairs":pairs,
        "mutates_tripplan":False,
        "fare_and_return_verified_2027":False,
    }


def research_backlog(inventory):
    """Actionable list only; never fill missing durations or infer return legs."""
    return [
        {"base_id":row["base_id"],"destination_id":row["destination_id"],
         "base_name":row["base_name"],"destination_name":row["destination_name"],
         "research_required":["operator_route_page","published_oneway_duration",
                              "source_date","station_reconciliation",
                              "independent_return_service","two_adults_fare",
                              "last_mile_to_attraction"]}
        for row in inventory["pairs"] if row["category"]=="missing"
    ]



def component_research_backlog(inventory):
    """Track *all* missing logistical components, not only missing outward times.

    Historical/indicative one-way durations never prove a 2027 return,
    station-to-attraction access, opening window or cost for two adults.
    The old research_backlog() remains an intentionally narrower API for
    records with no outward time.
    """
    result = []
    seen = set()
    for row in inventory["pairs"]:
        base = row["base_id"]
        dest = row["destination_id"]
        key = (base, dest)
        if key in seen:
            raise ValueError("duplicate base-destination pair in audit")
        seen.add(key)
        category = row["category"]
        if category not in {"historical", "indicative", "local", "missing"}:
            raise ValueError("unsupported rail evidence category")

        required = []
        outward = row.get("oneway_min")
        if category == "local":
            if base != dest or outward is not None:
                raise ValueError("local transport must not be inferred from a train")
            required += [
                "local_access_outbound",
                "local_access_return",
                "local_transport_two_adults_cost",
            ]
        else:
            if base == dest:
                raise ValueError("non-local category assigned to same-place pair")
            if category == "missing":
                if outward is not None:
                    raise ValueError("missing time must be null")
                required += ["operator_route_page", "published_oneway_duration"]
            elif type(outward) is not int or outward <= 0:
                raise ValueError("documentary duration must be a positive integer")
            if not row.get("source_url"):
                required.append("operator_route_page")
            if not row.get("source_checked_at"):
                required.append("source_date")
            required += [
                "station_reconciliation",
                "dated_outbound_service_2027",
                "independent_return_service",
                "two_adults_fare",
                "last_mile_to_attraction",
            ]
        # These are outing/attraction questions even for the local base.
        required += [
            "attraction_opening_window",
            "attraction_visit_duration_evidence",
        ]
        if row.get("return_2027_verified") is not False:
            raise ValueError("source inventory must not infer a verified return")
        if row.get("door_to_door_2027_verified") is not False:
            raise ValueError("source inventory must not infer complete itinerary")
        if row.get("fare_couple_2027_eur") is not None:
            raise ValueError("unexpected verified couple fare in 2026-only audit")
        result.append({
            "base_id": base,
            "destination_id": dest,
            "base_name": row["base_name"],
            "destination_name": row["destination_name"],
            "category": category,
            "known_outbound_oneway_min": outward,
            "source_url": row.get("source_url"),
            "research_required": list(dict.fromkeys(required)),
            "return_2027_verified": False,
            "confirmed_2027": False,
        })
    if len(result) != inventory["total_pairs"]:
        raise ValueError("component inventory does not cover all pairs")
    return result


def component_gap_summary(backlog):
    """Snapshot statistics; component *counts* are not trip quality scores."""
    counts = Counter()
    categories = Counter()
    for row in backlog:
        categories[row["category"]] += 1
        counts.update(row["research_required"])
    return {"pairs": len(backlog),
            "by_category": dict(sorted(categories.items())),
            "missing_components": dict(sorted(counts.items())),
            "verified_2027_itineraries": 0}


def audit_summary(inventory):
    return {key:inventory[key] for key in (
        "base_count","destination_count","total_pairs",
        "historical_pairs","indicative_pairs","local_pairs","missing_pairs")}
