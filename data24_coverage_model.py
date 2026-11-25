"""DATA24: catalog-wide documentary rail coverage, never a feasibility score."""
from __future__ import annotations

from collections import Counter
from base_recommendation_evidence_model import candidate_ids
from ux503_destination_base_comparison_model import build_destination_matrix
from base_research_expanded_model import load_research
from destination_identity import canonical_destination_id
from rail_reference_projection_model import decorate_comparison
from trip01_supplemental_discovery import build_exploration_discovery

CATEGORIES = ("historical", "reference_only", "local", "no_time")


def coverage_counts(categories):
    """Unknown categories are contract failures, not unresearched routes."""
    counts = Counter(categories)
    if set(counts).difference(CATEGORIES):
        raise ValueError("Categoria ferroviária desconhecida")
    total = sum(counts.values())
    eligible = total - counts["local"]
    timed = counts["historical"] + counts["reference_only"]
    return {
        "total": total, "eligible": eligible, "timed": timed,
        "historical": counts["historical"], "indicative": counts["reference_only"],
        "local": counts["local"], "missing": counts["no_time"],
        "fraction": timed / eligible if eligible else None,
    }


def rail_coverage(*, research=None, discovery=None, rail=None, exploration=None,
                  projection_options=None):
    """Enumerate directed pairs using the same evidence and overlays as UX124.

    Explicit catalog IDs are independent of the wishlist and its limits.
    No private state, persistence, external network or inferred reverse trips.
    """
    research = load_research(include_candidates=True) if research is None else research
    discovery = build_exploration_discovery() if discovery is None else discovery
    bases = candidate_ids(research)
    destinations = [row["id"] for row in discovery["destinations"]]
    if len({canonical_destination_id(key) for key in destinations}) != len(destinations):
        raise ValueError("Universo de destinos com identidades duplicadas")
    pairs = {}
    if destinations:
        raw = build_destination_matrix(bases, destinations, research=research,
                                       discovery=discovery, rail=rail,
                                       exploration=exploration)
        cells = decorate_comparison(raw, **(projection_options or {}))["cells"]
        expected = {(base, dest) for base in bases for dest in destinations}
        rows = {(row["base_id"], row["destination_id"]): row for row in raw["rows"]}
        if (len(rows) != len(raw["rows"]) or set(rows) != expected
                or set(cells) != expected):
            raise ValueError("Projeção ferroviária incompleta ou duplicada")
        for key, row in rows.items():
            cell = cells[key]
            if cell["category"] not in CATEGORIES:
                raise ValueError("Categoria ferroviária desconhecida")
            pairs[key] = {"row": row, "cell": cell}
    per_base = {base: [] for base in bases}
    for (base, _), pair in pairs.items():
        per_base[base].append(pair["cell"]["category"])
    return {
        "base_ids": bases, "destination_ids": destinations, "pairs": pairs,
        "global": coverage_counts(pair["cell"]["category"] for pair in pairs.values()),
        "by_base": {base: coverage_counts(categories) for base, categories in per_base.items()},
        "read_only": True, "official_plan_modified": False,
    }
