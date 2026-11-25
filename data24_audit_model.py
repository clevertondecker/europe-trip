"""DATA24A offline, public-only audit. Never import Streamlit or TripPlan."""
from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from data24_coverage_model import rail_coverage, coverage_counts
from attractions_model import load_attractions
from base_explorer_model import load_exploration
from base_research_expanded_model import load_research
from base_coverage_model import coverage_matrix, coverage_summary
from data23_france_candidates_model import load_data23
from dq32_macro_opportunities_model import load_macro_tourism
from dq30_walking_access_model import load_walking_access
from dq31_logistics_evaluation_model import logistics_comparison
from five_base_comparison_model import load_five_base_evidence
from rail_evidence_unified_model import load_rail_evidence
from trip01_supplemental_discovery import build_exploration_discovery


def attributed_photo(photo):
    """Documented attribution, not a network check or an implied attraction photo."""
    return isinstance(photo, dict) and all(
        isinstance(photo.get(key), str) and bool(photo[key].strip())
        for key in ("url", "source_page", "author", "license", "license_url")
    ) and all(photo[key].startswith("https://")
              for key in ("url", "source_page", "license_url"))


def attraction_inventory(discovery, catalog, data23, macro, geography):
    """Respect the discovery reconciliation and enrich only the exact source IDs."""
    source_rows = {}
    for records in (catalog["attractions"], data23["attractions"], macro["attractions"]):
        for row in records:
            if row["id"] in source_rows:
                raise ValueError("Duplicate source attraction")
            source_rows[row["id"]] = row
    access = defaultdict(list)
    for row in geography["walking_routes"]:
        if (row["status"] in ("official_published", "operator_published_walk_duration",
                              "pedestrian_routed")
                and row.get("duration_min") is not None and row.get("source_url")):
            access[row["destination_id"]].append(deepcopy(row))
    rows, destinations, seen = [], [], set()
    for dest in discovery["destinations"]:
        attrs = dest["attractions"]
        if len(attrs) != dest["attraction_count"]:
            raise ValueError("Inconsistent attraction count")
        destinations.append({"id": dest["id"], "name": dest["name"],
                             "attractions": len(attrs),
                             "photo_attributed": attributed_photo(dest.get("photo")),
                             "photo": deepcopy(dest.get("photo")),
                             "sources": deepcopy(dest.get("sources", [])),
                             "source_url": dest.get("source_url")})
        for attr in attrs:
            ident = attr["id"]
            if ident in seen:
                raise ValueError("Duplicate projected attraction")
            seen.add(ident)
            raw = source_rows.get(ident, {})
            ticket = raw.get("ticket") or {}
            status = ticket.get("status", "unknown")
            if status == "operator_published" and (
                    ticket.get("amount") is None or not ticket.get("currency") or
                    not ticket.get("per")):
                raise ValueError("Published ticket lacks amount, currency or modality")
            if status not in ("operator_published", "not_applicable", "unknown"):
                raise ValueError("Unknown ticket status")
            # Destination photography is not an attraction photograph.
            photo = raw.get("photo")
            duration = raw.get("visit_minutes")
            description = raw.get("summary") or raw.get("description")
            rows.append({
                "id": ident, "destination_id": dest["id"], "name": attr["name"],
                "kind": attr["kind"], "source_url": attr["source_url"],
                "additional_sources": deepcopy(attr.get("additional_sources", [])),
                "reconciled_source_ids": deepcopy(attr.get("reconciled_source_ids", [])),
                "checked_at": raw.get("checked_at"),
                "description": description,
                "editorial_duration_min": duration if
                    raw.get("visit_minutes_status") == "editorial_assumption"
                    else raw.get("editorial_duration_min"),
                "ticket_status": status, "ticket": deepcopy(ticket),
                "photo_attributed": attributed_photo(photo), "photo": deepcopy(photo),
                "station_access": deepcopy(access.get(ident, [])),
            })
    counts = {
        "destinations": len(destinations),
        "destinations_with_attractions": sum(x["attractions"] > 0 for x in destinations),
        "destinations_with_attributed_photo": sum(x["photo_attributed"] for x in destinations),
        "attractions": len(rows),
        "described": sum(bool(x["description"]) for x in rows),
        "editorial_duration": sum(x["editorial_duration_min"] is not None for x in rows),
        "ticket_published": sum(x["ticket_status"] == "operator_published" for x in rows),
        "ticket_not_applicable": sum(x["ticket_status"] == "not_applicable" for x in rows),
        "ticket_unknown": sum(x["ticket_status"] == "unknown" for x in rows),
        "attraction_photo_attributed": sum(x["photo_attributed"] for x in rows),
        "station_access_documented": sum(bool(x["station_access"]) for x in rows),
        "reconciled_aliases": sum(len(x["reconciled_source_ids"]) for x in rows),
    }
    return {"counts": counts, "destinations": destinations, "rows": rows,
            "by_kind": dict(Counter(x["kind"] for x in rows))}


