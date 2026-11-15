"""Canonical map catalog compiled from itinerary and legacy travel-plan places.

Use itinerary locations as the canonical geometry. Retain legacy descriptions/status
where available, without claiming the new catalog is synchronized from Drive.
"""
from __future__ import annotations
from typing import Any

ALIASES = {"roma":"rome","napoles":"naples","luxemburgo":"luxembourg"}
REVERSE_ALIASES = {v:k for k,v in ALIASES.items()}
COUNTRY = {"Itália":"Itália","França":"França","Suíça":"Suíça",
           "Alemanha":"Alemanha","Luxemburgo":"Luxemburgo"}
def build_catalog(legacy: list[dict], itinerary: dict,
                  researched_destinations: list[dict] | None = None) -> list[dict]:
    by_id: dict[str,dict[str,Any]] = {}
    for row in legacy:
        mapped = ALIASES.get(row["id"],row["id"])
        if mapped in by_id:
            raise ValueError("Identificador legado duplicado")
        by_id[mapped] = {**row,"id":mapped}
    for p in itinerary["places"]:
        key = p["id"]
        if key in by_id:
            base = by_id[key]
            by_id[key] = {**base, "lat":p["lat"],"lon":p["lon"],
                          "country":p["country"],"phase":p["phase"],
                          "role":p["role"] if not base.get("role") else base["role"]}
        else:
            by_id[key] = {
                "id":key,"name":p["name"],"country":p["country"],
                "lat":p["lat"],"lon":p["lon"],"phase":p["phase"],
                "role":p["role"],"description":p["description"],
                "duration":"A verificar","status":"opcional","source":"itinerary_research_2026",
            }
    for point in researched_destinations or []:
        if point["id"] not in by_id:
            by_id[point["id"]] = {
                "id": point["id"], "name": point["name"],
                "country": point["country"], "lat": point["lat"],
                "lon": point["lon"], "status": "opcional",
                "role": "Atrações pesquisadas",
                "description": "Destino do catálogo de atrações. Transporte desde a base a verificar.",
                "duration": "A verificar", "source": "attractions_research_2026",
            }
    for row in by_id.values():
        if "phase" not in row:
            row["phase"]="italy" if row["country"]=="Itália" else "france"
    return list(by_id.values())

def filter_catalog(rows: list[dict], countries: list[str] | None = None,
                   statuses: list[str] | None = None, phases: list[str] | None = None) -> list[dict]:
    # Explicit empty selection = no matches; None = no filter.
    return [r for r in rows if
            (countries is None or r["country"] in countries)
            and (statuses is None or r["status"] in statuses)
            and (phases is None or r["phase"] in phases)]
