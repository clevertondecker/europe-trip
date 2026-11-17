"""DQ3.1 — logistics-first, evidence-aware exploratory comparison.

The old documentary coverage and final decision gates remain unchanged.
This module never turns historical one-way trains into round trips, assumes
walking distances from centroids, or ranks cities with incomparable coverage.
"""
from __future__ import annotations

from copy import deepcopy
from math import isfinite

from base_coverage_model import coverage_matrix
from five_base_comparison_model import load_five_base_evidence
from rail_evidence_unified_model import load_rail_evidence, route_evidence, canonical_place
from base_explorer_model import load_exploration
from dq30_walking_access_model import load_walking_access

DEFAULT_WEIGHTS = {"logistics": 65, "living_cost": 30, "daily_practicality": 5}
LEVELS = ("triagem_exploratoria", "comparacao_fundamentada", "decisao_definitiva")
FALLBACK_BASKET = ("strasbourg", "colmar", "basel", "luxembourg_city",
                   "brussels", "bruges_be")


def validate_weights(weights: dict) -> dict:
    if not isinstance(weights, dict) or set(weights) != set(DEFAULT_WEIGHTS):
        raise ValueError("Pesos devem conter logística, custo e praticidade")
    if (any(type(v) not in (int, float) or not isfinite(v) or v < 0
            for v in weights.values()) or abs(sum(weights.values()) - 100) > 0.001):
        raise ValueError("Pesos devem ser não negativos e totalizar 100%")
    return dict(weights)


def select_common_basket(study: dict, *, selected_destinations=()) -> dict:
    """Keep the 15-place research basket; compare the SAME selected subset."""
    items = {d["id"]: d for d in study["common_destinations"]}
    selected = list(selected_destinations or ())
    if not selected:
        selected = [id for id in FALLBACK_BASKET if id in items]
        kind = "standard_exploratory_not_official"
    else:
        selected = list(dict.fromkeys(canonical_place(i) for i in selected))
        kind = "user_priority_candidates"
    if not selected or any(i not in items for i in selected):
        raise ValueError("Cesta contém destino fora dos 15 pesquisados")
    return {"ids": selected, "names": {i: items[i]["name"] for i in selected},
            "type": kind, "reference_basket_size": len(items),
            "same_basket_required": True}


def _exploration_reference(data, base_id, destination_id):
    for row in data["routes"]:
        if (canonical_place(row["base_id"]) == canonical_place(base_id)
                and canonical_place(row["destination_id"]) == destination_id
                and type(row["train_minutes_oneway_min"]) is int
                and row["train_minutes_oneway_min"] > 0
                and str(row.get("source_url", "")).startswith("https://")):
            return {"minutes": row["train_minutes_oneway_min"],
                    "source_url": row["source_url"],
                    "source_date": row.get("retrieved_at"),
                    "source_dataset": "exploration_bases_2027"}
    return None


def _known_access(destination_id, geo):
    # An official station -> attraction statement is useful as destination
    # context only; it does not confirm an end-to-end itinerary from any base.
    entries = [r for r in geo["walking_routes"]
               if r["destination_id"] in {
                   a["attraction_id"] for a in geo["attractions"]
                   if canonical_place(a["destination_id"]) == destination_id}
               and r["status"] in ("official_published",
                                    "operator_published_walk_duration",
                                    "pedestrian_routed")
               and r["duration_min"] is not None]
    return [{"attraction_id": r["destination_id"], "minutes": r["duration_min"],
             "distance_m": r["distance_m"], "status": r["status"],
             "source_url": r["source_url"], "scope": "station_to_one_attraction"}
            for r in entries]


def maturity_for_city(*, trains_known, basket_size, housing_observations,
                      daily_researched, final_ready=False):
    """Levels are evidence gates, not performance grades."""
    triage = bool(trains_known or housing_observations or daily_researched)
    founded = bool(basket_size and trains_known == basket_size
                   and housing_observations >= 3 and daily_researched)
    # All three final conditions must be true. Current source records cannot
    # certify real 2027 booking readiness.
    definitive = bool(founded and final_ready)
    return {
        "current": ("decisao_definitiva" if definitive else
                    "comparacao_fundamentada" if founded else
                    "triagem_exploratoria" if triage else
                    "pesquisa_inicial"),
        "triage_evidence": triage,
        "foundational_coverage_only": founded,
        "decision_verified_2027": definitive,
        "levels": LEVELS,
        "note": "Cobertura não valida retorno, tarifa completa ou reserva de 2027",
    }


