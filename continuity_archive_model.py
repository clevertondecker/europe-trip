"""UX 3.6: safe, manual portability with optimistic restore protection.

This is NOT a cloud vault. The generated JSON is plain text, controlled by
the traveler and never uploaded automatically to the application's public
GitHub repository. Remote private storage is a separate security decision.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime,timezone
from hashlib import sha256
import json

from trip_plan_model import validate_plan
from itinerary_flow_model import validate_flow_backup,selected_rows
from city_decision_store import validate_city_draft
from smart_calendar_model import review_calendar_change
from ux_navigation import AREAS,SECTIONS
from base_research_expanded_model import load_research
from ux41_favorites_model import validate_favorites
from ux502_destination_interests_model import empty_interests,validate_interests
from ux48_weekend_groups_model import validate_groups,empty_groups

ARCHIVE_SCHEMA=1
ARCHIVE_KIND="nossa-europa-local-archive"
MAX_FILE_BYTES=450_000
MAX_DRAFTS=12
CONTEXT_KEYS={"area","section","stage","destination_id","search",
              "organize_view","calendar_week","calendar_stage"}
VALID_ORGANIZE_VIEWS={"Por período ou data","Calendário inteligente",
                      "Calendário completo","Viagens agrupadas"}


def _json_bytes(value:dict)->bytes:
    return (json.dumps(value,ensure_ascii=False,sort_keys=True,
                       separators=(",",":"))+"\n").encode("utf-8")


def plan_fingerprint(plan:dict)->str:
    """Only a change detector, never an authorization or signature."""
    validate_plan(plan)
    return sha256(_json_bytes(plan)).hexdigest()


def validate_continuation(context:dict,plan:dict,catalog:dict)->dict:
    if not isinstance(context,dict) or not set(context)<=CONTEXT_KEYS:
        raise ValueError("Contexto de continuação inválido")
    values={
        "area":context.get("area","Meu roteiro"),
        "section":context.get("section","Meu planejamento"),
        "stage":context.get("stage","Itália"),
        "destination_id":context.get("destination_id"),
        "search":context.get("search",""),
        "organize_view":context.get("organize_view","Por período ou data"),
        "calendar_week":context.get("calendar_week"),
        "calendar_stage":context.get("calendar_stage","Itália"),
    }
    area=values["area"];section=values["section"]
    # Accept both old persisted routes and new public task names before validation.
    from ux64_navigation_model import TARGETS
    if (area,section) in TARGETS:
        values["area"],values["section"]=TARGETS[(area,section)]
        area,section=values["area"],values["section"]
    if area not in AREAS or section not in SECTIONS[area]:
        raise ValueError("Área ou tarefa do contexto não existe mais")
    if values["stage"] not in ("Itália","França") or values["calendar_stage"] not in ("Itália","França"):
        raise ValueError("Etapa de contexto inválida")
    if values["organize_view"] not in VALID_ORGANIZE_VIEWS:
        raise ValueError("Modo de organização desconhecido")
    search=values["search"]
    if not isinstance(search,str) or len(search)>160:
        raise ValueError("Busca no backup inválida")
    week=values["calendar_week"]
    if week is not None and (type(week) is not int or not 0<=week<=15):
        raise ValueError("Semana de calendário inválida")
    dest=values["destination_id"]
    selected={r["id"] for r in selected_rows(plan,catalog)}
    if dest is not None and (not isinstance(dest,str) or dest not in selected):
        # The person may have removed that location after exporting; do not
        # reopen a phantom editor or silently point to another location.
        raise ValueError("O passeio do contexto não existe neste backup")
    return values


def make_archive(plan:dict,catalog:dict,context:dict|None=None,
                 city_studies:list[dict]|None=None,
                 calendar_drafts:list[dict]|None=None,
                 city_favorites:list[str]|None=None,
                 weekend_groups:dict|None=None,
                 destination_interests:dict|None=None)->dict:
    validate_flow_backup(plan,catalog)
    continuation=validate_continuation(context or {},plan,catalog)
    studies=city_studies or []
    calendars=calendar_drafts or []
    if (not isinstance(studies,list) or not isinstance(calendars,list) or
        len(studies)+len(calendars)>MAX_DRAFTS):
        raise ValueError("Quantidade de estudos acima do limite")
    verified_studies=[deepcopy(validate_city_draft(x)) for x in studies]
    verified_calendars=[]
    for item in calendars:
        review_calendar_change(plan,item,catalog)
        verified_calendars.append(deepcopy(item))
    result={
        "schema_version":ARCHIVE_SCHEMA,
        "kind":ARCHIVE_KIND,
        "exported_at":datetime.now(timezone.utc).isoformat(),
        "storage":"local_file_only",
        "plan":deepcopy(plan),
        "continuation":continuation,
        "city_studies":verified_studies,
        "calendar_drafts":verified_calendars,
        "city_favorites":validate_favorites(city_favorites or [],load_research()),
        "destination_interests":validate_interests(
            destination_interests if destination_interests is not None else empty_interests()),
        "weekend_groups":validate_groups(
            weekend_groups if weekend_groups is not None else empty_groups(plan),plan,catalog),
    }
    if len(_json_bytes(result))>MAX_FILE_BYTES:
        raise ValueError("Backup grande demais")
    return result


def validate_archive(document:dict,catalog:dict)->dict:
    required={"schema_version","kind","exported_at","storage","plan",
              "continuation","city_studies","calendar_drafts"}
    if (not isinstance(document,dict) or
        not required<=set(document) or
        set(document)-required-{"city_favorites","weekend_groups","destination_interests"}):
        raise ValueError("Formato do arquivo desconhecido")
    if document["schema_version"]!=ARCHIVE_SCHEMA or document["kind"]!=ARCHIVE_KIND:
        raise ValueError("Versão incompatível do arquivo de continuidade")
    if document["storage"]!="local_file_only":
        raise ValueError("Arquivo declara tipo de armazenamento incompatível")
    try:
        stamp=datetime.fromisoformat(document["exported_at"].replace("Z","+00:00"))
    except (ValueError,AttributeError,TypeError) as exc:
        raise ValueError("Data de exportação inválida") from exc
    if stamp.tzinfo is None:
        raise ValueError("Data do backup precisa de fuso")
    plan=deepcopy(document["plan"])
    validate_flow_backup(plan,catalog)
    context=validate_continuation(document["continuation"],plan,catalog)
    studies=document["city_studies"];calendars=document["calendar_drafts"]
    if (not isinstance(studies,list) or not isinstance(calendars,list) or
        len(studies)+len(calendars)>MAX_DRAFTS):
        raise ValueError("Estudos do backup inválidos")
    for study in studies:validate_city_draft(study)
    for draft in calendars:review_calendar_change(plan,draft,catalog)
    fav=validate_favorites(document.get("city_favorites",[]),load_research())
    wishes=validate_interests(document.get("destination_interests",empty_interests()))
    weekends=validate_groups(document.get("weekend_groups",empty_groups(plan)),plan,catalog)
    return {**document,"plan":plan,"continuation":context,
            "city_studies":deepcopy(studies),
            "calendar_drafts":deepcopy(calendars),
            "city_favorites":fav,
            "destination_interests":wishes,
            "weekend_groups":weekends}


def export_archive(archive:dict,catalog:dict)->bytes:
    document=validate_archive(archive,catalog)
    raw=_json_bytes(document)
    if len(raw)>MAX_FILE_BYTES:raise ValueError("Backup grande demais")
    return raw


def import_archive(blob:bytes,catalog:dict)->dict:
    if not isinstance(blob,bytes) or not 0<len(blob)<=MAX_FILE_BYTES:
        raise ValueError("Arquivo vazio ou muito grande")
    try:
        raw=json.loads(blob.decode("utf-8"))
    except (UnicodeError,json.JSONDecodeError) as exc:
        raise ValueError("JSON de recuperação inválido") from exc
    return validate_archive(raw,catalog)


def persisted_data_fingerprint(archive:dict)->str:
    """Identity of decisions included in a snapshot, independent of UI position."""
    value={k:v for k,v in archive.items() if k not in ("exported_at","continuation")}
    return sha256(_json_bytes(value)).hexdigest()


def _interest_diff(before:dict,after:dict)->dict:
    old={row["destination_id"]:row["priority"] for row in before.get("items",[])}
    new={row["destination_id"]:row["priority"] for row in after.get("items",[])}
    return {"added":len(set(new)-set(old)),
            "removed":len(set(old)-set(new)),
            "priority_changed":sum(old[k]!=new[k] for k in set(old)&set(new))}


def preview_restore(current:dict,archive:dict,catalog:dict,
                    current_archive:dict|None=None)->dict:
    validate_plan(current)
    incoming=validate_archive(archive,catalog)
    other=incoming["plan"]
    same_id=current["plan_id"]==other["plan_id"]
    changed=sorted(k for k in set(current)|set(other)
                   if current.get(k)!=other.get(k) and
                   k not in ("revision","source_versions"))
    existing=(validate_archive(current_archive,catalog)
              if current_archive is not None else None)
    auxiliary_fields=(sorted(k for k in
        ("destination_interests","weekend_groups","city_favorites",
         "city_studies","calendar_drafts")
        if existing is not None and existing.get(k)!=incoming.get(k)))
    wish_changes=(_interest_diff(existing["destination_interests"],
                                 incoming["destination_interests"])
                  if existing is not None else None)
    has_changes=bool(changed or auxiliary_fields)
    relation=("same_plan_older" if same_id and other["revision"]<current["revision"]
              else "same_plan_same_revision_conflict" if same_id and
                  other["revision"]==current["revision"] and has_changes
              else "same_plan_newer" if same_id and other["revision"]>current["revision"]
              else "different_plan" if not same_id
              else "same_plan_identical")
    return {
        "current_plan_id":current["plan_id"],
        "expected_current_fingerprint":plan_fingerprint(current),
        "expected_archive_fingerprint":sha256(_json_bytes(incoming)).hexdigest(),
        "incoming_plan_id":other["plan_id"],
        "incoming_revision":other["revision"],
        "current_revision":current["revision"],
        "relation":relation,
        "changed_fields":changed,
        "auxiliary_changed_fields":auxiliary_fields,
        "wishlist_changes":wish_changes,
        "expected_current_decisions_fingerprint":(
            persisted_data_fingerprint(existing) if existing is not None else None),
        "places_before":len(selected_rows(current,catalog)),
        "places_after":len(selected_rows(other,catalog)),
        "archived_studies":len(incoming["city_studies"]),
        "archived_calendar_drafts":len(incoming["calendar_drafts"]),
        "notice":"Recuperar substitui o plano nesta sessão, não o GitHub. "
                 "Um arquivo local sem criptografia precisa ser guardado em local seguro.",
    }


def confirm_restore(current:dict,archive:dict,review:dict,catalog:dict,
                    *,confirmed:bool=False,current_archive:dict|None=None)->dict:
    """No write without explicit consent; reject stale preview and other file."""
    if not confirmed:return deepcopy(current)
    if (not isinstance(review,dict) or
        review.get("expected_current_fingerprint")!=plan_fingerprint(current) or
        review.get("current_plan_id")!=current["plan_id"]):
        raise ValueError("Seu plano mudou desde a revisão. Confira novamente")
    if review.get("expected_current_decisions_fingerprint") is not None:
        if current_archive is None or (
            persisted_data_fingerprint(validate_archive(current_archive,catalog)) !=
                review["expected_current_decisions_fingerprint"]):
            raise ValueError("Destinos ou outros dados mudaram desde a prévia. Revise novamente")
    incoming=validate_archive(archive,catalog)
    if sha256(_json_bytes(incoming)).hexdigest()!=review.get("expected_archive_fingerprint"):
        raise ValueError("O arquivo foi alterado após a revisão; valide novamente")
    plan=incoming["plan"]
    if (plan["plan_id"]!=review.get("incoming_plan_id") or
        plan["revision"]!=review.get("incoming_revision")):
        raise ValueError("O arquivo foi substituído após a revisão")
    # Do not reuse a lower/equal revision as though nothing happened.
    if plan["plan_id"]==current["plan_id"] and plan!=current:
        plan["revision"]=max(current["revision"],plan["revision"])+1
    validate_flow_backup(plan,catalog)
    return deepcopy(plan)
