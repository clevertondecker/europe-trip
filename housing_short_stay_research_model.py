"""Short-stay housing evidence for two people, separate from the official plan.

Historical monthly asking prices are never 2027 56–60-night quotes.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import date
from urllib.parse import urlparse
from math import isfinite

from base_research_expanded_model import load_research


def housing_research_overview(*, research=None):
    research = research if research is not None else load_research()
    rows = []
    for city in research["cities"]:
        offers = city["housing_offers"]
        rows.append({
            "base_id": city["id"], "base_name": city["name"],
            "country": city["country"],
            "historical_offers": len(offers),
            "direct_listing_links": sum(bool(o.get("listing_url")) for o in offers),
            "two_adults_documented": sum(o.get("two_adults_confirmed") is True
                                         for o in offers),
            "available_for_56_to_60_nights_2027": city["eligible_2027_quotes"],
            "verified_internet": sum(o.get("internet_verified") is True
                                     for o in offers),
            "total_price_for_2027": None,
            "work_from_home_ready": False,
            "decision_ready": False,
        })
    return {
        "bases": rows, "base_count": len(rows),
        "historical_observation_count": sum(x["historical_offers"] for x in rows),
        "verified_2027_quote_count": sum(x["available_for_56_to_60_nights_2027"]
                                         for x in rows),
        "official_base_modified": False,
    }


def evaluate_short_stay_quote(quote: dict) -> dict:
    """Separate booking availability, habitability, budget and upfront deposit."""
    if not isinstance(quote, dict):
        raise ValueError("Cotação inválida")
    q = deepcopy(quote)
    required = ("base_id", "checkin", "checkout", "source_url", "checked_at",
                "currency", "travelers", "private_entire_unit", "furnished",
                "short_stay_allowed", "available_on_dates", "internet_verified",
                "work_space_verified", "kitchen_verified", "laundry_verified",
                "station_access_verified", "mandatory_fees_verified")
    if any(key not in q for key in required):
        raise ValueError("Contrato de cotação incompleto")
    research = load_research()
    if q["base_id"] not in {x["id"] for x in research["cities"]}:
        raise ValueError("Base não cadastrada")
    try:
        checkin = date.fromisoformat(q["checkin"])
        checkout = date.fromisoformat(q["checkout"])
        date.fromisoformat(q["checked_at"])
    except (ValueError, TypeError) as exc:
        raise ValueError("Data da cotação inválida") from exc
    nights = (checkout - checkin).days
    if checkin <= date(2027, 9, 4) or not 56 <= nights <= 60:
        raise ValueError("Temporada deve iniciar após casamento e durar 56–60 noites")
    if type(q["travelers"]) is not int or q["travelers"] != 2:
        raise ValueError("Pesquisa para exatamente dois adultos")
    if q["currency"] not in ("EUR", "CHF"):
        raise ValueError("Moeda não prevista")
    p = urlparse(q.get("source_url") or "")
    if p.scheme != "https" or not p.netloc:
        raise ValueError("Fonte de hospedagem deve ser HTTPS")
    for name in ("rent_total", "cleaning_fee", "service_fee", "mandatory_taxes",
                 "utilities_total", "refundable_deposit"):
        value = q.get(name)
        if value is not None and (
            type(value) not in (int, float) or not isfinite(value) or value < 0
        ):
            raise ValueError("Valor obrigatório inválido: " + name)
    missing = []
    checks = {
        "private_entire_unit": "unidade_privativa",
        "furnished": "mobiliada",
        "short_stay_allowed": "estadia_de_56_60_noites",
        "available_on_dates": "disponibilidade_nas_datas",
        "internet_verified": "internet",
        "work_space_verified": "espaco_para_trabalho",
        "kitchen_verified": "cozinha",
        "laundry_verified": "lavanderia",
        "station_access_verified": "acesso_real_estacao",
        "mandatory_fees_verified": "taxas_obrigatorias",
    }
    for field, label in checks.items():
        if q[field] is not True:
            missing.append(label)
    prices = ("rent_total", "cleaning_fee", "service_fee", "mandatory_taxes",
              "utilities_total")
    if any(q.get(key) is None for key in prices):
        missing.append("total_de_despesas_comprovado")
    if q.get("refundable_deposit") is None:
        missing.append("exposicao_de_caixa_caucao")
    expense = round(sum(q[k] for k in prices), 2) if all(
        q.get(k) is not None for k in prices) else None
    upfront = (round(expense + q["refundable_deposit"], 2)
               if expense is not None and q.get("refundable_deposit") is not None else None)
    return {
        "base_id": q["base_id"], "checkin": q["checkin"],
        "checkout": q["checkout"], "nights": nights,
        "currency": q["currency"],
        "expense_total": expense,
        "refundable_deposit_separate": q.get("refundable_deposit"),
        "upfront_cash_exposure": upfront,
        "research_missing": missing,
        "structurally_complete": not missing,
        # User-supplied flags are not independently verified by this pure model.
        # A human/live source check remains required before a housing decision.
        "decision_ready_for_dates": False,
        "requires_live_listing_recheck": True,
        "official_plan_modified": False,
    }


def same_dates_housing_candidates(quotes: list[dict]) -> dict:
    """Comparable quotes must share dates, adults and currency; no auto-winner."""
    outputs = [evaluate_short_stay_quote(x) for x in quotes]
    groups = {(x["checkin"], x["checkout"], x["currency"]) for x in outputs}
    return {
        "entries": outputs, "same_dates_and_currency": len(groups) <= 1,
        "all_ready": bool(outputs) and len(groups) == 1 and all(
            x["decision_ready_for_dates"] for x in outputs),
        "recommended_base": None,
    }
