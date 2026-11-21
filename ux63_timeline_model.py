"""Pure, read-only timeline projection for planned visits and weekend groups."""
from __future__ import annotations
from itinerary_flow_model import selected_rows, UNASSIGNED, FRANCE_STAGE


def project_timeline(plan, catalog, weekend_groups=None, stage=None):
    rows = selected_rows(plan, catalog)
    groups = weekend_groups.get("groups", []) if isinstance(weekend_groups,dict) else []
    associated = {}
    for group in groups:
        for dest in group.get("destinations", []):
            associated[dest] = group
    result = []
    for row in rows:
        if stage is not None and row["stage"] != stage:
            continue
        group = associated.get(row["id"])
        exact = list(row["exact_dates"])
        period = row["period"] if row["period"] != UNASSIGNED else None
        if group and group.get("start_date") and not exact:
            exact = [group["start_date"]]
        if group and not period and group.get("period") not in (
                None, "", "Ainda não definido", "A definir"):
            period = group["period"]
        result.append({
            "id": row["id"], "name": row["name"], "stage": row["stage"],
            "attractions_count": len(row["attractions"]),
            "group_name": group["name"] if group else None,
            "grouped": group is not None,
            "period": period,
            "dates": exact,
            "organized": bool(period or exact),
            "dated": bool(exact),
            "status": ("Data definida" if exact else
                       "Período definido; data pendente" if period else
                       "Em grupo; período/data pendentes" if group else
                       "Sem período ou data"),
        })
    result.sort(key=lambda r: (
        0 if r["dated"] else 1 if r["period"] else 2,
        r["dates"][0] if r["dates"] else "",
        r["name"].casefold()))
    return result


def timeline_metrics(rows):
    return {"visits":len(rows),
            "grouped":sum(r["grouped"] for r in rows),
            "organized":sum(r["organized"] for r in rows),
            "dated":sum(r["dated"] for r in rows)}
