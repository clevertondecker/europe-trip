"""UX 5.0.3 — comparison presentation, always read-only."""
from __future__ import annotations
import streamlit as st
from base_research_expanded_model import load_research
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import (
    empty_interests, ordered_interests, selected_destinations_for_comparison, LABELS,
)
from ux503_destination_base_comparison_model import compare_wishlist_bases
from ux506_decision_readiness_projection import build_decision_readiness
from routes7_comparison_projection import decorate_comparison
from data8_tourism_ui import render_composed_attraction_details, render_data8_cost_simulator
from ux_navigation import set_task
from ux_shared_ui_presentation import page_header, kpi_cards, section_heading
from ux505_base_comparison_presentation import (
    comparison_overview, matrix_cell, known_findings, missing_research,
)


COUNTRY_FLAGS = {
    "França": "🇫🇷",
    "Alemanha": "🇩🇪",
    "Bélgica": "🇧🇪",
    "Luxemburgo": "🇱🇺",
    "Países Baixos": "🇳🇱",
    "Suíça": "🇨🇭",
}


def destination_country_label(name: str, country: str) -> str:
    """Presentation only: never infer a flag from the city name."""
    flag = COUNTRY_FLAGS.get(country)
    return f"{flag} {name}" if flag else name


def _return_to_wishlist():
    # Request a pre-widget navigation update on the next Streamlit run.
    st.session_state["ux503_pending_return_to_wishlist"] = True


