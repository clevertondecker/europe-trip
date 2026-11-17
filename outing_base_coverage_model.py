"""Read-only discovery coverage for home bases without the 4-base fare matrix.

This adapter joins existing research evidence by canonical ID, never creates
new train times, zero-cost routes, 2027 tickets or TripPlan mutations.
"""
from __future__ import annotations

from copy import deepcopy

from attractions_model import load_attractions
from base_explorer_model import load_exploration
from base_scenario_model import base_options
from rail_evidence_unified_model import (load_rail_evidence, route_evidence,
                                         canonical_place)

OFFICIAL_FARE_BASES = frozenset({"mulhouse", "strasbourg", "metz", "nancy"})


def _exploratory_evidence(exploration: dict, base_id: str, dest_id: str) -> dict | None:
    # The existing exploration study contains additional genuine operator
    # excerpts (e.g. Lille -> Rotterdam), absent from the rail adapter.
    matches = [r for r in exploration["routes"]
               if r["base_id"] == base_id and r["destination_id"] == dest_id
               and r["train_minutes_oneway_min"] is not None]
    if not matches:
        return None
    row = matches[0]
    return {
        "minutes": row["train_minutes_oneway_min"],
        "source_url": row["source_url"],
        "source_dataset": "exploration_bases_2027",
        "evidence_date": row.get("retrieved_at"),
    }


def preview_for_base(base_id: str, *, catalog: dict | None = None,
                     rail: dict | None = None, exploration: dict | None = None,
                     options: list[dict] | None = None) -> dict:
    """All canonical attractions remain visible, regardless of rail coverage.

    Train observations are historical one-way station-to-station only.
    A local destination is NOT a free transfer; local transport is unknown.
    """
    catalog = catalog if catalog is not None else load_attractions()
    rail = rail if rail is not None else load_rail_evidence()
    exploration = exploration if exploration is not None else load_exploration()
    options = options if options is not None else base_options()
    labels = {x["id"]: x for x in options}
    if base_id not in labels:
        raise ValueError("Cidade-base exploratória inexistente")
    destinations = []
    for place in catalog["destinations"]:
        did = place["id"]
        items = [a for a in catalog["attractions"] if a["destination_id"] == did]
        local = canonical_place(did) == canonical_place(base_id)
        rail_row = route_evidence(rail, base_id, did)
        minutes = rail_row["minimum_oneway_min"] if rail_row["status"] == "historical_time" else None
        source = rail_row.get("source_url") if minutes is not None else None
        dataset = rail_row.get("source_dataset") if minutes is not None else None
        checked = rail_row.get("source_date") if minutes is not None else None
        if minutes is None and not local:
            extra = _exploratory_evidence(exploration, base_id, did)
            if extra:
                minutes, source, dataset, checked = (
                    extra["minutes"], extra["source_url"],
                    extra["source_dataset"], extra["evidence_date"])
        if local:
            minutes, source, dataset, checked = None, None, None, None
        destinations.append({
            "destination_id": did,
            "name": place["name"],
            "country": place["country"],
            "attraction_count": len(items),
            "attractions": [{"id": a["id"], "name": a["name"],
                             "source_url": a["source_urls"][0]} for a in items],
            "local": local,
            "train_oneway_min": minutes,
            "train_evidence_url": source,
            "train_evidence_dataset": dataset,
            "train_evidence_date": checked,
            "train_status": ("local_transport_unverified" if local else
                             "historical_station_to_station" if minutes is not None else
                             "not_researched_for_this_pair"),
            "weekend_return_verified_2027": False,
            "full_couple_cost_eur": None,
            "last_mile_min": None,
        })
    destinations.sort(key=lambda x: (
        0 if x["local"] else 1 if x["train_oneway_min"] is not None else 2,
        x["train_oneway_min"] if x["train_oneway_min"] is not None else 999999,
        x["name"]))
    known = sum(x["train_oneway_min"] is not None for x in destinations)
    return {
        "base_id": base_id,
        "base_name": labels[base_id]["name"],
        "catalog_destinations": len(destinations),
        "catalog_attractions": sum(x["attraction_count"] for x in destinations),
        "timed_destination_count": known,
        "unknown_destination_count": len(destinations) - known - sum(x["local"] for x in destinations),
        "status": "historical_partial" if known else "attractions_only",
        "destinations": deepcopy(destinations),
        "advisory_only": True,
        "trip_plan_modified": False,
    }
