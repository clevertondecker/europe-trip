"""REC01: read-only, dynamically sized wishlist evidence matrix.

No ranking, scope inference, persistence, or changes to historical datasets.
"""
from __future__ import annotations

from importlib import import_module

from base_research_expanded_model import load_research
from rail_evidence_unified_model import canonical_place
from rail_reference_projection_model import decorate_comparison
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import selected_destinations_for_comparison


def candidate_ids(research: dict) -> list[str]:
    ids = [city["id"] for city in research["cities"]]
    if not ids or any(not isinstance(x, str) or canonical_place(x) != x for x in ids):
        raise ValueError("Universo de candidatas sem identificadores canônicos")
    if len(set(ids)) != len(ids):
        raise ValueError("Universo de candidatas duplicado")
    return ids


def _wishlist_matrix_builder():
    """Resolve the shared builder only when recommendations are requested.

    Streamlit can retain imported modules across source changes. If a worker
    still has an incompatible version, fail closed within the recommendations
    view rather than aborting the entire app. Do not reload a live module:
    concurrent Streamlit sessions may be using that module.
    """
    module = import_module("ux503_destination_base_comparison_model")
    builder = getattr(module, "build_wishlist_matrix", None)
    if not callable(builder):
        raise ImportError(
            "Versões incompatíveis dos módulos REC01/UX503. "
            "Reinicie o aplicativo para carregar o deploy atual."
        )
    return builder


def build_recommendation_matrix(interests: dict, destination_ids: list[str], *,
                                discovery=None, research=None, rail=None,
                                exploration=None, projection_options=None) -> dict:
    """Evaluate an explicitly chosen, nonempty scope across every valid base.

    Scope is a calculation input, never inferred from country or persisted.
    Keep raw historical rows distinct from the enriched presentation cells.
    """
    discovery = discovery if discovery is not None else build_exploration_discovery()
    research = research if research is not None else load_research(include_candidates=True)
    active = set(selected_destinations_for_comparison(interests, discovery))
    # The wishlist resolves historical aliases; an explicit scope must use
    # the exact active IDs of the current projection, not silently coerce input.
    if (not isinstance(destination_ids, list) or not destination_ids
            or any(not isinstance(x, str) or x not in active for x in destination_ids)
            or len(set(destination_ids)) != len(destination_ids)):
        raise ValueError("Selecione destinos ativos distintos para o escopo")
    comparison = _wishlist_matrix_builder()(
        interests, candidate_ids(research), discovery=discovery, research=research,
        rail=rail, exploration=exploration, visible_destination_ids=destination_ids)
    enriched = decorate_comparison(comparison, **(projection_options or {}))
    return {"comparison": comparison, "evidence": enriched,
            "read_only": True, "official_plan_modified": False}
