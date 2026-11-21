"""REC02 reproducible examples and measured scaling; no private data."""
from __future__ import annotations
import json
import sys
from time import perf_counter
import tracemalloc

from base_recommendation_model import evaluate_matrix, recommend_bases
from base_recommendation_evidence_model import build_recommendation_matrix
from recommendation_scope_model import confirm_scope
from rec01_feasibility import SCENARIOS, DATA23_SCENARIOS
from trip01_supplemental_discovery import build_exploration_discovery
from base_research_expanded_model import load_research
from base_explorer_model import load_exploration
from rail_evidence_unified_model import load_rail_evidence
from ux502_destination_interests_model import empty_interests, set_interest


def run_diagnostics():
    from copy import deepcopy
    started = perf_counter()
    discovery = build_exploration_discovery()
    research = load_research(include_candidates=True)
    rail, exploration = load_rail_evidence(), load_exploration()
    load_seconds = perf_counter() - started
    kwargs = dict(discovery=discovery,research=research,rail=rail,exploration=exploration)
    all_ids = sorted(d["id"] for d in discovery["destinations"])

    examples = {}
    product = [("paris","must_visit"),("colmar","must_visit"),
               ("strasbourg","interested"),("basel","interested"),
               ("lucerne","maybe"),("interlaken","must_visit")]
    for name, items in {**SCENARIOS,**DATA23_SCENARIOS,"product":product}.items():
        wishes = empty_interests()
        for d,p in items:
            wishes = set_interest(wishes,d,p,discovery)
        scope = confirm_scope(wishes,[d for d,_ in items],discovery)
        result = recommend_bases(wishes,scope,**kwargs)
        examples[name] = {
            "state":result["state"],
            "candidates":len(result["candidates"]),
            "full_groups":len(result["complete_groups"]),
            "conditional_pairs":len(result["conditional_comparisons"]),
            "highlights":[{k:c[k] for k in ("base_id","highlight_kind","reasons","weighted_coverage","must_visit")}
                          for c in result["candidates"] if c["highlight"]],
        }
    benchmark = {}
    for name,count in (("small",3),("medium",12),("all_real",len(all_ids)),("synthetic_200",200)):
        catalog = deepcopy(discovery)
        selected = all_ids[:count]
        if name == "synthetic_200":
            extra = ["rec02_synthetic_"+str(i) for i in range(max(0,count-len(all_ids)))]
            catalog["destinations"].extend({"id":x,"name":x,"country":"Synthetic"} for x in extra)
            selected = (all_ids+extra)[:count]
        wishes=empty_interests()
        for d in selected:
            wishes=set_interest(wishes,d,"interested",catalog)
        measurements=[]
        previous=None
        for _ in range(2):
            started=perf_counter()
            matrix=build_recommendation_matrix(wishes,selected,**{**kwargs,"discovery":catalog})
            matrix_seconds=perf_counter()-started
            tracemalloc.start()
            try:
                started=perf_counter()
                result=evaluate_matrix(matrix)
                engine_seconds=perf_counter()-started
                peak=tracemalloc.get_traced_memory()[1]/1024/1024
            finally:
                tracemalloc.stop()
            if previous is not None and previous != result:
                raise AssertionError("Non-deterministic recommendation")
            previous=result
            measurements.append({"matrix_seconds":round(matrix_seconds,4),
                                 "engine_seconds_with_tracing":round(engine_seconds,4),
                                 "engine_peak_mib_traced":round(peak,2)})
        benchmark[name]={"destinations":len(selected),"bases":len(research["cities"]),
                         "synthetic":name=="synthetic_200","measurements":measurements}
    return {"load_seconds":round(load_seconds,4),"examples":examples,"benchmark":benchmark}


if __name__ == "__main__":
    print(json.dumps(run_diagnostics(),ensure_ascii=False,indent=2))
