"""DATA26A: individual housing observations, not live booking confirmations.

The historical D-004 audit is immutable. This contract records documentary
evidence separately; no JSON field can grant independent verification.
"""
from __future__ import annotations

from evidence_validation import is_https_url

import json
from collections import defaultdict
from copy import deepcopy
from datetime import date
from pathlib import Path

from base_research_expanded_model import load_research
from housing_short_stay_research_model import evaluate_short_stay_quote

PATH = Path(__file__).resolve().parent / "data" / "housing_quote_observations_2027.json"

CHECKS = (
    "private_entire_unit", "furnished", "short_stay_allowed",
    "available_on_dates", "internet_verified", "work_space_verified",
    "kitchen_verified", "laundry_verified", "station_access_verified",
    "mandatory_fees_verified",
)
PRICES = ("rent_total", "cleaning_fee", "service_fee", "mandatory_taxes",
          "utilities_total", "refundable_deposit")
QUOTE_FIELDS = {"base_id", "checkin", "checkout", "source_url", "checked_at",
                "currency", "travelers", *CHECKS, *PRICES}
RECORD_FIELDS = {"id", "listing_id", "quote", "evidence_url",
                 "contract_terms", "cancellation_terms"}


def _text(value):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip()


def _iso(value):
    if not isinstance(value, str):
        raise ValueError("Data de evidência inválida")
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Data deve usar AAAA-MM-DD")
    return parsed


def _validate_and_project(payload, research):
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "quotes"}:
        raise ValueError("Contrato de observações de moradia inválido")
    if type(payload["schema_version"]) is not int or payload["schema_version"] != 1:
        raise ValueError("Versão de observações de moradia desconhecida")
    if not isinstance(payload["quotes"], list):
        raise ValueError("Observações devem ser uma lista")
    cities = {r["id"]: r for r in research["cities"]}
    ids, listings, urls = set(), set(), set()
    output = []
    for record in payload["quotes"]:
        if not isinstance(record, dict) or set(record) != RECORD_FIELDS:
            raise ValueError("Campos de observação de moradia inválidos")
        ident, listing, q = record["id"], record["listing_id"], record["quote"]
        if not _text(ident) or not _text(listing) or ident in ids:
            raise ValueError("Identidade de observação ausente ou duplicada")
        if not isinstance(q, dict) or set(q) != QUOTE_FIELDS:
            raise ValueError("Campos da cotação inválidos; use null para desconhecido")
        if not _text(q["base_id"]) or q["base_id"] not in cities:
            raise ValueError("Cidade-base desconhecida")
        if not is_https_url(q["source_url"]) or not is_https_url(record["evidence_url"]):
            raise ValueError("Fonte individual e evidência documental devem usar HTTPS")
        # An evidence link describes a captured observation; it is not proof
        # that a provider still offers the accommodation at the recorded price.
        checkin, checkout, checked = map(_iso, (q["checkin"], q["checkout"], q["checked_at"]))
        if checkin.year != 2027 or checkout.year != 2027 or checked > checkin:
            raise ValueError("Cotação fora do período de 2027 ou consulta posterior ao início")
        for field in CHECKS:
            if q[field] is not None and type(q[field]) is not bool:
                raise ValueError("Condição deve ser true, false ou null: " + field)
        for field in ("contract_terms", "cancellation_terms"):
            if record[field] is not None and not _text(record[field]):
                raise ValueError("Condição textual inválida: " + field)
        # Same listing/date observation cannot inflate the sample, even with
        # another currency. Cross-provider aliasing requires explicit review.
        key = (listing.casefold(), q["checkin"], q["checkout"])
        url_key = (q["source_url"].split("#", 1)[0], q["checkin"], q["checkout"])
        if key in listings or url_key in urls:
            raise ValueError("Cotação duplicada para o mesmo imóvel e período")
        result = evaluate_short_stay_quote(q, research=research)
        ids.add(ident)
        listings.add(key)
        urls.add(url_key)
        missing = list(result["research_missing"])
        if record["contract_terms"] is None:
            missing.append("condicoes_do_contrato")
        if record["cancellation_terms"] is None:
            missing.append("condicoes_de_cancelamento")
        output.append({
            "id": ident, "listing_id": listing,
            "quote": deepcopy(q), "evidence_url": record["evidence_url"],
            "contract_terms": record["contract_terms"],
            "cancellation_terms": record["cancellation_terms"],
            "evaluation": result,
            "missing_requirements": missing,
            "documented_complete": not missing,
            "independently_verified": False,
        })
    return output


def validate_housing_observations(payload, *, research=None):
    research = load_research(include_candidates=True) if research is None else research
    _validate_and_project(payload, research)
    return deepcopy(payload)


def load_housing_observations(path=PATH, *, research=None):
    return validate_housing_observations(json.loads(Path(path).read_text(encoding="utf-8")),
                                         research=research)


def project_housing_observations(payload, *, research=None):
    research = load_research(include_candidates=True) if research is None else research
    records = _validate_and_project(payload, research)
    by_base = defaultdict(list)
    for record in records:
        by_base[record["quote"]["base_id"]].append(record)
    result = {}
    for ident, rows in sorted(by_base.items()):
        grouped = defaultdict(list)
        for record in rows:
            q = record["quote"]
            grouped[(q["checkin"], q["checkout"], q["currency"])].append(record)
        groups = []
        for (checkin, checkout, currency), items in sorted(grouped.items()):
            groups.append({
                "checkin": checkin, "checkout": checkout, "currency": currency,
                "documented": len(items),
                "complete_documentation": sum(x["documented_complete"] for x in items),
                "independently_verified": 0,
                "records": sorted(items, key=lambda r: r["id"]),
            })
        result[ident] = {
            "documented": len(rows),
            "complete_documentation": sum(x["documented_complete"] for x in rows),
            "largest_comparable_documented_group": max(g["complete_documentation"] for g in groups),
            "independently_verified": 0,
            "groups": groups,
        }
    return {"by_base": result, "documented": len(records),
            "independently_verified": 0, "official_plan_modified": False}
