"""UX131: explicit transient research projection, not a wishlist document."""
from dataclasses import dataclass
from destination_identity import outing_destination_id
from ux502_destination_interests_model import validate_interests, ordered_interests, LABELS

PLANNED = "planned_only"
PRIORITY_LABELS = {**LABELS, PLANNED: "No roteiro · sem prioridade na lista"}
ORDER = {"must_visit":0, "interested":1, "maybe":2, PLANNED:3, "discarded":4}
PLANNED_WEIGHT = 1  # neutral minimum coefficient, not a user priority


@dataclass(frozen=True)
class ComparisonDestinations:
    plan_id: str
    revision: int
    entries: tuple
    unmatched: tuple


def project_comparison_destinations(interests, plan, discovery, catalog):
    from itinerary_flow_model import selected_rows, FRANCE_STAGE
    wishes=validate_interests(interests,discovery)
    by_id={outing_destination_id(d["id"]):d["id"] for d in discovery["destinations"]}
    planned=set()
    unmatched=[]
    if plan is not None:
        for row in selected_rows(plan,catalog):
            if row["stage"] != FRANCE_STAGE:
                continue
            key=by_id.get(outing_destination_id(row["id"]))
            if key is None:
                unmatched.append(row["name"])
            else:
                planned.add(key)
    priorities={r["destination_id"]:r["priority"] for r in wishes["items"]}
    entries=[]
    for key in sorted(set(priorities)|planned):
        original=priorities.get(key)
        effective=PLANNED if key in planned and original in (None,"discarded") else original
        entries.append((key,effective,original,key in planned))
    return ComparisonDestinations(plan["plan_id"] if plan else "",wishes["revision"],tuple(entries),tuple(sorted(unmatched)))


def from_state(state, discovery):
    from attractions_model import load_attractions
    from ux502_destination_interests_model import empty_interests
    return project_comparison_destinations(state.get("ux502_interests",empty_interests()),
        state.get("advisor_plan"),discovery,load_attractions())


def comparison_items(value, discovery):
    if not isinstance(value,ComparisonDestinations):
        return ordered_interests(value,discovery)
    return sorted([{"destination_id":key,"priority":priority,
                    "wishlist_priority":original,"in_plan":planned,
                    "origin": ("Minha lista + No roteiro" if original not in (None,"discarded") and planned
                               else "No roteiro · descartado na lista" if original=="discarded" and planned
                               else "No roteiro" if planned else "Minha lista")}
                   for key,priority,original,planned in value.entries],
                  key=lambda r:(ORDER[r["priority"]],r["destination_id"]))


def active_ids(value, discovery):
    return [r["destination_id"] for r in comparison_items(value,discovery)
            if r["priority"]!="discarded"]
