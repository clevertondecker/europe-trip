"""Shared documentary metric; REC01 diagnostic and REC02 use the same fraction."""
from __future__ import annotations
from fractions import Fraction

DEFAULT_WEIGHTS = {"must_visit": 5, "interested": 3, "maybe": 1}
TIMED = frozenset(("historical", "reference_only"))
CATEGORIES = TIMED | {"local", "no_time"}


def weighted_coverage(selected, weights=DEFAULT_WEIGHTS):
    """Measure presence of a timed reference, not evidence quality or feasibility.

    Historical and indicative categories contribute equally to presence only;
    callers retain category counts and provenance. Local is not a zero-minute
    train trip and is excluded from the denominator.
    """
    selected = list(selected)
    denominator = sum(weights[d["priority"]] for d, c in selected if c["category"] != "local")
    numerator = sum(weights[d["priority"]] for d, c in selected if c["category"] in TIMED)
    return numerator, denominator


def ratio(numerator, denominator):
    return Fraction(numerator, denominator) if denominator else None
