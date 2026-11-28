"""Escaped, read-only UI fragments for REC03A's city cards."""
from __future__ import annotations

from formatting import html_safe as _safe
from collections.abc import Mapping


def scope_chips(destination_ids: list[str], names: Mapping[str, str]) -> str:
    chips = "".join(
        f'<span class="ux99-destination-chip">{_safe(names.get(k, k))}</span>'
        for k in destination_ids
    )
    return ('<div class="ux99-scope-strip" role="group" aria-label="Destinos confirmados para pesquisa">'
            '<div class="ux99-scope-label"><strong>Seus destinos</strong>'
            '<span>Escopo confirmado para pesquisa, não para o roteiro</span></div>'
            f'<div class="ux99-destination-chips">{chips}</div></div>')


def insight_panels(insights: Mapping) -> str:
    """Static HTML; native Streamlit owns every selection and action."""
    def panel(kind: str, heading: str, items: list[dict]) -> str:
        lines = "".join(f'<li>{_safe(item["text"])}</li>' for item in items[:2])
        return (f'<section class="ux99-insight ux99-insight--{kind}">'
                f'<h4>{_safe(heading)}</h4><ul>{lines}</ul></section>')
    return ('<div class="ux99-insights" aria-label="Vantagens e pontos de atenção documentais">'
            + (panel("pros", "Vantagens comparativas", insights["advantages"])
               if insights["advantages"] else "")
            + (panel("neutral", "O que já foi pesquisado", insights.get("documented", []))
               if insights.get("documented") else "")
            + (panel("neutral", "Evidências ainda insuficientes", insights.get("neutral", []))
               if insights.get("neutral") else "")
            + panel("cons", "Pontos de atenção", insights["cautions"])
            + '</div>')
