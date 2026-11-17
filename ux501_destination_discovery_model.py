"""UX 5.0.1 — destination discovery independent of any chosen home base.

This is a read-only projection of existing versioned research. Source records,
canonical attraction IDs, semantic reconciliation, and official TripPlan are
never changed by browsing or filtering.
"""
from __future__ import annotations

from copy import deepcopy
from unicodedata import normalize

from attractions_model import load_attractions
from base_explorer_model import load_exploration
from base_research_expanded_model import load_research
from dq32_macro_opportunities_model import (
    load_macro_tourism, _registry, reconcile_attractions,
)
from rail_evidence_unified_model import canonical_place


CATEGORY_NAMES = {
    "arquitetura": "Patrimônio e arquitetura",
    "historia": "História e cultura",
    "história": "História e cultura",
    "museu": "Museus",
    "museum": "Museus",
    "heritage": "Patrimônio e arquitetura",
    "urban_walk": "Passeios urbanos",
    "nature": "Natureza",
    "natureza": "Natureza",
    "arte": "Arte e cultura",
    "cultura": "Arte e cultura",
}


def _category(name: str) -> str:
    return CATEGORY_NAMES.get(name, "Outras experiências")


def build_destination_discovery(*, catalog=None, exploration=None,
                                research=None, macro=None) -> dict:
    """Return a deterministic, base-free, deduplicated destination inventory."""
    catalog = catalog if catalog is not None else load_attractions()
    exploration = exploration if exploration is not None else load_exploration()
    research = research if research is not None else load_research()
    macro = macro if macro is not None else load_macro_tourism()

    destinations = _registry(catalog, exploration, research, macro)
    identities = reconcile_attractions(catalog, macro)
    source_names = {row["id"]: row["name"] for row in macro["attractions"]}
    photos = {canonical_place(row["id"]): deepcopy(row.get("photo"))
              for row in catalog["destinations"] if row.get("photo")}
    details = []
    for destination_id, place in destinations.items():
        attractions = (identities["canonical_by_city"].get(destination_id, [])
                       + identities["new_by_city"].get(destination_id, []))
        canonical_category = {
            row["id"]: row["category"] for row in catalog["attractions"]}
        new_category = {
            row["id"]: row["category"] for row in macro["attractions"]}
        selected = []
        categories = set()
        for attr in attractions:
            category = _category(canonical_category.get(
                attr["id"], new_category.get(attr["id"], "")))
            categories.add(category)
            selected.append({
                "id": attr["id"],
                "name": attr["name"],
                "category": category,
                "source_url": attr["source_url"],
                "kind": attr["kind"],
                "reconciled_source_ids": deepcopy(
                    attr.get("reconciled_source_ids", [])),
                "additional_sources": deepcopy(
                    attr.get("additional_sources", [])),
                "alias_names": [source_names[key] for key in
                                attr.get("reconciled_source_ids", [])],
            })
        details.append({
            "id": destination_id,
            "name": place["name"],
            "country": place["country"],
            "sources": deepcopy(place["registry_sources"]),
            "attractions": selected,
            "attraction_count": len(selected),
            "categories": sorted(categories),
            "photo": photos.get(destination_id),
            "source_url": (
                next((row["source_url"] for row in catalog["destinations"]
                      if canonical_place(row["id"]) == destination_id), None)
                or (selected[0]["source_url"] if selected else None)),
            "research_status": (
                "attractions_documented" if selected else
                "destination_known_attractions_not_indexed"),
            "feasible_from_base": None,
            "verified_weekend_return": False,
            "officially_selected": False,
        })
    details.sort(key=lambda x: (x["country"], x["name"], x["id"]))
    return {
        "destinations": details,
        "destination_count": len(details),
        "canonical_attractions_count": len(catalog["attractions"]),
        "dq32_source_records_count": len(macro["attractions"]),
        "unique_attractions_count": sum(d["attraction_count"] for d in details),
        "reconciled_aliases": deepcopy(identities["reconciled"]),
        "countries": sorted({d["country"] for d in details}),
        "categories": sorted({c for d in details for c in d["categories"]}),
        "base_required": False,
        "read_only": True,
    }


def filter_destinations(discovery: dict, *, country=None, categories=(),
                        query="", selected=()) -> list[dict]:
    """Pure filtering; unknown destinations remain visible without rail proof."""
    if country not in (None, *discovery["countries"]):
        raise ValueError("País desconhecido no catálogo")
    categories = tuple(categories)
    if any(category not in discovery["categories"] for category in categories):
        raise ValueError("Categoria desconhecida")
    valid_ids = {x["id"] for x in discovery["destinations"]}
    if len(set(selected)) != len(selected) or any(x not in valid_ids for x in selected):
        raise ValueError("Seleção exploratória inválida")
    search = normalize("NFKD", query.casefold())
    search = "".join(x for x in search if not (0x300 <= ord(x) <= 0x36F))
    result = []
    for destination in discovery["destinations"]:
        haystack = normalize("NFKD", " ".join([
            destination["name"], destination["country"],
            *[attr["name"] for attr in destination["attractions"]],
            *[name for attr in destination["attractions"]
              for name in attr["alias_names"]],
        ]).casefold())
        haystack = "".join(x for x in haystack if not (0x300 <= ord(x) <= 0x36F))
        if country is not None and destination["country"] != country:
            continue
        if categories and not set(categories).intersection(destination["categories"]):
            continue
        if search.strip() and search.strip() not in haystack:
            continue
        result.append(deepcopy(destination))
    priorities = {key: index for index, key in enumerate(selected)}
    result.sort(key=lambda row: (
        0 if row["id"] in priorities else 1,
        priorities.get(row["id"], 0),
        row["country"], row["name"]))
    return result
