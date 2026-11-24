"""ARCH 1.1 — pure read-only projections of the canonical TripPlan.

Legacy session keys are compatibility views. None is a second authority.
This module does not write session state or perform persistence.
"""
from __future__ import annotations
from copy import deepcopy
from trip_plan_model import validate_plan
from destination_identity import outing_destination_id, unique_outing_keys


def legacy_plan_projection(plan: dict) -> dict:
    """Fresh defensive snapshot for older page consumers and widgets."""
    validate_plan(plan)
    return {
        "explore_packages": {key: deepcopy(plan["packages"][original]) for key, original in unique_outing_keys(plan["packages"]).items()},
        "explore_calendar": {day: outing_destination_id(dest) for day, dest in plan["assignments"].items()},
        "explore_base": plan["base_city"],
        "unified_city": plan["base_city"].capitalize(),
        "unified_scenario": plan["budget_scenario"],
    }


def read_plan_view(plan: dict) -> dict:
    """Single immutable-by-convention snapshot for the read-only UI."""
    validate_plan(plan)
    return {
        "base_city": plan["base_city"],
        "budget_scenario": plan["budget_scenario"],
        "revision": plan["revision"],
        "packages": deepcopy(plan["packages"]),
        "assignments": deepcopy(plan["assignments"]),
        "preferences": deepcopy(plan.get("preferences") or {}),
        "mandatory_destinations": [outing_destination_id(d) for d in plan.get("mandatory_destinations", [])],
        "excluded_destinations": [outing_destination_id(d) for d in plan.get("excluded_destinations", [])],
    }


def legacy_drift(plan: dict, session: dict) -> dict:
    """Report legacy divergence without making widgets authoritative."""
    expected=legacy_plan_projection(plan)
    return {
        key: {"expected": deepcopy(value),
              "actual": deepcopy(session.get(key))}
        for key,value in expected.items()
        if key in session and session[key] != value
    }
