"""Canonical destination identity; aliases are explicit, not geographic guesses."""
from __future__ import annotations

_DESTINATION_ALIASES = {
    "roma": "rome", "napoles": "naples",
    "luxembourg_city": "luxembourg", "luxemburgo": "luxembourg",
    "bruxelles": "brussels", "bruxelas": "brussels",
    "bruges": "bruges_be", "brugge": "bruges_be",
    "köln": "cologne", "koln": "cologne",
}

def canonical_destination_id(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Identificador inválido")
    key = value.strip().casefold()
    return _DESTINATION_ALIASES.get(key, key)


# Outing IDs are a persisted namespace, not a separate geographic identity.
_ITALIAN_OUTING_IDS = {"rome": "italy_rome", "naples": "italy_naples"}

def outing_destination_id(value: str) -> str:
    key = canonical_destination_id(value)
    return _ITALIAN_OUTING_IDS.get(key, key)


def unique_outing_keys(values):
    """Reject ambiguous identities before projection or mutation; never discard data."""
    result = {}
    for value in values:
        key = outing_destination_id(value)
        if key in result:
            raise ValueError("Identificadores de destino conflitantes: " + result[key] + " / " + value)
        result[key] = value
    return result


def stored_outing_id(plan, value):
    """Use the existing persisted key when editing/scheduling an old plan."""
    key = outing_destination_id(value)
    packages = unique_outing_keys(plan.get("packages", {}))
    visits = unique_outing_keys(v["destination_id"] for v in plan.get("flexible_visits", []))
    return packages.get(key, visits.get(key, key))
