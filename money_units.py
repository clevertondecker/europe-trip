"""Precise cross-currency budget helpers; never sum EUR and CHF as plain numbers."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP


def amount(value, *, strictly_positive:bool=False)->Decimal:
    try:
        number=Decimal(str(value))
    except (ValueError,TypeError,InvalidOperation) as exc:
        raise ValueError("Valor monetário inválido") from exc
    if not number.is_finite() or (number<=0 if strictly_positive else number<0):
        raise ValueError("Valor monetário não finito, nulo ou negativo")
    return number


def known_eur_equivalent(costs:dict,eur_brl:float,chf_brl:float)->float:
    """For *ranking only*: normalize CHF with an explicit exchange-rate ratio.

    The original EUR and CHF totals must remain separate on the UI.
    """
    euros=amount(costs.get("EUR",0))
    francs=amount(costs.get("CHF",0))
    eur_rate=amount(eur_brl,strictly_positive=True)
    chf_rate=amount(chf_brl,strictly_positive=True)
    return float(euros+(francs*chf_rate/eur_rate))


def known_brl(costs:dict,eur_brl:float,chf_brl:float)->float:
    rate_eur=amount(eur_brl,strictly_positive=True)
    rate_chf=amount(chf_brl,strictly_positive=True)
    result=(amount(costs.get("EUR",0))*rate_eur+
            amount(costs.get("CHF",0))*rate_chf)
    return float(result.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP))


def money_delta(value)->Decimal:
    """A financial adjustment can represent a saving, but must be finite."""
    try:
        number=Decimal(str(value))
    except (ValueError,TypeError,InvalidOperation) as exc:
        raise ValueError("Ajuste financeiro inválido") from exc
    if not number.is_finite():
        raise ValueError("Ajuste financeiro não finito")
    return number
