"""UX97: accessible HTML projection of the canonical UX87 evidence cells.

This module emits ONLY display markup. It neither selects a city nor estimates
missing rail times, cost, 2027 schedules or comparative winners.
"""
from __future__ import annotations

from formatting import html_safe as _safe

from rail_reference_projection_model import format_minutes

COUNTRY_FLAGS = {"França":"🇫🇷", "Alemanha":"🇩🇪", "Bélgica":"🇧🇪",
                 "Luxemburgo":"🇱🇺", "Países Baixos":"🇳🇱", "Suíça":"🇨🇭",
                 "Itália":"🇮🇹", "Holanda":"🇳🇱", "Áustria":"🇦🇹", "Espanha":"🇪🇸"}

def destination_country_label(name, country):
    flag=COUNTRY_FLAGS.get(country)
    return f"{flag} {name}" if flag else name


TIMED=frozenset(("historical","reference_only"))
LABELS={
    "historical":"Histórico",
    "reference_only":"Indicativo",
    "local":"Acesso local pendente",
    "no_time":"Sem tempo",
}


def _cell_html(cell: dict) -> str:
    kind=cell["category"]
    if kind not in LABELS:
        raise ValueError("Categoria documental desconhecida")
    value=cell.get("display_min")
    if kind in TIMED:
        if type(value) is not int or value<=0:
            raise ValueError("Tempo de ida inconsistente")
        time=("~" if kind=="reference_only" else "")+format_minutes(value)
        amount=f'<strong class="ux97-cell-time">{_safe(time)}</strong>'
    else:
        if value is not None:
            raise ValueError("Categoria sem tempo não pode exibir duração")
        amount=""
    notes=(
        bool(cell.get("legacy_divergent_sources"))
        or bool(cell.get("station_caveat"))
        or bool(cell.get("evidence_notes"))
        or cell.get("station_comparability")=="city_level_ambiguous"
    )
    details=_safe(cell.get("label") or LABELS[kind])
    qualifiers=[]
    if cell.get("station_caveat"):
        qualifiers.append("Estações: "+str(cell["station_caveat"]))
    if cell.get("evidence_notes"):
        qualifiers.append("Observação: "+str(cell["evidence_notes"]))
    if cell.get("legacy_divergent_sources"):
        qualifiers.append("Existem referências divergentes para este trajeto")
    if cell.get("station_comparability")=="city_level_ambiguous":
        qualifiers.append("Comparabilidade das estações ainda não confirmada")
    # The visible icon is decorative: screen readers receive the actual caveats
    # within the table cell, not only a generic tooltip or separate expander.
    note=(
        '<span class="ux97-cell-note" aria-hidden="true">ⓘ</span>'
        '<span class="ux97-sr-only">Ressalvas: '
        +_safe("; ".join(qualifiers) if qualifiers else
               "Há ressalvas documentais. Consulte as fontes abaixo")
        +'.</span>'
    ) if notes else ""
    return (
        '<div class="ux97-cell" title="'+details+'">'
        +amount+f'<span class="ux97-status ux97-status--{kind}">'
        +_safe(LABELS[kind])+'</span>'+note+'</div>'
    )


def selected_matrix_html(projection: dict) -> str:
    """Same real destinations × the 2–5 canonical selected bases."""
    bases=projection["base_ids"]
    if not 2<=len(bases)<=5:
        raise ValueError("A matriz requer duas a cinco bases")
    rows=projection["destinations"]
    cells=projection["cells"]
    expected={(base,d["id"]) for base in bases for d in rows}
    if set(cells)!=expected:
        raise ValueError("Matriz não corresponde ao escopo confirmado")
    # Keep roughly 170 px per city; smaller viewports scroll the existing
    # accessible region instead of squeezing five cities into unreadable cells.
    min_table_width=max(520,160+170*len(bases))
    headers=''.join(
        f'<th scope="col">{_safe(projection["names"][base])}</th>'
        for base in bases)
    body=[]
    for destination in rows:
        star=('<span class="ux97-star" aria-label="Imperdível">★ </span>'
              if destination["priority"]=="must_visit" else "")
        cells_html=''.join(
            f'<td>{_cell_html(cells[(base,destination["id"])])}</td>'
            for base in bases)
        body.append(
            '<tr><th scope="row" class="ux97-destination">'
            +star+_safe(destination_country_label(destination["name"],destination.get("country")))+'</th>'+cells_html+'</tr>')
    return (
        '<div class="ux97-panel"><div class="ux97-section-title">'
        'Tempos de ida por destino</div>'
        '<p class="ux97-subtle">Mesmos destinos e mesmas categorias de evidência. '
        'Sem estimativa de retorno ou duração porta a porta.</p>'
        '<div class="ux97-scroll" role="region" tabindex="0" '
        'aria-label="Matriz da comparação de cidades selecionadas">'
        '<table class="ux97-table" style="min-width:'+str(min_table_width)+
        'px"><thead><tr><th scope="col">Destino</th>'
        +headers+'</tr></thead><tbody>'
        +''.join(body)+'</tbody></table></div>'
        '<p class="ux97-footnote">Histórico = registro anterior; Indicativo = '
        'referência não confirmada; acesso local e tempos ausentes são '
        'pendências, não inviabilidade. ⓘ Indica ressalva consultável nas fontes.'
        '</p></div>'
    )


def summary_panel_html(projection: dict) -> str:
    """Counts are documentary facts, never weights, ranks or cost claims."""
    bases=projection["base_ids"]
    total=len(projection["destinations"])
    common=len(projection["common_timed_destination_ids"])
    counts=projection["counts"]
    covered=sum(counts[base].get("historical",0)+
                counts[base].get("reference_only",0) for base in bases)
    possible=total*len(bases)
    local=sum(counts[base].get("local",0) for base in bases)
    missing=sum(counts[base].get("no_time",0) for base in bases)
    return (
        '<div class="ux97-panel"><div class="ux97-section-title">'
        'Resumo da comparação</div>'
        '<p class="ux97-subtle">Cobertura da pesquisa, não classificação '
        'das cidades.</p><div class="ux97-metrics">'
        f'<div class="ux97-metric"><strong>{common} / {total}</strong>'
        '<span>Destinos com ida pesquisada em todas as bases selecionadas</span></div>'
        f'<div class="ux97-metric"><strong>{covered} / {possible}</strong>'
        '<span>Referências de tempo existentes no escopo</span></div>'
        f'<div class="ux97-metric"><strong>{local}</strong>'
        '<span>Acessos locais pendentes</span></div>'
        f'<div class="ux97-metric"><strong>{missing}</strong>'
        '<span>Tempos não pesquisados</span></div></div>'
        '<div class="ux97-alert"><strong>Ainda falta verificar</strong><br>'
        'Retorno, frequência, última milha, hospedagem e horários de 2027.'
        '</div><p class="ux97-footnote">'
        'Não é possível indicar a melhor base ou o menor custo '
        'apenas com esta cobertura documental.</p></div>'
    )
