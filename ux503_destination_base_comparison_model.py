"""UX 5.0.3 — pure destination-led, evidence-first base comparison.

No ranking, schedule, fare estimate, route synthesis, or TripPlan mutation.
"""
from __future__ import annotations
from copy import deepcopy
from base_research_expanded_model import load_research, observed_housing
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import (
    empty_interests, ordered_interests, selected_destinations_for_comparison, LABELS,
)
from evidence_query_model import get_rail_evidence
from rail_evidence_unified_model import load_rail_evidence
from base_explorer_model import load_exploration
from rail_pair_projection_model import pair_projection_row
from destination_identity import canonical_destination_id

MISSING = ("Retorno de fim de semana não confirmado",
           "Acesso urbano e última milha a verificar")


def compare_wishlist_bases(interests: dict, base_ids: list[str], *,
                           discovery=None, research=None, rail=None, exploration=None,
                           visible_destination_ids=None) -> dict:
    """Manual comparison keeps its public two-to-five base contract."""
    if not isinstance(base_ids, list) or not 2 <= len(base_ids) <= 5:
        raise ValueError("Selecione de 2 a 5 cidades-base pesquisadas, sem duplicações")
    return build_wishlist_matrix(
        interests, base_ids, discovery=discovery, research=research, rail=rail,
        exploration=exploration, visible_destination_ids=visible_destination_ids)


def build_wishlist_matrix(interests: dict, base_ids: list[str], *,
                          discovery=None, research=None, rail=None, exploration=None,
                          visible_destination_ids=None) -> dict:
    """Read-only historical matrix for any nonempty distinct candidate set.

    The manual UI limit belongs to compare_wishlist_bases, not this projection.
    The default discovery remains legacy-compatible; callers provide an explicit
    exploratory catalog when evaluating supplemental destinations.
    """
    discovery = discovery if discovery is not None else build_destination_discovery()
    research = research if research is not None else load_research(include_candidates=True)
    _validated_bases(base_ids, research)
    from comparison_destinations_model import comparison_items, active_ids, PRIORITY_LABELS
    ordered = comparison_items(interests, discovery)
    active = active_ids(interests, discovery)
    if visible_destination_ids is not None:
        if (not isinstance(visible_destination_ids, (list, tuple)) or
                len(set(visible_destination_ids)) != len(visible_destination_ids) or
                any(x not in active for x in visible_destination_ids)):
            raise ValueError("Filtro visual contém destino inválido ou descartado")
        visible = set(visible_destination_ids)
    else:
        visible = set(active)
    priorities = {x["destination_id"]: x["priority"]
                  for x in ordered if x["destination_id"] in visible}
    result = build_destination_matrix(
        base_ids, list(priorities), discovery=discovery, research=research,
        rail=rail, exploration=exploration)
    for destination in result["destinations"]:
        priority = priorities[destination["id"]]
        destination.update(priority=priority, priority_label=PRIORITY_LABELS[priority])
    for row in result["rows"]:
        priority = priorities[row["destination_id"]]
        row.update(priority=priority, priority_label=PRIORITY_LABELS[priority])
    origins={x["destination_id"]:x.get("origin","Minha lista") for x in ordered}
    for row in result["destinations"]:
        row["origin"]=origins[row["id"]]
    result.update(discarded_count=len(ordered)-len(active),
                  active_destination_count=len(active))
    return result


def _validated_bases(base_ids, research):
    cities = {row["id"]: row for row in research["cities"]}
    if (not isinstance(base_ids, list) or not base_ids
            or any(not isinstance(x, str) or x not in cities for x in base_ids)
            or len(base_ids) != len(set(base_ids))):
        raise ValueError("Selecione cidades-base pesquisadas, sem duplicações")
    return cities


