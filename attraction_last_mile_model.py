"""Access evidence is keyed by actual arrival station, attraction entrance and mode.

No line-of-sight routing, inferred city-center station, or automatic summation.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from ux501_destination_discovery_model import build_destination_discovery

DATA = Path(__file__).resolve().parent / "data/attraction_access_research_pilot_2026_11.json"

MODES = frozenset({"walk", "tram", "bus", "metro", "taxi", "unknown"})
STATES = frozenset({"verified_sample", "partial", "unknown"})
DIRECTIONS = frozenset({"station_to_attraction", "attraction_to_station"})


def _valid_url(url):
    p = urlparse(url or "")
    return p.scheme == "https" and bool(p.netloc)


def validate_access_observation(row: dict, *, valid_attraction_ids: set | None = None):
    if not isinstance(row, dict):
        raise ValueError("Observação de acesso inválida")
    x = deepcopy(row)
    x.setdefault("direction", "station_to_attraction")
    if x["direction"] not in DIRECTIONS:
        raise ValueError("Direção de acesso inválida")
    if not x.get("attraction_id") or not x.get("destination_id"):
        raise ValueError("Acesso sem identidade de atração/destino")
    if valid_attraction_ids is not None and x["attraction_id"] not in valid_attraction_ids:
        raise ValueError("Atração não reconciliada no catálogo")
    if x.get("mode") not in MODES or x.get("state") not in STATES:
        raise ValueError("Estado/modo de acesso inválido")
    if not _valid_url(x.get("source_url")):
        raise ValueError("Acesso deve referenciar fonte HTTPS")
    date.fromisoformat(x["checked_at"])
    if x.get("observed_for_date") is not None:
        date.fromisoformat(x["observed_for_date"])
    for key in ("valid_from", "valid_until"):
        if x.get(key):
            date.fromisoformat(x[key])
    if x.get("valid_from") and x.get("valid_until"):
        if x["valid_from"] > x["valid_until"]:
            raise ValueError("Validade de acesso invertida")
    # Legacy arrival_station_id is only the forward station alias, never
    # a claim of which station a reverse transfer reaches.
    x["station_id"] = x.get("station_id") or (
        x.get("arrival_station_id")
        if x["direction"] == "station_to_attraction" else None)
    duration = x.get("duration_min")
    distance = x.get("distance_m")
    for value, field in ((duration, "duration_min"), (distance, "distance_m")):
        if value is not None and (type(value) is not int or value <= 0):
            raise ValueError(field + ": valor inválido ou não verificado")
    if duration is not None and (
        x["state"] != "verified_sample" or not x.get("station_id")
        or not x.get("entrance_id") or x["mode"] == "unknown"
        or not x.get("evidence_method")
    ):
        raise ValueError("Duração exige estação, entrada, modo, fonte e método")
    if x["state"] == "verified_sample" and duration is None:
        raise ValueError("Tempo da observação verificada ausente")
    if x["state"] == "verified_sample" and not (
            x.get("observed_for_date") or (
                x.get("valid_from") and x.get("valid_until"))):
        raise ValueError("Data efetiva da amostra não é checked_at")
    if x.get("station_id") is None and duration is not None:
        raise ValueError("Não inferir estação principal")
    return x


def observation_identity(row: dict):
    x = validate_access_observation(row)
    return (
        x["direction"], x.get("station_id"), x["attraction_id"],
        x.get("entrance_id"), x["mode"], x.get("line_or_walk_id"),
        x.get("observed_for_date"), x.get("valid_from"),
        x.get("valid_until"), x["source_url"], x["checked_at"])


def load_access_pilot(path=DATA, *, discovery=None):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema_version") != 1:
        raise ValueError("Versão do piloto inválida")
    discovery = discovery if discovery is not None else build_destination_discovery()
    by_id = {a["id"]: d["id"] for d in discovery["destinations"]
             for a in d["attractions"]}
    seen = {}
    observations = []
    for raw in doc.get("observations", []):
        row = validate_access_observation(raw, valid_attraction_ids=set(by_id))
        if row["destination_id"] != by_id[row["attraction_id"]]:
            raise ValueError("Atração e destino incompatíveis")
        key = observation_identity(row)
        if key in seen:
            if seen[key] != row:
                raise ValueError("Observações diferentes da mesma chave não podem se sobrescrever")
            continue
        seen[key] = row
        observations.append(row)
    return {"schema_version": 1, "observations": observations,
            "unreconciled_manual_notes": deepcopy(doc.get("unreconciled_manual_notes", []))}


def matching_access_options(records: list[dict], *, arrival_station_id: str,
                            attraction_id: str, entrance_id: str | None = None):
    """Do not reuse another station, entrance or train arrival silently."""
    valid = [validate_access_observation(x) for x in records]
    rows = [x for x in valid if x.get("station_id") == arrival_station_id
            and x.get("direction") == "station_to_attraction"
            and x["attraction_id"] == attraction_id
            and (entrance_id is None or x.get("entrance_id") == entrance_id)]
    return deepcopy(rows)


def station_to_attraction_duration(records: list[dict], *,
                                   arrival_station_id: str, attraction_id: str,
                                   entrance_id: str | None = None):
    """Only a *single* compatible verified observation; never add fragments."""
    rows = matching_access_options(
        records, arrival_station_id=arrival_station_id,
        attraction_id=attraction_id, entrance_id=entrance_id)
    confirmed = [x for x in rows if x["state"] == "verified_sample"
                 and x.get("duration_min") is not None]
    if len(confirmed) != 1:
        return {"duration_min": None, "status": "unknown_or_conflicting",
                "options": rows}
    return {"duration_min": confirmed[0]["duration_min"],
            "status": "historical_verified_sample_not_future_schedule",
            "source_url": confirmed[0]["source_url"], "options": rows}

def bidirectional_access(records: list[dict], *, attraction_id: str,
                         arrival_station_id: str, return_station_id: str,
                         arrival_entrance_id=None, departure_entrance_id=None,
                         arrival_date=None, return_date=None):
    """Find two independently sourced and dated access observations.

    Arrival and return station may differ. Never assume the trip back to a
    station has the same distance, travel time, opening or service calendar.
    """
    for d in (arrival_date, return_date):
        if d is not None:
            date.fromisoformat(d)
    result = {}
    for label, direction, station, entrance, trip_date in (
        ("to_attraction", "station_to_attraction", arrival_station_id,
         arrival_entrance_id, arrival_date),
        ("to_station", "attraction_to_station", return_station_id,
         departure_entrance_id, return_date),
    ):
        candidates = []
        for raw in records:
            item = validate_access_observation(raw)
            if (item.get("attraction_id") != attraction_id or
                    item["direction"] != direction or
                    item.get("station_id") != station or
                    (entrance is not None and item.get("entrance_id") != entrance) or
                    item["state"] != "verified_sample"):
                continue
            if trip_date and not (
                    item.get("observed_for_date") == trip_date or
                    (item.get("valid_from") and item.get("valid_until") and
                     item["valid_from"] <= trip_date <= item["valid_until"])):
                continue
            candidates.append(item)
        if len(candidates) != 1:
            return {"status": "missing_or_conflicting_access",
                    "missing_direction": direction,
                    "to_attraction": result.get("to_attraction"),
                    "to_station": None, "ready_for_2027": False}
        result[label] = candidates[0]
    if result["to_attraction"]["destination_id"] != result["to_station"]["destination_id"]:
        raise ValueError("Direções descrevem destinos incompatíveis")
    return {"status": "both_directions_documented", **result,
            "ready_for_2027": False}
