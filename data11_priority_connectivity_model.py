"""DATA 11: additional sourced one-way rail minima for priority screening bases.

Reuses DATA 10's strict source/identity/time validator, but maintains an
independent dataset and lower precedence. No service, fare or round-trip
evidence for 2027 is inferred.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json

from data10_connectivity_model import validate_connectivity_dataset

DATA = Path(__file__).resolve().parent / "data" / "data11_priority_connectivity_2026_11.json"
SCOPE = "data11_priority_city_pair_connectivity_2026_snapshot"
SELECTION = "fallback_after_historical_routes7_data9_data10"


def validate_priority_connectivity(payload, *, base_ids=None, destination_ids=None):
    if (not isinstance(payload, dict)
            or payload.get("scope") != SCOPE
            or payload.get("selection_policy") != SELECTION):
        raise ValueError("DATA 11 scope or precedence contract invalid")
    # Source identity, direction, dated provenance and absence of 2027 service
    # claims must match the conservative existing DATA 10 rules.
    borrowed = deepcopy(payload)
    borrowed["scope"] = "data10_city_pair_connectivity_2026_snapshot"
    borrowed["selection_policy"] = (
        "fallback_only_after_historical_and_routes7_and_data9")
    checked = validate_connectivity_dataset(
        borrowed, base_ids=base_ids, destination_ids=destination_ids)
    return {**checked, "scope": SCOPE, "dataset": "data11_priority_connectivity_2026_11"}


def load_priority_connectivity(path=DATA, *, base_ids=None, destination_ids=None):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_priority_connectivity(
        payload, base_ids=base_ids, destination_ids=destination_ids)
