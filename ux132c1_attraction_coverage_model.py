"""UX132C1 read-only presentation of the canonical DATA24 attraction inventory."""
from collections import defaultdict

from data24_audit_model import attraction_inventory, attraction_counts
from attractions_model import load_attractions
from data23_france_candidates_model import load_data23
from dq32_macro_opportunities_model import load_macro_tourism
from dq30_walking_access_model import load_walking_access
from trip01_supplemental_discovery import build_exploration_discovery
from ux132_research_coverage_model import _search_key

# key, label, denominator, missing key (None means not a gap metric)
INDICATORS = (
    ("destinations_with_attractions", "Destinos com atrações catalogadas", "destinations"),
    ("destinations_with_attributed_photo", "Destinos com foto contextual atribuída", "destinations"),
    ("described", "Atrações com descrição", "attractions"),
    ("editorial_duration", "Duração editorial documentada", "attractions"),
    ("ticket_published", "Ingresso com preço publicado", "attractions"),
    ("ticket_not_applicable", "Ingresso não aplicável", "attractions"),
    ("ticket_unknown", "Ingresso desconhecido", "attractions"),
    ("attraction_photo_attributed", "Foto própria atribuída", "attractions"),
    ("station_access_documented", "Acesso de estação documentado", "attractions"),
)
GAP_OPTIONS = {
    "Todas as lacunas": "all",
    "Destinos sem atrações": "catalog",
    "Foto contextual do destino": "context_photo",
    "Descrição da atração": "described",
    "Duração editorial": "editorial_duration",
    "Ingresso desconhecido": "ticket_unknown",
    "Foto própria da atração": "attraction_photo_attributed",
    "Acesso a partir da estação": "station_access_documented",
}
SORT_OPTIONS = ("Nome", "Mais pendências no filtro")


def build_attraction_view(*, discovery=None):
    discovery = build_exploration_discovery() if discovery is None else discovery
    inventory = attraction_inventory(discovery, load_attractions(), load_data23(),
                                     load_macro_tourism(), load_walking_access())
    return project_attraction_view(inventory)


def project_attraction_view(inventory):
    grouped = defaultdict(list)
    for attr in inventory["rows"]:
        grouped[attr["destination_id"]].append(attr)
    destinations = []
    for dest in inventory["destinations"]:
        rows = sorted(grouped[dest["id"]], key=lambda r: (_search_key(r["name"]), r["id"]))
        counts = attraction_counts([dest], rows)
        if counts["attractions"] != dest["attractions"]:
            raise ValueError("Inventário de atrações inconsistente")
        destinations.append({"id": dest["id"], "name": dest["name"],
                             "counts": counts, "rows": rows, "destination": dest})
    return {"counts": inventory["counts"],
            "destinations": sorted(destinations, key=lambda r: (_search_key(r["name"]), r["id"]))}


def indicator_rows(counts):
    """Ticket states are separate categories, not complements of one another."""
    rows = []
    for key, label, denominator in INDICATORS:
        total = counts[denominator]
        value = counts[key]
        rows.append({"key": key, "label": label, "documented": value, "total": total,
                     "fraction": value / total if total else None})
    return rows


def attraction_gaps(row):
    gaps = []
    if not row["description"]:
        gaps.append("described")
    if row["editorial_duration_min"] is None:
        gaps.append("editorial_duration")
    if row["ticket_status"] == "unknown":
        gaps.append("ticket_unknown")
    if not row["photo_attributed"]:
        gaps.append("attraction_photo_attributed")
    if not row["station_access"]:
        gaps.append("station_access_documented")
    return gaps


def gap_count(destination, gap):
    c = destination["counts"]
    if gap == "catalog":
        return int(c["attractions"] == 0)
    if gap == "context_photo":
        return 1 - c["destinations_with_attributed_photo"]
    if gap == "ticket_unknown":
        return c["ticket_unknown"]
    if gap == "all":
        # Number of distinct pending fields, not a quality score.
        return (gap_count(destination, "catalog") + gap_count(destination, "context_photo")
                + sum(len(attraction_gaps(row)) for row in destination["rows"]))
    if gap not in ("described", "editorial_duration", "attraction_photo_attributed",
                   "station_access_documented"):
        raise ValueError("Campo de pesquisa inválido")
    return c["attractions"] - c[gap]


def filter_destinations(view, *, query="", gap="all", gaps_only=False, sort="Nome"):
    if gap not in GAP_OPTIONS.values() or sort not in SORT_OPTIONS:
        raise ValueError("Filtro inválido")
    rows = [r for r in view["destinations"]
            if _search_key(query) in _search_key(r["name"])
            and (not gaps_only or gap_count(r, gap))]
    return sorted(rows, key=lambda r: ((-gap_count(r, gap) if sort != "Nome" else 0),
                                       _search_key(r["name"]), r["id"]))


def detail_rows(destination, *, gap="all", gaps_only=False):
    if gap not in GAP_OPTIONS.values():
        raise ValueError("Campo de pesquisa inválido")
    if not gaps_only or gap in ("catalog", "context_photo"):
        return list(destination["rows"])
    return [r for r in destination["rows"]
            if (bool(attraction_gaps(r)) if gap == "all" else gap in attraction_gaps(r))]
