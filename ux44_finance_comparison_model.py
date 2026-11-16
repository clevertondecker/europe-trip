"""Pure, read-only partial comparison of equal-duration city living costs.

A category may be an explicitly supplied hypothesis or an observed reference;
missing values never become zero. No changes to approved budget or TripPlan.
"""
from __future__ import annotations
from decimal import Decimal,InvalidOperation,ROUND_HALF_UP

CATEGORIES=("housing","fees","utilities_internet","groceries",
            "dining","urban_transport","outings")
LABELS={"housing":"Moradia para o período","fees":"Taxas de estadia",
        "utilities_internet":"Contas e internet","groceries":"Supermercado",
        "dining":"Restaurantes","urban_transport":"Transporte urbano",
        "outings":"Passeios e transporte turístico"}
TRAVELERS=2

def _money(value):
    if value is None or value=="":
        return None
    try:
        result=Decimal(str(value))
    except (InvalidOperation,TypeError,ValueError) as exc:
        raise ValueError("Valor monetário inválido") from exc
    if not result.is_finite() or result<0:
        raise ValueError("Valor não pode ser negativo ou infinito")
    return result

def _round(value):
    return float(value.quantize(Decimal("0.01"),rounding=ROUND_HALF_UP))

def compare_city_costs(city_values:dict[str,dict],*,nights:int=60,
                       travelers:int=TRAVELERS,eur_fx:float|None=None)->dict:
    """Use amounts explicitly entered for the full stay, in EUR for the couple.

    Every input includes 'amount', 'basis' ('manual_hypothesis' or
    'historical_reference'), and optional 'source_url'.
    They are NOT added to the global budget. Deposit is locked cash, not cost.
    """
    if type(nights) is not int or not 1<=nights<=100:
        raise ValueError("Noites inválidas")
    if type(travelers) is not int or not 1<=travelers<=10:
        raise ValueError("Quantidade de viajantes inválida")
    fx=_money(eur_fx)
    if fx is not None and fx<=0:
        raise ValueError("Câmbio inválido")
    if not isinstance(city_values,dict) or not 1<=len(city_values)<=3:
        raise ValueError("Informe uma a três cidades")
    result={}
    for city,entries in city_values.items():
        if not isinstance(city,str) or not city or not isinstance(entries,dict):
            raise ValueError("Cidade ou premissas inválidas")
        if set(entries)-set(CATEGORIES)-{"deposit"}:
            raise ValueError("Categoria desconhecida")
        values={}
        subtotal=Decimal("0")
        known_count=0
        missing=[]
        for category in CATEGORIES:
            supplied=entries.get(category)
            if supplied is None:
                missing.append(category)
                values[category]=None
                continue
            if not isinstance(supplied,dict) or supplied.get("basis") not in (
                "manual_hypothesis","historical_reference"):
                raise ValueError("Premissa sem procedência")
            amount=_money(supplied.get("amount"))
            if amount is None:
                missing.append(category)
                values[category]=None
                continue
            if supplied["basis"]=="historical_reference" and not supplied.get("source_url"):
                raise ValueError("Referência histórica exige fonte")
            subtotal+=amount
            known_count+=1
            values[category]={"amount_eur":_round(amount),
                "basis":supplied["basis"],"source_url":supplied.get("source_url")}
        deposit=_money(entries.get("deposit"))
        result[city]={"known_subtotal_eur":_round(subtotal) if known_count else None,
                      "known_subtotal_brl":_round(subtotal*fx) if fx is not None and known_count else None,
                      "categories":values,"missing_categories":missing,
                      "deposit_cash_hold_eur":_round(deposit) if deposit is not None else None,
                      "complete_cost_eur":None,
                      "booking_confirmed_2027":False,
                      "return_travel_verified":False,
                      "status":"partial_reference_not_2027_quote"}
    return {"nights":nights,"travelers":travelers,"cities":result,
            "comparison_is_partial":True,
            "applied_to_official_budget":False,
            "fx_brl_per_eur":_round(fx) if fx is not None else None,
            "methodology":"Cada valor é para a estadia completa do casal. "
            "Subtotal não é custo total e não é somado ao orçamento global."}

def differences(comparison:dict)->list[dict]:
    """Compare ONLY shared known categories; no winner for complete trip."""
    cities=list(comparison["cities"])
    if len(cities)<2:
        return []
    shared=[c for c in CATEGORIES if all(
        comparison["cities"][k]["categories"][c] is not None for k in cities)]
    return [{"category":c,"amounts_eur":{
                name:comparison["cities"][name]["categories"][c]["amount_eur"]
                for name in cities}}
            for c in shared]
