"""Map-ready origin/destination markers using only researched itinerary points.

No routing polyline or travel time is generated from coordinates.
"""
from __future__ import annotations
from unicodedata import normalize

def key(value: str) -> str:
    return "".join(c for c in normalize("NFKD", value.casefold()) if c.isalnum())

def route_endpoints(data: dict, outing: dict) -> list[dict]:
    locations={key(p["name"]):p for p in data["places"]}
    start=locations.get(key(outing["origin"]))
    finish=locations.get(key(outing["destination"]))
    if start is None or finish is None or start["id"] == finish["id"]:
        return []
    return [{**p, "status": "roteiro_proposto",
             "description": ("Origem do deslocamento pesquisado" if i==0
                             else "Destino do deslocamento pesquisado")}
            for i,p in enumerate((start,finish))]
