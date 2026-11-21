"""Source-backed DATA23 destination overlay for exploratory discovery.

Only explicitly reconciled places with tourism sources enter the wishlist.
Rail endpoints alone are not evidence of a tourism destination. No official
catalog, snapshots, TripPlan, or stored wishlist are changed by projection.
"""
from __future__ import annotations

from copy import deepcopy
from data23_france_candidates_model import load_data23
from rail_evidence_unified_model import canonical_place

# Explicit reconciliation, not a slug/translation inference.
PLACES = {
    "Angers": ("angers", "Angers", "França"),
    "Saumur": ("saumur", "Saumur", "França"),
    "Le Mans": ("le_mans", "Le Mans", "França"),
    "Annecy": ("annecy", "Annecy", "França"),
    "Rennes": ("rennes", "Rennes", "França"),
    "Saint-Malo": ("saint_malo", "Saint-Malo", "França"),
    "Dinan": ("dinan", "Dinan", "França"),
}
CATEGORY = {
    "angers_terra": "Natureza",
    "rennes_thabor": "Natureza",
    "le_mans_circuit": "Outras experiências",
}


def append_data23_destinations(discovery: dict, *, data=None) -> dict:
    """Expose only curated local/regionally sourced places, without overwrites."""
    data = load_data23() if data is None else data
    output = deepcopy(discovery)
    rows = {row["id"]: row for row in output["destinations"]}
    if len(rows) != len(output["destinations"]):
        raise ValueError("Catálogo de destinos duplicado")
    groups = {}
    for attraction in data["attractions"]:
        place = PLACES.get(attraction["place"])
        if place is None:
            continue
        destination_id, name, country = place
        if canonical_place(destination_id) != destination_id:
            raise ValueError("ID de destino DATA23 não canônico")
        group = groups.setdefault(destination_id, {
            "name": name, "country": country, "attractions": [],
            "source_url": attraction["source_url"],
        })
        group["attractions"].append({
            "id": attraction["id"],
            "name": attraction["name"],
            "category": CATEGORY.get(attraction["id"], "Patrimônio e arquitetura"),
            "source_url": attraction["source_url"],
            "kind": "supplemental_exploratory",
            "reconciled_source_ids": [],
            "additional_sources": [],
            "alias_names": [],
        })

    existing_attractions = {a["id"] for row in rows.values() for a in row["attractions"]}
    for destination_id, group in groups.items():
        # A future canonical destination must win. Reconciliation of overlapping
        # attraction records requires deliberate review, never duplicate entries.
        if destination_id in rows:
            continue
        attrs = group["attractions"]
        if len({a["id"] for a in attrs}) != len(attrs) or any(a["id"] in existing_attractions for a in attrs):
            raise ValueError("Atração DATA23 duplicada no catálogo")
        existing_attractions.update(a["id"] for a in attrs)
        rows[destination_id] = {
            "id": destination_id, "name": group["name"], "country": group["country"],
            "sources": ["data23_france_base_candidates_2026_11"],
            "attractions": attrs, "attraction_count": len(attrs),
            "categories": sorted({a["category"] for a in attrs}),
            # Attraction photographs stay on the sourced city research cards;
            # do not relabel them as destination-wide images.
            "photo": None, "source_url": group["source_url"],
            "research_status": "supplemental_attractions_documented",
            "feasible_from_base": None, "verified_weekend_return": False,
            "officially_selected": False,
        }
    output["destinations"] = sorted(rows.values(), key=lambda r: (r["country"], r["name"], r["id"]))
    output["destination_count"] = len(rows)
    output["unique_attractions_count"] = sum(r["attraction_count"] for r in rows.values())
    output["countries"] = sorted({r["country"] for r in rows.values()})
    output["categories"] = sorted({c for r in rows.values() for c in r["categories"]})
    return output
