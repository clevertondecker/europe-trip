"""Export the next *unresearched* city→destination pairs, never fake times.

Example:
  python tools/data13_research_queue.py --limit 448 > /tmp/data13-next.csv

The queue is a worklist, not verified evidence. Progress is calculated
separately from the shared display projection and counts only sourced times.
"""
from __future__ import annotations
import argparse
import csv
import sys
from collections import deque
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from base_scenario_model import base_options
from dq32_macro_opportunities_model import opportunity_overview


def queue_candidates():
    """Round-robin city bases so research improves comparative fairness."""
    city_queues=[]
    for base in base_options():
        view=opportunity_overview(base["id"])
        unknown=[
            {"base_id":base["id"],"base_name":base["name"],
             "destination_id":x["destination_id"],
             "destination_name":x["name"],"destination_country":x["country"],
             "research_status":"missing_sourced_oneway_minimum",
             "operator_source_url":"","oneway_min":""}
            for x in view["unresearched_destinations"]
        ]
        unknown.sort(key=lambda x:(x["destination_country"],x["destination_name"]))
        city_queues.append((len(unknown),base["id"],deque(unknown)))
    city_queues.sort(key=lambda x:(-x[0],x[1]))
    pending=[q for _,_,q in city_queues]
    while pending:
        for queue in list(pending):
            if queue:
                yield queue.popleft()
            else:
                pending.remove(queue)


def make_queue(limit=None):
    full=list(queue_candidates())
    if len({(r["base_id"],r["destination_id"]) for r in full})!=len(full):
        raise AssertionError("duplicate candidate route")
    if limit is None:
        return full
    if limit<0:
        raise ValueError("limit must be nonnegative")
    return full[:limit]


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--limit",type=int,default=448)
    args=parser.parse_args()
    writer=csv.DictWriter(sys.stdout,fieldnames=(
        "base_id","base_name","destination_id","destination_name",
        "destination_country","research_status","operator_source_url",
        "oneway_min"))
    writer.writeheader()
    writer.writerows(make_queue(args.limit))
