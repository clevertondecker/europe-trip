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