def pair_components(pair):
    """Independent documentary facts; no fabricated return, fare or total."""
    row, cell = pair["row"], pair["cell"]
    observations = row["observations"]
    fares = [deepcopy(x) for x in observations
             if x.get("fare_from_eur_person_oneway") is not None and x.get("source_url")]
    return {
        "category": cell["category"],
        "display_min": cell.get("display_min"),
        "display_basis": cell.get("display_basis"),
        "source_url": cell.get("reference_source_url") or cell.get("source_url") or row["source_url"],
        "historical_source_url": row["source_url"],
        "source_date": (cell.get("gap_checked_at") or cell.get("checked_at")
                        or row["source_date"]),
        "historical_source_date": row["source_date"],
        "historical_dataset": row["source_dataset"],
        "typical_min": row["typical_oneway_min"],
        "typical_label": cell.get("typical_label"),
        "transfers": row.get("transfers"),
        "fare_observations": fares,
        "observations": deepcopy(observations),
        "variation_status": cell["variation_status"],
        "contradiction_confirmed": cell["contradiction_confirmed"],
        "station_caveat": cell.get("station_caveat"),
        "return_2027_verified": False,
        "full_door_to_door_min": None,
    }


def build_audit():
    """Build once per CLI execution. Retain historic study separately from catalog scope."""
    discovery = build_exploration_discovery()
    research = load_research(include_candidates=True)
    catalog = load_attractions()
    macro = load_macro_tourism()
    data23 = load_data23()
    geography = load_walking_access()
    rail = load_rail_evidence()
    exploration = load_exploration()
    coverage = rail_coverage(research=research, discovery=discovery,
                             rail=rail, exploration=exploration)
    attractions = attraction_inventory(discovery, catalog, data23, macro, geography)
    pairs = [{"base_id": b, "destination_id": d, **pair_components(pair)}
             for (b, d), pair in sorted(coverage["pairs"].items())]
    by_destination = defaultdict(list)
    for pair in pairs:
        by_destination[pair["destination_id"]].append(pair["category"])
    historical = coverage_matrix("general")
    five = load_five_base_evidence()
    basket = [row["id"] for row in five["common_destinations"]]
    last_mile = logistics_comparison(
        [row["id"] for row in historical], selected_destinations=basket,
        coverage=historical, five=five, rail=rail, exploration=exploration,
        geography=geography)
    return {
        "schema_version": 1, "rail_counts": coverage["global"],
        "base_ids": coverage["base_ids"], "destination_ids": coverage["destination_ids"],
        "rail_by_base": coverage["by_base"],
        "rail_by_destination": {key: coverage_counts(by_destination[key])
                                for key in coverage["destination_ids"]},
        "rail_pairs": pairs, "attractions": attractions,
        "legacy_summary": coverage_summary(historical),
        "legacy_evidence": historical, "legacy_dq31": last_mile,
        "dq32_reconciled_aliases": deepcopy(discovery.get("reconciled_aliases", [])),
        "read_only": True, "official_plan_modified": False,
    }
