"""Owner-isolated private city-study collection, using UX3.6 GCS CAS.

Separate object from current TripPlan archive; no migration of public data.
Never interpret the owner supplied by imported JSON as authentication.
"""
from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime,timezone
from uuid import uuid4

from private_continuity_store import PrivateArchiveStore,object_key,StorageConflict

MAX_STUDIES=40
MAX_BYTES=400_000


class PrivateStudyStore(PrivateArchiveStore):
    def __init__(self,bucket:str,service_account:dict,owner_email:str):
        super().__init__(bucket,service_account,owner_email)
        self.key=object_key(owner_email).removesuffix("current.json")+"city_studies.json"


def _now():
    return datetime.now(timezone.utc).isoformat()


def validate_collection(value:dict)->dict:
    from city_decision_store import validate_city_draft
    if not isinstance(value,dict) or value.get("schema_version")!=1:
        raise ValueError("Coleção privada incompatível")
    entries=value.get("studies")
    if not isinstance(entries,list) or len(entries)>MAX_STUDIES:
        raise ValueError("Limite de estudos inválido")
    ids=set()
    for row in entries:
        if not isinstance(row,dict) or set(row)!={"id","created_at","updated_at","revision","draft"}:
            raise ValueError("Formato do estudo inválido")
        ident=row["id"]
        from uuid import UUID
        try:
            if not isinstance(ident,str) or str(UUID(ident))!=ident:raise ValueError("id")
        except (TypeError,ValueError,AttributeError) as exc:
            raise ValueError("Identificador de estudo inválido") from exc
        if ident in ids:raise ValueError("Estudo duplicado")
        ids.add(ident)
        if type(row["revision"]) is not int or row["revision"]<1:
            raise ValueError("Revisão inválida")
        for key in ("created_at","updated_at"):
            if not isinstance(row[key],str) or datetime.fromisoformat(row[key].replace("Z","+00:00")).tzinfo is None:
                raise ValueError("Data inválida")
        validate_city_draft(row["draft"])
    return deepcopy(value)


def empty_collection()->dict:
    return {"schema_version":1,"studies":[]}


def encode_collection(value:dict)->bytes:
    raw=json.dumps(validate_collection(value),ensure_ascii=False,sort_keys=True).encode("utf-8")
    if len(raw)>MAX_BYTES:raise ValueError("Coleção muito grande")
    return raw


def decode_collection(raw:bytes)->dict:
    if not isinstance(raw,bytes) or not 0<len(raw)<=MAX_BYTES:
        raise ValueError("Arquivo de estudos inválido")
    try:return validate_collection(json.loads(raw.decode("utf-8")))
    except (UnicodeDecodeError,json.JSONDecodeError) as exc:
        raise ValueError("JSON de estudos inválido") from exc


def add_study(collection:dict,draft:dict)->tuple[dict,str]:
    from city_decision_store import validate_city_draft
    result=validate_collection(collection)
    if len(result["studies"])>=MAX_STUDIES:raise ValueError("Limite de estudos atingido")
    ident=str(uuid4())
    at=_now()
    result["studies"].append({"id":ident,"created_at":at,"updated_at":at,
                              "revision":1,"draft":validate_city_draft(draft)})
    return result,ident


def change_study(collection:dict,study_id:str,operation:str,*,name:str|None=None,\n                 draft:dict|None=None)->tuple[dict,str|None]:
    result=validate_collection(collection)
    existing=next((s for s in result["studies"] if s["id"]==study_id),None)
    if existing is None:raise ValueError("Estudo não encontrado")
    if operation=="delete":
        result["studies"]=[s for s in result["studies"] if s["id"]!=study_id]
        return result,None
    if operation=="duplicate":
        draft=deepcopy(existing["draft"])
        draft["name"]=name or (draft["name"]+" (cópia)")[:80]
        return add_study(result,draft)
    if operation=="replace":
        from city_decision_store import validate_city_draft
        if draft is None:raise ValueError("Comparação atual ausente")
        existing["draft"]=validate_city_draft(draft)
        existing["revision"]+=1
        existing["updated_at"]=_now()
        return result,study_id
    if operation=="rename":
        from city_decision_store import validate_city_draft
        draft=deepcopy(existing["draft"])
        draft["name"]=name
        existing["draft"]=validate_city_draft(draft)
        existing["revision"]+=1
        existing["updated_at"]=_now()
        return result,study_id
    raise ValueError("Operação desconhecida")


def cloud_load(store:PrivateStudyStore)->tuple[dict,int|None]:
    loaded=store.load()
    if loaded is None:return empty_collection(),None
    raw,generation=loaded
    return decode_collection(raw),generation


def cloud_commit(store:PrivateStudyStore,collection:dict,generation:int|None)->int:
    # GCS ifGenerationMatch is enforced inside PrivateArchiveStore.save.
    return store.save(encode_collection(collection),generation)
