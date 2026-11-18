"""Evidence-limited trip-time scenarios. Two direction minima are NOT a return timetable."""
from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from rail_evidence_unified_model import canonical_place
from routes7_reference_model import load_route_references
from routes7_comparison_projection import decorate_comparison

DATA = Path(__file__).resolve().parent / "data/routes7_reverse_reference_pilot_2026_11.json"


def load_reverse_references(path=DATA):
    raw=json.loads(Path(path).read_text(encoding="utf-8"))
    if raw.get("schema_version")!=1 or raw.get("scope")!="reverse_direction_minimum_references_not_weekend_service":
        raise ValueError("invalid reverse reference schema")
    date.fromisoformat(raw["checked_at"])
    records={}
    for r in raw.get("records",[]):
        pair=(canonical_place(r["base_id"]),canonical_place(r["destination_id"]))
        if pair in records:
            raise ValueError("duplicate reverse reference")
        if (canonical_place(r["reverse_origin_id"])!=pair[1] or
            canonical_place(r["reverse_destination_id"])!=pair[0]):
            raise ValueError("reverse route not reciprocal")
        p=urlparse(r.get("source_url") or "")
        if p.scheme!="https" or not p.netloc or type(r.get("reverse_fastest_min")) is not int or r["reverse_fastest_min"]<=0:
            raise ValueError("reverse minimum requires published source")
        if any(r.get(k) is not None for k in ("weekend_frequency","train_transfer_count","roundtrip_fare_two_eur")):
            raise ValueError("weekend/fare/transfer gaps must remain unknown")
        if r.get("weekend_service_verified") is not False or r.get("exact_stations_verified") is not False:
            raise ValueError("undated route summary cannot prove dated service/stations")
        records[pair]=r
    return records


def planning_return_scenarios(comparison, *, reverse=None, references=None):
    """Only sum independently published lower bounds as a theoretical scenario.

    It is deliberately NOT an available round trip, itinerary or cost quote.
    """
    views=decorate_comparison(comparison,references=references)
    returns=reverse if reverse is not None else load_reverse_references()
    rows=[]
    for key,view in views["cells"].items():
        inbound=returns.get(key)
        outbound=view["fastest_min"] if view.get("fastest_min") is not None else view.get("legacy_min")
        reverse_min=inbound["reverse_fastest_min"] if inbound else None
        is_local=view["status"]=="local"
        rows.append({
            "base_id":key[0],"destination_id":key[1],
            "outbound_fastest_reference_min":outbound if not is_local else None,
            "reverse_fastest_reference_min":reverse_min,
            "two_direction_minimum_sum_min":outbound+reverse_min if
                (not is_local and outbound is not None and reverse_min is not None) else None,
            "sum_kind":"theoretical_lower_bound_not_schedulable" if
                (not is_local and outbound is not None and reverse_min is not None) else "unknown",
            "reverse_source_url":inbound["source_url"] if inbound else None,
            "weekend_return_verified":False,
            "weekend_frequency":"unknown",
            "transfers":"unknown",
            "couple_transport_cost_eur":None,
            "outing_feasible":None,
        })
    return {"rows":rows,"total_pairs":len(rows),
            "two_direction_lower_bounds":sum(r["two_direction_minimum_sum_min"] is not None for r in rows),
            "bookable_roundtrips":0,"ranking_available":False,
            "plan_mutated":False}
