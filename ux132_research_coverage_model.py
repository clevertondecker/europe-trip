"""Read-only presentation of DATA24 rail coverage; no recommendation logic."""
from unicodedata import normalize, combining
from data24_coverage_model import coverage_counts, rail_coverage
from data25_priority_rail_model import RESEARCH_BASE_IDS
from base_research_expanded_model import load_research
from trip01_supplemental_discovery import build_exploration_discovery


def build_coverage_view(*, research=None, discovery=None, projection_options=None):
    research = load_research(include_candidates=True) if research is None else research
    discovery = build_exploration_discovery() if discovery is None else discovery
    coverage = rail_coverage(research=research, discovery=discovery,
                             projection_options=projection_options)
    view = project_coverage_view(
        coverage,
        {row["id"]: row["name"] for row in research["cities"]},
        {row["id"]: row["name"] for row in discovery["destinations"]},
    )
    # Retain this execution's public projection for on-demand detail; no new matrix.
    view["pairs"] = coverage["pairs"]
    return view


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


SORT_OPTIONS = ("Nome", "Mais lacunas", "Menor cobertura")
STATUS_OPTIONS = {
    "Sem tempo pesquisado": "no_time",
    "Histórico": "historical",
    "Indicativo": "reference_only",
    "Local": "local",
    "Todas": None,
}


def _search_key(value):
    return "".join(c for c in normalize("NFKD", value.casefold())
                   if not combining(c)).strip()


def filter_coverage_rows(rows, *, query="", gaps_only=False, sort="Nome"):
    """Presentation-only filters: never recompute denominators or rank bases."""
    if sort not in SORT_OPTIONS:
        raise ValueError("Ordenação inválida")
    query = _search_key(query)
    filtered = [row for row in rows if query in _search_key(row["name"])
                and (not gaps_only or row["missing"] > 0)]
    def key(row):
        name = _search_key(row["name"])
        if sort == "Mais lacunas":
            return (-row["missing"], name, row["id"])
        if sort == "Menor cobertura":
            fraction = row["fraction"]
            return (fraction is None, fraction if fraction is not None else 0,
                    name, row["id"])
        return (name, row["id"])
    return sorted(filtered, key=key)


def connection_rows(view, axis, ident, status="Sem tempo pesquisado"):
    """Reuse exact directed cells; only expand the selected city's references."""
    if axis not in ("bases", "destinations") or status not in STATUS_OPTIONS:
        raise ValueError("Recorte de conexões inválido")
    if ident not in {row["id"] for row in view[axis]}:
        raise ValueError("Cidade desconhecida")
    names_b = {row["id"]: row["name"] for row in view["bases"]}
    names_d = {row["id"]: row["name"] for row in view["destinations"]}
    category_filter = STATUS_OPTIONS[status]
    result = []
    for (base, dest), pair in view["pairs"].items():
        if (base if axis == "bases" else dest) != ident:
            continue
        cell, raw = pair["cell"], pair["row"]
        category = cell["category"]
        if category_filter is not None and category != category_filter:
            continue
        timed = category in ("historical", "reference_only")
        # An alternative reference must never supply the provenance for a
        # historical minimum. For indicative cells prefer the displayed source.
        if category == "historical":
            url, date = raw.get("source_url"), raw.get("source_date")
        elif category == "reference_only":
            url = cell.get("reference_source_url") or cell.get("source_url")
            date = cell.get("gap_checked_at") or cell.get("checked_at")
        else:
            url, date = None, None
        if not isinstance(url, str) or not url.startswith("https://"):
            url = None
        result.append({
            "base_id": base, "destination_id": dest,
            "origin": names_b[base], "destination": names_d[dest],
            "category": category, "label": cell["label"],
            "minimum": cell.get("display_min") if timed else None,
            "source_url": url, "source_date": date,
            "typical_label": cell.get("typical_label") if timed else None,
            "station_caveat": cell.get("station_caveat"),
            "notes": cell.get("evidence_notes"),
            "variation": bool(cell.get("legacy_divergent_sources")
                              or cell.get("reference_differs_from_legacy")),
        })
    counterpart = "destination" if axis == "bases" else "origin"
    return sorted(result, key=lambda r: (_search_key(r[counterpart]),
                                         r["base_id"], r["destination_id"]))
