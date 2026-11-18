"""Shared, read-only temporal contract for rail observations and service legs.

Canonical instant fields are departure_at/arrival_at (ISO 8601 with explicit
UTC offsets). Historical HH:MM-only fields do NOT establish a usable instant.
A caller must never infer an overnight date or an offset from the city name.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def _parse_timestamp(value, field):
    if not isinstance(value, str):
        raise ValueError(f"{field}: timestamp obrigatório")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field}: ISO 8601 inválido") from exc
    return moment if moment.tzinfo is not None and moment.utcoffset() is not None else None


def _check_clock(raw, field):
    if not isinstance(raw, str):
        raise ValueError(f"{field}: hora local ausente")
    try:
        return datetime.strptime(raw, "%H:%M").time()
    except ValueError as exc:
        raise ValueError(f"{field}: esperado HH:MM") from exc


def _check_iana(moment, zone_name, field):
    if not zone_name:
        return
    try:
        zone = ZoneInfo(zone_name)
    except (ZoneInfoNotFoundError, KeyError, TypeError) as exc:
        raise ValueError(f"{field}: fuso IANA inválido") from exc
    # Round-trip through UTC catches DST gaps and incorrect offsets. A repeated
    # wall time is allowed if its explicitly supplied offset disambiguates it.
    local = moment.astimezone(timezone.utc).astimezone(zone)
    if (local.replace(tzinfo=None) != moment.replace(tzinfo=None)
            or local.utcoffset() != moment.utcoffset()):
        raise ValueError(f"{field}: offset incompatível com fuso e data")


def normalize_service_instants(row: dict, *, require_offsets: bool = False) -> dict:
    """Project an observed leg into two UTC-comparable aware datetimes.

    Supports:
    - departure_at/arrival_at: timezone-offset ISO timestamps (preferred).
    - older departure_local/arrival_local containing complete ISO timestamps.
    - travel_date + HH:MM clocks, arrival_date and explicit UTC offsets.
      With no offsets this returns local_clock_only rather than guessing.
    """
    if not isinstance(row, dict):
        raise ValueError("Trecho temporal inválido")
    departure = row.get("departure_at", row.get("departure_local"))
    arrival = row.get("arrival_at", row.get("arrival_local"))
    if departure is None or arrival is None:
        if require_offsets:
            raise ValueError("Instantes de ida/chegada ausentes")
        return {"precision": "unknown", "departure": None, "arrival": None}
    iso_mode = any("T" in x for x in (departure, arrival) if isinstance(x, str))
    if iso_mode:
        if any(not isinstance(x, str) or "T" not in x for x in (departure, arrival)):
            raise ValueError("Formatos de horário misturados")
        d, a = _parse_timestamp(departure, "departure_at"), _parse_timestamp(arrival, "arrival_at")
        if d is None or a is None:
            if require_offsets:
                raise ValueError("Instantes sem offset UTC explícito")
            return {"precision": "local_clock_only", "departure": None, "arrival": None}
    else:
        dep_clock = _check_clock(departure, "departure_local")
        arr_clock = _check_clock(arrival, "arrival_local")
        dep_date = row.get("travel_date")
        if not isinstance(dep_date, str):
            if require_offsets:
                raise ValueError("Data concreta de serviço ausente")
            return {"precision": "local_clock_only", "departure": None, "arrival": None}
        try:
            date.fromisoformat(dep_date)
            arr_date = row.get("arrival_date") or dep_date
            date.fromisoformat(arr_date)
        except ValueError as exc:
            raise ValueError("Data de partida/chegada inválida") from exc
        dep_offset = row.get("departure_utc_offset")
        arr_offset = row.get("arrival_utc_offset")
        if dep_offset is None or arr_offset is None:
            if require_offsets:
                raise ValueError("Offset UTC desconhecido em hora HH:MM histórica")
            return {"precision": "local_clock_only", "departure": None, "arrival": None}
        d = _parse_timestamp(f"{dep_date}T{departure}{dep_offset}", "departure_at")
        a = _parse_timestamp(f"{arr_date}T{arrival}{arr_offset}", "arrival_at")
        if d is None or a is None:
            raise ValueError("Offset UTC inválido")
    _check_iana(d, row.get("origin_timezone"), "departure_at")
    _check_iana(a, row.get("destination_timezone"), "arrival_at")
    if row.get("travel_date") and d.date().isoformat() != row["travel_date"]:
        raise ValueError("travel_date diferente da data local da partida")
    if row.get("arrival_date") and a.date().isoformat() != row["arrival_date"]:
        raise ValueError("arrival_date diferente da data local da chegada")
    if d.astimezone(timezone.utc) >= a.astimezone(timezone.utc):
        raise ValueError("Chegada não pode preceder partida no tempo real")
    return {"precision": "offset_aware", "departure": d, "arrival": a}
