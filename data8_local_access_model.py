"""DATA 8.3: two-direction *editorial walking* planning ranges.

Existing attraction_last_mile_model remains authoritative for documented
access samples. These ranges NEVER qualify as a verified rail connection.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from data8_priority_tourism_model import load_priority_lot

DATA = Path(__file__).resolve().parent / "data" / "data8_local_access_2026_11.json"
DIRECTIONS = {"station_to_attraction", "attraction_to_station"}


def validate_access_dataset(payload, *, tourism=None):
    tourism = tourism if tourism is not None else load_priority_lot()
    if (payload.get("schema_version") != 1 or
        payload.get("scope") != "editorial_local_access_not_a_verified_route"):
        raise ValueError("access research schema incompatible")
    date.fromisoformat(payload["checked_at"])
    seen, observations = set(), []
    for raw in payload.get("observations", []):
        x = deepcopy(raw)
        aid = x.get("attraction_id")
        if (aid not in tourism["by_id"] or
                x.get("destination_id") != tourism["by_id"][aid]["destination_id"]):
            raise ValueError("access cannot reference an unknown attraction")
        if (x.get("direction") not in DIRECTIONS or
            not x.get("station_id") or not x.get("entrance_id") or
            x.get("mode") != "walk" or x.get("state") != "editorial_range"):
            raise ValueError("access station/entrance/mode/precision invalid")
        key = (aid, x["direction"], x["station_id"], x["entrance_id"])
        if key in seen:
            raise ValueError("duplicate access scenario direction")
        seen.add(key)
        minimum, maximum = x.get("min_minutes"), x.get("max_minutes")
        if (type(minimum) is not int or type(maximum) is not int or
                not 1 <= minimum <= maximum <= 120):
            raise ValueError("unverified travel range invalid")
        url = urlparse(x.get("source_url") or "")
        if url.scheme != "https" or not url.netloc:
            raise ValueError("attraction research requires HTTPS page")
        date.fromisoformat(x["checked_at"])
        if x["checked_at"] > payload["checked_at"]:
            raise ValueError("source after snapshot")
        if ("NÃO publica" not in x.get("method", "") or
            x.get("distance_m") is not None or
            x.get("journey_date") is not None or
            x.get("joinable_to_rail_service") is not False or
            x.get("valid_for_2027") is not False):
            raise ValueError("editorial access may not claim verified routing")
        observations.append(x)
    return {"schema_version":1,"observations":observations,
            "by_attraction":{aid:[x for x in observations if x["attraction_id"]==aid]
                             for aid in {x["attraction_id"] for x in observations}},
            "source_scope":"editorial_walk_range_not_measured",
            "joinable_to_rail_service":False}


def load_access_dataset(path=DATA, *, tourism=None):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_access_dataset(data,tourism=tourism)


def local_access_scenario(attraction_id, *, station_id, evidence=None):
    """Only a symmetric-station lookup; directions and times stay independent."""
    data = evidence if evidence is not None else load_access_dataset()
    rows = [x for x in data["by_attraction"].get(attraction_id, [])
            if x["station_id"] == station_id]
    first = [x for x in rows if x["direction"] == "station_to_attraction"]
    second = [x for x in rows if x["direction"] == "attraction_to_station"]
    if len(first) != 1 or len(second) != 1:
        return {"state":"unknown_or_incomplete", "roundtrip_range_min":None,
                "ready_for_rail_2027":False,"missing_directions":True}
    to, back = first[0], second[0]
    if to["entrance_id"] != back["entrance_id"]:
        return {"state":"entry_mismatch","roundtrip_range_min":None,
                "ready_for_rail_2027":False}
    return {"state":"editorial_two_direction_range",
            "to_attraction_range_min":[to["min_minutes"],to["max_minutes"]],
            "to_station_range_min":[back["min_minutes"],back["max_minutes"]],
            "roundtrip_range_min":[to["min_minutes"]+back["min_minutes"],
                                    to["max_minutes"]+back["max_minutes"]],
            "station_id":station_id,"method":"editorial walk only",
            "ready_for_rail_2027":False,
            "valid_for_2027":False}


def access_research_summary(evidence=None):
    data = evidence if evidence is not None else load_access_dataset()
    return {"attractions_with_walk_estimates":len(data["by_attraction"]),
            "direction_observations":len(data["observations"]),
            "verified_2027_service_connections":0,
            "catalog_mutated":False}
