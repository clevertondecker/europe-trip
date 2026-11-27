"""DATA26B1: dated advertised fares, separate from service-specific quotes."""
import json
from datetime import date
from pathlib import Path
from rail_evidence_unified_model import canonical_place, load_rail_evidence
from data26b_rail_fare_evidence_model import load_rail_fares

PATH = Path(__file__).resolve().parent / "data" / "data26b1_fare_references_2026_11.json"

def load_fare_references(path=PATH):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data["schema_version"] != 1:
        raise ValueError("Versão inválida")
    checked = date.fromisoformat(data["checked_at"])
    scope = data["scope"]
    universe = {(b, d) for b in scope["bases"] for d in scope["batch_destinations"]}
    seen = set()
    reference_pairs = {(r["origin_id"], r["destination_id"]) for r in data["references"]}
    for row in data["references"] + data["gaps"]:
        pair = (row["origin_id"], row["destination_id"])
        slug = {"basel": "bale", "freiburg": "fribourg-en-brisgau", "luxembourg_city": "luxembourg", "bern": "berne", "bruges": "brugge"}.get(pair[1], pair[1])
        expected = "https://www.sncf-connect.com/train/trajet/" + pair[0] + "/" + slug
        if pair in reference_pairs:
            valid_source = row["source_url"] == expected
        else:
            reason = row.get("reason")
            valid_source = (row["source_url"] is None if reason in ("research_pending", "ambiguous_destination_wrong_country") else
                            row["source_url"] == expected if reason in ("no_numeric_fare_visible_in_consulted_snapshot", "no_usable_weekend_rail_fare_in_consulted_snapshot") else False)
        if pair not in universe or pair in seen or not valid_source:
            raise ValueError("Par ou fonte inválida/duplicada")
        seen.add(pair)
    if seen != universe:
        raise ValueError("Escopo incompleto")
    for row in data["references"]:
        if (type(row["amount_minor"]) is not int or row["amount_minor"] <= 0
                or row["currency"] != "EUR" or row["kind"] != "advertised_from"
                or type(row["passengers"]) is not int or row["passengers"] != 1
                or row["direction"] != "oneway" or row["fare_class"] != "second"
                or date.fromisoformat(row["travel_date"]) < checked
                or row["valid_for_2027"] is not False
                or any(row[k] is not None for k in ("discount_eligibility", "mandatory_fees_included", "availability", "service_id"))):
            raise ValueError("Referência indicativa inválida")
    return data

def fare_reference_coverage(data=None, legacy=None, quotes=None):
    data = load_fare_references() if data is None else data
    legacy = load_rail_evidence() if legacy is None else legacy
    quotes = load_rail_fares() if quotes is None else quotes
    scope = data["scope"]
    universe = {(canonical_place(b), canonical_place(d)) for b in scope["bases"] for d in scope["destinations"] if canonical_place(b) != canonical_place(d)}
    batch = {(canonical_place(b), canonical_place(d)) for b in scope["bases"] for d in scope["batch_destinations"]}
    previous = {(canonical_place(r["origin_id"]), canonical_place(r["destination_id"])) for r in legacy["observations"] if r.get("fare_from_eur_person_oneway") is not None and r.get("source_url")}
    added = {(canonical_place(r["origin_id"]), canonical_place(r["destination_id"])) for r in data["references"]}
    complete = {(r["outbound"]["origin_id"], r["outbound"]["destination_id"]) for r in quotes["records"] if r["scope"] == "roundtrip" and r["complete_documentation"]}
    def counts(pairs):
        return {"total": len(pairs), "legacy": len(previous & pairs),
                "with_references": len((previous | added) & pairs),
                "batch_references": len(added & pairs), "complete_roundtrip": len(complete & pairs)}
    return {"scope": counts(universe), "batch": counts(batch)}
