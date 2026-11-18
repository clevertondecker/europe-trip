"""Compatibility facade for historical ROUTES7 and UX503 imports.

The authoritative shared read-only rail presentation projection now lives in
rail_reference_projection_model.py. Keep this import path stable for callers.
"""
from rail_reference_projection_model import (
    format_minutes,
    _cached_route_gaps,
    decorate_comparison,
)

__all__ = ("format_minutes", "decorate_comparison")
