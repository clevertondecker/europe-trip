"""DATA22: isolated sourced rail observations for supplemental tourist destinations.

Obernai and Lucerne are deliberately excluded from the frozen historical
30-base x 46-destination rail inventory. This overlay augments the UX
comparison only, after every historical/canonical reference source.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
import json

DATA=Path(__file__).resolve().parent/"data"/"data22_supplemental_rail_2026_11.json"
SOURCE_KINDS={
    "official_operator_minimum":("www.sncf-connect.com","medium"),
    "secondary_route_minimum":("www.thetrainline.com","low"),
}
SLUGS={
    "metz":"metz","strasbourg":"strasbourg","lille":"lille",
    "mulhouse":"mulhouse","nancy":"nancy","colmar":"colmar","basel":"bale",
    "obernai":"obernai","lucerne":"lucerne",
}

def _check_source(row):
    kind=row["reference_kind"]
    if kind not in SOURCE_KINDS:
        raise ValueError("Unsupported supplemental rail evidence tier")
    host,confidence=SOURCE_KINDS[kind]
    url=urlsplit(row["source_url"])
    if (url.scheme!="https" or url.hostname!=host or url.port is not None
            or url.query or url.fragment or url.username or url.password):
        raise ValueError("Invalid supplemental rail URL")
    start=SLUGS.get(row["origin_id"])
    end=SLUGS.get(row["destination_id"])
    if not start or not end:
        raise ValueError("Unknown supplemental rail endpoint")
    if kind=="official_operator_minimum":
        valid=url.path in (f"/train/trajet/{start}/{end}",
                           f"/train/horaires/{start}/{end}")
    else:
        valid=url.path in (
            f"/en/train-times/{start}-to-{end}",
            f"/train-times/{start}-to-{end}",
            f"/fr/horaires-train/{start}-a-{end}",
        )
    if not valid or row["confidence"]!=confidence:
        raise ValueError("Supplemental source direction/identity mismatch")


def validate_data22(payload, *,base_ids=None,allowed_destinations=None):
    if (not isinstance(payload,dict) or payload.get("schema_version")!=1
            or payload.get("scope")!="supplemental_destinations_directional_rail_reference_2026"):
        raise ValueError("DATA22 contract mismatch")
    if date.fromisoformat(payload["checked_at"]).year!=2026:
        raise ValueError("DATA22 research must be historical 2026")
    if base_ids is None:
        from base_research_expanded_model import load_research
        base_ids={x["id"] for x in load_research()["cities"]}
    if allowed_destinations is None:
        from ux62_supplemental_outings import supplemental_choices
        allowed_destinations={x["id"] for x in supplemental_choices()}
    bases=set(base_ids)
    destinations=set(allowed_destinations)
    seen={}
    for row in payload["records"]:
        if not isinstance(row,dict) or not {
            "origin_id","destination_id","minimum_oneway_min","reference_kind",
            "source_url","source_checked_at","confidence","direction",
            "return_2027_verified","valid_for_2027","door_to_door_verified",
            "station_comparability","notes","mode"
        }.issubset(row):
            raise ValueError("Incomplete supplemental rail observation")
        key=row["origin_id"],row["destination_id"]
        if (key in seen or row["origin_id"] not in bases
                or row["destination_id"] not in destinations
                or type(row["minimum_oneway_min"]) is not int
                or not 1<=row["minimum_oneway_min"]<=1440
                or date.fromisoformat(row["source_checked_at"]).year!=2026
                or row["direction"]!="outbound_only"
                or row["mode"]!="rail"
                or row["return_2027_verified"] is not False
                or row["valid_for_2027"] is not False
                or row["door_to_door_verified"] is not False
                or row["station_comparability"]!="city_level_ambiguous"
                or not isinstance(row["notes"],str) or not row["notes"].strip()):
            raise ValueError("Invalid supplemental rail evidence or duplicate")
        _check_source(row)
        seen[key]=row.copy()
    return {"by_pair":seen,"records":list(seen.values()),
            "dataset":"data22_supplemental_rail_2026_11"}


def load_data22(path=DATA,**kwargs):
    return validate_data22(json.loads(Path(path).read_text(encoding="utf-8")),**kwargs)
