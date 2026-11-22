"""UX87 — read-only same-page evidence comparison for confirmed REC03A scope.

Uses canonical UX503 and ROUTES7 projections; CHOICE remains the only
comparison selection. No timetable, fare, score or official-plan mutations.
"""
from __future__ import annotations

from collections import Counter

import streamlit as st

from recommendation_scope_model import reconcile_scope
from routes7_comparison_projection import decorate_comparison, format_minutes
from ux503_destination_base_comparison_model import compare_wishlist_bases
from ux_shared_ui_presentation import section_heading

CATEGORIES = ("historical", "reference_only", "local", "no_time")
TIMED = ("historical", "reference_only")
LABELS = {
    "historical": "Dados históricos de ida",
    "reference_only": "Referências indicativas de ida",
    "local": "Acesso local a verificar",
    "no_time": "Sem tempo pesquisado",
}


def project_inline_comparison(interests, scope, base_ids, *, discovery, research,
                              rail=None, exploration=None, references=None,
                              gap_overlay=None):
    """Project selected bases against exactly the confirmed, current scope.

    The optional evidence arguments are injection seams for deterministic tests;
    production calls rely on the existing UX503/ROUTES7 sources and precedence.
    """
    checked = reconcile_scope(interests, scope, discovery)
    if checked["state"] != "ready" or checked["scope"] != scope:
        raise ValueError("O escopo mudou. Revise os destinos antes de comparar.")
    if (not isinstance(base_ids, list) or not 2 <= len(base_ids) <= 5
            or any(not isinstance(x, str) for x in base_ids)
            or len(base_ids) != len(set(base_ids))):
        raise ValueError("Selecione de duas a cinco cidades-base distintas.")
    raw = compare_wishlist_bases(
        interests, base_ids, discovery=discovery, research=research, rail=rail,
        exploration=exploration, visible_destination_ids=list(scope["destination_ids"]),
    )
    params = {}
    if references is not None:
        params["references"] = references
    if gap_overlay is not None:
        params["gap_overlay"] = gap_overlay
    display = decorate_comparison(raw, **params)
    cells = display["cells"]
    names = {s["base_id"]: s["base_name"] for s in raw["summaries"]}
    destinations = raw["destinations"]
    expected = {(base, d["id"]) for base in base_ids for d in destinations}
    if set(cells) != expected:
        raise ValueError("Matriz incompleta ou com destinos além do escopo.")
    counts, missing_must, table = {}, {}, []
    for base in base_ids:
        categories = [cells[(base, d["id"])]["category"] for d in destinations]
        if any(c not in CATEGORIES for c in categories):
            raise ValueError("Categoria de evidência desconhecida.")
        counts[base] = dict(Counter(categories))
        missing_must[base] = [d["name"] for d in destinations
                              if d["priority"] == "must_visit"
                              and cells[(base, d["id"])]["category"] == "no_time"]
    common = [d["id"] for d in destinations if all(
        cells[(base, d["id"])]["category"] in TIMED for base in base_ids)]
    for d in destinations:
        row = {"Destino": d["name"] + " · " + d["priority_label"]}
        for base in base_ids:
            cell = cells[(base, d["id"])]
            category = cell["category"]
            minutes = cell.get("display_min")
            if category in TIMED:
                if type(minutes) is not int or minutes <= 0:
                    raise ValueError("Tempo pesquisado inconsistente.")
                value = format_minutes(minutes)
                # Preserve the canonical evidence qualifier (including source
                # conflicts and station ambiguity) instead of flattening it.
                label = cell.get("label") or (
                    value + " · dado histórico" if category == "historical"
                    else "~" + value + " · referência indicativa"
                )
            else:
                if minutes is not None:
                    raise ValueError("Categoria sem tempo não pode ter minutos.")
                label = ("Acesso local a verificar" if category == "local"
                         else "Sem tempo pesquisado")
            row[names[base]] = label
        table.append(row)
    return {
        "base_ids": list(base_ids), "names": names, "destinations": destinations,
        "cells": cells, "counts": counts, "must_visit_without_time": missing_must,
        "common_timed_destination_ids": common, "table": table,
        "official_plan_modified": False, "ranking_available": False,
    }


