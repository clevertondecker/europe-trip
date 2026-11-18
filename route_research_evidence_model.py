"""Versioned read-only contracts for researched journey observations.

ARCH adapter is the sole authority for selecting a legacy display time.
This module validates *additional* research without changing that precedence.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from hashlib import sha256
from urllib.parse import urlparse
import json

from rail_evidence_unified_model import canonical_place
from rail_temporal_contract import normalize_service_instants

SCHEMA_VERSION = 1
SOURCE_NATURES = frozenset({
    "operator_date_specific_schedule", "operator_route_summary",
    "verified_secondary_reference", "manual_editorial_note",
})
EVIDENCE_STATES = frozenset({
    "timed_observation", "partial", "unknown", "conflict", "local_access_unknown",
})
TEMPORAL_VALIDITIES = frozenset({
    "historical_sample", "future_date_explicitly_verified",
    "validity_unknown", "not_applicable",
})


def _date(value, field, required=False):
    if value is None:
        if required:
            raise ValueError(f"{field}: data obrigatória")
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field}: data inválida")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field}: data inválida") from exc


def _time(value, field):
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field}: horário inválido")
    try:
        return datetime.strptime(value, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"{field}: usar HH:MM") from exc


def _https(value):
    parsed = urlparse(value or "")
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_observation(record: dict) -> dict:
    """Validate and normalize one observation; never silently fill missing evidence."""
    if not isinstance(record, dict) or record.get("schema_version") != SCHEMA_VERSION:
        raise ValueError("Versão da observação incompatível")
    row = deepcopy(record)
    for field, choices in (
        ("source_nature", SOURCE_NATURES),
        ("evidence_state", EVIDENCE_STATES),
        ("temporal_validity", TEMPORAL_VALIDITIES),
    ):
        if row.get(field) not in choices:
            raise ValueError(f"{field} desconhecido")
    for field in ("origin_id", "destination_id"):
        row[field] = canonical_place(row.get(field))
    is_local = row["origin_id"] == row["destination_id"]
    if is_local and row["evidence_state"] not in ("local_access_unknown", "unknown", "partial"):
        raise ValueError("Deslocamento local não é trem confirmado")
    if not is_local and row["evidence_state"] == "local_access_unknown":
        raise ValueError("Acesso local somente para mesmo destino")
    for field in ("origin_station_id", "destination_station_id", "service_id", "operator"):
        value = row.get(field)
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise ValueError(f"{field}: identidade inválida")
    checked = _date(row.get("checked_at"), "checked_at",
                    required=row["evidence_state"] not in ("unknown", "local_access_unknown"))
    travel = _date(row.get("travel_date"), "travel_date")
    _date(row.get("published_at"), "published_at")
    departure = _time(row.get("departure_local"), "departure_local")
    arrival = _time(row.get("arrival_local"), "arrival_local")
    # Historical clock-only records remain usable as source observations, but
    # never gain an invented offset or overnight arrival date.
    timing = normalize_service_instants(row)
    row["time_precision"] = timing["precision"]
    minutes = row.get("duration_min")
    if row["evidence_state"] == "timed_observation":
        if type(minutes) is not int or minutes <= 0:
            raise ValueError("Duração pesquisada deve ser inteiro positivo")
        if not _https(row.get("source_url")):
            raise ValueError("Tempo pesquisado exige URL HTTPS")
    elif minutes is not None:
        raise ValueError("Estado sem tempo não pode alegar duração")
    if row["source_nature"] == "manual_editorial_note" and row["evidence_state"] == "timed_observation":
        raise ValueError("Nota editorial não valida tempo de trem")
    if row["source_nature"] == "operator_date_specific_schedule":
        if not (travel and departure and arrival and row.get("origin_station_id")
                and row.get("destination_station_id")):
            raise ValueError("Horário específico exige data, partida, chegada e estações")
    if row["evidence_state"] in ("timed_observation", "partial", "conflict"):
        if not _https(row.get("source_url")):
            raise ValueError("Evidência pesquisada exige fonte HTTPS")
    if row["temporal_validity"] == "future_date_explicitly_verified":
        if (travel is None or travel.year < 2027 or
                row["source_nature"] != "operator_date_specific_schedule" or
                not _https(row.get("source_url")) or checked is None):
            raise ValueError("Validade futura requer observação do operador para a data")
    if row["temporal_validity"] == "historical_sample" and travel and travel.year >= 2027:
        raise ValueError("Amostra futura não é histórica")
    if row.get("transfers") is not None and (
        type(row["transfers"]) is not int or row["transfers"] < 0
    ):
        raise ValueError("Transferências precisam ser inteiras não negativas")
    for field in ("valid_from", "valid_until"):
        _date(row.get(field), field)
    if row.get("valid_from") and row.get("valid_until"):
        if row["valid_from"] > row["valid_until"]:
            raise ValueError("Janela de validade invertida")
    return row


def journey_identity(row: dict) -> tuple:
    """Directional service identity; unresearched properties remain None."""
    row = validate_observation(row)
    return (
        row["origin_id"], row["destination_id"],
        row.get("origin_station_id"), row.get("destination_station_id"),
        row.get("service_id"), row.get("travel_date"),
        row.get("departure_local"), row.get("departure_utc_offset"),
        row.get("operator") if not row.get("service_id") else None,
    )


def observation_id(row: dict) -> str:
    """Content-based identity including source to preserve independent observations."""
    row = validate_observation(row)
    keys = (
        "origin_id", "destination_id", "origin_station_id", "destination_station_id",
        "service_id", "operator", "travel_date", "arrival_date",
        "departure_local", "arrival_local", "departure_utc_offset",
        "arrival_utc_offset", "departure_at", "arrival_at",
        "source_url", "source_nature", "checked_at", "duration_min",
    )
    payload = json.dumps({k: row.get(k) for k in keys}, sort_keys=True,
                         ensure_ascii=False, separators=(",", ":"))
    return "rr1-" + sha256(payload.encode("utf-8")).hexdigest()[:24]


def validate_observations(records: list[dict]) -> dict:
    """Deduplicate identical records but keep conflicts and distinct source claims."""
    if not isinstance(records, list):
        raise ValueError("Observações devem ser uma lista")
    seen = set()
    unique = []
    groups = {}
    for raw in records:
        row = validate_observation(raw)
        key = observation_id(row)
        if key in seen:
            continue
        seen.add(key)
        row["observation_id"] = key
        unique.append(row)
        groups.setdefault(journey_identity(row), []).append(row)
    # Independent sources reporting the SAME service/timing corroborate it.
    # Source URL is provenance, never a reason for disagreement on its own.
    signature = lambda x: (
        x.get("duration_min"), x.get("arrival_local"), x.get("arrival_date"),
        x.get("arrival_utc_offset"), x.get("arrival_at"))
    conflicting = {
        str(key): [x["observation_id"] for x in group]
        for key, group in groups.items()
        if len({signature(x) for x in group}) > 1
    }
    corroborated = {
        str(key): [x["observation_id"] for x in group]
        for key, group in groups.items()
        if len(group) > 1 and len({signature(x) for x in group}) == 1
    }
    return {"schema_version": SCHEMA_VERSION, "observations": unique,
            "conflicts": conflicting, "corroborated": corroborated,
            "count": len(unique)}


def legacy_projection(base_id: str, destination_id: str, *, rail=None, exploration=None):
    """Read-only delegation; never changes existing display precedence or returns."""
    from evidence_query_model import get_rail_evidence
    return get_rail_evidence(base_id, destination_id,
                             rail=rail, exploration=exploration)
