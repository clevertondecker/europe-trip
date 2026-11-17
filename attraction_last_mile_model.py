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


def _valid_url(url):
    p = urlparse(url or "")
    return p.scheme == "https" and bool(p.netloc)


def validate_access_observation(row: dict, *, valid_attraction_ids: set | None = None):
    if not isinstance(row, dict):
        raise ValueError("Observação de acesso inválida")
    x = deepcopy(row)
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
    duration = x.get("duration_min")
    distance = x.get("distance_m")
    for value, field in ((duration, "duration_min"), (distance, "distance_m")):
        if value is not None and (type(value) is not int or value <= 0):
            raise ValueError(field + ": valor inválido ou não verificado")
    if duration is not None and (
        x["state"] != "verified_sample" or not x.get("arrival_station_id")
        or not x.get("entrance_id") or x["mode"] == "unknown"
        or not x.get("evidence_method")
    ):
        raise ValueError("Duração exige estação, entrada, modo, fonte e método")
    if x["state"] == "verified_sample" and duration is None:
        raise ValueError("Tempo da observação verificada ausente")
    if x.get("arrival_station_id") is None and duration is not None:
        raise ValueError("Não inferir estação principal")
    return x


def observation_identity(row: dict):
    return (
        row.get("arrival_station_id"), row["attraction_id"], row.get("entrance_id"),
        row.get("mode"), row.get("observed_for_date"), row.get("line_or_walk_id"),
        row.get("source_url"),
    )


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
    rows = [x for x in valid if x.get("arrival_station_id") == arrival_station_id
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
