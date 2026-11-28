"""Pure presentation helpers; explicit options preserve historical UI formats."""
from html import escape

REQUIRED = object()

def _number(value, *, decimals, missing, grouping=True, decimal_comma=True,
            trim_zeros=False, absolute=False, suffix=False, symbol=""):
    if value is None and missing is not REQUIRED:
        return missing
    if absolute:
        value = abs(value)
    result = format(value, f"{',' if grouping else ''}.{decimals}f")
    if decimal_comma:
        result = result.translate(str.maketrans(",.", ".,"))
    if trim_zeros and decimals:
        ending = ("," if decimal_comma else ".") + "0" * decimals
        if result.endswith(ending):
            result = result[:-len(ending)]
    if suffix:
        return result + " " + symbol
    if not symbol:
        return result
    return f"{symbol} {result}"

def brl(value, *, decimals=2, missing, **options):
    return _number(value, decimals=decimals, missing=missing, symbol="R$", **options)

def eur(value, *, decimals=2, missing, **options):
    return _number(value, decimals=decimals, missing=missing, symbol="€", **options)

def chf(value, *, decimals=2, missing, **options):
    return _number(value, decimals=decimals, missing=missing, symbol="CHF", **options)

def amount(value, *, decimals=2, missing, symbol="", **options):
    return _number(value, decimals=decimals, missing=missing, symbol=symbol, **options)

def minutes(value, *, missing="não informado", always_hours=False, allow_zero=True,
            nonpositive_as_zero=False, strict=True):
    if value is None:
        return missing
    if nonpositive_as_zero and not value > 0:
        return "0 min"
    if strict and (type(value) is not int or value < (0 if allow_zero else 1)):
        raise ValueError("duration invalid")
    return f"{value // 60}h{value % 60:02d}" if always_hours or value >= 60 else f"{value} min"

def html_safe(value):
    return escape(str(value), quote=True)
