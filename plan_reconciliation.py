"""Pure, side-effect-free comparison for explicit public GitHub plan reconciliation.

The UI never infers a remote SHA or changes a session plan during preview.
A reviewed local plan can be rebased to a newer revision, but the repository
must still recheck the SHA at the moment of saving.
"""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json

from trip_plan_model import validate_plan


def plan_digest(plan: dict) -> str:
    """Stable fingerprint of the *entire* plan, including its revision."""
    validate_plan(plan)
    payload = json.dumps(plan, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()


def _display(value) -> str:
    """Bound preview length; do not use this display representation for equality."""
    if value is None:
        return "—"
    rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
    return rendered if len(rendered) <= 160 else rendered[:157] + "..."


def compare_plans(local: dict, remote: dict) -> dict:
    """Return bounded field-level differences without modifying either argument."""
    validate_plan(local)
    validate_plan(remote)
    if local["plan_id"] != remote["plan_id"]:
        raise ValueError("O planejamento local e o remoto possuem IDs diferentes.")
    differences = []

    def walk(left, right, path: str):
        if left == right:
            return
        if isinstance(left, dict) and isinstance(right, dict):
            for key in sorted(set(left) | set(right)):
                lvalue = left.get(key, _MISSING)
                rvalue = right.get(key, _MISSING)
                walk(lvalue, rvalue, f"{path}.{key}" if path else str(key))
        elif isinstance(left, list) and isinstance(right, list):
            # Lists are editorial/ordered collections: show one complete change
            # rather than conflating a reorder with an item-level edit.
            differences.append({"field": path, "local": _display(left),
                                "github": _display(right)})
        else:
            differences.append({"field": path,
                                "local": "(ausente)" if left is _MISSING else _display(left),
                                "github": "(ausente)" if right is _MISSING else _display(right)})

    walk(local, remote, "")
    return {
        "plan_id": local["plan_id"],
        "local_revision": local["revision"],
        "remote_revision": remote["revision"],
        "local_digest": plan_digest(local),
        "remote_digest": plan_digest(remote),
        "different_fields": differences[:100],
        "difference_count": len(differences),
    }


_MISSING = object()


def prepare_reconciled_plan(local: dict, remote: dict) -> dict:
    """Only called following a user-approved comparison; never writes remotely."""
    compare_plans(local, remote)
    result = deepcopy(local)
    result["revision"] = max(local["revision"], remote["revision"]) + 1
    validate_plan(result)
    return result


def same_persisted_plan(local: dict, remote: dict) -> bool:
    """Equality for no-write reconciliation; includes plan ID and revision."""
    return compare_plans(local, remote)["difference_count"] == 0
