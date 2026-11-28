"""UX132: documentary coverage without itinerary or wishlist dependencies."""
import logging
from time import perf_counter
import streamlit as st

from ux132_research_coverage_model import (
    build_coverage_view, connection_rows, filter_coverage_rows,
    SORT_OPTIONS, STATUS_OPTIONS,
)
from rail_reference_projection_model import format_minutes
from ux_widget_state import widget_state, navigation_widget_state
from rail_evidence_unified_model import canonical_place

_LOG = logging.getLogger(__name__)


def _pct(counts):
    value = counts["fraction"]
    return "Não aplicável" if value is None else f"{value:.1%}".replace(".", ",")


def _table(rows):
    return [{
        "Cidade": r["name"],
        "Cobertura": r["fraction"] * 100 if r["fraction"] is not None else None,
        "Com tempo": r["timed"],
        "Elegíveis": r["eligible"],
        "Históricos": r["historical"],
        "Indicativos": r["indicative"],
        "Locais": r["local"],
        "Sem tempo": r["missing"],
    } for r in rows]


def render_rail_coverage(*, discovery=None, research=None):
    try:
        started = perf_counter()
        view = build_coverage_view(discovery=discovery, research=research)
        _LOG.debug("UX132 coverage projection: %.3fs", perf_counter() - started)
    except Exception:
        _LOG.exception("UX132 coverage unavailable")
        st.error("Não foi possível carregar a cobertura. Seu roteiro e suas escolhas permanecem intactos.")
        return

    counts = view["global"]
    cols = st.columns(4)
    cols[0].metric("Cidades-base", view["base_count"])
    cols[1].metric("Destinos no catálogo", view["destination_count"])
    cols[2].metric("Conexões com tempo", f'{counts["timed"]}/{counts["eligible"]}')
    cols[3].metric("Cobertura ferroviária", _pct(counts))
    st.caption("Universo global: pares dirigidos. Pares locais ficam fora do denominador.")
    st.info("Cobertura documental mede disponibilidade de referências, não viabilidade logística. "
            "Retorno, última milha e horários de 2027 não estão confirmados.")
    render_fare_evidence(view)
    priority = view["priority"]
    st.caption(f'Cinco bases prioritárias: {_pct(priority)} '
               f'({priority["timed"]}/{priority["eligible"]} pares não locais).')
    sections = ("Cidades-base", "Destinos")
    section = st.segmented_control(
        "Detalhamento da cobertura", sections,
        **navigation_widget_state("ux132_coverage_section", sections),
    ) or st.session_state["ux132_coverage_section_shadow"]
    rows = view["bases"] if section == "Cidades-base" else view["destinations"]
    axis = "bases" if section == "Cidades-base" else "destinations"
    cols = st.columns(3 if axis == "bases" else 2)
    query = cols[0].text_input("Pesquisar cidade", placeholder="Digite o nome",
                              **widget_state("ux132_search_" + axis, "", lambda v: isinstance(v, str)))
    order = cols[1].selectbox("Ordenar por", SORT_OPTIONS,
                             **widget_state("ux132_sort_" + axis, SORT_OPTIONS[0], lambda v: v in SORT_OPTIONS))
    if axis == "bases":
        scopes = ("Cinco bases prioritárias", "Todas as bases")
        scope = cols[2].selectbox("Recorte de bases", scopes,
                                  **widget_state("ux132_base_scope", scopes[0], lambda v: v in scopes))
        if scope == scopes[0]:
            rows = [r for r in rows if r["id"] in view["priority_ids"]]
    gaps_only = st.checkbox("Somente cidades com lacunas de tempo",
                            **widget_state("ux132_only_gaps_" + axis, False, lambda v: isinstance(v, bool)))
    total = len(rows)
    rows = filter_coverage_rows(rows, query=query, gaps_only=gaps_only, sort=order)
    st.caption(f'{len(rows)} de {total} cidades no recorte. Os filtros não alteram os '
               "indicadores globais. Cobertura não indica a melhor cidade.")
    if not rows:
        st.info("Nenhuma cidade corresponde aos filtros. Altere a busca ou o recorte.")
        return
    st.dataframe(_table(rows), hide_index=True, width="stretch",
                 column_config={"Cobertura": st.column_config.ProgressColumn(
                     "Cobertura", min_value=0, max_value=100, format="%.1f%%")},
                 key="ux132_coverage_table_" + section)
    st.markdown("#### Detalhamento da cidade")
    detail_key = "ux132_detail_" + section
    names = {canonical_place(r["id"]): r["name"] for r in rows}
    # A stable-ID selectbox supports keyboard access, restores state across pages
    # and avoids coupling the detail to ephemeral dataframe row positions.
    selected = st.selectbox("Escolha uma cidade para detalhar", list(names),
                            format_func=names.__getitem__,
                            **widget_state(detail_key, next(iter(names)), lambda v: v in names))
    row = next(r for r in rows if r["id"] == selected)
    with st.container(border=True):
        a, b = st.columns(2)
        a.metric(f'{row["name"]} — cobertura ferroviária', _pct(row))
        if row["fraction"] is not None:
            a.progress(row["fraction"])
        a.caption(f'{row["timed"]} de {row["eligible"]} conexões documentadas')
        b.metric("Lacunas de pesquisa", row["missing"])
        b.caption("Conexões sem tempo documentado")
        st.divider()
        st.markdown("#### Conexões e lacunas de pesquisa")
        status = st.selectbox("Tipo de evidência", list(STATUS_OPTIONS),
                              **widget_state("ux132_status_" + axis, next(iter(STATUS_OPTIONS)),
                                              lambda v: v in STATUS_OPTIONS))
        connections = connection_rows(view, axis, row["id"], status)
        st.caption(f'{len(connections)} conexões no filtro · os indicadores acima consideram '
                   "todos os pares não locais desta cidade.")
        if not connections:
            st.info("Nenhuma conexão neste filtro.")
        else:
            counterpart = "destination" if axis == "bases" else "origin"
            label = "Destino" if axis == "bases" else "Origem"
            if status == "Sem tempo pesquisado":
                # Keep the original compact gap table as the default.
                table = [{label: c[counterpart], "Pendência": c["label"]}
                         for c in connections]
                config = None
            else:
                table = [{
                    label: c[counterpart], "Evidência": c["label"],
                    "Fonte": c["source_url"],
                } for c in connections]
                config = {"Fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir fonte")}
            st.dataframe(table, hide_index=True, width="stretch",
                         column_config=config, key="ux132_gaps_" + section)
            timed = { (c["destination_id"] if axis == "bases" else c["base_id"]): c
                      for c in connections if c["category"] in ("historical", "reference_only")
                      or c.get("quality_review") }
            if timed:
                with st.expander("Consultar fonte e ressalvas"):
                    key = "ux132_connection_" + axis
                    owner_key = key + "_city"
                    if st.session_state.get(owner_key) != row["id"]:
                        st.session_state.pop(key + "_shadow", None)
                        st.session_state[owner_key] = row["id"]
                    chosen = st.selectbox(
                        "Conexão documentada", list(timed),
                        format_func=lambda k: timed[k][counterpart],
                        **widget_state(key, next(iter(timed)), lambda v: v in timed),
                    )
                    c = timed[chosen]
                    st.write(f'**{c["origin"]} → {c["destination"]}**')
                    st.write(c["label"])
                    st.caption("Data registrada: " + str(c["source_date"] or "Não informada"))
                    if c["source_url"]:
                        st.link_button("Abrir fonte do mínimo exibido", c["source_url"])
                    else:
                        st.caption("Fonte do mínimo não informada.")
                    if c["station_caveat"]:
                        st.caption(c["station_caveat"])
                    if c["notes"]:
                        st.caption(str(c["notes"]))
                    if c["variation"]:
                        st.caption("Há variação entre referências; não implica contradição confirmada.")
                    review = c.get("quality_review")
                    original = c.get("reviewed_observation")
                    if review and original:
                        st.markdown("**Auditoria documental DATA26C**")
                        reproduction = ("Valores reproduzidos" if review["selected_summary_reproduced"]
                                        else "Valores divergentes — histórico preservado")
                        modality = ("Modalidade inconclusiva — excluída da cobertura ferroviária"
                                    if review["modality_status"] == "inconclusive"
                                    else "Resumo ferroviário publicado; trechos não verificados")
                        st.write(reproduction)
                        st.caption(modality)
                        st.caption("Confiança da referência: " + {"medium": "média", "low": "baixa"}.get(original["confidence"], original["confidence"]))
                        st.caption("Observação original (mínimo / média): " +
                                   format_minutes(original["minimum_min"]) + " / " +
                                   format_minutes(original["average_min"]) +
                                   " · " + original["checked_at"])
                        st.link_button("Abrir fonte da observação auditada", original["source_url"])
                        st.caption("Reconsulta: " + review["checked_at"])
                        st.dataframe([{
                            "Mínimo": format_minutes(s["minimum_min"]),
                            "Média": format_minutes(s["average_min"]),
                            "Origem publicada": ", ".join(s["origin_station_labels"]),
                            "Chegada publicada": ", ".join(s["arrival_station_labels"]),
                            "Versão indexada": s["index_recency"],
                            "Base da modalidade": s["mode_basis"],
                        } for s in review["samples"]], hide_index=True, width="stretch",
                            key="ux132_review_samples_" + axis)
                        st.caption(review["note"])
                        for check in review.get("official_cross_checks", []):
                            st.markdown(f'[{check["finding"]}]({check["source_url"]})')
                    if c["alternative"]:
                        alt = c["alternative"]
                        st.markdown("**Referência indicativa alternativa (não substitui o histórico)**")
                        st.write(format_minutes(alt["minimum"]))
                        st.caption("Data registrada: " + str(alt["source_date"]))
                        st.link_button("Abrir fonte alternativa", alt["source_url"])
                        if alt["station_caveat"]:
                            st.caption(alt["station_caveat"])
                        if alt["notes"]:
                            st.caption(str(alt["notes"]))
                    if c["observations"]:
                        st.markdown("**Outras observações históricas catalogadas**")
                        observations = []
                        for obs in c["observations"]:
                            minutes = obs.get("minimum_oneway_min")
                            url = obs.get("source_url")
                            observations.append({
                                "Mínimo registrado": format_minutes(minutes) if type(minutes) is int and minutes > 0 else None,
                                "Data": obs.get("evidence_date"),
                                "Estação de origem": obs.get("origin_station"),
                                "Estação de destino": obs.get("destination_station"),
                                "Observação": obs.get("notes"),
                                "Fonte": url if isinstance(url, str) and url.startswith("https://") else None,
                            })
                        st.dataframe(observations, hide_index=True, width="stretch",
                                     column_config={"Fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir fonte")},
                                     key="ux132_observations_" + axis)
                    st.caption("Referência de ida; retorno, última milha e horários de 2027 não confirmados.")
        st.caption("Sem tempo pesquisado não significa ausência de conexão. "
                   "Local indica acesso urbano a verificar, não lacuna ferroviária.")


