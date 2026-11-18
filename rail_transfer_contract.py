"""Canonical transfers: count and station-specific connection details.

Old "transfers" can be an int (count only) or a list (documented connections).
A count alone does not prove a timed connection.
"""
from __future__ import annotations
from copy import deepcopy
from datetime import timezone
from urllib.parse import urlparse
from rail_temporal_contract import normalize_service_instants

def _https(url):
    p=urlparse(url or "")
    return p.scheme=="https" and bool(p.netloc)

def normalize_transfers(record: dict, *, require_details: bool=False) -> dict:
    if not isinstance(record, dict):
        raise ValueError("transfer record must be a mapping")
    legacy=record.get("transfers")
    count=record.get("transfer_count")
    legs=record.get("transfer_legs")
    if type(legacy) is int:
        if count is not None and count!=legacy:
            raise ValueError("legacy count conflicts with transfer_count")
        count=legacy
    elif isinstance(legacy,list):
        if legs is not None and legs!=legacy:
            raise ValueError("legacy legs conflict with transfer_legs")
        legs=legacy
    elif legacy is not None:
        raise ValueError("invalid legacy transfers")
    if legs is not None:
        if not isinstance(legs,list):
            raise ValueError("transfer_legs must be a list")
        if count is not None and count!=len(legs):
            raise ValueError("transfer count differs from detailed legs")
        count=len(legs)
    if count is not None and (type(count) is not int or count<0):
        raise ValueError("invalid transfer_count")
    if require_details and (count is None or (count>0 and legs is None)):
        raise ValueError("transfer count does not document the actual connections")
    legs=[] if legs is None else legs
    for leg in legs:
        if not isinstance(leg,dict) or not leg.get("station_id") or not _https(leg.get("source_url")):
            raise ValueError("invalid transfer identity or source")
        if require_details:
            timing=normalize_service_instants({
                "departure_at":leg.get("arrival_at",leg.get("arrival_local")),
                "arrival_at":leg.get("departure_at",leg.get("departure_local")),
                "origin_timezone":leg.get("timezone"),
                "destination_timezone":leg.get("timezone"),
            },require_offsets=True)
            if timing["precision"]!="offset_aware":
                raise ValueError("transfer lacks timed connection")
    return {"transfer_count":count,"transfer_legs":deepcopy(legs),
            "transfer_details_complete":count==0 or (
                 count is not None and len(legs)==count and bool(legs))}

def validate_transfer_chain(transfers, *, departure, arrival,
                            origin_station_id, destination_station_id):
    if departure.tzinfo is None or arrival.tzinfo is None:
        raise ValueError("transfer chain requires aware instants")
    if not transfers["transfer_details_complete"]:
        raise ValueError("missing connection details")
    last=departure.astimezone(timezone.utc)
    station_before=origin_station_id
    for leg in transfers["transfer_legs"]:
        t=normalize_service_instants({
            "departure_at":leg.get("arrival_at",leg.get("arrival_local")),
            "arrival_at":leg.get("departure_at",leg.get("departure_local")),
            "origin_timezone":leg.get("timezone"),
            "destination_timezone":leg.get("timezone"),
        },require_offsets=True)
        a=t["departure"].astimezone(timezone.utc)
        b=t["arrival"].astimezone(timezone.utc)
        station=leg["station_id"]
        if station in (station_before,destination_station_id):
            raise ValueError("transfer station mismatch")
        if not (last<=a<b<=arrival.astimezone(timezone.utc)):
            raise ValueError("transfer timing mismatch")
        last,station_before=b,station
    return True
