"""UX132C2: read-only documentary coverage of the audited D-004 bases."""
from base_research_expanded_model import load_research
from five_base_comparison_model import load_five_base_evidence
from data24_d004_audit_model import build_living_evidence, living_counts
from ux132_coverage_shared import search_key

INDICATORS = (
    ("Moradia", "Amostra histórica", "with_historical_housing"),
    ("Moradia", "Contador histórico: 3 ou mais cotações elegíveis declaradas", "with_three_verified_quotes"),
    ("Vida cotidiana", "Restaurante para dois (histórico)", "with_restaurant"),
    ("Vida cotidiana", "Passe urbano (histórico)", "with_urban_pass"),
    ("Vida cotidiana", "Cesta local completa comparável", "with_local_basket"),
    ("Clima", "Normais de setembro a novembro", "with_climate"),
    ("Trabalho remoto", "Coworking pesquisado (histórico)", "with_coworking"),
    ("Trabalho remoto", "Internet residencial confirmada para 2027", "with_residential_internet"),
)
PRIORITY = "priority"
ALL = "all"


def build_living_view(*, research=None, five=None):
    research = load_research(include_candidates=True) if research is None else research
    five = load_five_base_evidence() if five is None else five
    view = build_living_evidence(research, five)
    view["base_names"] = {r["id"]: r["name"] for r in research["cities"]}
    return view


def scope_membership(view):
    """Distinguish scope approval from evidence coverage; never invent empty rows."""
    approved = set(view["scope"]["approved_research_base_ids"])
    audited = {r["id"] for r in view["rows"]} & set(view["scope"]["descriptive_ids"])
    names = view.get("base_names", {})
    def describe(ids):
        return sorted(({"id": ident, "name": names.get(ident, ident)} for ident in ids),
                      key=lambda r: (search_key(r["name"]), r["id"]))
    return {"priority_audited": describe(approved & audited),
            "priority_unaudited": describe(approved - audited),
            "additional_audited": describe(audited - approved)}


def complementary_coworking(remote):
    """Compare only equivalent documented content, not provider name alone.

    Same provider with different price, modality, hours, notes or source is
    a distinct observation. Keep both original records unmodified.
    """
    primary, extra = remote.get("coworking"), remote.get("pack_reference")
    if not extra:
        return None
    if primary:
        fields = (("name", "name"), ("price_eur", "price_eur_2026"),
                  ("price_basis", "price_basis"), ("source_url", "source_url"),
                  ("source_type", "source_type"), ("schedule", "hours"), ("note", "limitations"))
        primary_date = primary.get("observed_at") or primary.get("checked_at")
        extra_date = extra.get("observed_at") or extra.get("checked_at")
        if primary_date == extra_date and all(primary.get(a) == extra.get(b) for a, b in fields):
            return None
    return extra


def scope_rows(view, scope=PRIORITY):
    if scope not in (PRIORITY, ALL):
        raise ValueError("Recorte não reconhecido")
    ids = set(view["scope"]["approved_research_base_ids"]
              if scope == PRIORITY else view["scope"]["descriptive_ids"])
    return sorted((r for r in view["rows"] if r["id"] in ids),
                  key=lambda r: (search_key(r["name"]), r["id"]))


def scope_counts(view, scope=PRIORITY):
    return living_counts(scope_rows(view, scope))


def indicator_rows(counts):
    n = counts["bases"]
    return [{"domain": domain, "label": label, "key": key, "count": counts[key],
             "total": n, "fraction": counts[key] / n if n else None}
            for domain, label, key in INDICATORS]


def city_detail(view, ident):
    return next((r for r in view["rows"] if r["id"] == ident), None)


def compact_rows(rows):
    """Documentary status only, without estimating missing costs or ranking."""
    result = []
    for row in rows:
        h, d, w = (row[k] for k in ("housing", "daily_life", "remote_work"))
        result.append({
            "id": row["id"], "name": row["name"],
            "historical_offers": h["summary"]["count"],
            "declared_quotes": h["overview"]["available_for_56_to_60_nights_2027"],
            "restaurant": d["restaurant_eur_two"] is not None,
            "urban_pass": d["urban_pass"] is not None,
            "local_basket": d["comparable_local_basket_eur"] is not None,
            "climate": (d["climate"] or {}).get("months_9_10_11") is not None,
            "coworking": w["coworking"] is not None,
            "internet_2027": w["residential_internet_2027"],
        })
    return result
