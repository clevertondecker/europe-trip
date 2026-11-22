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
    for base in selected:
        c = projection["counts"][base]
        st.markdown("**" + projection["names"][base] + "**")
        st.caption(
            f'{c.get("historical", 0)} com dados históricos · '
            f'{c.get("reference_only", 0)} com referências indicativas · '
            f'{c.get("local", 0)} acessos locais a verificar · '
            f'{c.get("no_time", 0)} sem tempo pesquisado'
        )
        if projection["must_visit_without_time"][base]:
            st.caption("Imperdíveis sem tempo pesquisado: " +
                       ", ".join(projection["must_visit_without_time"][base]))
    shared = len(projection["common_timed_destination_ids"])
    if shared == 0:
        st.warning("Ainda não temos dados de tempo em comum suficientes para comparar "
                   "essas cidades de forma conclusiva.")
    elif shared < total:
        st.info(f"Há tempos pesquisados em comum para {shared} de {total} destinos. "
                "Os demais não entram em uma comparação direta de duração.")
    else:
        st.info("Há tempos pesquisados para os mesmos destinos em todas as bases. "
                "Isso não comprova retorno, tarifas, frequências ou melhor cidade.")
    st.caption("Moradia, retorno ferroviário, último trecho e preços de 2027 seguem "
               "pendentes de confirmação. Mais referências não significam melhor logística.")

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
