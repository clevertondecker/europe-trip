"""REC02 transient scope: no wishlist/TripPlan schema or session dependency."""
from __future__ import annotations

from copy import deepcopy
from destination_identity import canonical_destination_id
from ux502_destination_interests_model import validate_interests

STAGE = "europe_season"


def _snapshot(interests, discovery):
    doc = validate_interests(interests, discovery)
    return {
        "revision": doc["revision"],
        "items": sorted((x["destination_id"], x["priority"]) for x in doc["items"]),
    }


def _active(snapshot):
    return {key for key, priority in snapshot["items"] if priority != "discarded"}


def confirm_scope(interests, destination_ids, discovery, *, stage=STAGE):
    """Explicit user action only. Return a disposable, session-local value."""
    snapshot = _snapshot(interests, discovery)
    active_by_identity = {canonical_destination_id(x): x for x in _active(snapshot)}
    if isinstance(destination_ids, list) and all(isinstance(x, str) and x.strip() for x in destination_ids):
        destination_ids = [active_by_identity.get(canonical_destination_id(x), x) for x in destination_ids]
    if (stage != STAGE or not isinstance(destination_ids, list)
            or not destination_ids
            or any(not isinstance(x, str) or x not in _active(snapshot)
                   for x in destination_ids)
            or len(set(destination_ids)) != len(destination_ids)):
        raise ValueError("Selecione destinos ativos distintos para a temporada")
    return {"stage": stage, "destination_ids": sorted(destination_ids),
            "snapshot": snapshot, "confirmed": True, "pending_ids": []}


def reconcile_scope(interests, scope, discovery, *, reset=False):
    """Reconcile edits; restore/import/account changes must pass reset=True.

    Same revision + changed content and backwards revision are stale contexts.
    New active IDs require explicit review; removing a wish never adds another.
    No data is persisted. Malformed restored widget state fails closed.
    """
    now = _snapshot(interests, discovery)
    active = _active(now)
    if not active:
        return {"state": "no_destinations", "scope": None, "pending_ids": []}
    if reset or scope is None:
        return {"state": "scope_required", "scope": None, "pending_ids": sorted(active)}
    try:
        if (not isinstance(scope, dict) or scope["stage"] != STAGE
                or type(scope["confirmed"]) is not bool):
            raise ValueError("Escopo inválido")
        old = scope["snapshot"]
        old_items = old["items"]
        if (type(old["revision"]) is not int or old["revision"] < 0
                or not isinstance(old_items, list)
                or any(not isinstance(x, (list, tuple)) or len(x) != 2
                       or not isinstance(x[0], str)
                       or x[1] not in ("must_visit", "interested", "maybe", "discarded")
                       for x in old_items)
                or len({x[0] for x in old_items}) != len(old_items)):
            raise ValueError("Snapshot inválido")
        old = {"revision": old["revision"], "items": sorted(tuple(x) for x in old_items)}
        chosen, pending = scope["destination_ids"], scope["pending_ids"]
        for ids in (chosen, pending):
            if (not isinstance(ids, list) or any(not isinstance(x, str) for x in ids)
                    or len(set(ids)) != len(ids)):
                raise ValueError("IDs inválidos")
        if not set(chosen) <= _active(old) or not set(pending) <= _active(old):
            raise ValueError("Escopo inconsistente")
        if now["revision"] < old["revision"] or (
                now["revision"] == old["revision"] and now != old):
            raise ValueError("Documento substituído")
    except (KeyError, TypeError, ValueError):
        return {"state": "scope_required", "scope": None, "pending_ids": sorted(active)}
    picked = sorted(set(chosen) & active)
    review = sorted((set(pending) | (active - _active(old))) & active)
    confirmed = bool(picked) and scope["confirmed"] and not review
    updated = {"stage": STAGE, "destination_ids": picked, "snapshot": now,
               "confirmed": confirmed, "pending_ids": review}
    return {"state": "ready" if confirmed else "scope_required",
            "scope": deepcopy(updated), "pending_ids": review}
