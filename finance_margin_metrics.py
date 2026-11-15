"""Compare budget margin against known excursion spending without false savings.

All monetary inputs validated; unknown costs remain pending rather than zero-priced.
"""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
def _d(value):
    try:
        number=Decimal(str(value))
        if not number.is_finite() or number<0:raise ValueError("Invalid finance input")
        return number
    except (InvalidOperation,TypeError) as exc:raise ValueError("Invalid finance input") from exc
def _brl(v):
    return float(v.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP))
def calculate_excursion_margin(finance_projection:dict,known_costs:dict,
                               eur_fx:float,chf_fx:float,missing:list[str])->dict:
    allowance=_d(finance_projection["budget_excursions_allowance_brl"])
    global_margin=Decimal(str(finance_projection["result"]["margin"]))
    if not global_margin.is_finite():raise ValueError("Invalid margin")
    eur=_d(known_costs["EUR"]);chf=_d(known_costs["CHF"])
    fx_eur=_d(eur_fx);fx_chf=_d(chf_fx)
    if not fx_eur or not fx_chf:raise ValueError("FX cannot be zero")
    spend=eur*fx_eur+chf*fx_chf
    used=min(spend,allowance)
    surplus=max(Decimal("0"),spend-allowance)
    remainder=max(Decimal("0"),allowance-spend)
    return {"allowance_brl":_brl(allowance),
            "known_spend_brl":_brl(spend),
            "covered_known_brl":_brl(used),
            "known_allowance_remaining_brl":_brl(remainder),
            "known_overage_brl":_brl(surplus),
            "budget_margin_brl":_brl(global_margin),
            "pending_count":len(missing),
            "utilization_pct":round(float(spend/allowance*100),1) if allowance else (100.0 if spend else 0.0),
            "coverage_caveat":"Saldo nominal da provisão: não é economia garantida. "
                "Preços históricos e despesas ainda desconhecidas podem mudar o resultado."}
def compare_excursion_profiles(items:dict[str,dict])->list[dict]:
    return [{"profile":profile,
             "budget_margin_brl":metrics["budget_margin_brl"],
             "known_spend_brl":metrics["known_spend_brl"],
             "known_allowance_remaining_brl":metrics["known_allowance_remaining_brl"],
             "pending_count":metrics["pending_count"]}
             for profile,metrics in items.items()]
