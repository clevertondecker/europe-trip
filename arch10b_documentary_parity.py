"""ARCH 1.0b — independently audit documentary railway selection.

Documentary coverage is a historical checklist, not the same contract as
the ARCH 1.0 display choice. Never silently rewrite percentages or scores.
"""
from __future__ import annotations
from copy import deepcopy

from base_coverage_model import _dataset_routes
from base_research_expanded_model import load_rail, load_research
from base_explorer_model import load_exploration
from attractions_model import load_base_routes
from five_base_comparison_model import load_five_base_evidence
from evidence_query_model import get_rail_evidence
from rail_evidence_unified_model import load_rail_evidence


def documentary_rail_parity(*, cities=None, legacy_rail=None, exploration=None,
                            five=None, base_routes=None, unified=None):
    study = load_research()
    cities = cities if cities is not None else study["cities"]
    legacy_rail = legacy_rail if legacy_rail is not None else load_rail()
    exploration = exploration if exploration is not None else load_exploration()
    five = five if five is not None else load_five_base_evidence()
    base_routes = base_routes if base_routes is not None else load_base_routes()
    unified = unified if unified is not None else load_rail_evidence()

    results = []
    for city in cities:
        origin = city["id"]
        basket, legacy = _dataset_routes(
            origin, legacy_rail, exploration, five, base_routes)
        for destination in basket:
            row = legacy.get(destination)
            current = get_rail_evidence(
                origin, destination, rail=unified, exploration=exploration)
            old_minutes = row["minutes"] if row is not None else None
            new_minutes = current["minimum_oneway_min"]
            old_url = row["source_url"] if row is not None else None
            new_url = current["source_url"]
            same_time = old_minutes == new_minutes
            same_source = old_url == new_url
            results.append({
                "base_id": origin,
                "destination_id": destination,
                "legacy_documentary_minutes": old_minutes,
                "shared_display_minutes": new_minutes,
                "legacy_documentary_source": old_url,
                "shared_display_source": new_url,
                "same_time": same_time,
                "same_source": same_source,
                "same_evidence": same_time and same_source,
                "legacy_fare_from_eur_person_oneway": (
                    row.get("fare_oneway") if row else None),
                "legacy_frequency": row.get("frequency") if row else None,
                "legacy_transfers": row.get("transfers") if row else None,
                "shared_observations_count": len(current["observations"]),
                "difference_reason": (
                    None if same_time and same_source
                    else "different_source_selection_or_documentary_scope"),
            })
    return {
        "rows": deepcopy(results),
        "pairs": len(results),
        "time_differences": sum(not x["same_time"] for x in results),
        "source_differences": sum(not x["same_source"] for x in results),
        "identical_pairs": sum(x["same_evidence"] for x in results),
        "safe_to_migrate_without_review": all(x["same_evidence"] for x in results),
        "documentary_model_modified": False,
        "notes": "Legacy frequency/transfer/checklist coverage differs from display selection; "
                 "audit differences before migrating the percentage model.",
    }
