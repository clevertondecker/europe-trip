"""Read-only service-calendar coherence checks for weekend trip research.

A documented outbound and inbound alone NEVER confirms an outing.
"""
from __future__ import annotations

from datetime import datetime, date, timedelta, timezone
from urllib.parse import urlparse
from copy import deepcopy

from rail_evidence_unified_model import canonical_place
from rail_temporal_contract import normalize_service_instants
from rail_transfer_contract import normalize_transfers, validate_transfer_chain


def _dt(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("Data/hora local obrigatória")
    try:
        moment = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("Timestamp ISO inválido") from exc
    if moment.tzinfo is None or moment.utcoffset() is None:
        raise ValueError("Fuso UTC obrigatório para comprovar ordem de horários")
    return moment


def _source(value: str) -> bool:
    p = urlparse(value or "")
    return p.scheme == "https" and bool(p.netloc)


def validate_service_leg(leg: dict) -> dict:
    """Check a researched directed leg without inventing frequencies or dates."""
    if not isinstance(leg, dict):
        raise ValueError("Trecho inválido")
    required = ("origin_id", "destination_id", "origin_station_id",
                "destination_station_id")
    if any(not leg.get(key) for key in required) or not (
            leg.get("departure_at") or leg.get("departure_local")) or not (
            leg.get("arrival_at") or leg.get("arrival_local")):
        raise ValueError("Faltam identidades/horários do trecho")
    origin = canonical_place(leg["origin_id"])
    destination = canonical_place(leg["destination_id"])
    if origin == destination:
        raise ValueError("Deslocamento urbano não é trem intermunicipal")
    if not _source(leg.get("source_url")):
        raise ValueError("Trecho deve ter fonte HTTPS")
    # Prefer explicit departure_at/arrival_at with offsets. Legacy ISO fields
    # are accepted by the common adapter; HH:MM alone is not enough here.
    moments = normalize_service_instants(leg, require_offsets=True)
    departure, arrival = moments["departure"], moments["arrival"]
    departure_utc = departure.astimezone(timezone.utc)
    arrival_utc = arrival.astimezone(timezone.utc)
    verified_dates = leg.get("calendar_dates_verified") or []
    if not isinstance(verified_dates, list):
        raise ValueError("Calendário de serviço inválido")
    for item in verified_dates:
        date.fromisoformat(item)
    transfers = normalize_transfers(leg, require_details=True)
    validate_transfer_chain(
        transfers, departure=departure, arrival=arrival,
        origin_station_id=leg["origin_station_id"],
        destination_station_id=leg["destination_station_id"])
    result = deepcopy(leg)
    result["origin_id"] = origin
    result["destination_id"] = destination
    result["calendar_date_applicable"] = departure.date().isoformat() in verified_dates
    result["sample_weekend"] = departure.weekday() >= 5
    result["departure_at"] = departure.isoformat()
    result["arrival_at"] = arrival.isoformat()
    result["time_precision"] = moments["precision"]
    result.update(transfers)
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
    start, arrive = _dt(out["departure_at"]), _dt(out["arrival_at"])
    leave, finish = _dt(back["departure_at"]), _dt(back["arrival_at"])
    # Always compare absolute instants; DST changes and overnight services
    # legitimately have different local dates and UTC offsets.
    if not (start.astimezone(timezone.utc) < arrive.astimezone(timezone.utc) <
            leave.astimezone(timezone.utc) < finish.astimezone(timezone.utc)):
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
    arrival_attraction = arrive.astimezone(timezone.utc) + timedelta(minutes=values[0])
    visit_start = max(arrival_attraction, opens.astimezone(timezone.utc))
    visit_end = visit_start + timedelta(minutes=values[2])
    if not (visit_end <= closes.astimezone(timezone.utc) and
            visit_end + timedelta(minutes=values[1]) <= leave.astimezone(timezone.utc)):
        return {"status": "incompatible", "reason": "opening_or_useful_time_conflict",
                "outing_feasible": False, "valid_for_2027": False}
    return {"status": "historical_schedule_coherent_only",
            "reason": "compatible_sample_not_future_guarantee",
            "outing_feasible": False, "valid_for_2027": False,
            "useful_minutes_on_sample": int((leave.astimezone(timezone.utc)-arrive.astimezone(timezone.utc)).total_seconds()//60),
            "start_of_visit": visit_start.isoformat(), "end_of_visit": visit_end.isoformat()}
