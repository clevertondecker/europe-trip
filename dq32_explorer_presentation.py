"""Pure presentation projection for DQ3.2, independent of Streamlit and TripPlan.

Travel times remain integer minutes in domain data and are only formatted here.
A published one-way minimum is not a day trip, timetable or journey forecast.
"""
from __future__ import annotations


COUNTRY_FLAGS = {
    "França": "🇫🇷", "Alemanha": "🇩🇪", "Bélgica": "🇧🇪",
    "Luxemburgo": "🇱🇺", "Suíça": "🇨🇭", "Países Baixos": "🇳🇱",
}


def format_travel_minutes(minutes: int | None) -> str:
    if minutes is None:
        return "A pesquisar"
    if type(minutes) is not int or minutes < 0:
        raise ValueError("Travel duration must be nonnegative integer minutes")
    if minutes < 60:
        return f"{minutes} min"
    hours, rest = divmod(minutes, 60)
    return f"{hours}h{rest:02d}"


def one_way_minutes(row: dict) -> int | None:
    historical = row.get("minimum_train_oneway_min")
    if historical is not None:
        return historical
    return row.get("indicative_train_oneway_min")


def evidence_label(row: dict) -> str:
    if row.get("local"):
        return "Local · acesso a verificar"
    if row.get("minimum_train_oneway_min") is not None:
        return "Histórico"
    if row.get("indicative_train_oneway_min") is not None:
        return "Referência indicativa"
    return "Sem referência"


def evidence_source(row: dict) -> str | None:
    return (row.get("train_source_url") if row.get("minimum_train_oneway_min") is not None
            else row.get("indicative_source_url")
            if row.get("indicative_train_oneway_min") is not None else None)


def visible_destinations(rows: list[dict], *, countries: list[str] | None = None,
                         duration: str = "Todas", sort: str = "Menor tempo") -> list[dict]:
    """Filter by outbound *minimum*, not estimated excursion feasibility."""
    windows = {"Todas", "Até 1h", "1–2h", "2–4h", "Mais de 4h", "Sem referência"}
    orders = {"Menor tempo", "Mais atrações", "Nome A–Z"}
    if duration not in windows or sort not in orders:
        raise ValueError("Unsupported DQ3.2 filter")
    allowed = set(countries) if countries is not None else None
    result = []
    for entry in rows:
        if allowed is not None and entry["country"] not in allowed:
            continue
        minutes = one_way_minutes(entry)
        if duration == "Até 1h" and (minutes is None or minutes > 60):
            continue
        if duration == "1–2h" and (minutes is None or not 60 < minutes <= 120):
            continue
        if duration == "2–4h" and (minutes is None or not 120 < minutes <= 240):
            continue
        if duration == "Mais de 4h" and (minutes is None or minutes <= 240):
            continue
        if duration == "Sem referência" and (minutes is not None or entry.get("local")):
            continue
        result.append(entry)

    if sort == "Mais atrações":
        result.sort(key=lambda r: (-r["attraction_count"], r["name"]))
    elif sort == "Nome A–Z":
        result.sort(key=lambda r: r["name"])
    else:
        result.sort(key=lambda r: (
            one_way_minutes(r) is None,
            one_way_minutes(r) if one_way_minutes(r) is not None else float("inf"),
            r["name"],
        ))
    return result


def table_rows(rows: list[dict]) -> list[dict]:
    """Keep minutes for audit/sort while displaying human-readable duration."""
    return [{
        "Destino": r["name"],
        "País": r["country"],
        "Tempo de ida": format_travel_minutes(one_way_minutes(r))
            if one_way_minutes(r) is not None else
            ("Local" if r.get("local") else "A pesquisar"),
        "Atrações identificadas": r["attraction_count"],
        "Evidência": evidence_label(r),
        "Fonte": evidence_source(r),
        "Mínimo de ida (min)": one_way_minutes(r),
    } for r in rows]
