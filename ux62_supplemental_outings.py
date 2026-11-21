"""Validated supplemental planning choices; never mutate the frozen rail catalog.

The supplemental dataset has sources but no verified ticket, duration or return.
Those unknowns must not be represented as zero-cost attractions or known journeys.
"""
from __future__ import annotations
from functools import lru_cache
from copy import deepcopy
import json
from trip01_supplemental_discovery import DATA, append_trip01_candidates


@lru_cache(maxsize=1)
def _entries():
    # Reuse the discovery validator: coordinates, URLs, unique IDs and licenses.
    append_trip01_candidates({"destinations": []})
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    return tuple(raw["destinations"])


def supplemental_choices():
    return [{
        "id": row["id"], "name": row["name"], "stage": "França",
        "attractions": [{"id": a["id"], "name": a["name"]}
                        for a in row["attractions"]],
        "research": "Fontes de pesquisa suplementar; tarifa e duração a verificar",
    } for row in _entries()]


def supplemental_attractions():
    """Typed unknown-cost rows for explicitly source-backed IDs only."""
    return [{
        "id": a["id"], "name": a["name"], "destination_id": d["id"],
        "summary": "Atração documentada; detalhes, ingresso e duração a confirmar.",
        "source_urls": [a["source_url"]],
        "ticket": {"status": "unknown", "amount": None, "currency": None,
                   "per": None, "validity": None, "notes": "Tarifa não pesquisada"},
        "visit_minutes": None,
        "visit_minutes_status": "unknown",
    } for d in _entries() for a in d["attractions"]]


def supplemental_destination(destination_id):
    return deepcopy(next((d for d in _entries() if d["id"] == destination_id), None))


def supplemental_allowed(destination_id):
    row = supplemental_destination(destination_id)
    if row is None:
        return None
    return {a["id"] for a in row["attractions"]}
