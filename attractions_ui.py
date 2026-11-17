"""Streamlit attraction explorer. Local session plans, no Drive writes or bookings."""
from __future__ import annotations

import json
from datetime import date
from html import escape
from urllib.parse import quote

import streamlit as st
import pandas as pd

from attractions_model import (
    load_attractions, load_base_routes, places_for_base, route_for,
    package_cost, approximate_feasibility, schedule_visit)
from calendar_model import calendar_plan
from planning_session import active_plan
from explorer_mutation_guard import can_edit, schedule_outing, unschedule_outing, SimulationWriteBlocked
from explorer_dialog_ui import render_attraction_dialog


def _destination_photo(destination: dict) -> None:
    photo=destination.get("photo")
    if not photo:
        st.markdown("<div class='attraction-no-photo'>✦ Explore a cidade</div>",
                    unsafe_allow_html=True)
        return
    st.markdown(
        f'<img class="attraction-photo" src="{escape(photo["url"],quote=True)}" '
        f'alt="Fotografia ilustrativa de {escape(destination["name"],quote=True)}" loading="lazy">',
        unsafe_allow_html=True)
    st.caption(f"Foto: {photo['author']} · {photo['license']} · "
               f"[crédito e licença]({photo['source_page']})")


def _label_cost(entry: dict) -> str:
    amount=entry["ticket"]["amount"]
    if amount is not None:
        return (f"{entry['ticket']['currency']} {amount:.2f}/adulto" +
                (" (ida e volta)" if entry["ticket"]["per"]=="adult_return" else ""))
    if entry["ticket"]["status"]=="not_applicable":
        return "Passeio externo sem bilhete"
    return "Ingresso a verificar"


def _attraction_filters(cat: dict) -> set[str]:
    return {a["category"] for a in cat["attractions"]}


def _selected_packages() -> dict[str,list[str]]:
    return active_plan()["packages"]


def _ux45_open_planner(destination_id: str) -> None:
    """Button callback runs before Streamlit instantiates navigation widgets."""
    from ux45_navigation_context import handoff
    handoff(st.session_state,area="Explorar",section="Passeios",
            destination_id=destination_id)
    st.session_state.pop("ux45_explore_result",None)


