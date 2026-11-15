"""Unified, read-only travel scenarios reconciled to the currently displayed budget.

No quotes are inferred. Drive components win when live; snapshot fallback is explicit.
"""
from __future__ import annotations
from math import isfinite
from finance_lifestyle import FRENCH_BUDGET
from money_units import money_delta

PARTS = ("rent", "groceries", "dining", "transport", "excursions")
LIVE_MATCH = {
    "rent": "França · aluguel mobiliado",
    "groceries": "França · supermercado",
    "dining": "França · bares e restaurantes",
    "transport": "França · transporte urbano",
    "excursions": "França · passeios e viagens",
}

def resolve_french_budget(scenario: dict, source_live: bool) -> dict:
    sid = scenario["id"]
    known = {row["name"]: float(row["amount"]) for row in scenario["components"]}
    if source_live:
        missing = [label for label in LIVE_MATCH.values() if label not in known]
        if missing:
            raise ValueError("Componentes franceses ausentes da planilha sincronizada: " + ", ".join(missing))
        amounts = {key: known[title] for key, title in LIVE_MATCH.items()}
        source = "drive"
    else:
        amounts = {key: float(FRENCH_BUDGET[sid][key]) for key in PARTS}
        source = "snapshot_2026"
    expected_days = max(1, int(scenario["days"]) - 10)
    gap = sum(amounts.values())
    if source_live:
        french_total = gap
        if gap <= 0:
            raise ValueError("Despesas da França não podem ser nulas")
    else:
        french_total = gap
    return {"amounts": amounts, "source": source, "french_days": expected_days,
            "france_subtotal": french_total}

def scenario_total(scenario: dict, budget: dict, *,
                   french_days: int, outings_weekly: float, outing_couple_eur: float,
                   fx_brl_per_eur: float, rent_override_eur_month: float | None = None,
                   flight_delta_brl: float = 0, excursions_delta_brl: float = 0,
                   local_transport_delta_brl: float = 0, rent_delta_brl: float = 0) -> dict:
    """Replace already budgeted subcategories, then add only other true deltas."""
    if not 30 <= french_days <= 100:
        raise ValueError("Estadia na França fora do intervalo de simulação")
    required_nonnegative=[outings_weekly,outing_couple_eur,fx_brl_per_eur]
    if rent_override_eur_month is not None:
        required_nonnegative.append(rent_override_eur_month)
    if any(not isinstance(v,(int,float)) or not isfinite(v) or v<0
           for v in required_nonnegative):
        raise ValueError("Parâmetros de consumo e câmbio devem ser não negativos e finitos")
    # Deltas describe signed changes: a cheaper flight or lower rent is a saving.
    signed=(flight_delta_brl,excursions_delta_brl,
            local_transport_delta_brl,rent_delta_brl)
    for adjustment in signed:
        money_delta(adjustment)
    if outings_weekly>7 or fx_brl_per_eur<=0:
        raise ValueError("Frequência ou câmbio inválidos")
    original = budget["amounts"]
    ratio = french_days / budget["french_days"]
    new_items = {
        "groceries": original["groceries"] * ratio,
        "transport": original["transport"] * ratio + local_transport_delta_brl,
        "excursions": original["excursions"] * ratio + excursions_delta_brl,
        "dining": (french_days / 7) * outings_weekly * outing_couple_eur * fx_brl_per_eur,
        "rent": (original["rent"] * ratio if rent_override_eur_month is None else
                 rent_override_eur_month * (french_days/30) * fx_brl_per_eur),
    }
    new_items["rent"] += rent_delta_brl
    # A negative delta is valid only if the *resulting* expense remains valid.
    if any(not isfinite(float(v)) or float(v)<0 for v in new_items.values()):
        raise ValueError("A economia excede a despesa desta categoria")
    changed = sum(new_items.values()) - sum(original.values())
    projected = round(scenario["reported_total_brl"] + changed + flight_delta_brl, 2)
    if not isfinite(projected) or projected<0:
        raise ValueError("O total da viagem não pode ser negativo")
    margin = round(scenario["cap_brl"] - projected, 2)
    reserve = scenario["emergency_reserve_brl"]
    if margin < 0: status = "acima_do_teto"
    elif margin < scenario["cap_brl"] * .05: status = "apertado"
    else: status = "margem_condicional"
    return {
        "total": projected, "margin": margin, "status": status,
        "reserve_already_in_total": reserve,
        "new_components": {k: round(v,2) for k,v in new_items.items()},
        "deltas": {k:round(new_items[k]-original[k],2) for k in PARTS},
        "flight_delta": flight_delta_brl, "source": budget["source"],
        "budget_fraction": round(projected/scenario["cap_brl"], 4),
        "days":french_days,
    }
