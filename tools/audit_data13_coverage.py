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
ELIGIBLE_PAIRS = 1350
TARGET_RESEARCHED = 675


def audit_coverage():
    rows = []
    origins = base_options()
    for base in origins:
        v = opportunity_overview(base["id"])
        assert v["registry_destinations"] == 46, "registry mismatch"
        data13_rows = [
            x for x in v["destinations"]
            if x.get("indicative_source_dataset") == "data13_directed_connectivity_2026_11"
        ]
        historical = v["rail_time_documented_count"]
        indicative = v["indicative_rail_reference_count"]
        local = len(v["local_destinations"])
        missing = v["unresearched_count"]
        assert historical + indicative + local + missing == 46
        assert local == 1
        rows.append({
            "base_id": base["id"], "base_name": base["name"],
            "historical": historical, "indicative": indicative,
            "new_data13_displayed": len(data13_rows),
            "unknown": missing, "local": local,
            "researched": historical + indicative,
            "coverage_pct": round(100*(historical+indicative)/45, 2),
        })
    assert len(rows) == 30
    researched = sum(x["researched"] for x in rows)
    new = sum(x["new_data13_displayed"] for x in rows)
    unknown = sum(x["unknown"] for x in rows)
    assert researched + unknown == ELIGIBLE_PAIRS
    assert researched - new == BASELINE_RESEARCHED, (
        "Historical coverage changed unexpectedly; investigate precedence")
    return {
        "scope": "directed_pairs_oneway_2026_no_2027_guarantee",
        "base_count": len(rows),
        "destination_count": 46,
        "eligible_pairs": ELIGIBLE_PAIRS,
        "historical_plus_indicative": researched,
        "new_displayed_data13": new,
        "previous_coverage": BASELINE_RESEARCHED,
        "unresearched": unknown,
        "coverage_pct": round(researched*100/ELIGIBLE_PAIRS,2),
        "target_50pct": TARGET_RESEARCHED,
        "still_needed_for_50pct": max(0,TARGET_RESEARCHED-researched),
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
