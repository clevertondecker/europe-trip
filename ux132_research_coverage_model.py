"""Read-only presentation of DATA24 rail coverage; no recommendation logic."""
from copy import deepcopy
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
        result.append({
            "base_id": base, "destination_id": dest,
            "origin": names_b[base], "destination": names_d[dest],
            "category": category, "label": cell["label"],
            **_documentary_detail(cell, raw),
        })
    counterpart = "destination" if axis == "bases" else "origin"
    return sorted(result, key=lambda r: (_search_key(r[counterpart]),
                                         r["base_id"], r["destination_id"]))


def _https(url):
    return url if isinstance(url, str) and url.startswith("https://") else None


def _documentary_detail(cell, raw):
    """Bind metadata to the already-selected canonical minimum, not to another source."""
    category = cell["category"]
    timed = category in ("historical", "reference_only")
    detail = {
        "minimum": cell.get("display_min") if timed else None,
        "source_url": None, "source_date": None, "station_caveat": None,
        "notes": None, "observations": [], "alternative": None,
        "variation": False,
    }
    if not timed:
        return detail
    observations = deepcopy(raw.get("observations", []))
    detail["variation"] = bool(cell.get("legacy_divergent_sources")
                               or cell.get("reference_differs_from_legacy"))
    if category == "reference_only":
        # The overlay already selected by decorate_comparison owns these fields.
        detail.update(source_url=_https(cell.get("source_url")),
                      source_date=cell.get("gap_checked_at") or cell.get("checked_at"),
                      station_caveat=cell.get("station_caveat"),
                      notes=cell.get("evidence_notes"), observations=observations)
        return detail

    # Historical source is the canonical row's primary observation. Match its
    # full provenance, not just the URL (which can contain several services).
    detail.update(source_url=_https(raw.get("source_url")),
                  source_date=raw.get("source_date"))
    primary = next((obs for obs in observations
                    if obs.get("source_url") == raw.get("source_url")
                    and obs.get("evidence_date") == raw.get("source_date")
                    and obs.get("source_dataset") == raw.get("source_dataset")
                    and obs.get("minimum_oneway_min") == detail["minimum"]), None)
    if primary is not None:
        detail["notes"] = primary.get("notes")
        origin = primary.get("origin_station")
        destination = primary.get("destination_station")
        if origin or destination:
            detail["station_caveat"] = (
                f'Estações registradas nesta observação: {origin or "origem não informada"}'
                f' → {destination or "destino não informado"}.')
        observations.remove(primary)
    detail["observations"] = observations
    # ROUTES7 can coexist with historical precedence. Only corroborated minima
    # are shown as alternatives; unreproduced snapshots are not researched times.
    if (cell.get("reference_display_allowed") and cell.get("fastest_min") is not None
            and _https(cell.get("source_url")) and cell.get("checked_at")):
        detail["alternative"] = {
            "minimum": cell["fastest_min"],
            "source_url": _https(cell["source_url"]),
            "source_date": cell["checked_at"],
            "station_caveat": cell.get("station_caveat"),
            "notes": cell.get("evidence_notes"),
        }
    return detail