def build_destination_matrix(base_ids: list[str], destination_ids: list[str], *,
                             discovery=None, research=None, rail=None,
                             exploration=None) -> dict:
    """Read-only projection of explicit directed pairs, independent of wishes.

    Exact catalog IDs and input order are preserved. Empty destinations are
    valid. The caller owns any wishlist-specific priorities or UI limits.
    """
    discovery = discovery if discovery is not None else build_destination_discovery()
    research = research if research is not None else load_research(include_candidates=True)
    cities = _validated_bases(base_ids, research)
    names = {x["id"]: x for x in discovery["destinations"]}
    if (not isinstance(destination_ids, list)
            or any(not isinstance(x, str) or x not in names for x in destination_ids)
            or len({canonical_destination_id(x) for x in destination_ids}) != len(destination_ids)):
        raise ValueError("Selecione destinos do catálogo, sem duplicações")
    wanted = [
        {"id": key, "name": names[key]["name"], "country": names[key]["country"],
         "priority": None, "priority_label": None}
        for key in destination_ids
    ]
    rail = rail if rail is not None else load_rail_evidence()
    exploration = exploration if exploration is not None else load_exploration()
    rows = []
    summaries = []
    for base_id in base_ids:
        city = cities[base_id]
        documented = 0
        missing_time = 0
        local = 0
        conflicts = 0
        for destination in wanted:
            evidence = get_rail_evidence(
                base_id, destination["id"], rail=rail, exploration=exploration)
            observations = evidence["observations"]
            projection_row = pair_projection_row(base_id, destination["id"], evidence)
            divergent = projection_row["divergent_sources"]
            if evidence["status"] == "local":
                local += 1
                status = "Local — acesso a verificar"
            elif evidence["minimum_oneway_min"] is not None:
                documented += 1
                status = "Ida histórica documentada"
            else:
                missing_time += 1
                status = ("Pesquisa parcial — sem tempo" if observations else
                          "Sem evidência ferroviária catalogada")
            if divergent:
                conflicts += 1
            primary = next((r for r in observations if
                            r.get("source_url") == evidence["source_url"] and
                            r.get("minimum_oneway_min") == evidence["minimum_oneway_min"]), {})
            rows.append({
                "base_id":base_id,"base_name":city["name"],
                "destination_id":destination["id"],"destination_name":destination["name"],
                "priority":destination["priority"],"priority_label":destination["priority_label"],
                "status":status,"evidence_status":evidence["status"],
                "minimum_oneway_min":evidence["minimum_oneway_min"],
                "typical_oneway_min":evidence["typical_oneway_min"],
                "source_url":evidence["source_url"],"source_date":evidence["source_date"],
                "source_dataset":evidence["source_dataset"],
                "transfers":primary.get("transfers"),
                "return_weekend_verified":False,
                "local_access_verified":False,
                "observations":deepcopy(observations),"divergent_sources":divergent,
                "variation_status":projection_row["variation_status"],
                "contradiction_confirmed":False,
                "research_gaps":list(MISSING) if evidence["status"] != "local"
                                 else ["Acesso local, transporte urbano e última milha a verificar"],
            })
        housing = observed_housing(city)
        pending = []
        if missing_time:
            pending.append(f"Pesquisar tempos de ida para {missing_time} destino(s)")
        if local:
            pending.append(f"Verificar acesso urbano em {local} destino(s) locais")
        if conflicts:
            pending.append(f"Conferir condições de observações com tempos diferentes em {conflicts} rota(s)")
        pending += ["Confirmar retorno de fim de semana e última milha",
                    "Confirmar moradia mobiliada para as datas de 2027"]
        summaries.append({
            "base_id":base_id,"base_name":city["name"],
            "documented_time_count":documented,"missing_time_count":missing_time,
            "local_count":local,"divergent_route_count":conflicts,
            "destination_count":len(wanted),"housing":housing,
            "housing_comparable_for_2027":False,
            "documentary_coverage_only":True,
            "logistics_quality_decidable":False,
            "known_conditions":"Tempos históricos de ida, sem retorno ou última milha confirmados",
            "research_gaps":pending,
        })
    return {"destinations":deepcopy(wanted),"base_ids":list(base_ids),
            "rows":rows,"summaries":summaries,
            "discarded_count":0,
            "active_destination_count":len(wanted),
            "comparison_ready":bool(wanted),
            "quality_ranking_available":False,
            "official_plan_modified":False}