def render_inline_comparison(interests, scope, selected, *, discovery, research):
    """Compact interpretation followed by an optional matrix, never another form."""
    if not 2 <= len(selected) <= 5:
        return
    try:
        projection = project_inline_comparison(
            interests, scope, selected, discovery=discovery, research=research)
    except (ValueError, KeyError, TypeError, ImportError, OSError):
        st.warning("Não foi possível comparar essas cidades com os dados atuais. "
                   "Revise o escopo ou tente novamente.")
        return
    st.markdown(section_heading(
        "SUA COMPARAÇÃO", "Comparando " +
        ", ".join(projection["names"][base] for base in selected),
        "Referências de ida para os mesmos destinos; não são deslocamentos totais nem horários de 2027.",
        variant="compact",
    ), unsafe_allow_html=True)
    total = len(projection["destinations"])
    # Compare the same dimension across all selected bases before showing
    # per-city details. Text wraps naturally for 2–5 cities and small screens.
    st.markdown("**O que está documentado em cada cidade**")
    st.caption("Cobertura da pesquisa, não qualidade da logística nem indicação de vencedora.")
    dimensions = (
        ("historical", "Trajetos com dados históricos"),
        ("reference_only", "Referências indicativas"),
        ("local", "Acessos locais ainda não verificados"),
        ("no_time", "Destinos sem tempo pesquisado"),
    )
    for category, title in dimensions:
        comparison = " · ".join(
            f'{projection["names"][base]}: {projection["counts"][base].get(category, 0)}'
            for base in selected
        )
        st.write(f"**{title}:** {comparison}")

    st.markdown("**Destinos imperdíveis: o que sabemos e o que falta**")
    must_visit = [d for d in projection["destinations"]
                  if d["priority"] == "must_visit"]
    if not must_visit:
        st.caption("Nenhum destino está marcado como imperdível neste escopo.")
    else:
        for base in selected:
            documented = [
                d["name"] for d in must_visit
                if projection["cells"][(base, d["id"])]["category"] in TIMED
            ]
            local = [
                d["name"] for d in must_visit
                if projection["cells"][(base, d["id"])]["category"] == "local"
            ]
            missing = projection["must_visit_without_time"][base]
            st.write("**" + projection["names"][base] + "**")
            st.caption("Referências de ida: " + (", ".join(documented) or "nenhuma")
                       + " · Sem tempo pesquisado: " + (", ".join(missing) or "nenhum")
                       + " · Acesso local pendente: " + (", ".join(local) or "nenhum"))

    shared = len(projection["common_timed_destination_ids"])
    if shared == 0:
        st.warning("Ainda não temos dados suficientes para comparar essas cidades "
                   "de forma conclusiva. Nenhum destino tem tempo pesquisado em "
                   "todas as cidades selecionadas.")
    elif shared < total:
        comparable = [d["name"] for d in projection["destinations"]
                      if d["id"] in projection["common_timed_destination_ids"]]
        st.info(f"Há referências de ida para os mesmos {shared} de {total} destinos: "
                + ", ".join(comparable)
                + ". Os demais ainda não permitem comparação direta de tempos.")
    else:
        st.info(f"Os {total} destinos possuem referências de ida em todas as cidades, "
                "mas isso não comprova qual tem melhor logística.")
    st.caption("Ausência de tempo pesquisado não significa rota inviável. "
               "Retorno ferroviário, frequência, última milha, hospedagem e "
               "preços de 2027 ainda precisam de confirmação. "
               "Mínimos de ida não são duração total da viagem.")

    if st.checkbox("Ver matriz de trajetos por destino", key="rec03a_inline_matrix"):
        st.dataframe(projection["table"], hide_index=True, use_container_width=True)
        if st.checkbox("Consultar fontes e lacunas da matriz",
                       key="rec03a_inline_sources"):
            for d in projection["destinations"]:
                st.markdown("**" + d["name"] + "**")
                for base in selected:
                    cell = projection["cells"][(base, d["id"])]
                    st.caption(projection["names"][base] + " · " +
                               LABELS[cell["category"]])
                    # Keep materially relevant caveats next to the source.
                    # The underlying rail projection remains authoritative.
                    for field, prefix in (
                        ("station_caveat", "Estações"),
                        ("evidence_notes", "Observação"),
                    ):
                        if cell.get(field):
                            st.caption(prefix + ": " + str(cell[field]))
                    checked_at = cell.get("gap_checked_at")
                    if checked_at:
                        st.caption("Fonte consultada em: " + str(checked_at))
                    if cell.get("legacy_divergent_sources"):
                        st.warning("Há tempos publicados divergentes para este trecho.")
                    url = cell.get("source_url")
                    if url:
                        st.link_button("Fonte · " + projection["names"][base] +
                                       " → " + d["name"], url)
                    elif cell["category"] in TIMED:
                        st.caption("Fonte de tempo não disponível para este trajeto.")
                    else:
                        st.caption("Pesquisa de tempo ou acesso ainda pendente.")
