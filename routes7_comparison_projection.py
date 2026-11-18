"""Compatibility facade for historical ROUTES7 and UX503 imports.

The authoritative shared read-only rail presentation projection now lives in
rail_reference_projection_model.py. Keep this import path and prior exported
names stable for callers. No independent selection or display rules here.
"""
from rail_reference_projection_model import (
    format_minutes,
    _cached_route_gaps,
    decorate_comparison,
    load_route_references,
    planning_reference,
    load_gap_enrichment,
    lru_cache,
)
