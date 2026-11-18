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
                               *, attraction_window: dict | None = None,
                               last_mile_pair: dict | None = None) -> dict:
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
    if last_mile_pair is not None:
        if last_mile_pair.get("status") != "both_directions_documented":
            return {"status": "missing_access_evidence", "reason": "reverse_last_mile_unknown",
                    "outing_feasible": False, "valid_for_2027": False}
        forward = last_mile_pair["to_attraction"]
        reverse = last_mile_pair["to_station"]
        if (forward.get("station_id") != out["destination_station_id"] or
                reverse.get("station_id") != back["origin_station_id"] or
                forward.get("attraction_id") != reverse.get("attraction_id") or
                forward.get("direction") != "station_to_attraction" or
                reverse.get("direction") != "attraction_to_station"):
            return {"status": "incompatible", "reason": "bidirectional_station_or_attraction_mismatch",
                    "outing_feasible": False, "valid_for_2027": False}
        if any(x.get("state") != "verified_sample" or not _source(x.get("source_url")) or
               type(x.get("duration_min")) is not int or x["duration_min"] <= 0
               for x in (forward, reverse)):
            return {"status": "missing_access_evidence", "reason": "unverified_last_mile",
                    "outing_feasible": False, "valid_for_2027": False}
        to_minutes, back_minutes = forward["duration_min"], reverse["duration_min"]
    else:
        required = ("arrival_station_id", "return_station_id",
                    "access_to_min", "access_back_min", "access_source_url")
        if any(attraction_window.get(x) is None for x in required):
            return {"status": "missing_access_evidence", "reason": "incomplete_last_mile_or_opening",
                    "outing_feasible": False, "valid_for_2027": False}
        if (out["destination_station_id"] != attraction_window["arrival_station_id"] or
                back["origin_station_id"] != attraction_window["return_station_id"]):
            return {"status": "incompatible", "reason": "station_mismatch",
                    "outing_feasible": False, "valid_for_2027": False}
        if not _source(attraction_window["access_source_url"]):
            raise ValueError("Fonte de acesso ausente")
        to_minutes, back_minutes = (
            attraction_window["access_to_min"], attraction_window["access_back_min"])
    duration = attraction_window.get("visit_minutes")
    if any(type(x) is not int or x <= 0 for x in (to_minutes, back_minutes, duration)):
        return {"status": "missing_access_evidence", "reason": "unknown_access_or_visit_minutes",
                "outing_feasible": False, "valid_for_2027": False}
    arrival_at_door = arrive.astimezone(timezone.utc) + timedelta(minutes=to_minutes)
    departure_from_door = leave.astimezone(timezone.utc) - timedelta(minutes=back_minutes)
    if arrival_at_door + timedelta(minutes=duration) > departure_from_door:
        return {"status": "incompatible", "reason": "insufficient_visit_window",
                "outing_feasible": False, "valid_for_2027": False}
    if attraction_window.get("opening_schedule") is not None:
        from tourism_visit_evidence_model import evaluate_visit_window
        opening = evaluate_visit_window(
            attraction_window["opening_schedule"],
            earliest_start=arrival_at_door,
            latest_end=departure_from_door,
            duration_min=duration)
        if opening["status"] != "historical_window_compatible":
            return {"status": "incompatible", "reason": "opening_or_useful_time_conflict",
                    "opening_status": opening["status"],
                    "outing_feasible": False, "valid_for_2027": False}
        visit_start, visit_end = opening["start"], opening["end"]
    else:
        needs = ("opens_at", "closes_at", "opening_source_url")
        if any(attraction_window.get(x) is None for x in needs):
            return {"status": "missing_access_evidence", "reason": "opening_window_unknown",
                    "outing_feasible": False, "valid_for_2027": False}
        if not _source(attraction_window["opening_source_url"]):
            raise ValueError("Fonte de horário de atração ausente")
        opens, closes = _dt(attraction_window["opens_at"]), _dt(attraction_window["closes_at"])
        visit_start = max(arrival_at_door, opens.astimezone(timezone.utc))
        visit_end = visit_start + timedelta(minutes=duration)
        if visit_end > closes.astimezone(timezone.utc) or visit_end > departure_from_door:
            return {"status": "incompatible", "reason": "opening_or_useful_time_conflict",
                    "outing_feasible": False, "valid_for_2027": False}
    return {"status": "historical_schedule_coherent_only",
            "reason": "compatible_sample_not_future_guarantee",
            "outing_feasible": False, "valid_for_2027": False,
            "useful_minutes_on_sample": int((leave.astimezone(timezone.utc)-arrive.astimezone(timezone.utc)).total_seconds()//60),
            "start_of_visit": visit_start.isoformat(), "end_of_visit": visit_end.isoformat()}
