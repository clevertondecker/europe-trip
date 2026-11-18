"""ROUTES 7 audit trail for 15 public city-level rail research pairs.

Snapshots are immutable claims, not current 2027 schedules. The legacy
get_rail_evidence() controls historical display precedence.
"""
from __future__ import annotations

import csv
import json
from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from rail_evidence_unified_model import canonical_place
from evidence_query_model import get_rail_evidence

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data/routes7_priority_reference_2026_11.json"
SNAPSHOT = ROOT / "data/europa2027_pesquisa_15_pares_original.csv"
ALLOWED_SOURCE_DOMAINS = {
    "official_operator": {"sncf-connect.com", "www.sncf-connect.com"},
    "secondary_timetable_aggregator": {"thetrainline.com", "www.thetrainline.com"},
}
FASTEST_STATES = {"corroborated_city_level", "snapshot_only_unreproduced"}
AVERAGE_STATES = {
    "not_provided", "corroborated_city_level",
    "disagrees_with_current_page", "snapshot_only_unreproduced",
}


def _positive(value):
    return type(value) is int and value > 0


def _url_valid(url, kind):
    parsed = urlparse(url or "")
    return (parsed.scheme == "https" and
            parsed.hostname in ALLOWED_SOURCE_DOMAINS.get(kind, set()))


def _snapshot_rows(path=SNAPSHOT):
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    identities = [(canonical_place(x["base_id"]), canonical_place(x["destination_id"]))
                  for x in rows]
    if len(rows) != 15 or len(set(identities)) != len(rows):
        raise ValueError("original CSV contains duplicate or missing pairs")
    def int_or_none(v):
        return int(v) if v else None
    return {(canonical_place(x["base_id"]), canonical_place(x["destination_id"])): {
        "fastest_min": int_or_none(x["published_fastest_oneway_min"]),
        "average_min": int_or_none(x["published_average_oneway_min"]),
        "source_url": x["source_url"] or None, "source_kind": x["source_kind"],
    } for x in rows}


def load_route_references(path=DATA, *, snapshot_path=SNAPSHOT):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if data.get("schema_version") != 2 or data.get("scope") != (
            "planning_reference_with_audited_provenance"):
        raise ValueError("routes7 schema mismatch")
    if data.get("snapshot_file") != "data/europa2027_pesquisa_15_pares_original.csv":
        raise ValueError("missing immutable original snapshot")
    date.fromisoformat(data["checked_at"])
    date.fromisoformat(data["rechecked_at"])
    bases, destinations = data["bases"], data["destinations"]
    if (len(bases) != 3 or len(set(bases)) != 3 or
            len(destinations) != 5 or len(set(destinations)) != 5):
        raise ValueError("pilot basket identity changed")
    expected = {(canonical_place(b), canonical_place(d))
                for b in bases for d in destinations}
    snapshots = _snapshot_rows(snapshot_path)
    if set(snapshots) != expected:
        raise ValueError("original CSV is missing or has duplicate pairs")
    records = {}
    for row in data["records"]:
        key = canonical_place(row["origin_id"]), canonical_place(row["destination_id"])
        if key not in expected or key in records:
            raise ValueError("duplicated or unexpected research pair")
        original = row.get("original_snapshot")
        if not isinstance(original, dict) or any(
                original.get(k) != snapshots[key].get(k)
                for k in ("fastest_min", "average_min", "source_url")):
            raise ValueError("research value changed since original CSV")
        if row.get("fastest_min") != original.get("fastest_min") or (
                row.get("average_min") != original.get("average_min")):
            raise ValueError("historical research values must not be overwritten")
        date.fromisoformat(row["checked_at"])
        if row["checked_at"] > data["checked_at"]:
            raise ValueError("snapshot date mismatch")
        if any(row.get(key) is not None for key in ("fare_for_two_eur", "transfer_count")):
            raise ValueError("no verified fare or connections in this pilot")
        if row.get("weekend_return_status") != "unknown":
            raise ValueError("weekend return not proven")
        local = key[0] == key[1]
        if local:
            if (row["source_kind"] != "local" or row.get("time_scope") != "local"
                    or any(row.get(k) is not None for k in (
                        "fastest_min", "average_min", "source_url"))
                    or row.get("station_status") != "not_applicable"
                    or row.get("source_research_status") != "local"
                    or row.get("confidence") != "not_applicable"):
                raise ValueError("local access is not railway time")
        else:
            if (row["source_kind"] not in ALLOWED_SOURCE_DOMAINS or
                    row["source_kind"] != snapshots[key]["source_kind"] or
                    not _url_valid(row.get("source_url"), row["source_kind"]) or
                    row.get("time_scope") != "public_route_summary_not_date_specific" or
                    not _positive(row.get("fastest_min"))):
                raise ValueError("invalid operator/secondary source or duration")
            if row["average_min"] is not None and (
                    not _positive(row["average_min"]) or
                    row["average_min"] < row["fastest_min"]):
                raise ValueError("average lower than published fastest")
            if row.get("fastest_provenance") not in FASTEST_STATES or (
                    row.get("average_provenance") not in AVERAGE_STATES):
                raise ValueError("invalid field-level provenance")
            recheck = row.get("recheck")
            if recheck:
                if not _url_valid(recheck.get("source_url"), row["source_kind"]):
                    raise ValueError("recheck source type inconsistent")
                date.fromisoformat(recheck["checked_at"])
                if recheck["checked_at"] > data["rechecked_at"]:
                    raise ValueError("recheck date after dataset")
            if row["fastest_provenance"] == "corroborated_city_level":
                if not recheck or recheck.get("fastest_min") != row["fastest_min"]:
                    raise ValueError("claimed reproduced time not reproduced")
                if row.get("source_research_status") != "route_summary_rechecked":
                    raise ValueError("reproduced source must be marked rechecked")
                if row.get("confidence") != "low":
                    raise ValueError("reproduced city-level source is low confidence")
            elif (row.get("confidence") != "insufficient" or
                  row.get("source_research_status") != "snapshot_preserved_not_reproduced"):
                raise ValueError("unreproduced source cannot be marked researched")
            if row["average_provenance"] == "corroborated_city_level":
                if row["average_min"] is None or not recheck or (
                        recheck.get("average_min") != row["average_min"]):
                    raise ValueError("published average not reproduced")
            if row["average_provenance"] == "disagrees_with_current_page":
                if row["average_min"] is None or not recheck or (
                        recheck.get("average_min") in (None, row["average_min"])):
                    raise ValueError("average discrepancy has no recheck evidence")
            if (row.get("station_comparability") not in (
                    "city_level_ambiguous", "station_named_in_route_page") or
                    row.get("comparability") not in (
                    "indicative_only_not_station_comparable",
                    "city_level_reference_not_dated_service")):
                raise ValueError("unreconciled stations must not claim schedule")
            if (row["station_comparability"] == "city_level_ambiguous" and
                    row["comparability"] != "indicative_only_not_station_comparable"):
                raise ValueError("unknown stations cannot be declared comparable")
            if (row["station_comparability"] == "station_named_in_route_page" and
                    row["comparability"] != "city_level_reference_not_dated_service"):
                raise ValueError("named stations are not date-specific services")
            if row["station_comparability"] == "city_level_ambiguous":
                if (row.get("station_status") != "station_not_reconciled" or
                        row.get("origin_station_id") is not None or
                        row.get("destination_station_id") is not None):
                    raise ValueError("unreconciled stations must remain unknown")
            if row["station_comparability"] == "station_named_in_route_page":
                if (row.get("station_status") != "route_page_identified_stations" or
                        not row.get("origin_station_id") or
                        not row.get("destination_station_id")):
                    raise ValueError("named stations require source-consistent identities")
            if row.get("confidence") not in ("low", "insufficient"):
                raise ValueError("undated source cannot have high confidence")
        records[key] = deepcopy(row)
    if set(records) != expected or len(records) != 15:
        raise ValueError("incomplete pilot matrix")
    return {"by_pair": records, "records": list(records.values()),
            "bases": list(bases), "destinations": list(destinations),
            "checked_at": data["checked_at"]}


