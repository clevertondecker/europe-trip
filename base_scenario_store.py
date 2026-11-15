"""Portable, versioned hypothetical base scenarios (never TripPlan changes).

The public repository is not a private persistence backend.  Export/import
allows durable backup without silently publishing travel preferences.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from base_scenario_model import base_options,choose_exploratory_base

SCHEMA_VERSION=1
MAX_BYTES=128_000


def make_scenario(name:str,city_id:str,days:int,notes:str="")->dict:
    if not isinstance(name,str) or not 1<=len(name.strip())<=80:
        raise ValueError("Informe um nome de 1 a 80 caracteres")
    if type(days) is not int or not 7<=days<=100:
        raise ValueError("Duração fora de 7–100 dias")
    if not isinstance(notes,str) or len(notes)>2000:
        raise ValueError("Anotações muito longas")
    choose_exploratory_base(city_id,base_options())
    return {"schema_version":SCHEMA_VERSION,"name":name.strip(),
            "city_id":city_id,"days":days,"notes":notes,
            "saved_at":datetime.now(timezone.utc).isoformat(),
            "status":"exploratory_only"}


def validate_scenario(data:dict)->dict:
    if type(data) is not dict or data.get("schema_version")!=SCHEMA_VERSION:
        raise ValueError("Versão do cenário não suportada")
    required={"schema_version","name","city_id","days","notes","saved_at","status"}
    if set(data)!=required or data["status"]!="exploratory_only":
        raise ValueError("Arquivo de cenário inválido")
    make_scenario(data["name"],data["city_id"],data["days"],data["notes"])
    if not isinstance(data["saved_at"],str):
        raise ValueError("Data de salvamento inválida")
    datetime.fromisoformat(data["saved_at"].replace("Z","+00:00"))
    return dict(data)


def scenario_export(data:dict)->bytes:
    return (json.dumps(validate_scenario(data),ensure_ascii=False,
                       indent=2)+"\n").encode("utf-8")


def scenario_import(contents:bytes)->dict:
    if not isinstance(contents,bytes) or len(contents)>MAX_BYTES:
        raise ValueError("Arquivo muito grande ou inválido")
    return validate_scenario(json.loads(contents.decode("utf-8")))
