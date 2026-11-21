"""Read-only projection of destination interests and canonical selected visits.

This is not a new source of planning state. Wishlist and TripPlan remain distinct.
"""
from __future__ import annotations

from ux502_destination_interests_model import (
    PRIORITIES, empty_interests, validate_interests,
)
from itinerary_flow_model import selected_rows, UNASSIGNED


def build_destination_board(interests, plan, discovery, catalog, weekend_groups=None):
    """One row per place; interest, outing, group and time are independent facets."""
    wishes = validate_interests(interests if interests is not None else empty_interests(),
                                discovery)
    known = {row["id"]: row for row in discovery["destinations"]}
    visits = {row["id"]: row for row in selected_rows(plan, catalog)}
    grouped, group_timed = set(), set()
    if isinstance(weekend_groups, dict):
        for group in weekend_groups.get("groups", []):
            ids = group.get("destinations", [])
            grouped.update(ids)
            if group.get("start_date") or group.get("period") not in (
                None, "", "Ainda não definido", "A definir"):
                group_timed.update(ids)
    priorities = {r["destination_id"]: r["priority"] for r in wishes["items"]}
    all_ids = set(priorities) | set(visits)
    rows = []
    for destination_id in all_ids:
        interest = priorities.get(destination_id)
        visit = visits.get(destination_id)
        if interest == "discarded" and visit is None:
            continue
        place = known.get(destination_id, {})
        organized = bool(visit and (
            visit["period"] != UNASSIGNED or visit["exact_dates"] or
            destination_id in group_timed))
        rows.append({
            "id": destination_id,
            "name": place.get("name") or (visit["name"] if visit else destination_id),
            "country": place.get("country", ""),
            "priority": interest,
            "wanted": interest is not None and interest != "discarded",
            "planned": visit is not None,
            "attractions_count": len(visit["attractions"]) if visit else 0,
            "in_group": destination_id in grouped,
            "organized": organized,
            "dated": bool(visit and visit["exact_dates"]),
            "stage": visit["stage"] if visit else None,
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
    from itinerary_flow_model import destinations, ITALY_STAGE, FRANCE_STAGE
    if stage not in (ITALY_STAGE, FRANCE_STAGE):
        raise ValueError("Etapa de organização inválida")
    choices = {row["id"]: row for row in destinations(catalog)}
    board = build_destination_board(interests, plan, discovery, catalog)
    result = {"eligible": [], "other_stage": [], "unsupported": []}
    for row in board:
        if not row["wanted"] or row["planned"]:
            continue
        choice = choices.get(row["id"])
        if choice is None:
            result["unsupported"].append(row)
        elif choice["stage"] != stage:
            result["other_stage"].append(row)
        else:
            result["eligible"].append(row)
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
