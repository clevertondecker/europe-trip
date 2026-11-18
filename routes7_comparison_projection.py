"""UX 5.0.5: non-mutating, mutually-exclusive rail time distribution.

A rechecked undated city-route minimum is *indicative*, not an itinerary.
Historical rail evidence retains the existing display precedence.
"""
from __future__ import annotations

from routes7_reference_model import load_route_references, planning_reference


def format_minutes(value):
    if value is None:
        return "não informado"
    if type(value) is not int or value < 1:
        raise ValueError("duration invalid")
    return f"{value // 60}h{value % 60:02d}" if value >= 60 else f"{value} min"


def decorate_comparison(result, *, references=None):
    """All matrix categories are mutually exclusive, including custom baskets."""
    refs = references if references is not None else load_route_references()
    cells = {}
    categories = {
        "historical": 0, "reference_only": 0, "local": 0, "no_time": 0,
    }
    for row in result["rows"]:
        key = row["base_id"], row["destination_id"]
        if key in cells:
            raise ValueError("duplicate base-destination pair")
        legacy = {
            "status": row["evidence_status"],
            "minimum_oneway_min": row["minimum_oneway_min"],
            "source_url": row["source_url"],
        }
        evidence = planning_reference(*key, references=refs, legacy=legacy)
        basis = evidence["display_basis"]
        if basis == "local_not_rail":
            category = "local"
            label = "Local · acesso urbano pendente"
        elif basis == "legacy_historical":
            category = "historical"
            label = f'{format_minutes(evidence["display_min"])} · histórico'
            if row.get("divergent_sources"):
                label += " · divergência histórica"
            if evidence.get("reference_differs_from_legacy"):
                label += " · outra referência indicativa"
        elif basis == "indicative_published_city_minimum":
            category = "reference_only"
            label = f'~{format_minutes(evidence["display_min"])} · mínimo indicativo'
            if evidence.get("station_comparability") == "city_level_ambiguous":
                label += " · estação pendente"
        else:
            category = "no_time"
            label = "Tempo não estimado"
            if evidence["status"] == "unreproduced_snapshot":
                label += " · fonte original não reproduzida"
        categories[category] += 1

        if evidence.get("average_min") is not None:
            average_label = f'{format_minutes(evidence["average_min"])} · média publicada'
        elif evidence.get("rechecked_average_min") is not None and evidence.get(
                "average_provenance") == "disagrees_with_current_page":
            average_label = (
                f'{format_minutes(evidence["rechecked_average_min"])} · média reconsultada; '
                f'{format_minutes(evidence["original_snapshot_average_min"])} no snapshot')
        else:
            average_label = "Tempo médio não documentado"
        cells[key] = {
            **evidence, "base_id": key[0], "destination_id": key[1],
            "category": category, "label": label, "typical_label": average_label,
            "historical_source_url": row["source_url"],
            "legacy_divergent_sources": bool(row.get("divergent_sources")),
            "station_caveat": (
                "Referência por cidade; estação de embarque/chegada não reconciliada."
                if evidence.get("station_comparability") == "city_level_ambiguous"
                else ("Estações citadas na fonte, sem serviço datado."
                      if evidence.get("station_comparability") == "station_named_in_route_page"
                      else None)),
        }
    if sum(categories.values()) != len(cells):
        raise AssertionError("comparative coverage overlaps")
    return {
        "cells": cells, "total": len(cells), **categories,
        "comparison_mutated": False, "automatic_base_ranking": False,
    }