def _render_research_only_outings(base_id: str, catalog: dict) -> None:
    """Read-only general catalog; no undocumented journey is called feasible."""
    from outing_base_coverage_model import preview_for_base

    coverage = preview_for_base(base_id, catalog=catalog)
    st.info(
        "Catálogo geral: os 14 destinos e 65 atrações não foram pesquisados "
        "individualmente como passeios viáveis saindo de " +
        coverage["base_name"] + ". Esta consulta é exploratória e não "
        "altera as escolhas do roteiro oficial.")
    a, b, c = st.columns(3)
    a.metric("Destinos no catálogo geral", coverage["catalog_destinations"])
    b.metric("Atrações no catálogo geral", coverage["catalog_attractions"])
    c.metric("Destinos com trem histórico documentado",
             coverage["timed_destination_count"])
    st.caption(
        "Os tempos de trem são os menores tempos históricos publicados "
        "para UM trecho, estação a estação. Se houver duração típica da "
        "mesma fonte, ela aparece separadamente. Retorno, última milha, "
        "tarifas completas e datas de 2027 permanecem a verificar.")

    a, b = st.columns(2)
    with a:
        st.markdown("#### Com referência ferroviária")
        st.caption(str(coverage["timed_destination_count"]) +
                   " destino(s) com tempo histórico de ida registrado; "
                   "não significa bate-volta viável.")
    with b:
        st.markdown("#### Sem tempo ferroviário pesquisado")
        st.caption(str(coverage["unknown_destination_count"]) +
                   " destino(s) sem duração histórica neste estudo. "
                   "Não significa ausência de ligação.")
    selected_group = st.selectbox(
        "Cobertura ferroviária",
        ["Todos", "Com referência ferroviária", "Sem tempo pesquisado",
         "Destino local"],
        key="explore_readonly_rail_group")
    available = [
        row for row in coverage["destinations"]
        if (selected_group == "Todos"
            or selected_group == "Com referência ferroviária"
            and row["train_oneway_min"] is not None
            or selected_group == "Sem tempo pesquisado"
            and not row["local"] and row["train_oneway_min"] is None
            or selected_group == "Destino local" and row["local"])
    ]
    countries = sorted({x["country"] for x in coverage["destinations"]})
    chosen_countries = st.multiselect(
        "Filtrar países do catálogo", countries,
        default=countries, key="explore_readonly_countries")
    available = [x for x in available if x["country"] in chosen_countries]
    rows = []
    for item in available:
        if item["local"]:
            transport = "Local · acesso urbano desconhecido"
        elif item["train_oneway_min"] is not None:
            transport = (str(item["train_oneway_min"]) +
                         " min · menor tempo histórico publicado")
            if item["train_typical_historical_min"] is not None:
                transport += ("; típico " +
                              str(item["train_typical_historical_min"]) + " min")
        else:
            transport = "Tempo ferroviário ainda não pesquisado"
        rows.append({
            "Destino do catálogo": item["name"],
            "Atrações catalogadas": item["attraction_count"],
            "Referência de transporte": transport,
            "Viabilidade desde a base": "Não confirmada",
        })
    st.markdown("#### Destinos para consulta exploratória")
    if not available:
        st.info("Nenhum destino corresponde aos filtros escolhidos.")
        return
    st.dataframe(pd.DataFrame(rows), hide_index=True,
                 use_container_width=True)
    names = {row["destination_id"]: row["name"] for row in available}
    current = st.session_state.get("explore_readonly_destination")
    if current not in names:
        st.session_state["explore_readonly_destination"] = next(iter(names))
    chosen = st.selectbox(
        "Destino a explorar", list(names),
        format_func=lambda key: names[key],
        key="explore_readonly_destination")
    selected = next(row for row in available
                    if row["destination_id"] == chosen)
    if selected["train_oneway_min"] is not None:
        st.write("**Menor tempo histórico publicado (somente ida):** " +
                 str(selected["train_oneway_min"]) +
                 " min, estação a estação.")
        if selected["train_typical_historical_min"] is not None:
            st.write("**Tempo típico da mesma fonte:** " +
                     str(selected["train_typical_historical_min"]) + " min.")
        st.markdown("[Fonte ferroviária histórica](" +
                    selected["train_evidence_url"] + ")")
    elif selected["local"]:
        st.caption("Transporte local até as atrações ainda não documentado.")
    else:
        st.caption("Tempo de trem desde esta base ainda não pesquisado.")
    for attr in selected["attractions"]:
        st.markdown("- **" + escape(attr["name"]) + "** · " +
                    "[Fonte da atração](" + attr["source_url"] + ")")
    st.warning(
        "O catálogo geral não comprova a viabilidade deste passeio. "
        "Retorno, acessos, tarifa normal do casal e horários em 2027 "
        "não estão confirmados. Nenhuma tarifa ou escolha oficial foi alterada.")


