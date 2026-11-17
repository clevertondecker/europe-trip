"""ARCH 1.1 — pure read-only projections of the canonical TripPlan.

Legacy session keys are compatibility views. None is a second authority.
This module does not write session state or perform persistence.
"""
from __future__ import annotations
from copy import deepcopy
from trip_plan_model import validate_plan


def legacy_plan_projection(plan: dict) -> dict:
    """Fresh defensive snapshot for older page consumers and widgets."""
    validate_plan(plan)
    return {
        "explore_packages": deepcopy(plan["packages"]),
        "explore_calendar": deepcopy(plan["assignments"]),
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
        "mandatory_destinations": deepcopy(plan.get("mandatory_destinations") or []),
        "excluded_destinations": deepcopy(plan.get("excluded_destinations") or []),
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
