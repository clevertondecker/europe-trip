"""REC04 financial input annotation: fees are expenses, deposits are refundable cash.

Only user-entered values are considered; unknown costs remain None. This
projection is never a city price quote, nor an official TripPlan update.
"""
from __future__ import annotations
from math import isfinite


def housing_cashflow(*,fx_brl_per_eur,fees_eur=None,refundable_deposit_eur=None,
                     projected_total_brl=None):
    if (type(fx_brl_per_eur) not in (float,int) or not isfinite(fx_brl_per_eur)
            or fx_brl_per_eur<=0):
        raise ValueError("Câmbio deve ser positivo e finito")
    for value in (fees_eur,refundable_deposit_eur):
        if value is not None and (type(value) not in (float,int)
                                  or not isfinite(value) or value<0):
            raise ValueError("Custos devem ser positivos ou desconhecidos")
    if projected_total_brl is not None and (
            type(projected_total_brl) not in (float,int)
            or not isfinite(projected_total_brl) or projected_total_brl<0):
        raise ValueError("Total inválido")
    fee=None if fees_eur is None else round(fees_eur*fx_brl_per_eur,2)
    deposit=None if refundable_deposit_eur is None else round(refundable_deposit_eur*fx_brl_per_eur,2)
    return {
        "one_time_fee_expense_brl":fee,
        "refundable_deposit_brl":deposit,
        # A deposit is tied-up cash, NOT added to the vacation expense.
        "initial_cash_reference_brl":(
            None if deposit is None or projected_total_brl is None else
            round(projected_total_brl+deposit,2)),
        "quote_2027_verified":False,
    }