def _render_dq32_macro_opportunities(base_id: str) -> None:
    """Broad travel discovery is not itinerary viability or an official edit."""
    from dq32_macro_opportunities_model import opportunity_overview

    overview=opportunity_overview(base_id)
    st.markdown("### Descoberta ampliada · DQ 3.2")
    st.caption(
        "Primeiro conhecer destinos e atrações; depois verificar transportes e "
        "passeios. Estas oportunidades são exploratórias, sem garantia de "
        "bate-volta e sem alterar o roteiro oficial.")
    a,b,c=st.columns(3)
    a.metric("Destinos no universo exploratório",overview["registry_destinations"])
    b.metric("Atrações locais documentadas",overview["known_local_attractions"])
    c.metric("Destinos com trem histórico publicado",overview["rail_time_documented_count"])
    st.caption(
        "O universo reúne pesquisa ampliada, catálogo histórico e fontes de "
        "turismo. Não representa quantidade de passeios viáveis. A ausência de "
        "uma ligação pesquisada não significa que a cidade seja inacessível.")
    kind=st.selectbox(
        "Oportunidades para investigar",
        ["Atrações da própria base", "Trem histórico documentado",
         "Outros destinos, transporte não pesquisado"],
        key="ux_dq32_opportunity_group")
    groups={
        "Atrações da própria base":overview["local_destinations"],
        "Trem histórico documentado":overview["historical_rail_destinations"],
        "Outros destinos, transporte não pesquisado":overview["unresearched_destinations"],
    }
    shown=groups[kind]
    if not shown:
        st.info("Ainda não temos evidências desta categoria para a base. "
                "Isso é uma lacuna de pesquisa, não uma avaliação negativa.")
        return
    items=[]
    for place in shown:
        duration=("Menor tempo histórico: "+
                  str(place["minimum_train_oneway_min"])+" min (ida)"
                  if place["minimum_train_oneway_min"] is not None
                  else "Local · acesso a verificar" if place["local"]
                  else "Transporte não pesquisado")
        items.append({"Destino":place["name"],
                      "Atrações identificadas":place["attraction_count"],
                      "Transporte":duration,
                      "Passeio confirmado":"Não"})
    st.dataframe(pd.DataFrame(items),hide_index=True,width="stretch")
    labels={place["destination_id"]:place["name"] for place in shown}
    key=st.session_state.get("ux_dq32_selected_destination")
    if key not in labels:
        st.session_state["ux_dq32_selected_destination"]=next(iter(labels))
    chosen=st.selectbox(
        "Ver fontes e atrações desta oportunidade",list(labels),
        format_func=lambda k:labels[k],key="ux_dq32_selected_destination")
    dest=next(place for place in shown if place["destination_id"]==chosen)
    if dest["train_source_url"]:
        st.markdown("[Fonte do menor tempo ferroviário histórico]("+
                    dest["train_source_url"]+")")
    if dest["attractions"]:
        for attraction in dest["attractions"]:
            st.markdown("- **"+escape(attraction["name"])+"** · "+
                        "[Fonte turística]("+attraction["source_url"]+")")
    else:
        st.caption("Destino identificado no universo de pesquisas, mas ainda "
                   "sem atrações individuais cadastradas nesta camada.")
    st.caption("Tempo de retorno, frequência, acessos, tarifas e disponibilidade "
               "em 2027 permanecem a pesquisar. Sem Haversine ou roteamento presumido.")


