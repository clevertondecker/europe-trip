"""Reproduce REC01 coverage using actual validated repository loaders.

Run from repository root: python rec01_feasibility.py
No claims about future timetable, costs, reachability or editorial verification.
"""
from __future__ import annotations

import json
from fractions import Fraction
from collections import Counter
from recommendation_metrics import weighted_coverage, ratio
from base_recommendation_evidence_model import build_recommendation_matrix, candidate_ids
from base_research_expanded_model import load_research
from base_explorer_model import load_exploration
from rail_evidence_unified_model import load_rail_evidence
from data23_france_candidates_model import load_data23
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import empty_interests, set_interest

I, Q, T = "must_visit", "interested", "maybe"
SCENARIOS = {
    "france": [("paris", I), ("strasbourg", I), ("colmar", Q), ("nancy", Q), ("metz", T)],
    "multi_country": [("paris", I), ("cologne", Q), ("brussels", Q), ("basel", I), ("lucerne", T)],
    "border": [("luxembourg_city", I), ("trier", Q), ("saarbrucken", T), ("metz", I)],
    "must_visit": [(d, I) for d in ("paris", "strasbourg", "brussels", "basel", "interlaken", "amsterdam")],
    "small": [("paris", I), ("colmar", Q), ("basel", T)],
    "large": [("paris", I), ("strasbourg", I), ("colmar", Q), ("brussels", Q),
              ("bruges_be", T), ("amsterdam", I), ("cologne", Q), ("aachen", T),
              ("luxembourg_city", Q), ("basel", I), ("lucerne", T), ("interlaken", Q)],
    "supplemental": [("obernai", I), ("lucerne", Q)],
}
DATA23_SCENARIOS = {
    "data23_a": [("angers", I), ("saumur", Q), ("rennes", I), ("saint_malo", Q)],
    "data23_b": [("annecy", I), ("dinan", Q), ("strasbourg", Q), ("paris", I)],
    "data23_mixed": [("saumur", I), ("saint_malo", Q), ("colmar", Q), ("paris", I), ("dinan", T)],
}
WEIGHTS = ((5, 3, 1), (10, 3, 1), (3, 2, 1))
THRESHOLDS = (60, 70, 80, 90, 100)


def coverage_report(matrix: dict) -> dict:
    comparison, enriched = matrix["comparison"], matrix["evidence"]
    cells = enriched["cells"]
    destinations = comparison["destinations"]
    bases = comparison["base_ids"]
    counts = Counter(c["category"] for c in cells.values())
    candidates = []
    gaps = Counter()
    must_gaps = Counter()
    for base in bases:
        selected = [(d, cells[(base, d["id"])]) for d in destinations]
        known = [(d, c) for d, c in selected if c["category"] in ("historical", "reference_only")]
        nonlocal_rows = [(d, c) for d, c in selected if c["category"] != "local"]
        must_covered = all(c["category"] != "no_time" for d, c in selected if d["priority"] == I)
        for d, c in selected:
            if c["category"] == "no_time":
                gaps[d["id"]] += 1
                if d["priority"] == I:
                    must_gaps[d["id"]] += 1
        fractions = []
        for weights in WEIGHTS:
            weight = dict(zip((I, Q, T), weights))
            numerator, denominator = weighted_coverage(selected, weight)
            fractions.append(ratio(numerator, denominator))
        candidates.append({
            "base_id": base, "known": len(known), "local": len(selected)-len(nonlocal_rows),
            "must_covered": must_covered, "fractions": fractions,
            "complete_without_local": len(known) == len(selected),
            "identified": len(known) + len(selected)-len(nonlocal_rows),
            "must_count": sum(d["priority"] == I for d, _ in selected),
            "must_identified": sum(d["priority"] == I and c["category"] != "no_time" for d, c in selected),
        })
    def eligible(index, threshold):
        return sum(c["must_covered"] and c["fractions"][index] is not None
                   and c["fractions"][index] >= Fraction(threshold, 100)
                   for c in candidates)
    with_time = sum(c["known"] > 0 for c in candidates)
    complete = [c["base_id"] for c in candidates if c["complete_without_local"]]
    # Strict common full-scope time group; descriptive only, not 2027 feasibility.
    comparable = len(complete) if len(complete) >= 2 else 0
    return {
        "coverage_by_base": [{
            "base_id": c["base_id"],
            "weighted_coverage_pct": (round(float(c["fractions"][0])*100, 2)
                                      if c["fractions"][0] is not None else None),
            "must_identified": c["must_identified"], "must_total": c["must_count"],
        } for c in candidates],
        "strict_complete_group_count": comparable,
        "partial_evidence_count": sum(c["identified"] > 0 for c in candidates)-comparable,
        "insufficient_evidence_count": sum(c["identified"] == 0 for c in candidates),
        "top_missing_destinations": sorted(gaps.items(), key=lambda x: (-x[1], x[0])),
        "must_missing_destinations": sorted(must_gaps.items(), key=lambda x: (-x[1], x[0])),
        "bases": len(bases), "destinations": len(destinations),
        "with_time": with_time, "without_time": len(bases)-with_time,
        "categories": {k: counts[k] for k in ("historical", "reference_only", "local", "no_time")},
        "thresholds": {str(t): eligible(0, t) for t in THRESHOLDS},
        "sensitivity_at_80": {"-".join(map(str, w)): eligible(i, 80) for i, w in enumerate(WEIGHTS)},
        "complete_without_local": [c["base_id"] for c in candidates if c["complete_without_local"]],
    }


