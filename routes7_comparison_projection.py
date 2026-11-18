"""Read-only ROUTES 7 presentation over current UX503 comparison.

Keep minimum legacy times authoritative. Route-summary minimum is a labeled
planning reference, not a date-specific 2027 train or typical time.
"""
from __future__ import annotations

from routes7_reference_model import load_route_references, planning_reference


def format_minutes(value):
    if value is None:
        return "não informado"
    if type(value) is not int or value < 1:
        raise ValueError("duration invalid")
    return f"{value // 60}h{value % 60:02d}" if value >= 60 else f"{value} min"


def decorate_comparison(result, *, references=None):
    """Keep original comparison unchanged; add a display overlay by pair."""
    refs=references if references is not None else load_route_references()
    index={}
    for row in result["rows"]:
        key=(row["base_id"],row["destination_id"])
        if key in index:
            raise ValueError("Duplicate comparison row")
        legacy={
            "status":row["evidence_status"],
            "minimum_oneway_min":row["minimum_oneway_min"],
            "source_url":row["source_url"],
        }
        v=planning_reference(*key,references=refs,legacy=legacy)
        if v["status"]=="local":
            label="Local · acesso a verificar"
        elif v["display_basis"]=="legacy_historical":
            label=f'{format_minutes(v["display_min"])} · ida histórica'
            if row["divergent_sources"]:
                label+=" · fontes divergentes"
            if v.get("conflict_with_legacy"):
                label+=" · outra referência disponível"
        elif v["display_basis"]=="published_fastest_reference":
            label=f'~{format_minutes(v["display_min"])} · mínimo publicado'
        else:
            label="Pesquisa parcial · sem tempo" if row["observations"] else "Tempo não pesquisado"
        if v.get("average_min") is not None:
            typical_label=f'{format_minutes(v["average_min"])} · média publicada'
        else:
            typical_label="Tempo típico não pesquisado"
        index[key]={**v,"label":label,"typical_label":typical_label,
                    "destination_id":key[1],"base_id":key[0]}
    return {
        "cells":index,
        "total":len(index),
        "historical":sum(row["minimum_oneway_min"] is not None for row in result["rows"]),
        "reference_only":sum(x["display_basis"]=="published_fastest_reference" for x in index.values()),
        "local":sum(x["status"]=="local" for x in index.values()),
        "no_time":sum(x["display_min"] is None and x["status"]!="local" for x in index.values()),
        "comparison_mutated":False,
    }
