"""UX 4.2: single task selector for city-base research.

Presentation-only activity values. No changes to TripPlan or catalog.
"""
from __future__ import annotations

ACTIVITIES=("Explorar cidades","Comparar favoritas","Passeios e conexões")
LEGACY_ACTIVITIES={
    "Visão da cidade":ACTIVITIES[0],
    "Pesquisa ampliada":ACTIVITIES[0],
    "Explorar uma cidade":ACTIVITIES[0],
    "Todas as candidatas":ACTIVITIES[0],
    "Comparar cidades":ACTIVITIES[1],
    "Destinos próximos":ACTIVITIES[2],
    "Comparar mesmas viagens":ACTIVITIES[2],
    "Uma ou duas bases":ACTIVITIES[2],
}

def normalize_activity(value:str|None)->str:
    """Map obsolete labels to a visible activity without erasing legacy state."""
    if value in ACTIVITIES:
        return value
    return LEGACY_ACTIVITIES.get(value,ACTIVITIES[0])
