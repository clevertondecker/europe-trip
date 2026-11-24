"""Read-only projection of destination interests and canonical selected visits.

This is not a new source of planning state. Wishlist and TripPlan remain distinct.
"""
from __future__ import annotations

from ux502_destination_interests_model import (
    PRIORITIES, empty_interests, validate_interests,
)
from itinerary_flow_model import selected_rows
from destination_identity import canonical_destination_id
from itinerary_eligibility import itinerary_eligibility
from ux63_timeline_model import project_timeline


def build_destination_board(interests, plan, discovery, catalog, weekend_groups=None):
    """One row per place; interest, outing, group and time are independent facets."""
    wishes = validate_interests(interests if interests is not None else empty_interests(),
                                discovery)
    known = {canonical_destination_id(row["id"]): row for row in discovery["destinations"]}
    visits = {canonical_destination_id(row["id"]): row for row in selected_rows(plan, catalog)}
    timing = {canonical_destination_id(row["id"]): row for row in project_timeline(plan, catalog, weekend_groups)}
    priorities = {canonical_destination_id(r["destination_id"]): r["priority"] for r in wishes["items"]}
    all_ids = set(priorities) | set(visits)
    rows = []
    for destination_id in all_ids:
        interest = priorities.get(destination_id)
        visit = visits.get(destination_id)
        if interest == "discarded" and visit is None:
            continue
        place = known.get(destination_id, {})
        temporal = timing.get(destination_id, {})
        rows.append({
            "id": destination_id,
            "name": place.get("name") or (visit["name"] if visit else destination_id),
            "country": place.get("country", ""),
            "priority": interest,
            "wanted": interest is not None and interest != "discarded",
            "planned": visit is not None,
            "attractions_count": len(visit["attractions"]) if visit else 0,
            "in_group": bool(temporal.get("grouped")),
            "organized": bool(temporal.get("organized")),
            "dated": bool(temporal.get("dated")),
            "group_id": temporal.get("group_id"),
            "group_name": temporal.get("group_name"),
            "group_sequence": temporal.get("group_sequence"),
            "group_period": temporal.get("group_period"),
            "group_dates": temporal.get("group_dates", []),
            "individual_period": temporal.get("period"),
            "individual_dates": temporal.get("dates", []),
            "stage": visit["stage"] if visit else None,
            "eligibility": itinerary_eligibility(destination_id, catalog),
        })
    order = {p: i for i, p in enumerate(PRIORITIES)}
    rows.sort(key=lambda r: (0 if r["planned"] else 1,
                              order.get(r["priority"], len(order)),
                              r["name"].casefold(), r["id"]))
    return rows


def organizer_wishlist_candidates(interests, plan, discovery, catalog, stage):
    """Present wishlist-only places in the organizer, without confirming them.

    A wishlist ID is promotable only if it matches a validated outing choice
    in the current stage. Never guess an ID from similar names.
    """
    from itinerary_flow_model import ITALY_STAGE, FRANCE_STAGE
    if stage not in (ITALY_STAGE, FRANCE_STAGE):
        raise ValueError("Etapa de organização inválida")
    board = build_destination_board(interests, plan, discovery, catalog)
    result = {"eligible": [], "other_stage": [], "unsupported": []}
    for row in board:
        if not row["wanted"] or row["planned"]:
            continue
        eligibility = itinerary_eligibility(row["id"], catalog, stage)
        bucket = "unsupported" if eligibility["status"] == "research_only" else eligibility["status"]
        result[bucket].append({**row, "eligibility": eligibility})
    return result


def board_metrics(rows):
    """Avoid counting a wish as a confirmed visit or an undated group as dated."""
    return {
        "wished": sum(r["wanted"] for r in rows),
        "planned": sum(r["planned"] for r in rows),
        "organized": sum(r["planned"] and r["organized"] for r in rows),
        "dated": sum(r["dated"] for r in rows),
        "grouped": sum(r["planned"] and r["in_group"] for r in rows),
    }
