"""Shared historical-pair input for the authoritative rail display projection."""
from __future__ import annotations


def pair_projection_row(base_id: str, destination_id: str, evidence: dict) -> dict:
    """Preserve the exact directed pair and distinguish sourced divergence.

    This does not choose a source: evidence_query_model already resolved
    historical precedence; rail_reference_projection_model applies overlays.
    """
    times = {r.get("minimum_oneway_min") for r in evidence["observations"]
             if type(r.get("minimum_oneway_min")) is int
             and r["minimum_oneway_min"] > 0}
    dated = {r.get("evidence_date") for r in evidence["observations"]
             if r.get("evidence_date")}
    services = {r.get("observation_type") for r in evidence["observations"]
                if r.get("observation_type")}
    return {
        "base_id": base_id,
        "destination_id": destination_id,
        "evidence_status": evidence["status"],
        "minimum_oneway_min": evidence["minimum_oneway_min"],
        "source_url": evidence["source_url"],
        "divergent_sources": len(times) > 1,  # legacy flag: variation, not contradiction
        "variation_status": ("multiple_dates" if len(times) > 1 and len(dated) > 1
                             else "different_observation_types" if len(times) > 1 and len(services) > 1
                             else "conditions_unresolved" if len(times) > 1 else "not_observed"),
        "contradiction_confirmed": False,
    }
