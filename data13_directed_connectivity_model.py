"""DATA 13: directional SNCF rail minima, deliberately lower precedence.

Every record must contain an individual source URL, actual published minimum
and audited direction. This module does not infer reverse trips or 2027 service.
"""
from __future__ import annotations
from copy import deepcopy
from pathlib import Path
import json

from data10_connectivity_model import validate_connectivity_dataset

DEFAULT = Path(__file__).resolve().parent / "data" / "data13_directed_connectivity_2026_11.json"
SCOPE = "data13_directed_rail_reference_2026_snapshot"
POLICY = "fallback_after_historical_routes7_data9_data10_data11_data12"


def validate_data13(payload, *, base_ids=None, destination_ids=None):
    if not isinstance(payload, dict) or payload.get("scope") != SCOPE or (
            payload.get("selection_policy") != POLICY):
        raise ValueError("DATA13 identity or fallback policy invalid")
    adapted = deepcopy(payload)
    adapted["scope"] = "data10_city_pair_connectivity_2026_snapshot"
    adapted["selection_policy"] = (
        "fallback_only_after_historical_and_routes7_and_data9")
    validated = validate_connectivity_dataset(
        adapted, base_ids=base_ids, destination_ids=destination_ids)
    return {**validated, "scope": SCOPE,
            "dataset": "data13_directed_connectivity_2026_11"}


def load_data13(path=DEFAULT, *, base_ids=None, destination_ids=None):
    return validate_data13(
        json.loads(Path(path).read_text(encoding="utf-8")),
        base_ids=base_ids, destination_ids=destination_ids)
