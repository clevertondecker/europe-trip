"""UX 5.0.3 — comparison presentation, always read-only."""
from __future__ import annotations
import streamlit as st
from base_research_expanded_model import load_research
from ux501_destination_discovery_model import build_destination_discovery
from ux502_destination_interests_model import (
    empty_interests, ordered_interests, selected_destinations_for_comparison, LABELS,
)
from ux503_destination_base_comparison_model import compare_wishlist_bases
from ux506_decision_readiness_projection import build_decision_readiness
from routes7_comparison_projection import decorate_comparison
from routes7_return_scenarios_model import planning_return_scenarios
from ux_navigation import set_task
from ux505_base_comparison_presentation import (
    comparison_overview, matrix_cell, known_findings, missing_research,
)


def _return_to_wishlist():
    # Request a pre-widget navigation update on the next Streamlit run.
    st.session_state["ux503_pending_return_to_wishlist"] = True


def render_wishlist_base_comparison(*, plan, discovery=None, research=None):
    discovery = discovery if discovery is not None else build_destination_discovery()
    research = research if research is not None else load_research()
    st.markdown("### Como seria visitar nossos destinos a partir de cada cidade?")
    st.write("Compare os tempos de trem que já pesquisamos para diferentes "
             "cidades-base. Quando faltarem informações, mostramos o que "
             "ainda precisa ser investigado.")
    st.caption("Você escolhe as cidades-base e os destinos desta comparação. "
               "A tela não recomenda nem seleciona uma cidade vencedora.")
    interests = st.session_state.get("ux502_interests", empty_interests())
    cities = {c["id"]:c for c in research["cities"]}
    official = plan["base_city"]
    favorite = set(st.session_state.get("ux41_favorites", []))
    preferred = [x for x in [official, *sorted(favorite)] if x in cities]
    choices = list(dict.fromkeys([*preferred, *sorted(
        cities, key=lambda x: (cities[x]["name"], x))]))
    defaults = list(dict.fromkeys([x for x in
                [official,"strasbourg","lille","mulhouse"] if x in cities]))[:4]
    if len(defaults) < 2:
        defaults = choices[:2]
    if "ux503_bases" not in st.session_state:
        candidate = st.session_state.get("ux504_bases_shadow", defaults)
        st.session_state["ux503_bases"] = ([x for x in candidate if x in choices]
                                          if isinstance(candidate, list) else defaults)

    def label(city_id):
        tags = []
        if city_id == official:
            tags.append("referência oficial")
        if city_id in favorite:
            tags.append("favorita")
        suffix = (" · " + ", ".join(tags)) if tags else ""
        return cities[city_id]["name"] + " · " + cities[city_id]["country"] + suffix

    st.markdown("#### 1. Onde poderíamos ficar?")
    selected = st.multiselect(
        "Cidades-base para comparar (2 a 5)",choices,
        format_func=label,key="ux503_bases",
        help="Seleção apenas para pesquisa; não altera a base oficial.")
    st.session_state["ux504_bases_shadow"] = list(selected)
    st.caption("Base do roteiro oficial: **" + label(official) + "**. "
               "Removê-la desta comparação não altera a viagem.")
    if st.button("Voltar à minha lista", key="ux503_back_to_wishes"):
        _return_to_wishlist()
        st.rerun()
    if len(selected) < 2 or len(selected) > 5:
        st.warning("Selecione entre duas e cinco cidades-base para comparar.")
        return
    try:
        active = selected_destinations_for_comparison(interests, discovery)
        ordered = ordered_interests(interests, discovery)
    except ValueError as exc:
        st.error("Lista de destinos incompatível: " + str(exc))
        return
    if not active:
        if ordered:
            st.info("Todos os destinos da lista foram descartados. "
                    "Reclassifique pelo menos um em Minha lista para compará-lo.")
        else:
            st.info("Sua lista está vazia. Escolha primeiro os destinos em "
                    "Explorar → Minha lista para entender a logística das cidades-base.")
        return

    names = {row["id"]: row for row in discovery["destinations"]}
    priorities = {row["destination_id"]:LABELS[row["priority"]] for row in ordered}
    # View-only projection. The UX 5.0.2 document is never filtered or overwritten.
    if "ux503_visible_destinations" not in st.session_state:
        previous = st.session_state.get("ux504_visible_destinations_shadow")
        st.session_state["ux503_visible_destinations"] = (
            [x for x in previous if x in active] if isinstance(previous,list)
            else active[:5])
    st.markdown("#### 2. Quais destinos queremos considerar?")
    selected_view = st.multiselect(
        "Destinos para exibir nesta comparação", active,
        format_func=lambda x: names[x]["name"] + " · " + priorities[x],
        key="ux503_visible_destinations",
        help="Filtra apenas esta tela. Não altera ou remove destinos da lista salva.")
    st.session_state["ux504_visible_destinations_shadow"] = list(selected_view)
    visible = [x for x in active if x in selected_view]
    st.caption(f"Exibindo {len(visible)} de {len(active)} destinos desejados. "
               "Este filtro não altera a lista salva.")
    if not visible:
        st.info("Selecione pelo menos um destino para visualizar a matriz.")
        return
    try:
        result = compare_wishlist_bases(
            interests, list(selected), discovery=discovery, research=research,
            visible_destination_ids=visible)
    except ValueError as exc:
        st.error("Não foi possível montar a comparação: " + str(exc))
        return

    # UI-only summary; all values and identities come from the existing model.
    overview = comparison_overview(result)
    st.markdown("#### Resumo da comparação")
    st.write(overview["description"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Trajetos com tempo pesquisado", overview["documented"])
    c2.metric("Trajetos sem tempo identificado", overview["missing"])
    c3.metric("Deslocamentos locais", overview["local"])
    st.caption(f'{overview["total"]} combinações ('
               f'{len(result["base_ids"])} cidades-base × '
               f'{len(result["destinations"])} destinos). '
               "Cobertura de pesquisa não significa qualidade de transporte.")

    # New read-only decision layer: never modifies choices or official TripPlan.
    decision = build_decision_readiness(result, discovery=discovery, research=research)
    st.markdown("#### O que já sabemos para decidir?")
    st.caption("Visitar um lugar, voltar de trem e morar na cidade-base são "
               "perguntas diferentes. Os dados ainda não comprovam nenhum "
               "roteiro completo nem aluguel de 56–60 noites em 2027.")
    if decision["tourism_source_scope"] == "legacy_catalog_only":
        st.info("Pesquisa turística adicional ainda não integrada: estes "
                "indicadores incluem somente o catálogo principal.")
    else:
        st.caption("Inclui o piloto turístico com regras atuais de visita "
                   "e fonte. Horários publicados não confirmam abertura "
                   "em uma data de 2027.")
    tourism_table = [
        {
            "Destino": x["destination_name"],
            "Atrações no catálogo": x["catalog_attraction_count"],
            "Ingressos históricos publicados": x["published_ticket_amounts_historical"],
            "Horários/regras atuais documentados": x["published_opening_hours"],
            "Novas fichas turísticas": x["enriched_current_opening_rules"],
            "Visita em 2027": "Ainda não validada",
        }
        for x in decision["destinations"]
    ]
    st.dataframe(tourism_table, hide_index=True, width="stretch")
    if decision["housing_source_scope"] == "legacy_housing_only":
        st.caption("Contratos adicionais de hospedagem ainda não integrados; "
                   "indicadores de moradia baseados no histórico cadastrado.")
    with st.expander("Atrações: experiência, ingresso, horários e pendências",
                     expanded=False):
        for entry in decision["attraction_details"]:
            st.markdown("**" + entry["name"] + "**")
            if entry["description"]:
                st.write(entry["description"])
            if entry["why_visit"]:
                st.caption("Por que visitar: " + entry["why_visit"])
            if entry["opening_rule"]:
                st.write("Funcionamento pesquisado: " + entry["opening_rule"])
                st.caption("Regra atual/histórica; não é confirmação para datas de 2027.")
            else:
                st.caption("Horários de visita ainda não pesquisados.")
            ticket = entry["ticket_main"] or {}
            amount = ticket.get("amount")
            if amount is not None:
                st.caption("Ingresso de referência: " + str(amount) + " " +
                           str(ticket.get("currency") or "") +
                           " (confirmar unidade/validade para a viagem)")
            elif ticket.get("status") == "not_applicable":
                st.caption("Sem ingresso principal aplicável segundo a referência histórica.")
            else:
                st.caption("Preço de ingresso desconhecido.")
            activity = entry["additional_activity"] or {}
            if activity:
                st.caption("Atividade adicional: " + str(activity.get("name")) +
                           " — " + str(activity.get("amount")) + " " +
                           str(activity.get("currency") or "") +
                           " (referência publicada; não cotação para 2027)")
            if entry["visit_minutes"] is not None:
                st.caption("Duração de visita: " + str(entry["visit_minutes"]) +
                           " min · " + str(entry["visit_duration_status"]))
            else:
                st.caption("Duração de visita não documentada.")
            if entry["last_mile_observations"]:
                st.caption("Acessos registrados: " +
                           str(len(entry["last_mile_observations"])) +
                           " · nenhum percurso completo de 2027 garantido.")
            if entry["opening_source_url"]:
                st.link_button("Fonte da visita", entry["opening_source_url"],
                               key="tourism_source_" + entry["attraction_id"])
    with st.expander("Transporte: o que falta para uma visita completa",
                     expanded=False):
        for journey in decision["journeys"]:
            st.write(journey["base_id"] + " → " + journey["destination_id"])
            st.caption("Ida histórica: " +
                       (str(journey["historical_rail_oneway_min"]) + " min" if
                        journey["historical_rail_oneway_min"] is not None else
                        "desconhecida") +
                       " · retorno/última milha: a verificar" +
                       " · estado temporal: " + journey["temporal_association_status"])
            if journey["association_reasons"]:
                st.caption("Faltam: " + ", ".join(journey["association_reasons"]))
    with st.expander("Condições de moradia nas cidades-base", expanded=False):
        housing_table = [
            {
                "Cidade-base": x["base_name"],
                "Anúncios históricos": x["historical_offer_count"],
                "Cotações 2027 (56–60 noites)": x["verified_56_to_60_night_quotes_2027"],
                "Internet verificada": x["remote_work_internet_verified_count"],
                "Custo total da estadia": "Desconhecido",
                "Taxas e caução": "Não verificadas",
                "Espaço de trabalho": "Não confirmado",
                "Acesso real à estação": "Não confirmado",
            }
            for x in decision["base_housing"]
        ]
        st.dataframe(housing_table, hide_index=True, width="stretch")
    st.caption("Sem ranking automático: cobertura documental não equivale "
               "a qualidade logística, viabilidade do passeio ou moradia.")

    st.markdown("#### Tempos de ida: históricos e referências para planejamento")
    enriched = decorate_comparison(result)
    st.caption(
        f'{enriched["historical"]} pares com histórico, '
        f'{enriched["reference_only"]} com mínimo publicado adicional, '
        f'{enriched["local"]} local(is), '
        f'{enriched["no_time"]} ainda sem tempo de referência. '
        "Um mínimo publicado não é tempo típico nem garantia de 2027."
    )
    indexed = {(r["base_id"], r["destination_id"]): r
               for r in result["rows"]}
    matrix = []
    for destination in result["destinations"]:
        line = {"Destino · prioridade": destination["name"] + " · " +
                destination["priority_label"]}
        for base_id in selected:
            route = indexed[(base_id, destination["id"])]
            line[cities[base_id]["name"]] = (
                enriched["cells"][(base_id, destination["id"])]["label"])
        matrix.append(line)
    st.dataframe(matrix, hide_index=True, width="stretch")
    st.caption("Ida histórica ou referência de tempo mínimo publicado, "
               "sem data ferroviária confirmada para 2027. "
               "Média publicada é outra métrica, e retorno continua pendente. "
               "Em telas pequenas, deslize a tabela horizontalmente.")
    with st.expander("Fontes, tempos típicos e ressalvas dos 15 pares",
                     expanded=False):
        for destination in result["destinations"]:
            st.markdown("**" + destination["name"] + "**")
            for base_id in selected:
                item = enriched["cells"][(base_id, destination["id"])]
                st.write(
                    cities[base_id]["name"] + ": " + item["label"] +
                    " · " + item["typical_label"]
                )
                if item.get("station_status") == "station_not_reconciled":
                    st.caption("Estações/serviços específicos ainda não reconciliados.")
                if item.get("source_url"):
                    st.markdown("[Fonte da referência](" + item["source_url"] + ")")
        st.caption("Sem retorno de fim de semana ou tarifa confirmada neste overlay.")

    with st.expander("Referências para ida e volta (sem garantia de horário)",
                     expanded=False):
        scenarios = planning_return_scenarios(result)
        st.caption("Somatório de dois tempos mínimos publicados em sentidos "
                   "separados: piso teórico, NÃO duração real reservável, "
                   "nem garantia de ida/volta no fim de semana.")
        for row in scenarios["rows"]:
            if row["reverse_source_url"]:
                st.write(
                    cities[row["base_id"]]["name"] + " ↔ " +
                    names[row["destination_id"]]["name"] + " · " +
                    str(row["outbound_fastest_reference_min"]) + " min ida (mín.) + " +
                    str(row["reverse_fastest_reference_min"]) + " min volta (mín.)"
                )
                st.caption("Piso hipotético: " +
                           str(row["two_direction_minimum_sum_min"]) +
                           " min nos trens, sem transferências extras ou acesso local.")
                st.markdown("[Referência da volta](" + row["reverse_source_url"] + ")")
        st.caption("Frequência de sábado/domingo, número de conexões, "
                   "acesso a atrações e tarifa total do casal: desconhecidos.")

    left, right = st.columns(2)
    with left:
        st.markdown("#### O que podemos concluir com os dados atuais?")
        for finding in known_findings(result):
            st.markdown("- " + finding)
    with right:
        st.markdown("#### O que ainda precisamos pesquisar?")
        for gap in missing_research(result):
            st.markdown("- " + gap)

    with st.expander("Detalhes por destino, fontes e outras informações",
                     expanded=False):
        st.caption("Datas de observação, transferências, divergências e "
                   "evidências de moradia são históricas; nenhuma informação "
                   "confirma a logística ou os preços de 2027.")
        detail = st.selectbox(
            "Examinar um destino", visible,
            format_func=lambda x: names[x]["name"] + " · " + priorities[x],
            key="ux503_detail_destination")
        if detail:
            destination = next(x for x in result["destinations"]
                               if x["id"] == detail)
            st.markdown("**" + destination["name"] + "** · " +
                        destination["priority_label"])
            for base_id in selected:
                route = indexed[(base_id, detail)]
                with st.container(border=True):
                    st.markdown("**" + cities[base_id]["name"] + "** · " +
                                route["status"])
                    st.write(matrix_cell(route))
                    if route["typical_oneway_min"] is not None:
                        st.caption("Tempo típico observado: " +
                                   str(route["typical_oneway_min"]) + " min")
                    st.write("Transferências: " +
                             (str(route["transfers"]) if
                              route["transfers"] is not None
                              else "Não pesquisadas"))
                    st.caption("Data da observação: " +
                               str(route["source_date"] or "Não informada"))
                    st.caption("Retorno de fim de semana e última milha "
                               "não verificados.")
                    if route["divergent_sources"]:
                        st.warning("Fontes com tempos divergentes; "
                                   "verificar condições e datas.")
                    if route["source_url"]:
                        st.link_button("Fonte selecionada", route["source_url"])
                    for observation in route["observations"]:
                        source = observation.get("source_url")
                        if source and source != route["source_url"]:
                            st.markdown("[Observação alternativa](" +
                                        source + ")")
        st.markdown("##### Moradia e pendências por cidade-base")
        for summary in result["summaries"]:
            with st.container(border=True):
                st.markdown("**" + summary["base_name"] +
                            "** · condições e pesquisas pendentes")
                st.caption(
                    f'{summary["documented_time_count"]} trajetos com tempo '
                    f'pesquisado; {summary["missing_time_count"]} sem tempo; '
                    f'{summary["local_count"]} locais.')
                housing = summary["housing"]
                if housing["count"]:
                    st.write("Moradia: " + str(housing["count"]) +
                             " anúncios históricos; mediana € " +
                             str(round(housing["median_eur_month"])) +
                             "/mês. Valores não confirmados para 2027.")
                else:
                    st.write("Moradia: sem amostras comparáveis documentadas.")
                for item in summary["research_gaps"]:
                    st.markdown("- " + item)
