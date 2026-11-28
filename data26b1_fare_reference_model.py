"""Indicative calendar references, not individual fare quotes."""
import json
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit
from rail_evidence_unified_model import canonical_place, load_rail_evidence
from data26b_rail_fare_evidence_model import load_rail_fares

PATH = Path(__file__).resolve().parent / "data" / "data26b1_fare_references_2026_11.json"
BASES = {"lille", "metz", "nancy", "mulhouse", "strasbourg"}
COUNTRIES = {"paris":"FR", "colmar":"FR", "reims":"FR", "dijon":"FR", "basel":"CH",
             "bern":"CH", "interlaken":"CH", "freiburg":"DE", "luxembourg_city":"LU",
             "brussels":"BE", "bruges_be":"BE", "amsterdam":"NL"}
DOMAINS = {"sncf-connect.com", "ter.sncf.com", "ouigo.com", "bahn.de", "sbb.ch", "cfl.lu",
           "belgiantrain.be", "b-europe.com", "nsinternational.com", "eurostar.com", "tgv-lyria.com"}
GAPS = {"research_pending", "source_no_price", "technical_failure", "ambiguous_destination",
        "insufficient_conditions", "non_rail_offer", "unavailable_on_date", "historical_not_reproduced"}
HISTORICAL = {"corroborated_price", "divergent_price", "not_reproduced", "not_reproduced_nonrail"}

def official_source(value):
    if not isinstance(value, str):
        return False
    try:
        p = urlsplit(value)
        host = p.hostname or ""
        return p.scheme == "https" and not p.username and not p.password and p.port in (None, 443) and any(host == d or host == "www." + d or (d == "bahn.de" and host == "int.bahn.de") or (d == "sbb.ch" and host == "network.sbb.ch") or (d == "b-europe.com" and host == "travel.b-europe.com") for d in DOMAINS)
    except ValueError:
        return False

def pair(row):
    return canonical_place(row["origin_id"]), canonical_place(row["destination_id"])

def _unique(values):
    normalized = [canonical_place(x) for x in values]
    if len(set(normalized)) != len(normalized):
        raise ValueError("Aliases duplicados no escopo")
    return set(normalized)

