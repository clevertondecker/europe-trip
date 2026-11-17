"""Read-only service-calendar coherence checks for weekend trip research.

A documented outbound and inbound alone NEVER confirms an outing.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta
from urllib.parse import urlparse
from copy import deepcopy

from rail_evidence_unified_model import canonical_place


def _dt(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Data/hora local obrigatória")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Timestamp ISO inválido") from exc


def _source(value: str) -> bool:
    p = urlparse(value or "")
    return p.scheme == "https" and bool(p.netloc)


def validate_service_leg(leg: dict) -> dict:
    """Check a researched directed leg without inventing frequencies or dates."""
    if not isinstance(leg, dict):
        raise ValueError("Trecho inválido")
    required = ("origin_id", "destination_id", "origin_station_id",
                "destination_station_id", "departure_local", "arrival_local")
    if any(not leg.get(key) for key in required):
        raise ValueError("Faltam identidades/horários do trecho")
    origin = canonical_place(leg["origin_id"])
    destination = canonical_place(leg["destination_id"])
    if origin == destination:
        raise ValueError("Deslocamento urbano não é trem intermunicipal")
    if not _source(leg.get("source_url")):
        raise ValueError("Trecho deve ter fonte HTTPS")
    departure = _dt(leg["departure_local"])
    arrival = _dt(leg["arrival_local"])
    if departure.tzinfo != arrival.tzinfo:
        raise ValueError("Fusos inconsistentes")
    if not departure < arrival:
        raise ValueError("Chegada precisa ocorrer após partida")
    verified_dates = leg.get("calendar_dates_verified") or []
    if not isinstance(verified_dates, list):
        raise ValueError("Calendário de serviço inválido")
    for item in verified_dates:
        date.fromisoformat(item)
    transfers = leg.get("transfers")
    if not isinstance(transfers, list):
        raise ValueError("Transferências exigem lista documentada")
    prev_arrival = departure
    last_station = leg["origin_station_id"]
    for transfer in transfers:
        if any(not transfer.get(k) for k in ("station_id", "arrival_local",
                                               "departure_local", "source_url")):
            raise ValueError("Transferência incompleta")
        if not _source(transfer["source_url"]):
            raise ValueError("Transferência sem fonte")
        a, b = _dt(transfer["arrival_local"]), _dt(transfer["departure_local"])
        if not prev_arrival <= a < b <= arrival:
            raise ValueError("Transferência fora da ordem temporal")
        if transfer["station_id"] in (None, "", last_station):
            raise ValueError("Estação de transferência inválida")
        prev_arrival, last_station = b, transfer["station_id"]
    result = deepcopy(leg)
    result["origin_id"] = origin
    result["destination_id"] = destination
    result["calendar_date_applicable"] = departure.date().isoformat() in verified_dates
    result["sample_weekend"] = departure.weekday() >= 5
    return result


def weekend_roundtrip_evidence(outbound: dict | None, inbound: dict | None,
                               *, attraction_window: dict | None = None) -> dict:
    """Report compatibility, never auto-grant 2027 feasibility.

    Required contextual evidence includes attraction opening/visit and compatible
    station-to-attraction and reverse access. Without it there is NO feasible claim.
    """
    if not outbound or not inbound:
        return {"status": "insufficient_evidence", "reason": "missing_outbound_or_return",
                "outing_feasible": False, "valid_for_2027": False}
    out = validate_service_leg(outbound)
    back = validate_service_leg(inbound)
    if out["origin_id"] != back["destination_id"] or out["destination_id"] != back["origin_id"]:
        return {"status": "incompatible", "reason": "reversed_city_pair_mismatch",
                "outing_feasible": False, "valid_for_2027": False}
    start, arrive = _dt(out["departure_local"]), _dt(out["arrival_local"])
    leave, finish = _dt(back["departure_local"]), _dt(back["arrival_local"])
    if not (start < arrive < leave < finish):
        return {"status": "incompatible", "reason": "schedule_order_inconsistent",
                "outing_feasible": False, "valid_for_2027": False}
    if not (out["calendar_date_applicable"] and back["calendar_date_applicable"]):
        return {"status": "partial_calendar", "reason": "service_dates_not_verified",
                "outing_feasible": False, "valid_for_2027": False}
    if not (out["sample_weekend"] and back["sample_weekend"]):
        return {"status": "not_weekend_sample", "reason": "sample_not_saturday_sunday",
                "outing_feasible": False, "valid_for_2027": False}
    if attraction_window is None:
        return {"status": "documented_legs_only", "reason": "missing_attraction_and_last_mile",
                "outing_feasible": False, "valid_for_2027": False}
    needs = ("arrival_station_id", "return_station_id", "access_to_min",
             "access_back_min", "visit_minutes", "opens_at", "closes_at",
             "access_source_url", "opening_source_url")
    if any(attraction_window.get(x) is None for x in needs):
        return {"status": "missing_access_evidence", "reason": "incomplete_last_mile_or_opening",
                "outing_feasible": False, "valid_for_2027": False}
    if (out["destination_station_id"] != attraction_window["arrival_station_id"] or
            back["origin_station_id"] != attraction_window["return_station_id"]):
        return {"status": "incompatible", "reason": "station_mismatch",
                "outing_feasible": False, "valid_for_2027": False}
    if not all(_source(attraction_window[x]) for x in ("access_source_url", "opening_source_url")):
        raise ValueError("Acesso/horário de atração sem fonte")
    values = [attraction_window[x] for x in ("access_to_min", "access_back_min", "visit_minutes")]
    if any(type(x) is not int or x <= 0 for x in values):
        raise ValueError("Duração de deslocamento/visita sem comprovação positiva")
    opens, closes = _dt(attraction_window["opens_at"]), _dt(attraction_window["closes_at"])
    visit_start = max(arrive + timedelta(minutes=values[0]), opens)
    visit_end = visit_start + timedelta(minutes=values[2])
    if not (visit_end <= closes and
            visit_end + timedelta(minutes=values[1]) <= leave):
        return {"status": "incompatible", "reason": "opening_or_useful_time_conflict",
                "outing_feasible": False, "valid_for_2027": False}
    return {"status": "historical_schedule_coherent_only",
            "reason": "compatible_sample_not_future_guarantee",
            "outing_feasible": False, "valid_for_2027": False,
            "useful_minutes_on_sample": int((leave-arrive).total_seconds()//60),
            "start_of_visit": visit_start.isoformat(), "end_of_visit": visit_end.isoformat()}