def run_assessment() -> dict:
    research = load_research(include_candidates=True)
    discovery = build_exploration_discovery()
    rail, exploration = load_rail_evidence(), load_exploration()
    valid = {d["id"] for d in discovery["destinations"]}
    def evaluate(items):
        interests = empty_interests()
        for destination_id, priority in items:
            interests = set_interest(interests, destination_id, priority, discovery)
        return coverage_report(build_recommendation_matrix(
            interests, [d for d, _ in items], discovery=discovery, research=research,
            rail=rail, exploration=exploration))
    missing = sorted({r["destination_id"] for r in load_data23()["routes"]} - valid)
    active_scenarios = {**SCENARIOS, **DATA23_SCENARIOS}
    skipped = {name: sorted({d for d, _ in items}-valid)
               for name, items in active_scenarios.items()
               if any(d not in valid for d, _ in items)}
    return {
        "skipped_scenarios_missing_ids": skipped,
        "candidate_count": len(candidate_ids(research)),
        "selectable_destination_count": len(valid),
        "data23_missing_destination_ids": missing,
        "housing_cities_with_historical_offers": sum(bool(c["housing_offers"]) for c in research["cities"]),
        "housing_cities_with_eligible_2027_quotes": sum(c["eligible_2027_quotes"] > 0 for c in research["cities"]),
        "overall": evaluate([(d, Q) for d in sorted(valid)]),
        "scenarios": {name: evaluate(items) for name, items in active_scenarios.items()
                      if name not in skipped},
        "limitations": "Documentary outbound evidence only; not a ranking or verified return.",
    }


def run_benchmark() -> dict:
    """Report real and synthetic sizes separately; no private cache."""
    from time import perf_counter
    import tracemalloc
    from copy import deepcopy

    research = load_research(include_candidates=True)
    discovery = build_exploration_discovery()
    rail, exploration = load_rail_evidence(), load_exploration()
    ids = sorted(d["id"] for d in discovery["destinations"])
    results = {}
    for label, count in (("small", 3), ("medium", 12),
                         ("all_real", len(ids)), ("synthetic_200", 200)):
        catalog = deepcopy(discovery)
        selected = ids[:count]
        if label == "synthetic_200":
            extras = ["rec01_synthetic_"+str(i) for i in range(count-len(ids))]
            catalog["destinations"].extend({"id": d, "name": d, "country": "Synthetic"}
                                           for d in extras)
            selected = ids + extras
        wishes = empty_interests()
        for d in selected:
            wishes = set_interest(wishes, d, Q, catalog)
        timings, peaks = [], []
        prior = None
        for _ in range(2):
            tracemalloc.start()
            started = perf_counter()
            try:
                matrix = build_recommendation_matrix(wishes, selected, discovery=catalog,
                            research=research, rail=rail, exploration=exploration)
                timings.append(round(perf_counter()-started, 4))
                peaks.append(round(tracemalloc.get_traced_memory()[1]/1024/1024, 2))
            finally:
                tracemalloc.stop()
            signature = [(key, cell["category"], cell["display_min"])
                         for key, cell in matrix["evidence"]["cells"].items()]
            if prior is not None and signature != prior:
                raise AssertionError("Non-deterministic matrix projection")
            prior = signature
        results[label] = {"destinations": len(selected), "bases": len(research["cities"]),
                          "cells": len(prior), "seconds_with_tracing": timings,
                          "peak_mib_traced": peaks, "synthetic": label == "synthetic_200"}
    return results


if __name__ == "__main__":
    import sys
    output = run_benchmark() if "--benchmark" in sys.argv else run_assessment()
    print(json.dumps(output, ensure_ascii=False, indent=2))
