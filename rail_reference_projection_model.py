"""Shared non-mutating projection of rail times for DQ3.2 and UX503.

A rechecked undated city-route minimum is *indicative*, not an itinerary.
Historical rail evidence retains the existing display precedence.
"""
from __future__ import annotations

from formatting import minutes

from routes7_reference_model import load_route_references, planning_reference
from functools import lru_cache
from copy import deepcopy
from rail_gap_enrichment_model import load_gap_enrichment
from data10_connectivity_model import load_connectivity_references
from data11_priority_connectivity_model import load_priority_connectivity
from data12_lille_connectivity_model import load_lille_connectivity
from data13_directed_connectivity_model import load_data13
from data22_supplemental_rail_model import load_data22
from data23_france_candidates_model import load_data23
from data25_priority_rail_model import load_data25
from data26c_priority_rail_model import load_data26c_rail


def format_minutes(value):
    return minutes(value, missing="não informado", allow_zero=False)


@lru_cache(maxsize=1)
def _cached_route_gaps():
    return load_gap_enrichment()

@lru_cache(maxsize=1)
def _cached_connectivity():
    return load_connectivity_references()


@lru_cache(maxsize=1)
def _cached_priority_connectivity():
    return load_priority_connectivity()


@lru_cache(maxsize=1)
def _cached_lille_connectivity():
    return load_lille_connectivity()


@lru_cache(maxsize=1)
def _cached_data13():
    return load_data13()


@lru_cache(maxsize=1)
def _cached_data22():
    return load_data22()


@lru_cache(maxsize=1)
def _cached_data23():
    return {(r['base_id'],r['destination_id']):r for r in load_data23()['routes']}


@lru_cache(maxsize=1)
def _cached_data25():
    return load_data25()


@lru_cache(maxsize=1)
def _cached_data26c():
    return load_data26c_rail()