def render_explorer(trip_data: dict, sync_sources: dict, map_view) -> None:
    attractions=load_attractions()
    routes=load_base_routes()
    by_id={d["id"]:d for d in attractions["destinations"]}
    by_attr={a["id"]:a for a in attractions["attractions"]}

    st.markdown(
        "<div class='page-section'>O que poderemos conhecer a partir da nossa base?</div>",
        unsafe_allow_html=True)
    st.caption("Atrações consultadas em fontes de turismo. Duração de visita é sugestão editorial; "
               "tarifas de trem e de ingressos são exemplos publicados em 2026, não bilhetes de 2027. "
               "Trocar a cidade-base não aprova a decisão D-004.")
    # The exploratory city is shared with the comparison and finance pages.
    # The attractions route matrix currently supports four official bases only.
    from base_scenario_model import base_options, hypothetical_city_name
    from exploratory_selection import sync_city_widget, set_city_from_widget
    options=base_options()
    ids=[entry["id"] for entry in options]
    candidate=st.session_state.get("scenario_base_selected",active_plan()["base_city"])
    if candidate not in ids:
        candidate=active_plan()["base_city"]
    sync_city_widget("attractions_scenario_base",ids)
    base=st.selectbox("Cidade-base da pesquisa exploratória",ids,
        index=ids.index(candidate),
        format_func=lambda code:hypothetical_city_name(code,options),
        key="attractions_scenario_base",on_change=set_city_from_widget,
        args=("attractions_scenario_base",))
    st.session_state["scenario_base_selected"]=base
    official_base=active_plan()["base_city"]
    editable=can_edit(base, active_plan(), st.session_state.get("ux_mode", "Oficial"))
    if not editable:
        st.info("Simulação independente: o roteiro oficial permanece em "+
                by_id[official_base]["name"]+
                ". As seleções de passeios oficiais não podem ser alteradas "
                "por engano ao avaliar outra cidade.")
    _render_dq32_macro_opportunities(base)
    if base not in {"mulhouse","strasbourg","metz","nancy"}:
        _render_research_only_outings(base,attractions)
        return
    available=places_for_base(attractions,routes,base)
    country_options=sorted({p["destination"]["country"] for p in available})
    category_options=sorted(_attraction_filters(attractions))
    with st.expander("Filtrar países, atrações e tipo de viagem",expanded=False):
        a,b,c=st.columns(3,gap="medium")
        with a:
            selected_countries=st.multiselect("Países",country_options,
                                              default=country_options,key="explore_countries")
        with b:
            selected_categories=st.multiselect("Tipo de atração",category_options,
                                               default=category_options,key="explore_categories")
        with c:
            transport_filter=st.selectbox(
                "Acesso",["Todos","Apenas trem documentado / local","Pernoite em estudo"],
                key="explore_route_filter")
        x,y=st.columns(2,gap="medium")
        with x:
            ticket_filter=st.selectbox(
                "Custo de acesso",["Todos","Passeio externo","Ingresso publicado","Ingresso a cotar"],
                key="explore_ticket_filter")
        with y:
            interest_filter=st.selectbox(
                "Minha preferência",["Todas","Quero visitar","Opcional","Descartar"],
                key="explore_interest_filter")
        max_minutes=st.slider("Tempo máximo de trem conhecido por trecho (minutos)",
                              20,180,180,10,key="explore_max_minutes",
                              help="Não equivale ao tempo porta a porta. Rotas sem tempo confirmado ficam visíveis em Todos.")
    filtered=[]
    for item in available:
        dest=item["destination"]
        r=item["route"]
        marks_for_filter=st.session_state.get("explore_marks",{})
        desired_ticket={"Passeio externo":"not_applicable",
                        "Ingresso publicado":"operator_published",
                        "Ingresso a cotar":"unknown"}.get(ticket_filter)
        relevant=[x for x in attractions["attractions"]
                  if x["destination_id"]==dest["id"] and x["category"] in selected_categories
                  and (desired_ticket is None or x["ticket"]["status"]==desired_ticket)
                  and (interest_filter=="Todas"
                       or marks_for_filter.get(x["id"],"Opcional")==interest_filter)]
        if dest["country"] not in selected_countries or not relevant:
            continue
        if transport_filter=="Apenas trem documentado / local" and (
            r["train_minutes_one_way"] is None and base!=dest["id"]):
            continue
        if transport_filter=="Pernoite em estudo" and dest["kind"]!="overnight":
            continue
        if r["train_minutes_one_way"] is not None and r["train_minutes_one_way"]>max_minutes:
            continue
        filtered.append({**item,"filtered_attractions":relevant})
    packages=_selected_packages()
    all_selected=[x for selected in packages.values() for x in selected]
    cost=package_cost(attractions,routes,base,all_selected)

    counts=[
        ("Destinos exibidos",len(filtered),"Inclui cidades e região alpina"),
        ("Atrações encontradas",sum(len(x["filtered_attractions"]) for x in filtered),
         "Filtro por categoria aplicado"),
        ("Rotas com tempo publicado",sum(
            x["route"]["train_minutes_one_way"] is not None for x in filtered),
         "Tempo estação a estação"),
        ("Opções alpinas",sum(x["destination"]["kind"]=="overnight" for x in filtered),
         "Pernoite pode ser necessário")
    ]
    for col,(title,value,subtitle) in zip(st.columns(4,gap="small"),counts):
        with col:
            st.markdown("<div class='page-stat page-stat--blue'>"
                        f"<div class='page-stat__label'>{escape(title)}</div>"
                        f"<div class='page-stat__value'>{value}</div>"
                        f"<div class='page-stat__hint'>{escape(subtitle)}</div></div>",
                        unsafe_allow_html=True)
    if filtered:
        markers=[{**by_id[base],"status":"roteiro_proposto","description":"Base hipotética"}]
        markers.extend([{**it["destination"],"status":"candidata" if it["destination"]["kind"]=="overnight" else "opcional",
                         "description":"Destino pesquisado"} for it in filtered if it["destination"]["id"]!=base])
        st.markdown("<div class='page-section'>Mapa dos destinos pesquisados</div>",
                    unsafe_allow_html=True)
        map_view(markers,height=360,show_labels=False,center=(48.0,7.4),zoom=5.8)
        st.caption("Pinos das cidades e regiões; o mapa não traça ferrovias nem apresenta geocodificação "
                   "precisa de cada atração. Distância na ficha é somente em linha reta.")
    else:
        st.info("Nenhum destino corresponde aos filtros escolhidos.")

    st.markdown("<div class='page-section'>Destinos e passeios</div>",unsafe_allow_html=True)
    feedback=st.session_state.pop("explore_feedback",None)
    if feedback:
        st.success(feedback+" Alterações ainda não foram salvas remotamente.")
    outcome=st.session_state.get("ux45_explore_result")
    if outcome:
        message=("incluído" if outcome["action"]=="added" else
                 "atualizado" if outcome["action"]=="updated" else "removido")
        st.success(outcome["name"]+" "+message+" no planejamento desta sessão.")
        st.caption(str(outcome["attraction_count"])+" atração(ões) · "+
                   ("período "+outcome["period"] if outcome["period"]!="Ainda não definido"
                    else "sem período definido")+" · "+
                   (str(len(outcome["dates"]))+" data(s) planejada(s)"
                    if outcome["dates"] else "sem data definida")+
                   (" · transporte de retorno a confirmar" if outcome["transport_pending"]
                    else "")+" · ainda não salvo remotamente.")
        next_col,view_col=st.columns(2)
        if next_col.button("Continuar explorando",key="ux45_explore_continue"):
            st.session_state.pop("ux45_explore_result",None)
            st.rerun()
        if outcome["action"]!="removed":
            view_col.button("Ver no meu roteiro",key="ux45_explore_to_planner",
                            on_click=_ux45_open_planner,
                            args=(outcome["destination_id"],))
    for start in range(0,len(filtered),2):
        for col,item in zip(st.columns(2,gap="medium"),filtered[start:start+2]):
            d=item["destination"]
            r=item["route"]
            km=item["distance_straight_km"]
            example_ids=[a["id"] for a in item["filtered_attractions"][:3]]
            partial=package_cost(attractions,routes,base,example_ids)
            def fmt(cost):return f"€{cost:.2f}"
            if r["train_minutes_one_way"] is not None:
                travel_label=f"{r['train_minutes_one_way']} min no trem/trecho (ida)"
                fare=(f"Desde €{r['fare_eur_person_oneway']:.2f} por pessoa, "
                      "só ida, histórico e condicional; volta a verificar"
                      if r["fare_eur_person_oneway"] is not None else
                      "Tarifa de ida e volta não pesquisada")
            elif d["id"]==base:
                travel_label="Na cidade-base"
                fare="Transporte local a verificar"
            else:
                travel_label="Trem/tempo a verificar"
                fare="Tarifa ida+volta a verificar"
            with col:
                with st.container(border=True):
                    _destination_photo(d)
                    st.markdown(f"### {escape(d['name'])} · {escape(d['country'])}")
                    st.caption(f"{len(item['filtered_attractions'])} atrações catalogadas · "
                               f"{km:.1f} km em linha reta (NÃO é distância de trem)")
                    st.markdown(f"**{escape(travel_label)}**  \n{escape(fare)}")
                    st.caption(" · ".join(a["name"] for a in item["filtered_attractions"][:3]))
                    st.caption(approximate_feasibility(d,r))
                    if not partial["complete"]:
                        st.caption(f"Conhecido nas 3 atrações exibidas: "
                                   f"€{partial['known_by_currency']['EUR']:.2f} e "
                                   f"CHF{partial['known_by_currency']['CHF']:.2f}; "
                                   "não é custo completo")
                    if st.button("Ver atrações e montar passeio",key=f"explore_open_{d['id']}",
                                 use_container_width=True):
                        st.session_state["explore_selected_destination"]=d["id"]
                        st.rerun()

    chosen=st.session_state.get("explore_selected_destination")
    if chosen in by_id:
        render_attraction_dialog(chosen,base,attractions,routes,by_id,by_attr)

    st.markdown("<div class='page-section'>Minha lista de passeios e custos conhecidos</div>",
                unsafe_allow_html=True)
    if not packages:
        st.info("Abra um destino, escolha de uma a cinco atrações e salve o passeio. "
                "Depois você poderá adicioná-lo ao calendário e simular o custo.")
    else:
        current_list=[a for selected in packages.values() for a in selected]
        current_cost=package_cost(attractions,routes,base,current_list)
        st.markdown("**Destinos da lista:** "+", ".join(by_id[k]["name"] for k in packages))
        for col,(title,value,desc) in zip(st.columns(3,gap="small"),[
            ("Bilhetes conhecidos em EUR",f"€ {current_cost['known_by_currency']['EUR']:.2f}",
             "Para dois, com desconto quando indicado"),
            ("Bilhetes conhecidos em CHF",f"CHF {current_cost['known_by_currency']['CHF']:.2f}",
             "Separado de euros"),
            ("Custos ainda não verificados",str(len(current_cost["missing"])),
             "Transporte, ingressos ou custos locais")
        ]):
            with col:
                st.markdown("<div class='page-stat page-stat--mint'>"
                            f"<div class='page-stat__label'>{escape(title)}</div>"
                            f"<div class='page-stat__value'>{escape(value)}</div>"
                            f"<div class='page-stat__hint'>{escape(desc)}</div></div>",
                            unsafe_allow_html=True)
        with st.expander("Discriminar valores e condições",expanded=False):
            if current_cost["breakdown"]:
                st.dataframe(pd.DataFrame(current_cost["breakdown"]),hide_index=True,
                             use_container_width=True)
            if current_cost["conditional"]:
                st.warning("Tarifas reduzidas condicionais: "+"; ".join(current_cost["conditional"]))
            if current_cost["missing"]:
                st.write("**Pendente:** "+ "; ".join(current_cost["missing"]))
        st.caption("Valores parciais: não incluem passagem normal quando só há tarifa Fluo, "
                   "cartão Fluo, hotel, refeições, táxis, viagem até estação nem horários de retorno. "
                   "Nenhuma tarifa de 2027 foi confirmada.")

        st.markdown("#### Reservar um dia no calendário *provisório*")
        from datetime import date as Date
        depart=st.session_state.get("itinerary_departure",Date.fromisoformat(trip_data["departure_candidate"]))
        total_days=st.session_state.get("itinerary_total_days",70)
        initial=st.session_state.get("itinerary_vacation_days",25)
        italy=st.session_state.get("itinerary_italy_days",10)
        setup=st.session_state.get("itinerary_setup_days",4)
        days=calendar_plan(depart,total_days,italy,initial,setup)
        allowed=[x for x in days if x["stage"]=="França"
                 and x["activity"]!="Instalação" and
                 "Trabalho remoto" not in x["activity"]]
        if allowed:
            left,right=st.columns(2,gap="medium")
            with left:
                destid=st.selectbox("Passeio da lista",list(packages),
                                     format_func=lambda k:by_id[k]["name"],key="explore_schedule_destination")
            with right:
                picked=st.selectbox("Dia disponível (férias ou fim de semana)",
                                    [r["date"] for r in allowed],key="explore_schedule_day")
            if st.button("Adicionar passeio ao calendário",key="explore_schedule_add",
                         use_container_width=True,disabled=not editable):
                try:
                    schedule_visit(days,active_plan()["assignments"],picked,destid)
                    schedule_outing(base,st.session_state.get("ux_mode","Oficial"),picked,destid)
                    st.rerun()
                except (ValueError, SimulationWriteBlocked) as e:
                    st.warning(str(e))
            assignments=st.session_state.get("explore_calendar",{})
            if assignments:
                for day,destid in sorted(assignments.items()):
                    one,two=st.columns([5,1],gap="small")
                    with one:st.markdown(f"**{day}:** {by_id.get(destid,{}).get('name',destid)}")
                    with two:
                        if st.button("Remover",key=f"explore_calendar_remove_{day}",disabled=not editable):
                            try:
                                unschedule_outing(base,st.session_state.get("ux_mode","Oficial"),day)
                                st.rerun()
                            except (ValueError, SimulationWriteBlocked) as exc:
                                st.warning(str(exc))

        st.markdown("#### Levar o custo conhecido ao orçamento")
        left,right=st.columns(2,gap="medium")
        with left:
            euro_fx=st.number_input("Câmbio hipotético R$/€",min_value=4.0,max_value=10.0,
                                    value=6.3,step=.05,key="explore_euro_fx")
        with right:
            franc_fx=st.number_input("Câmbio hipotético R$/CHF",min_value=4.0,max_value=12.0,
                                     value=7.1,step=.05,key="explore_chf_fx")
        def _send_budget_reference() -> None:
            # on_click runs at the start of the next rerun, before navigation radio
            # is instantiated; otherwise Streamlit would reject key mutation.
            st.session_state["explore_budget_reference"]={
                "eur":current_cost["known_by_currency"]["EUR"],
                "chf":current_cost["known_by_currency"]["CHF"],
                "fx_eur":euro_fx,"fx_chf":franc_fx,
                "base":base,"incomplete":not current_cost["complete"],
                "destinations":list(packages)}
            st.session_state["unified_city"]=by_id[base]["name"]
            st.session_state["main_navigation"]="Orçamento"
        st.button("Comparar no orçamento sem dupla contagem →",
                  key="explore_to_budget",use_container_width=True,
                  on_click=_send_budget_reference)
        with st.expander("Backup técnico das atrações (opcional)"):
            st.caption("A seleção completa está no planejamento. "
                       "Este arquivo separado serve apenas como cópia de segurança.")
            export={"base":base,"preferences":active_plan().get("preferences",{}),
                    "packages":active_plan()["packages"],
                    "calendar":active_plan()["assignments"],
                    "cost_known":current_cost,
                    "note":"Custo parcial com referências históricas, não cotação de 2027."}
            st.download_button("Baixar arquivo de backup",
                               data=json.dumps(export,ensure_ascii=False,indent=2),
                               file_name="nossa_europa_2027_atracoes.json",
                               mime="application/json",use_container_width=True)
    st.caption("Fotos: Wikimedia Commons com atribuição e licença em cada card. "
               "Fontes de turismo e operadores consultadas em novembro/2026; "
               "rever todas as datas e condições antes de viajar.")
