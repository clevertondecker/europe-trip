"""DATA 9.1: deterministic, read-only rail research backlog across 30 bases.

The canonical DQ 3.2 view and the main comparison share rail precedence.
This audits coverage, not availability, feasibility, fares or 2027 services.
"""
from __future__ import annotations

from collections import Counter
from rail_component_contract import build_component_records
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



def component_research_backlog(inventory, *, evidence_by_pair=None):
    """Read-only evidence-component backlog; preserves the legacy API."""
    return build_component_records(inventory, evidence_by_pair=evidence_by_pair)


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
