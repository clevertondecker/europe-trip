"""REC02: contextual investigation, not global ranking or travel feasibility."""
from __future__ import annotations
from collections import defaultdict
from copy import deepcopy
from itertools import combinations
from fractions import Fraction

from base_recommendation_evidence_model import build_recommendation_matrix
from recommendation_scope_model import reconcile_scope
from recommendation_metrics import DEFAULT_WEIGHTS, TIMED, CATEGORIES, weighted_coverage, ratio
from trip01_supplemental_discovery import build_exploration_discovery

POLICY_VERSION = "rec02-logistics-v1"
LIMITATION = ("Mínimos publicados de ida, evidências históricas/indicativas; "
              "retorno, última milha e horários de 2027 não confirmados.")
CRITERIA = {
    "complete": "Mesmo conjunto completo de trajetos e destinos locais; menor média ponderada de mínimos, empates incluídos.",
    "conditional": "Interseção explícita de trajetos conhecidos; sem extrapolar para toda a lista.",
    "investigation": "Fronteira de cobertura documental: outra base só supera se documenta todos os mesmos trajetos e locais e acrescenta evidência.",
}
def _weights(weights):
    result = dict(DEFAULT_WEIGHTS if weights is None else weights)
    if set(result) != set(DEFAULT_WEIGHTS) or any(type(v) is not int or v <= 0 for v in result.values()):
        raise ValueError("Pesos de prioridade inválidos")
    return result


def _fraction_view(n, d):
    return {"numerator": n, "denominator": d,
            "value": float(ratio(n, d)) if d else None}


def _mean(ids, cells, base, by_id, weights):
    n = sum(cells[(base, d)]["display_min"] * weights[by_id[d]["priority"]] for d in ids)
    d = sum(weights[by_id[x]["priority"]] for x in ids)
    return _fraction_view(n, d)


def _comparison(ids, bases, cells, by_id, weights, local_sets, full):
    ids = sorted(ids)
    measures = {b: _mean(ids, cells, b, by_id, weights) for b in bases}
    # Arithmetic exactness for ties, independently from displayed rounding.
    best = min(Fraction(x["numerator"], x["denominator"]) for x in measures.values())
    excluded = sorted(set(by_id) - set(ids))
    return {"kind": "complete" if full else "conditional",
            "base_ids": list(bases), "destination_ids": ids,
            "omitted_destination_ids": excluded,
            "omitted_by_base": {b: sorted(set(excluded) - local_sets[b]) for b in bases},
            "local_destination_ids_by_base": {b: sorted(local_sets[b]) for b in bases},
            "must_visit_omitted": [d for d in excluded if by_id[d]["priority"] == "must_visit"],
            "weighted_minimum_oneway": measures,
            "lowest_on_this_set": [b for b in bases if Fraction(measures[b]["numerator"], measures[b]["denominator"]) == best],
            "evidence_categories_by_base": {b: {d: cells[(b,d)]["category"] for d in ids} for b in bases},
            "mixed_evidence": len({cells[(b,d)]["category"] for b in bases for d in ids}) > 1,
            "total_logistics_decidable": False,
            "limitation": LIMITATION}


