"""UX115: small provenance-checked overlay for gaps in the legacy UX34 matrix.

Operator-published one-way minima are NOT confirmed 2027 itineraries.
Do not mutate the frozen four-base itinerary dataset or substitute a guessed
multi-leg/return journey. Existing timed evidence takes precedence.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

DATA=Path(__file__).resolve().parent/"data"/"ux115_rail_gap_evidence_2026_11.json"


def validate_rail_gap_overlay(data:dict)->None:
    if (data.get("schema_version")!=1 or data.get("confirmed_2027") is not False
            or data.get("time_scope")!="operator_published_fastest_oneway_2026_station_to_station"):
        raise ValueError("Invalid UX115 scope or claims about 2027")
    date.fromisoformat(data["checked_at"])
    seen=set()
    for item in data["routes"]:
        pair=(item["base_id"],item["destination_id"])
        if pair in seen:
            raise ValueError("Duplicate UX115 railway pair")
        seen.add(pair)
        minutes=item["fastest_train_oneway_min"]
        if (type(minutes) is not int or minutes<=0 or minutes>1440
                or item["return_verified_2027"] is not False
                or item["fare_eur_person_oneway"] is not None
                or item["representative_minutes"] is not None):
            raise ValueError("Unsupported estimated time/fare or return claim")
        if (not item["source_url"].startswith("https://www.sncf-connect.com/train/")
                or not item["origin_station"] or not item["destination_station"]
                or not item["operator"] or not item["notes"]):
            raise ValueError("Rail minimum requires primary source and station scope")
        date.fromisoformat(item["checked_at"])
        connections=item["connections_minimum"]
        if connections is not None and (type(connections) is not int or connections<0):
            raise ValueError("Invalid number of train connections")
    for item in data["research_gaps"]:
        pair=(item["base_id"],item["destination_id"])
        if pair in seen or not item.get("reason") or not item.get("research_urls"):
            raise ValueError("Unknown journey cannot be published as a timed route")
        seen.add(pair)
        if any(not link.startswith("https://") for link in item["research_urls"]):
            raise ValueError("Invalid research gap source")


def load_rail_gap_overlay(path:Path=DATA)->dict:
    payload=json.loads(Path(path).read_text(encoding="utf-8"))
    validate_rail_gap_overlay(payload)
    return payload


def unresolved_gap_reason(base_id:str,destination_id:str)->str|None:
    """Explain genuinely unresolved research without fabricating an itinerary."""
    for item in load_rail_gap_overlay()["research_gaps"]:
        if item["base_id"]==base_id and item["destination_id"]==destination_id:
            return item["reason"]
    return None


def documented_gap_route(base_id:str,destination_id:str)->dict|None:
    """Return only genuine observed minimum, not a fabricated 2027 scenario."""
    for item in load_rail_gap_overlay()["routes"]:
        if item["base_id"]==base_id and item["destination_id"]==destination_id:
            return {
                "minutes":item["fastest_train_oneway_min"],"fare":None,
                "source":item["source_url"],"fare_condition":"unknown",
                "basis":item["checked_at"],"note":item["notes"],
                "return_verified":False,"representative_minutes":None,
                "transfers":item["connections_minimum"],
                "operator":item["operator"],
                "origin_station":item["origin_station"],
                "destination_station":item["destination_station"],
                "frequency_reference":None,"provenance":"ux115_operator_minimum_2026",
                "missing":["Horário e retorno de 2027","Última milha",
                           "Tarifa e conexões da data real"],
            }
    return None