def render_wishlist_base_comparison(*, plan, discovery=None, research=None):
    discovery = discovery if discovery is not None else build_exploration_discovery()
    research = research if research is not None else load_research(include_candidates=True)
    st.markdown(page_header(
        "Comparar cidades-base", "NOSSA EUROPA 2027 · EXPLORAR",
        "Compare os deslocamentos pesquisados sem decidir antecipadamente a melhor base.",
        tag="Pesquisa comparativa", variant="compact",
    ),unsafe_allow_html=True)
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

    from rec03b_handoff_ui import render_manual_context
    render_manual_context()
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
    from attractions_model import load_attractions
    from itinerary_eligibility import itinerary_eligibility
    catalog = load_attractions()
    statuses = {d["id"]: itinerary_eligibility(d["id"], catalog)["status"] for d in discovery["destinations"] if d["id"] in active}
    exploratory = [d["name"] for d in discovery["destinations"]
                   if statuses.get(d["id"]) == "research_only"]
    st.caption(f\'{sum(x == "eligible" for x in statuses.values())} podem entrar no roteiro · {len(exploratory)} em pesquisa\')
    if exploratory:
        st.caption("Somente pesquisa e comparação por enquanto: " + ", ".join(exploratory) +
                   ". Ainda não podem ser incluídos no roteiro.")
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
        format_func=lambda x: destination_country_label(
                names[x]["name"], names[x]["country"]) + " · " + priorities[x],
        key="ux503_visible_destinations",
        help="Filtra apenas esta tela. Não altera ou remove destinos da lista salva.")
    st.session_state["ux504_visible_destinations_shadow"] = list(selected_view)
    visible = [x for x in active if x in selected_view]
    render_manual_context(selected,visible)
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

    # UI-only coverage of exactly the same selected base x destination matrix.
    # Keep canonical legacy coverage as a separate dimension in the details.
    enriched = decorate_comparison(result)
    st.markdown(section_heading(
        "EVIDÊNCIAS DA MATRIZ", "O que sabemos até agora",
        "Dados históricos, indicações e lacunas são categorias distintas.",
        variant="compact",
    ),unsafe_allow_html=True)
    cards=kpi_cards([
        {"name":"Histórico de trem","value":enriched["historical"],"icon":"▤",
         "hint":"Registros históricos"},
        {"name":"Referências indicativas","value":enriched["reference_only"],
         "icon":"◈","hint":"Não confirmadas para 2027"},
        {"name":"Sem tempo pesquisado","value":enriched["no_time"],"icon":"○",
         "hint":"Tempo desconhecido"},
        {"name":"Deslocamento local","value":enriched["local"],"icon":"⌖",
         "hint":"Categoria própria"},
    ])
    with st.container(key="ux82_compare_metrics"):
        for column,markup in zip(st.columns(4,gap="small"),cards):
            column.markdown(markup,unsafe_allow_html=True)
    st.caption("Trajetos com algum tempo pesquisado: "+
               str(enriched["historical"]+enriched["reference_only"])+
               " (histórico e referência indicativa não são equivalentes).")
    st.markdown("#### O que ainda precisamos pesquisar?")
    st.caption(
        f'{enriched["total"]} combinações: uma categoria por par. '
        "Mínimos indicativos e amostras de 2026 possuem proveniências diferentes; "
        "não são médias típicas nem percursos completos. Fontes secundárias são "
        "identificadas. Não há disponibilidade de retorno comprovada para 2027."
    )

    # New read-only decision layer: never modifies choices or official TripPlan.
    decision = build_decision_readiness(result, discovery=discovery, research=research)
    # Decision readiness evaluates historical evidence and verified logistics.
    # An additional directional minimum must be visible, but must not be
    # promoted into a confirmed return, timetable, or historical observation.
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
            "Destino": destination_country_label(x["destination_name"],
                names[x["destination_id"]]["country"]),
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
            render_composed_attraction_details(entry)
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
            reference = enriched["cells"].get((journey["base_id"], journey["destination_id"]))
            if reference and reference["category"] == "reference_only":
                st.caption("Referência adicional de ida: " + reference["label"] +
                           " · não é evidência histórica comparável nem confirma 2027.")
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

    st.markdown("#### Tempo ferroviário de ida para planejar")
    st.caption("Histórico e mínimos de referência não são médias típicas. "
               "Onde a estação está indefinida, o valor é apenas indicativo.")
    indexed = {(r["base_id"], r["destination_id"]): r
               for r in result["rows"]}
    matrix = []
    for destination in result["destinations"]:
        line = {"Destino · prioridade": destination_country_label(
            destination["name"],destination["country"]) + " · " +
                destination["priority_label"]}
        for base_id in selected:
            route = indexed[(base_id, destination["id"])]
            line[cities[base_id]["name"]] = (
                enriched["cells"][(base_id, destination["id"])]["label"])
        matrix.append(line)
    st.dataframe(matrix, hide_index=True, width="stretch")
    st.caption("Valores de ida: histórico legado, mínimo indicativo publicado, "
               "amostra de 2026 ou referência secundária (rotulada em cada célula). "
               "Nenhum é confirmação de viagem em 2027; estações, retorno e "
               "última milha continuam pendentes. Em telas pequenas, deslize a tabela.")
    still_missing = [
        {"Cidade-base": cities[b]["name"],
         "Destino": destination_country_label(
             dest["name"], dest["country"]),
         "Pendente": "Pesquisar tempo ferroviário de ida e fonte"}
        for b in selected for dest in result["destinations"]
        if enriched["cells"][(b, dest["id"])]["category"] == "no_time"
    ]
    if still_missing:
        with st.expander("Combinações ainda sem tempo pesquisado (" +
                         str(len(still_missing)) + ")", expanded=False):
            st.dataframe(still_missing, hide_index=True, width="stretch")
            st.caption("Falta de referência não significa ligação inviável. "
                       "Novos dados exigem fonte, data, origem/destino e grau de confiança.")
    st.caption("Retorno, tarifas e acesso até as atrações continuam sem comprovação "
               "para as datas da temporada. Valores ausentes não significam inviabilidade.")

    with st.expander("Detalhes por destino, fontes e outras informações",
                     expanded=False):
        st.caption("Datas de observação, transferências, divergências e "
                   "evidências de moradia são históricas; nenhuma informação "
                   "confirma a logística ou os preços de 2027.")
        detail = st.selectbox(
            "Examinar um destino", visible,
            format_func=lambda x: destination_country_label(
                names[x]["name"], names[x]["country"]) + " · " + priorities[x],
            key="ux503_detail_destination")
        if detail:
            destination = next(x for x in result["destinations"]
                               if x["id"] == detail)
            st.markdown("**" + destination_country_label(destination["name"],
                destination["country"]) + "** · " +
                        destination["priority_label"])
            for base_id in selected:
                route = indexed[(base_id, detail)]
                item = enriched["cells"][(base_id, detail)]
                with st.container(border=True):
                    st.markdown("**" + cities[base_id]["name"] + "**")
                    st.write(item["label"])
                    st.caption(item["typical_label"])
                    if item["station_caveat"]:
                        st.caption(item["station_caveat"])
                    if item.get("gap_applied"):
                        st.caption("Pesquisa adicional consultada em " +
                                   str(item["gap_checked_at"]) +
                                   " · fonte " +
                                   ("secundária, confiança baixa" if
                                    item["gap_evidence_type"] == "secondary_sample"
                                    else "operadora, referência histórica") +
                                   " · ida apenas; nenhuma confirmação para 2027.")
                    if item.get("reference_differs_from_legacy"):
                        st.caption("A referência publicada difere do histórico. "
                                   "Não é conflito comprovado entre os mesmos serviços.")
                    if item.get("fastest_provenance") == "snapshot_only_unreproduced":
                        st.warning("Número registrado no snapshot, mas não reproduzido "
                                   "como referência independente nesta reconsulta.")
                    st.write("Transferências: " +
                             (str(route["transfers"]) if route["transfers"] is not None
                              else "Não pesquisadas"))
                    st.caption("Histórico selecionado em: " +
                               str(route["source_date"] or "Data desconhecida"))
                    st.caption("Retorno de fim de semana e última milha: não confirmados.")
                    if route["divergent_sources"]:
                        st.caption("Há tempos publicados diferentes; podem representar serviços ou datas distintos. "
                                   "As condições não permitem concluir contradição.")
                    historical_url = item.get("historical_source_url")
                    reference_url = item.get("reference_source_url")
                    if historical_url:
                        title = ("Fonte compartilhada: histórico e referência"
                                 if reference_url == historical_url
                                 else "Fonte do histórico")
                        st.markdown("[" + title + "](" + historical_url + ")")
                    if reference_url and reference_url != historical_url:
                        st.markdown("[Fonte da referência publicada](" +
                                    reference_url + ")")
                    for observation in route["observations"]:
                        source = observation.get("source_url")
                        if source and source != route["source_url"]:
                            st.markdown("[Observação histórica alternativa](" +
                                        source + ")")
            render_data8_cost_simulator(detail)
        st.markdown("##### Moradia e pendências por cidade-base")
        for summary in result["summaries"]:
            with st.container(border=True):
                st.markdown("**" + summary["base_name"] +
                            "** · condições e pesquisas pendentes")
                st.caption("Cobertura histórica original: " +
                           str(summary["documented_time_count"]) + " com tempo, " +
                           str(summary["missing_time_count"]) + " sem tempo, " +
                           str(summary["local_count"]) +
                           " locais. As referências indicativas são separadas.")
                housing = summary["housing"]
                if housing["count"]:
                    st.write("Moradia: " + str(housing["count"]) +
                             " anúncios históricos; mediana € " +
                             str(round(housing["median_eur_month"])) +
                             "/mês. Valores não confirmados para 2027.")
                else:
                    st.write("Moradia: sem amostras comparáveis documentadas.")
                st.caption("Pendências abaixo refletem a cobertura histórica; "
                           "a matriz acima também apresenta referências indicativas "
                           "adicionais, que não comprovam retorno ou viabilidade.")
                for item in summary["research_gaps"]:
                    st.markdown("- " + item)