def render_fare_evidence(view, fares=None):
    with st.expander("Tarifas e retornos documentados"):
        try:
            from data26b_rail_fare_evidence_model import load_rail_fares
            fares = load_rail_fares() if fares is None else fares
            names = {canonical_place(r["id"]): r["name"] for r in view["bases"] + view["destinations"]}
            st.caption(f'{fares["documented"]} observações · {fares["roundtrips"]} com retorno registrado.')
            st.caption("Evidência documental, sem confirmação independente para 2027. Não altera o orçamento.")
            from data26b1_fare_reference_model import load_fare_references, fare_reference_coverage
            refs = load_fare_references()
            coverage = fare_reference_coverage(data=refs, quotes=fares)
            total = coverage["scope"]
            st.caption(f'Cobertura acumulada: {total["with_references"]}/{total["total"]} pares com referência indicativa (inclui legado); {total["complete_roundtrip"]}/{total["total"]} com cotação completa de ida e volta.')
            batch = coverage["batch"]
            st.caption(f'Pesquisa atual ({refs["checked_at"]}): {batch["batch_references"]}/{batch["total"]} pares com referência de calendário; {batch["net_new_references"]} novos pares e {batch["legacy_overlap"]} já documentados no legado.')
            st.caption(f'{batch["pending"]} pares pendentes · {batch["consulted_without_result"]} consultados sem resultado aproveitável nesta pesquisa.')
            st.caption("Valores anunciados por pessoa, somente ida, em datas específicas. Marca ferroviária no calendário não comprova todos os trechos. Perfil, descontos e taxas podem ser desconhecidos.")
            labels = {"observed_calendar": "Calendário observado", "corroborated_price": "Histórico: preço corroborado", "divergent_price": "Histórico: preço divergente", "not_reproduced": "Histórico: não reproduzido", "not_reproduced_nonrail": "Histórico: oferta atual rodoviária"}
            def city(ident):
                return names.get(canonical_place(ident), ident.replace("_", " ").title())
            status_options = ("Observações recentes", "Histórico", "Lacunas")
            choice = st.selectbox("Evidência tarifária", status_options, key="ux132_fare_reference_status")
            base_options = ["Todas"] + sorted(coverage["by_base"])
            base = st.selectbox("Base da pesquisa tarifária", base_options, format_func=lambda x: x if x == "Todas" else city(x), key="ux132_fare_reference_base")
            def selected(r):
                return base == "Todas" or canonical_place(r["origin_id"]) == base
            if choice == "Lacunas":
                gap_labels = {"research_pending":"Pendente", "source_no_price":"Fonte sem preço", "technical_failure":"Falha técnica", "ambiguous_destination":"Destino ambíguo", "insufficient_conditions":"Condições insuficientes", "non_rail_offer":"Oferta não ferroviária", "unavailable_on_date":"Indisponibilidade na data", "historical_not_reproduced":"Histórico não reproduzido"}
                rows = [{"Origem":city(r["origin_id"]), "Destino":city(r["destination_id"]), "Motivo":gap_labels[r["reason"]], "Consulta":r["researched_at"], "Fonte":r["source_url"]} for r in refs["gaps"] if selected(r)]
            else:
                rows = [{"Origem":city(r["origin_id"]), "Destino":city(r["destination_id"]), "Data de viagem":r["travel_date"], "Valor":r["amount_minor"]/100, "Moeda":r["currency"], "Marca exibida":r["commercial_brand"], "Consulta":r["researched_at"], "Estado":labels[r["status"]], "Fonte":r["source_url"]} for r in refs["references"] if selected(r) and (r["status"] == "observed_calendar") == (choice == "Observações recentes")]
            if rows:
                st.dataframe(rows, hide_index=True, column_config={"Fonte": st.column_config.LinkColumn("Fonte", display_text="Abrir fonte")}, key="ux132_fare_reference_rows")
            else:
                st.caption("Nenhuma observação neste filtro.")
            if not fares["records"]:
                st.caption("Nenhuma cotação individual cadastrada.")
            for record in fares["records"]:
                q, out, back = record["quote"], record["outbound"], record["inbound"]
                origin = names.get(out["origin_id"], out["origin_id"].replace("_", " ").title())
                destination = names.get(out["destination_id"], out["destination_id"].replace("_", " ").title())
                scope = "Ida e retorno" if back else "Somente ida"
                amount = q["total_minor"]
                price = "Preço desconhecido" if amount is None else f'{q["currency"]} {amount // 100},{amount % 100:02d}'
                fees = {True: "Taxas e reservas obrigatórias incluídas", False: "Taxas ou reservas obrigatórias excluídas", None: "Inclusão de taxas e reservas desconhecida"}[q["mandatory_fees_included"]]
                state = {"documented_offer": "Oferta documentada", "unavailable": "Indisponível na consulta", "unknown": "Disponibilidade desconhecida"}[q["availability"]]
                with st.container(border=True):
                    st.write(f"**{origin} → {destination} · {scope}**")
                    st.write(f'{("Total documentado" if q["mandatory_fees_included"] is True else "Valor observado")}: {price} · 2 adultos · {state}')
                    st.caption(f'{fees} · Classe: {q["fare_class"] or "Desconhecida"}')
                    st.caption(f'Consulta: {q["checked_at_time"] or q["checked_at"]}')
                    st.markdown(f'[Fonte da tarifa]({q["source_url"]})')
                    if back:
                        st.caption("Retorno temporalmente coerente · " + ("Calendário documentado" if record["return_calendar_documented"] else "Calendário incompleto"))
                        if not record["same_destination_station"] or not record["same_base_station"]:
                            st.caption("Estações diferentes; deslocamento entre estações não verificado.")
                    st.caption("Documentação tarifária completa para o escopo" if record["complete_documentation"] else "Documentação tarifária incompleta")
                    with st.container():
                        st.markdown("**Condições e horários**")
                        st.write("Condições: " + (q["fare_conditions"] or "Desconhecidas"))
                        st.write("Elegibilidade: " + (q["discount_eligibility"] or "Desconhecida"))
                        commercial = {None: "Desconhecido", "allowed": "Permitido", "conditional": "Condicional", "not_allowed": "Não permitido"}
                        st.caption(f'Reembolso: {commercial[q["refundability"]]} · Alteração: {commercial[q["changeability"]]}')
                        st.write("Bilhete: " + {None: "Desconhecido", "integrated": "Integrado", "separate": "Separado"}[q["ticket_structure"]])
                        for label, leg in (("Ida", out), ("Retorno", back)):
                            if leg:
                                st.write(f'{label}: {leg["origin_station_id"]} → {leg["destination_station_id"]}')
                                st.caption(f'{leg["departure_at"]} → {leg["arrival_at"]}')
                                st.markdown(f'[Fonte do trecho — {label}]({leg["source_url"]})')
                        st.caption("Viabilidade da visita e última milha não verificadas.")
        except Exception:
            _LOG.exception("DATA26B fare evidence unavailable")
            st.warning("Observações tarifárias indisponíveis.")