def planning_reference(base_id, destination_id, *, references=None, legacy=None):
    base_id, destination_id = canonical_place(base_id), canonical_place(destination_id)
    references = references if references is not None else load_route_references()
    old = legacy if legacy is not None else get_rail_evidence(base_id, destination_id)
    historical = old.get("minimum_oneway_min")
    row = references["by_pair"].get((base_id, destination_id))
    if old.get("status") == "local" or base_id == destination_id:
        return {"status": "local", "fastest_min": None, "average_min": None,
                "display_min": None, "display_basis": "local_not_rail",
                "source_url": None, "legacy_min": None,
                "weekend_return_known": False}
    result = {
        "status": "unknown", "fastest_min": None, "average_min": None,
        "display_min": historical, "legacy_min": historical,
        "display_basis": "legacy_historical" if historical is not None else "unknown",
        "source_url": old.get("source_url"), "historical_source_url": old.get("source_url"),
        "confidence": "unknown", "reference_differs_from_legacy": False,
        "conflict_with_legacy": False, "weekend_return_known": False,
        "typical_time_known": False, "station_comparability": "unknown",
        "comparability": "unknown", "reference_display_allowed": False,
    }
    if row is None:
        result["status"] = "legacy_only" if historical is not None else "unknown"
        return result
    corroborated = row.get("fastest_provenance") == "corroborated_city_level"
    shown = row["fastest_min"] if corroborated else None
    result.update({
        "status": "published_reference" if corroborated else "unreproduced_snapshot",
        "fastest_min": shown, "original_snapshot_fastest_min": row["fastest_min"],
        "average_min": row["average_min"] if row.get("average_provenance") == "corroborated_city_level" else None,
        "original_snapshot_average_min": row["average_min"],
        "rechecked_average_min": row["recheck"].get("average_min") if row.get("recheck") else None,
        "display_min": historical if historical is not None else shown,
        "display_basis": "legacy_historical" if historical is not None else (
            "indicative_published_city_minimum" if corroborated else "unknown"),
        "source_url": row.get("recheck", {}).get("source_url") if row.get("recheck") else row["source_url"],
        "reference_source_url": row["source_url"],
        "source_kind": row["source_kind"], "checked_at": row.get("recheck", {}).get("checked_at") if row.get("recheck") else row["checked_at"],
        "confidence": row["confidence"], "station_comparability": row["station_comparability"],
        "comparability": row["comparability"], "fastest_provenance": row["fastest_provenance"],
        "average_provenance": row["average_provenance"],
        "reference_display_allowed": corroborated,
        "reference_differs_from_legacy": historical is not None and shown is not None and historical != shown,
        "conflict_with_legacy": False,  # only same service/dates/stations can truly conflict
        "typical_time_known": row.get("average_provenance") == "corroborated_city_level",
    })
    return result
