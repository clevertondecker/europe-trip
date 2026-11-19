"""DATA 13 matrix coverage: report only displayable, sourced one-way minima.

Usage: python tools/audit_data13_coverage.py [--json]
The audit does not fetch network content or change datasets or TripPlan.
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dq32_macro_opportunities_model import opportunity_overview
from base_scenario_model import base_options

BASELINE_RESEARCHED = 227


def audit_coverage():
    rows = []
    origins = base_options()
    if not origins:
        raise AssertionError('No canonical bases found')
    destination_count = None
    for base in origins:
        v = opportunity_overview(base["id"])
        if destination_count is None:
            destination_count = v["registry_destinations"]
        assert v["registry_destinations"] == destination_count, "registry mismatch"
        data13_rows = [
            x for x in v["destinations"]
            if x.get("indicative_source_dataset") == "data13_directed_connectivity_2026_11"
        ]
        historical = v["rail_time_documented_count"]
        indicative = v["indicative_rail_reference_count"]
        local = len(v["local_destinations"])
        missing = v["unresearched_count"]
        assert historical + indicative + local + missing == destination_count
        assert local == 1
        rows.append({
            "base_id": base["id"], "base_name": base["name"],
            "historical": historical, "indicative": indicative,
            "new_data13_displayed": len(data13_rows),
            "unknown": missing, "local": local,
            "researched": historical + indicative,
            "coverage_pct": round(100*(historical+indicative)/(destination_count-local), 2),
        })
    assert len(rows) == len(origins)
    eligible_pairs = sum(destination_count - x['local'] for x in rows)
    target_researched = (eligible_pairs + 1) // 2
    researched = sum(x["researched"] for x in rows)
    new = sum(x["new_data13_displayed"] for x in rows)
    unknown = sum(x["unknown"] for x in rows)
    assert researched + unknown == eligible_pairs
    assert researched - new == BASELINE_RESEARCHED, (
        "Historical coverage changed unexpectedly; investigate precedence")
    return {
        "scope": "directed_pairs_oneway_2026_no_2027_guarantee",
        "base_count": len(rows),
        "destination_count": destination_count,
        "eligible_pairs": eligible_pairs,
        "historical_plus_indicative": researched,
        "new_displayed_data13": new,
        "previous_coverage": BASELINE_RESEARCHED,
        "unresearched": unknown,
        "coverage_pct": round(researched*100/eligible_pairs,2),
        "target_50pct": target_researched,
        "still_needed_for_50pct": max(0,target_researched-researched),
        "per_base": sorted(rows,key=lambda x:(-x["researched"],x["base_name"])),
        "coverage_is_not_accessibility_or_return_guarantee": True,
    }


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--json",action="store_true")
    args=parser.parse_args()
    report=audit_coverage()
    if args.json:
        print(json.dumps(report,ensure_ascii=False,indent=2))
    else:
        print("DATA13_COVERAGE_AUDIT="+json.dumps(report,ensure_ascii=False))
