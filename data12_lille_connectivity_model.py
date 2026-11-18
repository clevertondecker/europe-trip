"""DATA12: validated, sourced outbound rail minima from Lille.

Additive overlay; existing researched evidence always wins. Reuses DATA10's
strict contract for provenance, direction and 2027 disclaimers.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import json
from data10_connectivity_model import validate_connectivity_dataset

DATA = Path(__file__).resolve().parent / "data" / "data12_lille_connectivity_2026_11.json"
SCOPE = "data12_lille_directed_rail_reference_2026_snapshot"
ORDER = "fallback_after_historical_routes7_data9_data10_data11"


def validate_lille_connectivity(payload, *, base_ids=None, destination_ids=None):
    if (not isinstance(payload, dict) or payload.get("scope") != SCOPE
            or payload.get("selection_policy") != ORDER):
        raise ValueError("DATA12 scope/precedence mismatch")
    sample = deepcopy(payload)
    sample["scope"] = "data10_city_pair_connectivity_2026_snapshot"
    sample["selection_policy"] = "fallback_only_after_historical_and_routes7_and_data9"
    checked = validate_connectivity_dataset(
        sample, base_ids=base_ids, destination_ids=destination_ids)
    if any(row["origin_id"] != "lille" for row in checked["records"]):
        raise ValueError("DATA12 covers Lille outbound only")
    return {**checked, "scope": SCOPE, "dataset": "data12_lille_connectivity_2026_11"}


def load_lille_connectivity(path=DATA, *, base_ids=None, destination_ids=None):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return validate_lille_connectivity(
        payload, base_ids=base_ids, destination_ids=destination_ids)
