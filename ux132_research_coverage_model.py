"""Read-only presentation of DATA24 rail coverage; no recommendation logic."""
from data24_coverage_model import coverage_counts, rail_coverage
from data25_priority_rail_model import RESEARCH_BASE_IDS
from base_research_expanded_model import load_research
from trip01_supplemental_discovery import build_exploration_discovery


def build_coverage_view(*, research=None, discovery=None, projection_options=None):
    research = load_research(include_candidates=True) if research is None else research
    discovery = build_exploration_discovery() if discovery is None else discovery
    coverage = rail_coverage(research=research, discovery=discovery,
                             projection_options=projection_options)
    return project_coverage_view(
        coverage,
        {row["id"]: row["name"] for row in research["cities"]},
        {row["id"]: row["name"] for row in discovery["destinations"]},
    )


def project_coverage_view(coverage, base_names, destination_names):
    """Aggregate directed pairs using the canonical DATA24 denominator."""
    base_ids = coverage["base_ids"]
    destination_ids = coverage["destination_ids"]
    pairs = coverage["pairs"]
    by_base = {base: [] for base in base_ids}
    by_destination = {dest: [] for dest in destination_ids}
    for (base, dest), pair in pairs.items():
        category = pair["cell"]["category"]
        by_base[base].append((dest, category))
        by_destination[dest].append((base, category))

    def summarize(groups, names, counterpart_names):
        result = []
        for ident, entries in groups.items():
            result.append({
                "id": ident, "name": names[ident],
                **coverage_counts(category for _, category in entries),
                "missing_names": sorted(
                    (counterpart_names[key] for key, category in entries
                     if category == "no_time"), key=str.casefold),
            })
        return sorted(result, key=lambda row: row["name"].casefold())

    priority = set(RESEARCH_BASE_IDS).intersection(base_ids)
    return {
        "base_count": len(base_ids),
        "destination_count": len(destination_ids),
        "global": dict(coverage["global"]),
        "priority": coverage_counts(
            category for base in priority for _, category in by_base[base]),
        "priority_ids": sorted(priority),
        "bases": summarize(by_base, base_names, destination_names),
        "destinations": summarize(by_destination, destination_names, base_names),
    }
