"""Shared, read-only selection of exploratory home bases.

The hypothetical base is intentionally independent of TripPlan.base_city.
Never treat missing quotations as zero or market rent as a furnished short stay.
"""
from __future__ import annotations

from base_explorer_model import load_exploration


def base_options(data: dict | None = None) -> list[dict]:
    """One source for explored French bases; labels reflect evidence coverage."""
    source = data if data is not None else load_exploration()
    routes = source["routes"]
    output = []
    for item in source["bases"]:
        rows = [r for r in routes if r["base_id"] == item["id"]]
        with_time = sum(r["train_minutes_oneway_min"] is not None for r in rows)
        with_fare = sum(r["fare_from_eur_person_oneway"] is not None for r in rows)
        output.append({
            "id": item["id"], "name": item["name"], "country": item["country"],
            "official_supported": bool(item["official_base"]),
            "routes": len(rows), "time_coverage": with_time,
            "fare_coverage": with_fare,
            # These are research coverage labels, never booking readiness.
            "research_status": ("Rotas pesquisadas" if rows and
                                with_time == len(rows) and with_fare == len(rows)
                                else "Pesquisa parcial" if rows else "Sem rotas pesquisadas"),
        })
    return output


def choose_exploratory_base(candidate: str, options: list[dict]) -> str:
    """Validate selection without touching an official plan."""
    if candidate not in {item["id"] for item in options}:
        raise ValueError("Cidade-base exploratória inválida")
    return candidate


def hypothetical_city_name(base_id: str, options: list[dict]) -> str:
    return next(item["name"] for item in options if item["id"] == choose_exploratory_base(base_id, options))