def logistics_comparison(base_ids, *, selected_destinations=(), weights=None,
                         coverage=None, five=None, rail=None, exploration=None,
                         geography=None):
    """Return an honest same-basket matrix, with explicit missing values.

    Housing is a historical *sample* and no mixed-unit weighted score is
    generated. The weights express research priority, not an invented rating.
    """
    weights = validate_weights(weights or DEFAULT_WEIGHTS)
    five = five if five is not None else load_five_base_evidence()
    rail = rail if rail is not None else load_rail_evidence()
    exploration = exploration if exploration is not None else load_exploration()
    geography = geography if geography is not None else load_walking_access()
    coverage = coverage if coverage is not None else coverage_matrix("general")
    lookup = {x["id"]: x for x in coverage}
    ids = list(base_ids)
    if not ids or len(set(ids)) != len(ids) or any(i not in lookup for i in ids):
        raise ValueError("Cidades-base inválidas ou duplicadas")
    basket = select_common_basket(five, selected_destinations=selected_destinations)
    rows = []
    for base_id in ids:
        city = lookup[base_id]
        routes = []
        for destination_id in basket["ids"]:
            local = canonical_place(base_id) == destination_id
            evidence = route_evidence(rail, base_id, destination_id)
            minutes = (evidence.get("minimum_oneway_min")
                       if evidence["status"] == "historical_time" and not local else None)
            source = evidence.get("source_url") if minutes is not None else None
            src_date = evidence.get("source_date") if minutes is not None else None
            source_dataset = evidence.get("source_dataset") if minutes is not None else None
            if minutes is None and not local:
                extra = _exploration_reference(exploration, base_id, destination_id)
                if extra:
                    minutes, source, src_date, source_dataset = (
                        extra["minutes"], extra["source_url"],
                        extra["source_date"], extra["source_dataset"])
            routes.append({
                "destination_id": destination_id,
                "local": local,
                "oneway_train_min": minutes,
                "train_source_url": source,
                "train_source_date": src_date,
                "train_source_dataset": source_dataset,
                "return_train_min": None,
                "weekend_return_verified": False,
                "station_to_attraction_evidence": _known_access(destination_id, geography),
                "attraction_to_attraction_min": None,
                "complete_door_to_door_min": None,
                "full_two_person_transport_eur": None,
                "trip_status": ("local_access_unknown" if local else
                                "historical_oneway_partial" if minutes is not None
                                else "not_researched"),
            })
        timed = [r for r in routes if r["oneway_train_min"] is not None]
        housing = city["housing"]
        daily = city["criteria"]["daily_life_remote_work"]["documented_count"] > 0
        maturity = maturity_for_city(
            trains_known=len(timed), basket_size=len(routes),
            housing_observations=housing["count"], daily_researched=daily,
            final_ready=city["decision_ready"])
        missing = []
        if len(timed) < len(routes):
            missing.append("Tempos ferroviários comparáveis dos destinos faltantes")
        missing += ["Retornos e conexões nos dias de passeio",
                    "Última milha e percursos entre atrações",
                    "Custo total de deslocamento para duas pessoas"]
        if housing["count"] == 0:
            missing.append("Referências de aluguel mobiliado")
        if not daily:
            missing.append("Custo de vida e condições de trabalho remoto")
        rows.append({
            "id": base_id, "name": city["name"],
            "basket_ids": list(basket["ids"]),
            "routes": routes,
            "train_time_coverage": len(timed),
            "basket_size": len(routes),
            "complete_itineraries": 0,
            "housing_sample_count": housing["count"],
            "housing_historical_median_eur_month": housing["median_eur_month"],
            "daily_researched": daily,
            "documentary_weighted_percent": city["documentary_weighted_percent"],
            "maturity": maturity,
            "missing": missing,
            "quality_score_0_100": None,
            "confidence_note": "Sem comparação completa porta a porta; informações ausentes não equivalem a zero",
            "final_decision_ready": False,
        })
    return {"rows": deepcopy(rows), "basket": basket, "weights": weights,
            "quality_ranking_available": False,
            "scoring_reason": "Ainda não há logística completa e custos equivalentes por cidade-base",
            "official_plan_modified": False,
            "source_policy": "2026 historical / read-only / no assumed returns"}
