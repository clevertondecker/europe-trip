"""ARCH 1.0: canonical read-only display selection for railway evidence.

The unified adapter retains source-specific precedence and all observations.
Exploration data is a sourced fallback ONLY when there is no timed record in
the unified adapter. No return, tariff or reachability is inferred.
"""
from __future__ import annotations

from copy import deepcopy

from base_explorer_model import load_exploration
from rail_evidence_unified_model import (
    canonical_place, load_rail_evidence, route_evidence,
)


def get_rail_evidence(base_id: str, destination_id: str, *,
                      rail: dict | None = None,
                      exploration: dict | None = None) -> dict:
    """Resolve one historical time for presentation, preserving alternatives.

    Display precedence:
    1. route_evidence() on rail_evidence_unified_model's sources.
    2. First valid 2026 exploration_bases_2027 observation when the unified
       adapter contains no usable time.
    3. Unknown (never zero, never 'no train exists').
    """
    origin = canonical_place(base_id)
    destination = canonical_place(destination_id)

    def result(status, minimum=None, typical=None, source=None, date=None,
               dataset=None, observations=None, reason=None, regional=None):
        return {
            "origin_id": origin, "destination_id": destination,
            "status": status, "minimum_oneway_min": minimum,
            "typical_oneway_min": typical, "regional_oneway_min": regional,
            "source_url": source, "source_date": date,
            "source_dataset": dataset,
            "observations": deepcopy(observations or []),
            "selection_reason": reason,
            "return_2027_verified": False, "comparable": False,
            "evidence_scope": "historical_oneway_station_to_station"
                              if minimum is not None else "unknown",
        }

    # No train is needed when destination and base are the same city;
    # local urban travel is still UNKNOWN, not zero.
    if origin == destination:
        return result("local", reason="local_mobility_unverified")

    rail = rail if rail is not None else load_rail_evidence()
    view = route_evidence(rail, origin, destination)
    observations = view.get("observations", [])
    if view["status"] == "historical_time":
        return result(
            "historical_time", minimum=view["minimum_oneway_min"],
            typical=view["typical_oneway_min"],
            regional=view["regional_oneway_min"],
            source=view["source_url"], date=view["source_date"],
            dataset=view["source_dataset"], observations=observations,
            reason="unified_adapter_precedence",
        )

    exploration = exploration if exploration is not None else load_exploration()
    for row in exploration["routes"]:
        if (canonical_place(row["base_id"]) == origin
                and canonical_place(row["destination_id"]) == destination
                and type(row.get("train_minutes_oneway_min")) in (int, float)
                and row["train_minutes_oneway_min"] > 0
                and isinstance(row.get("source_url"), str)
                and row["source_url"].startswith("https://")):
            return result(
                "historical_time",
                minimum=row["train_minutes_oneway_min"], typical=None,
                source=row["source_url"], date=row.get("retrieved_at"),
                dataset="exploration_bases_2027",
                observations=observations,
                reason="exploration_fallback_no_unified_time",
            )

    return result(
        "not_researched" if not observations else "partial",
        observations=observations, reason="no_sourced_time_available",
    )
