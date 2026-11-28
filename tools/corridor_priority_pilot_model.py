"""First corridor pilot: the same public basket for existing city bases.

Official operator route pages are research *references*, not dated 2027 trips.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from base_research_expanded_model import load_research
from rail_evidence_unified_model import load_rail_evidence
from evidence_query_model import get_rail_evidence
from base_explorer_model import load_exploration
from ux501_destination_discovery_model import build_destination_discovery

DATA = Path(__file__).resolve().parents[1] / "data/corridor_priority_pilot_2026_11.json"


def load_pilot(path=DATA, *, research=None, discovery=None):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("no_private_wishlist_read") is not True:
        raise ValueError("Escopo público/versão incompatíveis")
    date.fromisoformat(data["checked_at"])
    research = research if research is not None else load_research()
    discovery = discovery if discovery is not None else build_destination_discovery()
    bases = {x["id"] for x in research["cities"]}
    destinations = {x["id"] for x in discovery["destinations"]}
    if (not data.get("base_ids") or not data.get("public_fixed_basket") or
            len(set(data["base_ids"])) != len(data["base_ids"]) or
            len(set(data["public_fixed_basket"])) != len(data["public_fixed_basket"]) or
            any(x not in bases for x in data["base_ids"]) or
            any(x not in destinations for x in data["public_fixed_basket"])):
        raise ValueError("Cesta pública não estável ou IDs inválidos")
    seen = set()
    for row in data["route_page_references"]:
        pair = (row["origin_id"], row["destination_id"])
        if (pair in seen or pair[0] not in data["base_ids"] or
                pair[1] not in data["public_fixed_basket"]):
            raise ValueError("Par duplicado ou fora do piloto")
        seen.add(pair)
        p = urlparse(row["source_url"])
        if p.scheme != "https" or not p.netloc:
            raise ValueError("Referência sem URL HTTPS")
        if (row.get("historical_oneway_min") is not None or
                row.get("weekend_return_verified") is not False or
                row.get("applicable_2027") is not False):
            raise ValueError("Página de operador não comprova horário 2027")
    return deepcopy(data)


def pilot_matrix(*, research=None, discovery=None, rail=None, exploration=None):
    data = load_pilot(research=research, discovery=discovery)
    rail = rail if rail is not None else load_rail_evidence()
    exploration = exploration if exploration is not None else load_exploration()
    links = {(x["origin_id"], x["destination_id"]): x
             for x in data["route_page_references"]}
    out = []
    for base in data["base_ids"]:
        for destination in data["public_fixed_basket"]:
            known = get_rail_evidence(base, destination, rail=rail,
                                      exploration=exploration)
            supplemental = links.get((base, destination))
            status = (
                "historical_time" if known["minimum_oneway_min"] is not None else
                "operator_page_without_sourced_duration" if supplemental else
                "partial" if known["status"] == "partial" else
                "not_researched"
            )
            out.append({
                "base_id": base, "destination_id": destination,
                "status": status,
                "minimum_oneway_station_min": known["minimum_oneway_min"],
                "primary_source_url": known["source_url"],
                "historical_source_date": known["source_date"],
                "optional_operator_route_page": supplemental["source_url"] if supplemental else None,
                "return_weekend_2027_verified": False,
                "station_access_verified": False,
                "cost_for_two_2027": None,
                "missing": ["service_date_and_stations", "outbound_and_return",
                            "last_mile", "attraction_opening", "couple_cost"],
            })
    return {
        "schema_version": 1, "bases": data["base_ids"],
        "basket_ids": data["public_fixed_basket"], "matrix": out,
        "coverage_time_count": sum(x["minimum_oneway_station_min"] is not None for x in out),
        "operator_pages_sourced": len(links),
        "ranking_available": False, "private_wishlist_accessed": False,
        "trip_plan_modified": False,
    }
