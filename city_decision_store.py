"""Private-to-the-user portable UX 3.4 city study drafts (never public GitHub).

Export/download or in-memory Streamlit session only; no implicit remote writes.
A draft's original reference is *informational*, not permission to mutate
the current TripPlan. Reopening always recalculates against the current plan.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from math import isfinite

from city_decision_model import MAX_ALTERNATIVES,MAX_DESTINATIONS,names_and_bases
from base_change_model import destination_catalog

SCHEMA_VERSION=1
MAX_BYTES=65536


def validate_city_draft(draft:dict)->dict:
    keys={"schema_version","name","official_at_creation","plan_revision_at_creation",
          "alternatives","destination_ids","stay_days","rents_eur_month",
          "eur_fx","notes","saved_at","status"}
    if not isinstance(draft,dict) or set(draft)!=keys or draft["schema_version"]!=SCHEMA_VERSION:
        raise ValueError("Versão ou formato do cenário inválido")
    if draft["status"]!="exploratory_only":
        raise ValueError("Cenário deve ser exclusivamente exploratório")
    if (not isinstance(draft["name"],str) or
        not 1<=len(draft["name"].strip())<=80):
        raise ValueError("Nome do cenário inválido")
    if not isinstance(draft["notes"],str) or len(draft["notes"])>1000:
        raise ValueError("Anotações inválidas")
    if (not isinstance(draft["saved_at"],str) or
        not isinstance(draft["plan_revision_at_creation"],int) or
        isinstance(draft["plan_revision_at_creation"],bool) or
        draft["plan_revision_at_creation"]<0):
        raise ValueError("Data ou revisão inválida")
    moment=datetime.fromisoformat(draft["saved_at"].replace("Z","+00:00"))
    if moment.tzinfo is None:
        raise ValueError("Data deve ter fuso horário")
    names=names_and_bases()
    current=draft["official_at_creation"]
    others=draft["alternatives"]
    if (current not in names or not isinstance(others,list) or
        not 1<=len(others)<=MAX_ALTERNATIVES or
        len(set(others))!=len(others) or current in others or
        any(k not in names for k in others)):
        raise ValueError("Cidades do cenário inválidas")
    destinations=draft["destination_ids"]
    valid_destinations=destination_catalog()
    if (not isinstance(destinations,list) or
        not 1<=len(destinations)<=MAX_DESTINATIONS or
        len(set(destinations))!=len(destinations) or
        any(d not in valid_destinations for d in destinations)):
        raise ValueError("Destinos inválidos")
    days=draft["stay_days"]
    fx=draft["eur_fx"]
    if (type(days) is not int or not 40<=days<=80 or
        not isinstance(fx,(int,float)) or isinstance(fx,bool) or
        not isfinite(fx) or fx<=0):
        raise ValueError("Duração ou câmbio inválido")
    rents=draft["rents_eur_month"]
    if not isinstance(rents,dict) or not set(rents)<=set([current]+others):
        raise ValueError("Provisões de moradia inválidas")
    for value in rents.values():
        if (value is not None and
            (not isinstance(value,(int,float)) or isinstance(value,bool) or
             not isfinite(value) or not 0<value<=20000)):
            raise ValueError("Valor de provisão inválido")
    return dict(draft)


def make_city_draft(name:str,comparison:dict,notes:str="")->dict:
    draft={
        "schema_version":SCHEMA_VERSION,"name":name,
        "official_at_creation":comparison["official_base"],
        "plan_revision_at_creation":comparison["plan_revision"],
        "alternatives":comparison["alternatives"][:],
        "destination_ids":comparison["destinations"][:],
        "stay_days":comparison["french_days"],
        "rents_eur_month":dict(comparison["rents_eur_month"]),
        "eur_fx":comparison["eur_fx"],"notes":notes,
        "saved_at":datetime.now(timezone.utc).isoformat(),
        "status":"exploratory_only",
    }
    return validate_city_draft(draft)


def export_city_draft(draft:dict)->bytes:
    return (json.dumps(validate_city_draft(draft),ensure_ascii=False,indent=2)+"\n").encode("utf-8")


def import_city_draft(contents:bytes)->dict:
    if not isinstance(contents,bytes) or not 0<len(contents)<=MAX_BYTES:
        raise ValueError("Arquivo muito grande ou vazio")
    try:
        doc=json.loads(contents.decode("utf-8"))
    except (UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("JSON inválido") from exc
    return validate_city_draft(doc)