def decorate_comparison(result, *, references=None, gap_overlay=None,
                        connectivity_overlay=None, priority_overlay=None,
                        lille_overlay=None, data13_overlay=None, supplemental_overlay=None,
                        candidate_overlay=None, data25_overlay=None, data26c_overlay=None):
    """All matrix categories are mutually exclusive, including custom baskets."""
    refs = references if references is not None else load_route_references()
    gaps = gap_overlay if gap_overlay is not None else _cached_route_gaps()
    connectivity = (connectivity_overlay if connectivity_overlay is not None
                    else _cached_connectivity())
    priority = (priority_overlay if priority_overlay is not None
                else _cached_priority_connectivity())
    lille = lille_overlay if lille_overlay is not None else _cached_lille_connectivity()
    data13 = data13_overlay if data13_overlay is not None else _cached_data13()
    supplemental = (supplemental_overlay if supplemental_overlay is not None
                    else _cached_data22())
    candidate = candidate_overlay if candidate_overlay is not None else _cached_data23()
    data25 = data25_overlay if data25_overlay is not None else _cached_data25()
    data26c = data26c_overlay if data26c_overlay is not None else _cached_data26c()
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
        from rail_evidence_unified_model import canonical_place
        source_key = tuple(canonical_place(part) for part in key)
        evidence = planning_reference(*source_key, references=refs, legacy=legacy)
        # Existing documented observations always win. A missing or unreproduced
        # time may use an independent, explicitly less certain DATA 9 reference.
        gap_row = gaps["by_pair"].get(key) or gaps["by_pair"].get(source_key)
        if (gap_row is not None and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis": "gap_reference",
                "display_min": gap_row["oneway_min"],
                "source_url": gap_row["source_url"],
                "reference_source_url": gap_row["source_url"],
                "gap_evidence_type": gap_row["evidence_type"],
                "gap_checked_at": gap_row["source_checked_at"],
                "gap_service_date": gap_row["service_date"],
                "confidence": gap_row["confidence"],
                "station_comparability": "city_level_ambiguous",
                "comparability": "indicative_only_not_station_comparable",
                "weekend_return_known": False,
                "valid_for_2027": False,
            }
        # DATA 10 is the last sourced fallback. Never overwrite older evidence
        # or claim the reverse journey, a future timetable or local transport.
        connectivity_row = connectivity["by_pair"].get(key) or connectivity["by_pair"].get(source_key)
        if (connectivity_row is not None
                and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis": "data10_reference",
                "display_min": connectivity_row["minimum_oneway_min"],
                "source_url": connectivity_row["source_url"],
                "reference_source_url": connectivity_row["source_url"],
                "gap_checked_at": connectivity_row["source_checked_at"],
                "confidence": connectivity_row["confidence"],
                "source_kind": connectivity_row["reference_kind"],
                "station_comparability": "city_level_ambiguous",
                "comparability": "indicative_only_not_station_comparable",
                "weekend_return_known": False,
                "valid_for_2027": False,
            }
        # DATA 11 extends researched coverage without overwriting historical,
        # ROUTES7, DATA 9 or DATA 10. Only source-level outbound minima are known.
        priority_row = priority["by_pair"].get(key) or priority["by_pair"].get(source_key)
        if (priority_row is not None
                and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis": "data11_reference",
                "display_min": priority_row["minimum_oneway_min"],
                "source_url": priority_row["source_url"],
                "reference_source_url": priority_row["source_url"],
                "gap_checked_at": priority_row["source_checked_at"],
                "confidence": priority_row["confidence"],
                "source_kind": priority_row["reference_kind"],
                "station_comparability": "city_level_ambiguous",
                "comparability": "indicative_only_not_station_comparable",
                "weekend_return_known": False,
                "valid_for_2027": False,
            }
        # DATA12 is the last-resort sourced Lille overlay, never a return route.
        lille_row = lille["by_pair"].get(key) or lille["by_pair"].get(source_key)
        if (lille_row is not None and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis": "data12_reference",
                "display_min": lille_row["minimum_oneway_min"],
                "source_url": lille_row["source_url"],
                "reference_source_url": lille_row["source_url"],
                "gap_checked_at": lille_row["source_checked_at"],
                "confidence": lille_row["confidence"],
                "source_kind": lille_row["reference_kind"],
                "station_comparability": "city_level_ambiguous",
                "comparability": "indicative_only_not_station_comparable",
                "weekend_return_known": False,
                "valid_for_2027": False,
            }
        data13_row = data13["by_pair"].get(key) or data13["by_pair"].get(source_key)
        if (data13_row is not None and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis": "data13_reference",
                "display_min": data13_row["minimum_oneway_min"],
                "source_url": data13_row["source_url"],
                "reference_source_url": data13_row["source_url"],
                "gap_checked_at": data13_row["source_checked_at"],
                "confidence": data13_row["confidence"],
                "source_kind": data13_row["reference_kind"],
                "arrival_station": (
                    "Interlaken Ost" if data13_row["source_url"].endswith("-to-interlaken-ost")
                    else "Basel SBB" if data13_row["source_url"].endswith("-to-basel-sbb")
                    else None
                ),
                "station_comparability": (
                    "station_named_in_route_page" if data13_row["source_url"].endswith(
                        ("-to-interlaken-ost", "-to-basel-sbb"))
                    else "city_level_ambiguous"
                ),
                "comparability": "indicative_only_not_station_comparable",
                "weekend_return_known": False,
                "valid_for_2027": False,
            }
        # DATA22 fills only still-missing routes to *supplemental* tourist
        # destinations. It does not alter canonical coverage or reverse trips.
        sup_row = supplemental["by_pair"].get(key) or supplemental["by_pair"].get(source_key)
        if (sup_row is not None and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis": "data22_supplemental_reference",
                "display_min": sup_row["minimum_oneway_min"],
                "source_url": sup_row["source_url"],
                "reference_source_url": sup_row["source_url"],
                "gap_checked_at": sup_row["source_checked_at"],
                "confidence": sup_row["confidence"],
                "source_kind": sup_row["reference_kind"],
                "station_comparability": "city_level_ambiguous",
                "comparability": "indicative_only_not_station_comparable",
                "weekend_return_known": False,
                "valid_for_2027": False,
                "evidence_notes": sup_row["notes"],
            }
        # Supplemental base-city sources apply only when older projections
        # have no time. A directional minimum is never a confirmed 2027 journey.
        city_row = candidate.get(key)
        if (city_row is not None and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis":"data23_candidate_reference",
                "display_min":city_row["minimum_oneway_min"],
                "source_url":city_row["source_url"],
                "reference_source_url":city_row["source_url"],
                "gap_checked_at":city_row["checked_at"],
                "confidence":city_row["confidence"],
                "source_kind":city_row["reference_kind"],
                "station_comparability":"city_level_ambiguous",
                "comparability":"indicative_only_not_station_comparable",
                "weekend_return_known":False,"valid_for_2027":False,
                "evidence_notes":city_row["notes"],
            }
        # DATA25 is strictly additive, after every existing evidence source.
        new_row = data25["by_pair"].get(key) or data25["by_pair"].get(source_key)
        if (new_row is not None and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            evidence = {
                **evidence,
                "display_basis": "data25_priority_reference",
                "display_min": new_row["oneway_min"],
                "source_url": new_row["source_url"],
                "reference_source_url": new_row["source_url"],
                "gap_checked_at": new_row["source_checked_at"],
                "confidence": new_row["confidence"],
                "source_kind": new_row["evidence_type"],
                "station_comparability": "city_level_ambiguous",
                "comparability": "indicative_only_not_station_comparable",
                "weekend_return_known": False,
                "valid_for_2027": False,
                "evidence_notes": new_row["note"],
            }
        # DATA26C fills remaining gaps after every existing evidence source.
        data26c_row = data26c["by_pair"].get(key) or data26c["by_pair"].get(source_key)
        if (data26c_row is not None and evidence.get("display_min") is None
                and row["evidence_status"] != "local"):
            quality_review = deepcopy(data26c_row.get("quality_review"))
            inconclusive = (quality_review or {}).get("modality_status") == "inconclusive"
            # Do not inherit ROUTES7 metadata: an unreproduced snapshot may
            # describe another observation, date, station or commercial offer.
            published_origin = data26c_row.get("published_origin_station")
            published_arrival = data26c_row.get("published_arrival_station")
            evidence = {
                "status": "modality_inconclusive" if inconclusive else "published_reference",
                "display_basis": "data26c_inconclusive" if inconclusive else "data26c_priority_reference",
                "display_min": None if inconclusive else data26c_row["oneway_min"],
                "fastest_min": None if inconclusive else data26c_row["oneway_min"],
                "average_min": None if inconclusive else data26c_row["published_average_min"],
                "legacy_min": None,
                "source_url": data26c_row["source_url"],
                "reference_source_url": data26c_row["source_url"],
                "checked_at": data26c_row["source_checked_at"],
                "gap_checked_at": data26c_row["source_checked_at"],
                "source_capture_date": data26c_row["source_capture_date"],
                "confidence": data26c_row["confidence"],
                "source_kind": data26c_row["evidence_type"],
                "published_origin_station": published_origin,
                "published_arrival_station": published_arrival,
                "origin_station_id": data26c_row["origin_station_id"],
                "destination_station_id": data26c_row["destination_station_id"],
                "station_status": data26c_row["station_status"],
                "station_comparability": "station_named_in_route_page" if (
                    published_origin or published_arrival) else "city_level_ambiguous",
                "comparability": "indicative_only_not_station_comparable",
                "fastest_provenance": "data26c_published_summary",
                "average_provenance": "data26c_published_summary",
                "reference_display_allowed": not inconclusive,
                "reference_differs_from_legacy": False,
                "conflict_with_legacy": False,
                "typical_time_known": False,
                "weekend_return_known": False,
                "valid_for_2027": False,
                "evidence_notes": data26c_row["note"],
                "data26c_quality_review": quality_review,
                "data26c_reviewed_observation": {
                    "minimum_min": data26c_row["oneway_min"],
                    "average_min": data26c_row["published_average_min"],
                    "source_url": data26c_row["source_url"],
                    "checked_at": data26c_row["source_checked_at"],
                    "confidence": data26c_row["confidence"],
                    "published_origin_station": published_origin,
                    "published_arrival_station": published_arrival,
                },
            }
        basis = evidence["display_basis"]
        if basis == "local_not_rail":
            category = "local"
            label = "Local — acesso a verificar"
        elif basis == "legacy_historical":
            category = "historical"
            label = f'{format_minutes(evidence["display_min"])} · histórico'
            if row.get("divergent_sources"):
                label += " · tempos publicados diferentes"
            if evidence.get("reference_differs_from_legacy"):
                label += " · outra referência indicativa"
        elif basis == "gap_reference":
            category = "reference_only"
            kind = evidence["gap_evidence_type"]
            qualifier = {
                "official_route_minimum": "mínimo publicado",
                "official_timetable_sample": "amostra datada de 2026",
                "secondary_sample": "referência secundária",
            }[kind]
            label = f'~{format_minutes(evidence["display_min"])} · {qualifier}'
        elif basis == "data10_reference":
            category = "reference_only"
            qualifier = ("mínimo publicado · operadora"
                         if evidence.get("source_kind") == "official_operator_minimum"
                         else "referência secundária · mínimo divulgado")
            label = f'~{format_minutes(evidence["display_min"])} · {qualifier}'
        elif basis == "data11_reference":
            category = "reference_only"
            qualifier = ("mínimo publicado · operadora"
                         if evidence.get("source_kind") == "official_operator_minimum"
                         else "referência secundária · mínimo divulgado")
            label = f'~{format_minutes(evidence["display_min"])} · {qualifier}'
        elif basis == "data12_reference":
            category = "reference_only"
            qualifier = ("mínimo publicado · operadora"
                         if evidence.get("source_kind") == "official_operator_minimum"
                         else "referência secundária · mínimo divulgado")
            label = f'~{format_minutes(evidence["display_min"])} · {qualifier}'
        elif basis == "data13_reference":
            category = "reference_only"
            qualifier = ("mínimo publicado · operadora"
                         if evidence.get("source_kind") == "official_operator_minimum"
                         else "referência secundária · mínimo divulgado")
            label = f'~{format_minutes(evidence["display_min"])} · {qualifier}'
        elif basis in ("data25_priority_reference", "data26c_priority_reference"):
            category = "reference_only"
            qualifier = ("referência secundária · mínimo divulgado"
                         if evidence.get("source_kind") == "secondary_sample"
                         else "mínimo publicado · operadora")
            label = f'~{format_minutes(evidence["display_min"])} · {qualifier}'
        elif basis == "data23_candidate_reference":
            category = "reference_only"
            label = f'~{format_minutes(evidence["display_min"])} · mínimo publicado · operadora'
        elif basis == "data22_supplemental_reference":
            category = "reference_only"
            qualifier = ("mínimo publicado · operadora"
                         if evidence["source_kind"] == "official_operator_minimum"
                         else "referência secundária · mínimo divulgado")
            label = f'~{format_minutes(evidence["display_min"])} · {qualifier}'
        elif basis == "indicative_published_city_minimum":
            category = "reference_only"
            label = f'~{format_minutes(evidence["display_min"])} · mínimo indicativo'
            if evidence.get("station_comparability") == "city_level_ambiguous":
                label += " · estação pendente"
        else:
            category = "no_time"
            label = "Tempo não pesquisado"
            if evidence["status"] == "modality_inconclusive":
                label = "Tempo ferroviário não comprovado · modalidade inconclusiva"
            elif evidence["status"] == "unreproduced_snapshot":
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
            "variation_status": row.get("variation_status", "conditions_unresolved" if row.get("divergent_sources") else "not_observed"),
            "contradiction_confirmed": False,
            "gap_applied": basis == "gap_reference",
            "connectivity_applied": basis == "data10_reference",
            "priority_connectivity_applied": basis == "data11_reference",
            "lille_connectivity_applied": basis == "data12_reference",
            "data13_connectivity_applied": basis == "data13_reference",
            "supplemental_connectivity_applied": basis == "data22_supplemental_reference",
            "candidate_connectivity_applied": basis == "data23_candidate_reference",
            "data25_connectivity_applied": basis == "data25_priority_reference",
            "data26c_connectivity_applied": basis == "data26c_priority_reference",
            "station_caveat": (
                ("Estação publicada: " + " → ".join(name for name in (
                    evidence.get("published_origin_station"), evidence.get("published_arrival_station")
                ) if name) + "; não reconciliada, sem serviço datado.")
                if basis == "data26c_priority_reference" and (evidence.get("published_origin_station")
                    or evidence.get("published_arrival_station"))
                else "Fonte refere-se à chegada na estação " + evidence["arrival_station"]
                + "; não confirma acesso a atrações fora da estação."
                if evidence.get("arrival_station")
                else ("Referência por cidade; estação de embarque/chegada não reconciliada."
                      if evidence.get("station_comparability") == "city_level_ambiguous"
                      else ("Estações citadas na fonte, sem serviço datado."
                            if evidence.get("station_comparability") == "station_named_in_route_page"
                            else None))),
        }
    if sum(categories.values()) != len(cells):
        raise AssertionError("comparative coverage overlaps")
    return {
        "cells": cells, "total": len(cells), **categories,
        "comparison_mutated": False, "automatic_base_ranking": False,
    }
