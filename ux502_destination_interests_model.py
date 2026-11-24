"""UX 5.0.2 — versioned, pure destination wishes, distinct from the TripPlan."""
from __future__ import annotations
from copy import deepcopy
import json
from trip01_supplemental_discovery import build_exploration_discovery
from destination_identity import canonical_destination_id as canonical_place

KIND = "nossa-europa-destination-interests"
VERSION = 1
PRIORITIES = ("must_visit", "interested", "maybe", "discarded")
LABELS = dict(zip(PRIORITIES, ("Imperdível", "Quero conhecer", "Talvez", "Descartar")))
LIMIT = 200


def empty_interests() -> dict:
    return {"kind": KIND, "schema_version": VERSION, "revision": 0, "items": []}


def _ids(discovery=None) -> set[str]:
    discovery = discovery if discovery is not None else build_exploration_discovery()
    return {row["id"] for row in discovery["destinations"]}


def validate_interests(document: dict, discovery=None) -> dict:
    valid = _ids(discovery)
    if (not isinstance(document, dict) or set(document) !=
        {"kind", "schema_version", "revision", "items"} or
        document.get("kind") != KIND or
        type(document.get("schema_version")) is not int or
        document["schema_version"] != VERSION or
        type(document.get("revision")) is not int or
        document["revision"] < 0 or
        not isinstance(document.get("items"), list) or
        len(document["items"]) > LIMIT):
        raise ValueError("Versão ou formato dos destinos desejados inválido")
    seen = set()
    clean = deepcopy(document)
    # Respect the inventory namespace when reading historical projections.
    by_identity = {canonical_place(key): key for key in valid}
    for row in clean["items"]:
        if (not isinstance(row, dict) or
            set(row) != {"destination_id", "priority"} or
            not isinstance(row["destination_id"], str) or
            canonical_place(row["destination_id"]) not in by_identity or
            canonical_place(row["destination_id"]) in seen or
            row["priority"] not in PRIORITIES):
            raise ValueError("Destino ou prioridade inválida, ou repetida")
        seen.add(canonical_place(row["destination_id"]))
        row["destination_id"] = by_identity[canonical_place(row["destination_id"])]
    return clean


def set_interest(document: dict, destination_id: str, priority: str, discovery=None) -> dict:
    result = validate_interests(document, discovery)
    valid = _ids(discovery)
    destination_id = {canonical_place(key): key for key in valid}.get(canonical_place(destination_id))
    if destination_id not in valid or priority not in PRIORITIES:
        raise ValueError("Destino ou prioridade desconhecidos")
    found = next((row for row in result["items"] if row["destination_id"] == destination_id), None)
    if found:
        if found["priority"] == priority:
            return result
        found["priority"] = priority
    else:
        if len(result["items"]) >= LIMIT:
            raise ValueError("Limite de destinos alcançado")
        result["items"].append({"destination_id": destination_id, "priority": priority})
    result["revision"] += 1
    return result


def remove_interest(document: dict, destination_id: str, discovery=None) -> dict:
    result = validate_interests(document, discovery)
    result["items"] = [row for row in result["items"]
                       if canonical_place(row["destination_id"]) != canonical_place(destination_id)]
    if len(result["items"]) != len(document["items"]):
        result["revision"] += 1
    return result


def ordered_interests(document: dict, discovery=None) -> list[dict]:
    validated = validate_interests(document, discovery)
    return sorted(validated["items"], key=lambda row:
                  PRIORITIES.index(row["priority"]))


def selected_destinations_for_comparison(interests: dict, discovery=None) -> list[str]:
    return [row["destination_id"] for row in ordered_interests(interests, discovery)
            if row["priority"] != "discarded"]


def reconcile_transient(interests: dict, transient: list[str], discovery=None) -> tuple[dict, list[str]]:
    result = validate_interests(interests, discovery)
    if not isinstance(transient, list) or len(set(transient)) != len(transient):
        raise ValueError("Seleção temporária inválida")
    by_identity = {canonical_place(key): key for key in _ids(discovery)}
    missing = [by_identity.get(canonical_place(x), canonical_place(x)) for x in transient
               if canonical_place(x) not in {canonical_place(r["destination_id"]) for r in result["items"]}]
    if any(x not in _ids(discovery) for x in missing) or len(set(missing)) != len(missing):
        raise ValueError("Destino temporário inválido")
    return result, missing


def export_interests(document: dict, discovery=None) -> bytes:
    return (json.dumps(validate_interests(document, discovery), ensure_ascii=False,
                       sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def import_interests(raw: bytes, discovery=None) -> dict:
    if not isinstance(raw, bytes) or not 0 < len(raw) <= 80_000:
        raise ValueError("Arquivo de interesses inválido")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (ValueError, UnicodeError) as exc:
        raise ValueError("JSON de interesses inválido") from exc
    return validate_interests(document, discovery)
