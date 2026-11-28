"""Exploratory geographic comparison, separate from official base selection.

Never treats an unregistered candidate as a researched registered city.
"""
from __future__ import annotations

from copy import deepcopy

from base_research_expanded_model import load_research
from rail_evidence_unified_model import canonical_place, load_rail_evidence
from base_explorer_model import load_exploration
from evidence_query_model import get_rail_evidence
from ux501_destination_discovery_model import build_destination_discovery

# Discovery hypotheses, not catalog registration or user choices.
REFERENCE_BASES = ("mulhouse", "strasbourg", "lille")
REGISTERED_ALTERNATIVES = ("metz", "liege", "freiburg")
EXPLORATORY_CANDIDATES = (
    {"id": "maastricht", "name": "Maastricht", "country": "Países Baixos"},
    {"id": "basel", "name": "Basel", "country": "Suíça"},
    {"id": "amsterdam", "name": "Amsterdam", "country": "Países Baixos"},
)
PUBLIC_DEMONSTRATION_BASKET = ("aachen", "baden_baden", "cologne")


def geographic_screening(*, basket=None, research=None, discovery=None,
                         rail=None, exploration=None) -> dict:
    """Read-only, unbiased coverage for the *same* disclosed destinations."""
    research = research if research is not None else load_research()
    discovery = discovery if discovery is not None else build_destination_discovery()
    rail = rail if rail is not None else load_rail_evidence()
    exploration = exploration if exploration is not None else load_exploration()
    cities = {canonical_place(x["id"]): x for x in research["cities"]}
    destinations = {canonical_place(x["id"]): x for x in discovery["destinations"]}
    basket = tuple(PUBLIC_DEMONSTRATION_BASKET if basket is None else basket)
    normalized = [canonical_place(x) for x in basket]
    if not normalized or len(set(normalized)) != len(normalized):
        raise ValueError("Cesta fixa precisa de destinos únicos")
    if any(x not in destinations for x in normalized):
        raise ValueError("Destino não cadastrado para comparação")
    eligible = (*REFERENCE_BASES, *REGISTERED_ALTERNATIVES)
    if any(x not in cities for x in eligible):
        raise ValueError("Cidade de referência não está no cadastro")
    registered = []
    matrix = []
    for base_id in eligible:
        city = cities[base_id]
        status = []
        for destination_id in normalized:
            evidence = get_rail_evidence(
                base_id, destination_id, rail=rail, exploration=exploration)
            is_local = evidence["status"] == "local"
            state = (
                "registered_local_unknown" if is_local else
                "registered_with_historical_time"
                if evidence["minimum_oneway_min"] is not None else
                "registered_partially_researched"
                if evidence["status"] == "partial" else
                "registered_without_rail_evidence"
            )
            matrix.append({
                "base_id": base_id, "destination_id": destination_id,
                "registration_status": "registered",
                "research_status": state,
                "historical_oneway_station_minutes": evidence["minimum_oneway_min"],
                "source_url": evidence["source_url"],
                "checked_at": evidence["source_date"],
                "return_2027_verified": False,
                "journey_feasible": None,
            })
            status.append(state)
        registered.append({
            "id": base_id, "name": city["name"], "country": city["country"],
            "registration_status": "registered", "shortlist": bool(city["shortlist"]),
            "existing_historical_evidence_pairs": status.count("registered_with_historical_time"),
            "unresearched_pairs": status.count("registered_without_rail_evidence"),
            "basket_size": len(normalized), "decision_ready": False,
        })
    exploratory = []
    for candidate in EXPLORATORY_CANDIDATES:
        candidate_id = canonical_place(candidate["id"])
        if candidate_id in cities:
            raise ValueError(
                "Candidata exploratória agora cadastrada: revisar status explicitamente")
        exploratory.append({
            **deepcopy(candidate), "registration_status": "exploratory_not_registered",
            "research_status": "catalog_registration_pending",
            "comparability": "not_in_registered_rail_coverage_denominator",
            "decision_ready": False,
        })
    return {
        "schema_version": 1,
        "comparison_scope": "fixed_public_basket_read_only",
        "basket_ids": normalized,
        "registered_bases": registered,
        "exploratory_candidates": exploratory,
        "base_destination_matrix": matrix,
        "existing_pairs": len(matrix),
        "exploratory_pairs_in_coverage": 0,
        "ranking_available": False, "official_plan_modified": False,
        "wishlist_modified": False,
    }
