"""Sourced regional discoveries are proposals, never wishlist/itinerary updates."""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
import json

from base_research_expanded_model import load_research
from ux501_destination_discovery_model import build_destination_discovery
from rail_evidence_unified_model import canonical_place

DATA = Path(__file__).resolve().parent / "data/regional_opportunities_pilot_2026_11.json"


def load_regional_opportunities(path=DATA, *, discovery=None, research=None):
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("schema_version") != 1 or not doc.get("fixed_reference_basket_untouched"):
        raise ValueError("Versão e cesta de referência incompatíveis")
    date.fromisoformat(doc["checked_at"])
    rows = doc.get("proposals", [])
    if not 3 <= len(rows) <= 5:
        raise ValueError("Piloto precisa de 3–5 oportunidades no total")
    if len({r["corridor"] for r in rows}) > 2:
        raise ValueError("Piloto tem mais de dois corredores")
    discovery = discovery if discovery is not None else build_destination_discovery()
    research = research if research is not None else load_research()
    current = {canonical_place(x["id"]) for x in discovery["destinations"]}
    bases = {canonical_place(x["id"]) for x in research["cities"]}
    seen = set()
    for row in rows:
        key = canonical_place(row["proposed_destination_id"])
        if key in current:
            raise ValueError("Proposta já existe no catálogo: " + key)
        if key in seen:
            raise ValueError("Proposta duplicada: " + key)
        seen.add(key)
        if not row.get("name") or not row.get("country") or not row.get("example_attraction"):
            raise ValueError("Oportunidade sem identidade ou motivação")
        if not row.get("relevant_registered_bases") or any(
            base not in bases for base in row["relevant_registered_bases"]):
            raise ValueError("Proposta vinculada a base não cadastrada")
        date.fromisoformat(row["checked_at"])
        link = urlparse(row.get("source_url") or "")
        if link.scheme != "https" or not link.netloc:
            raise ValueError("Proposta sem fonte HTTPS")
        if (row.get("historical_train_time_min") is not None or
                row.get("weekend_return_verified") is not False or
                row.get("last_mile_verified") is not False or
                row.get("rail_service_researched") is not False or
                row.get("seasonality_2027_verified") is not False):
            raise ValueError("Descoberta não comprova transporte ou validade 2027")
    return deepcopy(doc)


def opportunity_projection(*, discovery=None, research=None) -> dict:
    """Separate candidate catalog; does not read, write or expand personal interests."""
    data = load_regional_opportunities(discovery=discovery, research=research)
    return {
        "schema_version": 1,
        "regional_discovery_proposals": data["proposals"],
        "fixed_wishlist_reference": "external_read_only_not_accessed",
        "wishlist_mutated": False,
        "trip_plan_mutated": False,
        "comparison_basket_mutated": False,
        "viable_weekend_claims": 0,
    }
