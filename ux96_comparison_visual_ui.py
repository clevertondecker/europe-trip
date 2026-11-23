"""UX96: presentation-only city comparison elements.

No external images or fabricated geography/prices. All values come from the
existing REC03A recommendation projection; card selection remains CHOICE.
"""
from __future__ import annotations

from html import escape


def _safe(value) -> str:
    return escape(str(value), quote=True)


def city_card_header(candidate: dict, city: dict, *, is_selected: bool = False,
                     is_official: bool = False) -> str:
    """A compact visual header; interactive controls remain native Streamlit."""
    name=_safe(city["name"])
    country=_safe(city["country"])
    counts=(
        ("historical",candidate["historical_count"],"Históricos"),
        ("indicative",candidate["indicative_count"],"Indicativos"),
        ("local",len(candidate["local_destination_ids"]),"Locais pendentes"),
        ("unknown",len(candidate["missing_destination_ids"]),"Sem tempo"),
    )
    badges="".join(
        f'<span class="ux96-badge ux96-badge--{kind}">'
        f'{int(number)} {_safe(label)}</span>'
        for kind,number,label in counts
    )
    flags=(
        ('<span class="ux96-city-flag ux96-city-flag--selected">Selecionada</span>' if is_selected else "")
        + ('<span class="ux96-city-flag ux96-city-flag--official">'
           'Base oficial</span>' if is_official else "")
    )
    return (
        '<div class="ux96-city-header" role="group" aria-label="Resumo da cidade-base">'
        '<div class="ux96-city-heading">'
        '<span class="ux96-city-icon" aria-hidden="true">▦</span>'
        '<div class="ux96-city-heading-copy">'
        f'<strong>{name}</strong><span>{country}</span>'
        '</div></div>'
        f'<div class="ux96-city-flags">{flags}</div>'
        f'<div class="ux96-badges" aria-label="Cobertura documental, não avaliação da cidade">{badges}</div>'
        '</div>'
    )


def selected_context(base_ids: list[str], cities: dict, destination_count: int) -> str:
    """A read-only view of CHOICE and already-confirmed scope; no selection UI."""
    names=[_safe(cities[base]["name"]) for base in base_ids if base in cities]
    chips=("".join(f'<span class="ux96-selected-chip">{name}</span>' for name in names)
           if names else '<span class="ux96-selection-empty">Selecione cidades nos cartões abaixo</span>')
    return (
        '<div class="ux96-selection-strip">'
        '<div class="ux96-selection-description"><span>SELEÇÃO ATUAL</span>'
        '<strong>Cidades para comparar</strong></div>'
        f'<div class="ux96-selection-chips">{chips}</div>'
        f'<div class="ux96-selection-total"><strong>{int(destination_count)}</strong>'
        ' destinos do escopo</div>'
        '</div>'
    )