def evaluate_matrix(matrix, *, weights=None):
    """Pure REC01 consumer, also usable with the exact UX503 subset matrix.

    O(B*D + B²*D): one comparison per pair outside equal full-scope groups,
    not an exponential enumeration; IDs and denominators always explicit.
    """
    weights = _weights(weights)
    raw, evidence = matrix["comparison"], matrix["evidence"]
    bases = sorted(raw["base_ids"])
    destinations = sorted(raw["destinations"], key=lambda x: x["id"])
    by_id = {d["id"]: d for d in destinations}
    scope_ids = set(by_id)
    cells = evidence["cells"]
    if (not bases or len(set(bases)) != len(bases) or not destinations
            or len(by_id) != len(destinations)
            or any(d["priority"] not in weights for d in destinations)
            or set(cells) != {(b,d) for b in bases for d in by_id}):
        raise ValueError("Matriz de evidências incompleta ou inválida")
    names = {s["base_id"]: s["base_name"] for s in raw.get("summaries", [])}
    must = {d for d in by_id if by_id[d]["priority"] == "must_visit"}
    known, local, missing, candidates = {}, {}, {}, {}
    for b in bases:
        for d in by_id:
            c = cells[(b,d)]
            category, minutes = c["category"], c.get("display_min")
            if (category not in CATEGORIES or c.get("base_id") != b or c.get("destination_id") != d
                    or (category in TIMED and (type(minutes) is not int or minutes <= 0))
                    or (category not in TIMED and minutes is not None)):
                raise ValueError("Célula ferroviária inconsistente")
        known[b] = {d for d in by_id if cells[(b,d)]["category"] in TIMED}
        local[b] = {d for d in by_id if cells[(b,d)]["category"] == "local"}
        missing[b] = scope_ids - known[b] - local[b]
        n, denom = weighted_coverage(((by_id[d],cells[(b,d)]) for d in by_id), weights)
        min_counts = {str(t): sum(cells[(b,d)]["display_min"] <= t for d in known[b])
                      for t in (60,120,180)}
        candidates[b] = {"base_id": b, "base_name": names.get(b,b), "eligible": True,
                         "known_destination_ids": sorted(known[b]), "local_destination_ids": sorted(local[b]),
                         "missing_destination_ids": sorted(missing[b]),
                         "historical_count": sum(cells[(b,d)]["category"] == "historical" for d in by_id),
                         "indicative_count": sum(cells[(b,d)]["category"] == "reference_only" for d in by_id),
                         "weighted_coverage": _fraction_view(n,denom),
                         "must_visit": {"known": sorted(must & known[b]), "local": sorted(must & local[b]),
                                        "missing": sorted(must & missing[b])},
                         "minimum_oneway_within_minutes": min_counts,
                         "weighted_minimum_oneway": {**_mean(sorted(known[b]),cells,b,by_id,weights),
                                                     "destination_ids": sorted(known[b])},
                         "evidence": {d: deepcopy(cells[(b,d)]) for d in sorted(by_id)},
                         "local_only": bool(local[b]) and not known[b],
                         "reasons": [], "highlight": False}
    full_groups = defaultdict(list)
    minimum_common = 1 if len(by_id) == 1 else 2
    for b in bases:
        if not missing[b] and len(known[b]) >= minimum_common:
            full_groups[(tuple(sorted(known[b])), tuple(sorted(local[b])))].append(b)
    groups = []
    complete_members = set()
    full_pairs = set()
    for (ids,_), members in sorted(full_groups.items()):
        if len(members) < 2:
            continue
        g = _comparison(ids,members,cells,by_id,weights,local,True)
        groups.append(g)
        complete_members.update(members)
        full_pairs.update(combinations(members,2))
        for b in g["lowest_on_this_set"]:
            candidates[b]["highlight"] = True
            candidates[b]["reasons"].append("menor_minimo_ponderado_no_mesmo_escopo_completo")
    conditional = []
    conditional_members = set()
    for a,b in combinations(bases,2):
        if (a,b) in full_pairs:
            continue
        ids = known[a] & known[b]
        if len(ids) >= minimum_common:
            g = _comparison(ids,[a,b],cells,by_id,weights,local,False)
            conditional.append(g)
            conditional_members.update((a,b))
    # Coverage set inclusion, not cross-denominator comparison or a composite score.
    # Separate known and local to avoid treating access pending as a train duration.
    for b,c in candidates.items():
        if b in complete_members:
            c["group"] = "comparable"
        elif known[b] or local[b]:
            c["group"] = "conditional" if (b in conditional_members or not missing[b]) else "investigate"
        else:
            c["group"] = "investigate"
        c["comparable"] = b in complete_members or b in conditional_members
        if known[b] or local[b]:
            dominated = any(known[b] <= known[a] and local[b] <= local[a]
                            and (known[b] != known[a] or local[b] != local[a]) for a in bases if a != b)
            # Every non-dominated alternative remains a contextual research candidate.
            # No conditional time victory is promoted to an overall highlight.
            if b not in complete_members and not dominated:
                c["highlight"] = True
                c["reasons"].append("fronteira_documental_do_escopo")
            if not (must & missing[b]):
                c["reasons"].append("imperdiveis_identificados")
            else:
                c["reasons"].append("imperdiveis_com_evidencia_pendente")
            if c["local_only"]:
                c["reasons"].append("acesso_local_a_verificar")
            if not missing[b] and b not in complete_members:
                c["reasons"].append("alternativa_individual_sem_grupo_completo")
            if b in conditional_members:
                c["reasons"].append("comparacao_condicional_disponivel")
        else:
            c["reasons"].append("sem_tempo_ou_identificacao_local")
        if missing[b]:
            c["reasons"].append("destinos_com_tempo_pendente")
    # Separate global full-comparison status from useful conditional pair evidence.
    state = "comparable" if groups else ("partial_evidence" if any(known[b] or local[b] for b in bases)
                                          else "insufficient_evidence")
    return {"policy_version": POLICY_VERSION, "state": state,
            "criteria": deepcopy(CRITERIA), "weights": weights, "destinations": deepcopy(destinations),
            "candidates": list(candidates.values()), "complete_groups": groups,
            "conditional_comparisons": conditional,
            "highlight_ids": [b for b in bases if candidates[b]["highlight"]],
            "has_conditional_comparison": bool(conditional), "global_ranking": False,
            "official_plan_modified": False, "limitation": LIMITATION}


def recommend_bases(interests, scope=None, *, discovery=None, research=None, rail=None,
                    exploration=None, projection_options=None, weights=None, reset=False):
    """Entrypoint for REC03; failure is distinguishable from absent rail records.

    Invalid datasets/wishlist propagate exceptions; UI must present error. No
    result from previous scope can be silently substituted on failure.
    """
    discovery = discovery if discovery is not None else build_exploration_discovery()
    checked = reconcile_scope(interests, scope, discovery, reset=reset)
    if checked["state"] != "ready":
        return {"policy_version": POLICY_VERSION, "state": checked["state"],
                "scope": checked["scope"], "pending_ids": checked["pending_ids"],
                "candidates": [], "complete_groups": [], "conditional_comparisons": [],
                "highlight_ids": [], "global_ranking": False, "official_plan_modified": False}
    matrix = build_recommendation_matrix(interests, checked["scope"]["destination_ids"],
                                         discovery=discovery, research=research, rail=rail,
                                         exploration=exploration, projection_options=projection_options)
    return {**evaluate_matrix(matrix, weights=weights), "scope": checked["scope"], "pending_ids": []}
