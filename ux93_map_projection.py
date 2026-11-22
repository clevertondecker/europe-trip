"""Read-only map categories from existing destination wishes and TripPlan.

No new persistence and no implication that a marker is a reservation.
The category is an annotation of the current map projection, not a mutation
of the travel itinerary or source catalog.
"""
from __future__ import annotations

from copy import deepcopy
from rail_evidence_unified_model import canonical_place
from catalog import ALIASES as MAP_CATALOG_ALIASES

# Explicitly reconciled against itinerary_options_2027.json (map geometry)
# and italy_honeymoon_research_2027.json (canonical TripPlan choice IDs).
# Ravello and Pompeii have no supported map points, so deliberately absent.
ITALY_TO_MAP = {
    "italy_rome": "rome",
    "italy_naples": "naples",
    "italy_salerno": "salerno",
    "italy_maiori": "maiori",
    "italy_minori": "minori",
    "italy_amalfi": "amalfi",
    "italy_positano": "positano",
    "italy_capri": "capri",
}


def map_identity(source_id: str) -> str:
    """Only explicit catalog/Italy aliases; never infer from display names."""
    key = canonical_place(source_id)
    key = ITALY_TO_MAP.get(key, key)
    return canonical_place(MAP_CATALOG_ALIASES.get(key, key))


def unmapped_wishes(places: list[dict], interests: dict | None) -> set[str]:
    """Read-only set of wished IDs without verified points in this map catalog."""
    mapped = {map_identity(row["id"]) for row in places}
    return {row["destination_id"]
            for row in (interests or {}).get("items", [])
            if row.get("priority") != "discarded"
            and isinstance(row.get("destination_id"), str)
            and map_identity(row["destination_id"]) not in mapped}


GROUPS = ("Na minha lista", "No roteiro", "Base candidata", "Outros destinos")
STAGES = {"Itália": "italy", "Temporada europeia": "france"}


def annotate_map_places(places: list[dict], interests: dict | None,
                        plan: dict) -> list[dict]:
    wishes = {map_identity(row["destination_id"])
              for row in (interests or {}).get("items", [])
              if row.get("priority") != "discarded"
              and isinstance(row.get("destination_id"), str)}
    visits = {map_identity(v["destination_id"])
              for v in plan.get("flexible_visits", [])
              if isinstance(v.get("destination_id"), str)}
    visits.update(map_identity(key) for key in plan.get("packages", {}))
    output = []
    for place in places:
        copy = deepcopy(place)
        destination_id = map_identity(copy["id"])
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