def _day(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Data inválida")
    return parsed

def validate_catalog_scope(bases, destinations):
    from base_research_expanded_model import load_research
    from trip01_supplemental_discovery import build_exploration_discovery
    countries = {"França":"FR", "Alemanha":"DE", "Suíça":"CH", "Luxemburgo":"LU",
                 "Bélgica":"BE", "Países Baixos":"NL", "Holanda":"NL"}
    base_catalog = {canonical_place(r["id"]): countries.get(r["country"]) for r in load_research(include_candidates=True)["cities"]}
    dest_catalog = {canonical_place(r["id"]): countries.get(r["country"]) for r in build_exploration_discovery()["destinations"]}
    # Bern is a historical research endpoint, not yet a tourism catalog entry.
    # SBB documents its Swiss identity; do not add it to discovery or DATA24.
    # https://www.sbb.ch/en/travel-information/stations/find-station/bern-station.html
    research_only = {"bern": "CH"}
    mismatches = []
    for b in sorted(bases):
        if base_catalog.get(b) != "FR":
            mismatches.append(f"base {b}: {base_catalog.get(b)}")
    for d in sorted(destinations):
        actual = dest_catalog.get(d, research_only.get(d))
        if actual != COUNTRIES[d]:
            mismatches.append(f"destino {d}: {actual} != {COUNTRIES[d]}")
    if mismatches:
        raise ValueError("Identidade ou país divergente do catálogo: " + "; ".join(mismatches))

def validate_review(row, checked):
    review = row["review"]
    if not isinstance(review, dict) or not official_source(review.get("source_url")):
        raise ValueError("Fonte de revisão inválida")
    research = _day(review["researched_at"])
    capture = review["source_capture_date"]
    if research > checked or research > _day(row["travel_date"]) or (capture is not None and _day(capture) > research):
        raise ValueError("Data de revisão inválida")
    amount = review["amount_minor"]
    if amount is not None and (type(amount) is not int or amount <= 0):
        raise ValueError("Preço revisado inválido")
    mode = review["transport_mode"]
    expected = ("not_reproduced_nonrail" if mode == "bus" else "not_reproduced" if amount is None else
                "corroborated_price" if amount == row["amount_minor"] else "divergent_price")
    if mode not in ("bus", "rail_label", "unknown") or row["status"] != expected or not review.get("note"):
        raise ValueError("Classificação de revisão inconsistente")

def validate_fare_references(data):
    if type(data["schema_version"]) is not int or data["schema_version"] != 2:
        raise ValueError("Versão inválida")
    checked = _day(data["checked_at"])
    scope = data["scope"]
    bases, destinations, batch = (_unique(scope[k]) for k in ("bases", "destinations", "batch_destinations"))
    if bases != BASES or destinations != set(COUNTRIES) or not batch or not batch <= destinations:
        raise ValueError("Escopo histórico inválido")
    validate_catalog_scope(bases, destinations)
    universe = {(b,d) for b in bases for d in batch}
    covered, seen, gaps = set(), set(), set()
    for r in data["references"]:
        p = pair(r)
        if p not in universe or r["origin_country"] != "FR" or r["destination_country"] != COUNTRIES[p[1]] or not official_source(r["source_url"]):
            raise ValueError("Identidade ou fonte inválida")
        travel, research = _day(r["travel_date"]), _day(r["researched_at"])
        capture = r["source_capture_date"]
        if research > travel or research > checked or (capture is not None and _day(capture) > research):
            raise ValueError("Datas inconsistentes")
        if (type(r["amount_minor"]) is not int or r["amount_minor"] <= 0
            or r["currency"] not in ("EUR", "CHF", "GBP") or r["kind"] != "advertised_from"
            or type(r["passengers"]) is not int or r["passengers"] != 1 or r["direction"] != "oneway"
            or r["valid_for_2027"] is not False or any(r[k] is not None for k in
               ("discount_eligibility", "mandatory_fees_included", "availability", "service_id"))
            or not r["evidence_note"] or not r["distributor"]):
            raise ValueError("Referência inválida")
        status = r["status"]
        if status == "observed_calendar":
            if r["transport_mode"] != "rail_label" or r["review"] is not None or r["fare_class"] not in (None,"second","first"):
                raise ValueError("Modalidade ou estado inválido")
            covered.add(p)
        elif status not in HISTORICAL or r["transport_mode"] != "unknown" or not r["review"]:
            raise ValueError("Histórico inválido")
        if status in HISTORICAL:
            validate_review(r, checked)
        key = (p, travel, research, capture, r["source_url"], r["amount_minor"], r["commercial_brand"],
               "historical" if status in HISTORICAL else "calendar")
        if key in seen:
            raise ValueError("Observação duplicada")
        seen.add(key)
    for g in data["gaps"]:
        p = pair(g)
        reason = g["reason"]
        if p not in universe or p in gaps or p in covered or reason not in GAPS:
            raise ValueError("Lacuna inválida")
        if reason == "research_pending":
            if g["researched_at"] is not None or g["source_url"] is not None:
                raise ValueError("Pesquisa pendente não pode ter consulta")
        elif not g["researched_at"] or _day(g["researched_at"]) > checked or (g["source_url"] is not None and not official_source(g["source_url"])):
            raise ValueError("Proveniência da lacuna inválida")
        gaps.add(p)
    if covered | gaps != universe:
        raise ValueError("Escopo incompleto")
    for check in data["alternative_source_checks"]:
        if pair(check) not in universe or not official_source(check["source_url"]) or _day(check["researched_at"]) > checked or not check["note"]:
            raise ValueError("Consulta alternativa inválida")
    return data

def load_fare_references(path=PATH):
    return validate_fare_references(json.loads(Path(path).read_text(encoding="utf-8")))

def fare_reference_coverage(data=None, legacy=None, quotes=None):
    data = load_fare_references() if data is None else data
    legacy = load_rail_evidence() if legacy is None else legacy
    quotes = load_rail_fares() if quotes is None else quotes
    scope = data["scope"]
    universe = {(canonical_place(b), canonical_place(d)) for b in scope["bases"] for d in scope["destinations"]}
    batch = {(canonical_place(b), canonical_place(d)) for b in scope["bases"] for d in scope["batch_destinations"]}
    previous = {pair(r) for r in legacy["observations"] if r.get("mode") == "rail"
                and type(r.get("fare_from_eur_person_oneway")) in (int,float)
                and r["fare_from_eur_person_oneway"] > 0 and official_source(r.get("source_url"))
                and r.get("fare_conditions") and r.get("evidence_date")}
    added = {pair(r) for r in data["references"] if r["status"] == "observed_calendar"}
    complete = {pair(r["outbound"]) for r in quotes["records"] if r["scope"] == "roundtrip" and r["complete_documentation"]}
    pending = {pair(g) for g in data.get("gaps", []) if g["reason"] == "research_pending"}
    consulted = {pair(g) for g in data.get("gaps", []) if g["reason"] != "research_pending"}
    def counts(pairs):
        return {"total":len(pairs), "legacy":len(previous & pairs), "with_references":len((previous | added) & pairs),
                "batch_references":len(added & pairs), "complete_roundtrip":len(complete & pairs),
                "pending":len(pending & pairs), "consulted_without_result":len(consulted & pairs)}
    return {"scope":counts(universe), "batch":counts(batch),
            "by_base":{b:counts({p for p in universe if p[0]==b}) for b in sorted({p[0] for p in universe})},
            "by_destination":{d:counts({p for p in universe if p[1]==d}) for d in sorted({p[1] for p in universe})}}
