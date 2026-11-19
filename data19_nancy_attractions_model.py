"""DATA19 Nancy regional attraction candidates, without speculative journeys."""
import json
from pathlib import Path
from urllib.parse import urlsplit
DATA=Path(__file__).resolve().parent/"data"/"data19_nancy_attractions_2026_11.json"
def validate_data19(payload):
    if payload.get("schema_version")!=1 or payload.get("scope")!="DATA19_NANCY_RESEARCH_ONLY" or payload.get("base_id")!="nancy":
        raise ValueError("Invalid DATA19 scope")
    if payload.get("existing_canonical_nancy_count")!=6:raise ValueError("Canonical Nancy reconciliation")
    records=payload.get("attraction_candidates",[])
    if len(records)!=11 or len({x["id"] for x in records})!=11:raise ValueError("Missing or duplicate Nancy candidates")
    if sum(x["zone"]=="regional" for x in records)!=5:raise ValueError("Missing regional destinations")
    for r in records:
        u=urlsplit(r.get("source_url",""))
        p=r.get("photo") or {}
        if (not r["id"].startswith("data19_nancy_") or not r["name"] or not r["municipality"] or
            not r["description"] or not r["visit_tip"] or u.scheme!="https" or not u.hostname or
            not p.get("file_title") or not p.get("source_page","").startswith("https://commons.wikimedia.org/wiki/File:")
            or p.get("license_verified_for_reuse") is not False):
            raise ValueError("Missing verified source or identified Wikimedia image")
        if (any(r[k] is not None for k in ("rail_minutes","last_mile_minutes","door_to_door_minutes","ticket_eur"))
            or r["open_2027_verified"] is not False or r["return_2027_verified"] is not False or r["feasibility"]!="unknown"):
            raise ValueError("Unverified travel, opening, or fares")
    return {"total":len(records),"city":sum(r["zone"]=="cidade" for r in records),
            "metro":sum(r["zone"]=="metro" for r in records),
            "regional":sum(r["zone"]=="regional" for r in records)}
def load_data19(path=DATA):
    data=json.loads(Path(path).read_text(encoding="utf-8"))
    validate_data19(data)
    return data
