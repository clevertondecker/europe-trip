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
    return st.session_state.setdefault("explore_packages",{})


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
    if "explore_base" not in st.session_state:
        suggested=st.session_state.get("unified_city")
        st.session_state["explore_base"]=(
            suggested.casefold() if isinstance(suggested,str) and
            suggested.casefold() in {"mulhouse","strasbourg","metz","nancy"} else "mulhouse")
    base=st.selectbox("Nossa cidade-base francesa (simulação)",
                      ["mulhouse","strasbourg","metz","nancy"],
                      format_func=lambda code: by_id[code]["name"],
                      key="explore_base")
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
    for start in range(0,len(filtered),2):
        for col,item in zip(st.columns(2,gap="medium"),filtered[start:start+2]):
            d=item["destination"]
            r=item["route"]
            km=item["distance_straight_km"]
            example_ids=[a["id"] for a in item["filtered_attractions"][:3]]
            partial=package_cost(attractions,routes,base,example_ids)
            def fmt(cost):return f"€{cost:.2f}"
            if r["train_minutes_one_way"] is not None:
                travel_label=f"{r['train_minutes_one_way']} min no trem/trecho"
                fare=f"€{r['fare_eur_person_oneway']*4:.2f} / casal ida+volta*"
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
    if chosen and chosen in by_id:
        d=by_id[chosen]
        st.divider()
        st.markdown(f"<div class='page-section'>Atrações em {escape(d['name'])}</div>",
                    unsafe_allow_html=True)
        r=route_for(routes,base,chosen)
        st.caption(f"Da base {by_id[base]['name']} · "
                   f"trem: {str(r['train_minutes_one_way'])+' min/trecho' if r['train_minutes_one_way'] is not None else 'não verificado'} "
                   "· duração porta a porta ainda não pesquisada")
        attractions_here=[a for a in attractions["attractions"] if a["destination_id"]==chosen]
        marks=st.session_state.setdefault("explore_marks",{})
        for a in attractions_here:
            with st.container(border=True):
                left,right=st.columns([3,1],gap="medium")
                with left:
                    st.markdown(f"**{escape(a['name'])}**")
                    st.write(a["summary"])
                    st.caption(f"{a['category']} · visita sugerida: {a['visit_minutes']} min "
                               f"(hipótese) · {_label_cost(a)}")
                    if a["seasonality"]:
                        st.caption("Sazonalidade: "+a["seasonality"])
                    st.markdown(f"[Fonte da atração]({a['source_urls'][0]}) · "
                                f"[Abrir localização no Google Maps]"
                                f"(https://www.google.com/maps/search/?api=1&query="
                                f"{quote(a['name']+', '+d['name'])})")
                with right:
                    current=marks.get(a["id"],"Opcional")
                    marked=st.selectbox("Interesse",["Quero visitar","Opcional","Descartar"],
                                        index=["Quero visitar","Opcional","Descartar"].index(current),
                                        key=f"explore_mark_{a['id']}")
                    marks[a["id"]]=marked
        st.markdown("#### Montar passeio nessa cidade")
        previous=packages.get(chosen,[])
        if not previous:
            previous=[a["id"] for a in attractions_here[:3]]
        chosen_ids=st.multiselect(
            "Selecione até cinco atrações para visitar no mesmo passeio",
            [a["id"] for a in attractions_here],
            default=previous,max_selections=5,
            format_func=lambda code:by_attr[code]["name"],
            key=f"explore_package_select_{chosen}")
        time_total=sum(by_attr[x]["visit_minutes"] for x in chosen_ids)
        st.caption(f"Tempo apenas dentro das atrações: {time_total//60}h{time_total%60:02d}. "
                   "Não inclui caminhada, refeições, espera ou viagem desde a base.")
        if st.button("Salvar passeio na minha lista",key=f"explore_save_{chosen}",
                     use_container_width=True,disabled=not chosen_ids):
            packages[chosen]=chosen_ids
            st.session_state["explore_packages"]=packages
            st.success("Passeio incluído na lista desta sessão. O custo será calculado pela base selecionada.")
        if chosen in packages:
            if st.button("Remover passeio da lista",key=f"explore_remove_{chosen}",
                         use_container_width=True):
                packages.pop(chosen,None)
                st.session_state["explore_packages"]=packages
                st.rerun()

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
                         use_container_width=True):
                try:
                    st.session_state["explore_calendar"]=schedule_visit(
                        days,st.session_state.get("explore_calendar",{}),picked,destid)
                    st.success("Dia adicionado ao calendário provisório desta sessão.")
                except ValueError as e:
                    st.warning(str(e))
            assignments=st.session_state.get("explore_calendar",{})
            if assignments:
                for day,destid in sorted(assignments.items()):
                    one,two=st.columns([5,1],gap="small")
                    with one:st.markdown(f"**{day}:** {by_id.get(destid,{}).get('name',destid)}")
                    with two:
                        if st.button("Remover",key=f"explore_calendar_remove_{day}"):
                            st.session_state["explore_calendar"]={k:v for k,v in assignments.items() if k!=day}
                            st.rerun()

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
        export={
            "saved_at":"2026-11-14","base":base,
            "preferences":marks,"packages":packages,
            "calendar":st.session_state.get("explore_calendar",{}),
            "cost_known":current_cost,
            "note":"Exportação da sessão, não sincronizada com Drive. Valores históricos/parciais."
        }
        st.download_button("Exportar plano desta sessão (JSON)",
                           data=json.dumps(export,ensure_ascii=False,indent=2),
                           file_name="nossa_europa_2027_atracoes.json",
                           mime="application/json",use_container_width=True)
    st.caption("Fotos: Wikimedia Commons com atribuição e licença em cada card. "
               "Fontes de turismo e operadores consultadas em novembro/2026; "
               "rever todas as datas e condições antes de viajar.")
