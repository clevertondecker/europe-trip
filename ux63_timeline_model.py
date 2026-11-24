"""Shared read-only temporal projection: individual dates never derive from groups."""
from __future__ import annotations
from itinerary_flow_model import selected_rows, UNASSIGNED, FRANCE_STAGE
from ux48_weekend_groups_model import PERIODS, _trip_days


def project_timeline(plan, catalog, weekend_groups=None, stage=None):
    rows = selected_rows(plan, catalog)
    groups = (weekend_groups.get("groups", []) if isinstance(weekend_groups, dict)
              and weekend_groups.get("plan_id", plan["plan_id"]) == plan["plan_id"] else [])
    associated = {}
    for group in groups:
        for index, dest in enumerate(group.get("destinations", []), 1):
            associated[dest] = (group, index)
    result = []
    for row in rows:
        if stage is not None and row["stage"] != stage:
            continue
        group, sequence = (associated.get(row["id"], (None, None))
                           if row["stage"] == FRANCE_STAGE else (None, None))
        exact = list(row["exact_dates"])
        period = row["period"] if row["period"] != UNASSIGNED else None
        group_period = None
        group_dates = []
        if group:
            if group.get("period") in PERIODS and group["period"] not in (UNASSIGNED, "A definir"):
                group_period = group["period"]
            if group.get("start_date"):
                group_dates = _trip_days(group["start_date"], group.get("nights", 0))
        organized = bool(period or exact or group_period or group_dates)
        status = ("Data individual definida" if exact else
                  "Viagem com intervalo definido · dia individual pendente" if group_dates else
                  "Período definido · data pendente" if period or group_period else
                  "Em grupo · período/data pendentes" if group else "Sem período ou data")
        result.append({
            "id": row["id"], "name": row["name"], "stage": row["stage"],
            "attractions_count": len(row["attractions"]),
            "group_id": group.get("id") if group else None,
            "group_name": group.get("name") if group else None,
            "grouped": group is not None, "group_sequence": sequence,
            "period": period, "dates": exact,
            "group_period": group_period, "group_dates": group_dates,
            "organized": organized, "dated": bool(exact), "status": status,
        })
    result.sort(key=lambda r: (
        0 if r["dated"] or r["group_dates"] else 1 if r["organized"] else 2,
        (r["dates"] or r["group_dates"] or [""])[0],
        r["group_sequence"] or 0, r["name"].casefold()))
    return result


def timeline_metrics(rows):
    return {"visits":len(rows),
            "grouped":sum(r["grouped"] for r in rows),
            "organized":sum(r["organized"] for r in rows),
            "dated":sum(r["dated"] for r in rows)}
