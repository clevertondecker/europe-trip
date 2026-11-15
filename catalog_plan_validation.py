"""Verify package-to-destination membership against the existing catalog."""
from __future__ import annotations


def allowed_attractions(catalog:dict,destination:str)->set[str]:
    if destination not in {d["id"] for d in catalog["destinations"]}:
        raise ValueError("Destino não consta do catálogo")
    return {a["id"] for a in catalog["attractions"]
            if a["destination_id"]==destination}


def validate_catalog_packages(plan:dict,catalog:dict)->None:
    for destination,ids in plan["packages"].items():
        allowed=allowed_attractions(catalog,destination)
        if (not isinstance(ids,list) or not 1<=len(ids)<=5 or
                len(set(ids))!=len(ids) or any(x not in allowed for x in ids)):
            raise ValueError("O roteiro contém atrações inválidas para o destino")
