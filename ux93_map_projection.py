"""Read-only map categories from existing destination wishes and TripPlan.

No new persistence and no implication that a marker is a reservation.
The category is an annotation of the current map projection, not a mutation
of the travel itinerary or source catalog.
"""
from __future__ import annotations

from copy import deepcopy
from rail_evidence_unified_model import canonical_place

GROUPS = ("Na minha lista", "No roteiro", "Base candidata", "Outros destinos")
STAGES = {"Itália": "italy", "Temporada europeia": "france"}


def annotate_map_places(places: list[dict], interests: dict | None,
                        plan: dict) -> list[dict]:
    wishes = {canonical_place(row["destination_id"])
              for row in (interests or {}).get("items", [])
              if row.get("priority") != "discarded"
              and isinstance(row.get("destination_id"), str)}
    visits = {canonical_place(v["destination_id"])
              for v in plan.get("flexible_visits", [])
              if isinstance(v.get("destination_id"), str)}
    visits.update(canonical_place(key) for key in plan.get("packages", {}))
    output = []
    for place in places:
        copy = deepcopy(place)
        destination_id = canonical_place(copy["id"])
        if destination_id in visits:
            group = "No roteiro"
        elif destination_id in wishes:
            group = "Na minha lista"
        elif copy.get("status") == "candidata":
            group = "Base candidata"
        else:
            group = "Outros destinos"
        copy["ux93_group"] = group
        copy["role"] = group + " · " + (copy.get("role") or "Referência geográfica")
        output.append(copy)
    return output


def filter_map_places(places: list[dict], *, group: str = "Todos",
                      stage: str = "Todas") -> list[dict]:
    if group not in ("Todos", *GROUPS) or stage not in ("Todas", *STAGES):
        raise ValueError("Filtro do mapa desconhecido")
    phase = STAGES.get(stage)
    return [p for p in places
            if (group == "Todos" or p["ux93_group"] == group)
            and (phase is None or p.get("phase") == phase)]
