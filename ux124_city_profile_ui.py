"""UX124 shared, topic-based research profile. No planning writes."""
from __future__ import annotations
import streamlit as st
from ux124_city_profile_model import (TOPICS,city_profile,
    personalize_routes,route_scope,ROUTE_SCOPES,MISSING_WISHLIST_SCOPE)
from ux502_destination_interests_model import empty_interests,ordered_interests,LABELS
from routes7_comparison_projection import format_minutes
from ux47_photo_ui import photo_markup,photo_credit
from ux113_comparison_panorama_ui import coworking_night_status
from ux124b_profile_presentation import city_intro,practical_facts,compact_money,route_preview,route_list_html,ticket_text,typical_time_label,logistics_table,destination_name,editorial_risk_text

def money(value,unit="€"):
    return ("Não pesquisado" if value is None else
            f"{value:,.2f}".replace(",","_").replace(".",",").replace("_",".")+" "+unit)

def source(url,label="Fonte"):
    if isinstance(url,str) and url.startswith("https://"):
        st.markdown("["+label+"]("+url+")")

def _facts(rows):
    for item in rows:
        st.write(item["summary"])
        source(item.get("source_url"))
        st.caption(str(item.get("observed_at",""))+" · "+str(item.get("limitations","")))

def _evidence(view,*sections):
    rows=[e for e in view["profile"]["evidence"] if e["section"] in sections]
    if rows:
        with st.expander("Fontes e contexto do assunto"):
            _facts(rows)

def _remember_control(key,shadow):
    value=st.session_state.get(key)
    if value is not None:
        st.session_state[shadow]=value

def _control(label,options,default,key,*,hidden=False):
    # A widget disappears on a handoff; its existing session-only shadow
    # retains the valid selection without a second navigation mechanism.
    shadow="rec03a_profile_view_"+key
    saved=st.session_state.get(shadow,default)
    if saved not in options:
        saved=default
    if st.session_state.get(key) not in options:
        st.session_state[key]=saved
    value=st.segmented_control(label,list(options),key=key,
        label_visibility="collapsed" if hidden else "visible",
        on_change=_remember_control,args=(key,shadow))
    return value if value in options else saved

def _open_wishlist_logistics(prefix,base):
    # Explicit intent overrides the previous filter; ordinary returns restore it.
    for key,value in ((prefix+"_topic_"+base,"Logística"),(prefix+"_routes_"+base,ROUTE_SCOPES[0])):
        st.session_state[key]=value
        st.session_state["rec03a_profile_view_"+key]=value

def _overview_details(v):
    p=v["profile"]
    with st.expander("Fontes e pendências da pesquisa",expanded=False):
        st.caption(f'{v["housing"]["count"]} anúncios históricos · {v["catalog_destination_count"]} destinos no catálogo atual.')
        demo=p.get("demographics") or {}
        if demo.get("population_municipal") is not None:
            st.write(f'{demo["population_municipal"]:,}'.replace(",",".")+
                       f' habitantes no município · {demo["reference_year"]} · não área metropolitana')
            source(demo.get("source_url"),"Fonte estatística")
        # Retain the exact source summary as documentation; it is not lead copy.
        st.caption(p["summary"])
        facts={e["summary"] for e in p["evidence"]}
        for item in dict.fromkeys(p["advantages"]+p["limitations"]):
            if item not in facts:
                st.caption(item)
        historical=v["editorial"]
        if historical:
            st.caption("Avaliação editorial de 2026, não pontuação atual.")
            st.write(historical["summary"])
            for item in historical["advantages"]+historical["risks"]:
                st.caption(item)
            source(v["editorial_source"],"Matriz histórica")
        _facts(p["evidence"])
        source(p["official_statistics_source"]["url"],"Base estatística oficial")
        for item in dict.fromkeys(p["research_gaps"]+v["pack"].get("missing",[])+v["context_gaps"]):
            st.caption(item)
        if v["city"].get("screening_notes"):
            st.caption(v["city"]["screening_notes"])
        st.caption("Dados ausentes não equivalem a zero. Pesquisa histórica não é cotação, reserva ou nota de qualidade.")

def _overview(v):
    p=v["profile"]
    st.markdown("#### Como seria morar aqui por dois meses?")
    st.write(city_intro(p))
    desired=route_scope(v["routes"],ROUTE_SCOPES[0])
    h=v["housing"]
    with st.container(key="ux124b-overview-metrics"):
        a,b=st.columns(2,gap="small")
        with a:
            with st.container(border=True,key="ux124b-rent"):
                st.metric("Aluguel mensal · mediana histórica",compact_money(h["median_eur_month"]))
                st.caption(f'{h["count"]} anúncios de 2026 · não cotação de 2027'
                           if h["count"] else "Sem amostra — não significa falta de imóveis.")
        with b:
            with st.container(border=True,key="ux124b-routes-metric"):
                st.metric("Destinos desejados com referência de ida",
                          f'{desired["timed"]} de {desired["eligible"]}' if desired["eligible"] else "—")
                if desired["total"]:
                    gaps=[]
                    if desired["missing"]:
                        gaps.append(f'{desired["missing"]} sem tempo')
                    if desired["local"]:
                        gaps.append(f'{desired["local"]} locais (fora do denominador)')
                    st.caption(" · ".join(gaps+["Não confirma bate-volta."]))
                else:
                    st.caption("Escolha destinos em Minha lista para personalizar esta leitura.")
    preview=route_preview(v["routes"])
    if preview:
        st.markdown("**Conexões com seus destinos**")
        st.markdown(route_list_html(preview),unsafe_allow_html=True)
        st.caption("Referências de ida; retorno, frequência e última milha a confirmar.")
        st.button("Ver todos os meus destinos",key=v["widget_prefix"]+"_overview_logistics_"+v["city"]["id"],
                  on_click=_open_wishlist_logistics,args=(v["widget_prefix"],v["city"]["id"]))
        missing=[r["name"] for r in desired["rows"] if r["priority"]=="must_visit" and r["cell"]["category"]=="no_time"]
        if missing:
            st.warning("Imperdíveis sem tempo pesquisado: "+", ".join(missing))
    office=(v["cost"] or {}).get("coworking")
    pack_office=v["pack"].get("remote_work",{}).get("coworking_reference")
    facts=practical_facts(p)
    with st.container(key="ux124b-overview-considerations"):
        if facts:
            st.markdown("**Características complementares**")
            st.markdown("\n".join("- "+x for x in facts))
        st.markdown("**Pontos de atenção**")
        if v["city"].get("screening_notes"):
            st.write(v["city"]["screening_notes"])
            st.caption("Observação da pesquisa histórica.")
        historical=v["editorial"]
        if historical and historical.get("risks"):
            st.caption(editorial_risk_text(historical["risks"][0]))
        st.caption("Ainda pendente para 2027: contrato, disponibilidade, taxas e caução da moradia.")
    st.markdown("**Trabalho remoto**")
    if office:
        st.write(office["name"]+" — "+coworking_night_status(office))
        if office.get("schedule"):
            st.caption("Horário publicado: "+office["schedule"])
    elif pack_office:
        st.write(pack_office["name"])
        st.caption("Horário: "+str(pack_office.get("hours") or "Não pesquisado")+" · modalidade a confirmar.")
    else:
        st.caption("Coworking ainda não pesquisado.")
    st.caption("Internet do imóvel não confirmada.")
    if not preview:
        st.caption("Retorno ferroviário e última milha a confirmar.")
    _overview_details(v)

def _housing(v):
    st.markdown("#### Moradia e bairros")
    h=v["housing"]
    if h["count"]:
        with st.container(border=True):
            st.metric("Mediana mensal da amostra",compact_money(h["median_eur_month"]))
            st.caption("Faixa: "+compact_money(h["minimum_eur_month"])+" a "+compact_money(h["maximum_eur_month"])+
                       f' · {h["count"]} anúncios de 2026 · não cotação de 2027.')
    else:
        st.metric("Mediana mensal da amostra","Não pesquisado")
        st.caption("Sem amostra histórica, não significa falta de imóveis.")
    offers=v["city"]["housing_offers"]
    if offers:
        with st.expander("Consultar anúncios históricos"):
            st.dataframe([{"Imóvel":o["observed_title_or_address"],
                           "€/mês":o["monthly_eur"],"m²":o["size_m2"],
                           "Dois adultos":"Documentados" if o.get("two_adults_confirmed") is True else "Não confirmados",
                           "Contas":o.get("utilities"),"Data":o.get("checked_at"),
                           "Internet":"Confirmada" if o.get("internet_verified") else "A verificar",
                           "Taxas":"Documentadas" if o.get("all_mandatory_fees_known") else "A verificar",
                           "Estação próxima":"Verificada" if o.get("near_station_verified") else "A verificar",
                           "56–60 noites":"Confirmadas" if o.get("short_stay_56_to_60_nights_confirmed") else "A verificar",
                           "Disponibilidade 2027":"Confirmada" if o.get("available_for_autumn_2027") else "A verificar",
                           "Fonte":o.get("listing_url") or o["catalogue_url"]} for o in offers],
                         hide_index=True,width="stretch",
                         column_config={"Fonte":st.column_config.LinkColumn(display_text="Consultar")})
    st.markdown("**Bairros para investigar**")
    neighborhoods=v["pack"].get("neighborhoods",[])
    if not neighborhoods:
        st.caption("Ainda não pesquisados.")
    for item in neighborhoods:
        st.markdown("**"+item["name"]+"** — "+item["reason_to_investigate"])
        source(item["source_url"],"Referência do bairro")
    if v["cost"]:
        st.caption("Aluguel residencial convencional: "+money(v["cost"]["residential_rent_eur_sqm_month"],"€/m²/mês"))
        source(v["round2_sources"][0]["url"],"Indicador residencial, não temporada")
    if v["market"] or v["editorial"] or v["audit"]:
        with st.expander("Outras referências históricas de imóveis e contrato"):
            # Separate source samples; never pool these into the canonical median.
            if v["market"]:
                known={(x["observed_title_or_address"].casefold(),x["monthly_eur"],x["size_m2"]) for x in offers}
                for item in v["market"]["offers"]:
                    key=(item["street"].casefold(),item["observed_eur_month"],item["size_m2"])
                    if key not in known:
                        st.write(item["street"]+" · "+money(item["observed_eur_month"])+"/mês · "+str(item["size_m2"])+" m²")
                        source(item["source_url"],"Catálogo histórico")
            if v["editorial"]:
                for item in v["editorial"]["sample_ads"]:
                    source(item["url"],item["label"])
            if v["audit"]:
                for item in v["audit"]["housing"]+v["audit"]["risks"]:
                    st.caption(item)
                for url in v["audit"]["source_urls"]:
                    source(url)
            st.caption("Bail mobilité depende de elegibilidade; não presumir contrato aplicável.")
            source(v["round2_sources"][1]["url"],"Regras contratuais francesas — referência histórica")
    st.caption("Antes de reservar: confirmar estadia para dois, internet, taxas, caução e disponibilidade em 2027.")
    _evidence(v,"housing")

def _logistics(v):
    st.markdown("#### Conexões de ida")
    desired=route_scope(v["routes"],ROUTE_SCOPES[0])
    scope=_control("Destinos",ROUTE_SCOPES,ROUTE_SCOPES[0] if desired["total"] else ROUTE_SCOPES[1],
                   v["widget_prefix"]+"_routes_"+v["city"]["id"])
    selection=route_scope(v["routes"],scope)
    rows=selection["rows"]
    counts=[f'{scope}: {selection["timed"]}/{selection["eligible"]} destinos não locais com tempo de ida']
    if selection["local"]:
        counts.append(f'{selection["local"]} locais')
    if selection["missing"]:
        counts.append(f'{selection["missing"]} sem tempo')
    if scope==MISSING_WISHLIST_SCOPE:
        st.caption(f'{selection["missing"]} sem tempo. Não confirma bate-volta.')
    else:
        st.caption(" · ".join(counts)+". Não confirma bate-volta.")
    if scope==MISSING_WISHLIST_SCOPE:
        st.caption("Destinos ativos da sua lista sem referência de tempo de ida. "
                   "Não significa que o trajeto seja impossível; o acesso local e as "
                   "referências indicativas não entram neste recorte.")
    if not rows:
        if scope==MISSING_WISHLIST_SCOPE:
            st.info("Nenhum destino da sua lista neste recorte." if desired["total"] else
                    "Sua lista ainda não tem destinos ativos. Escolha lugares em Minha lista.")
        else:
            st.info("Nenhum destino neste recorte. Altere o filtro ou consulte Minha lista.")
    else:
        table,has_typical=logistics_table(rows)
        st.dataframe(table,hide_index=True,width="stretch")
        if not has_typical:
            st.caption("Tempo médio/típico ainda não documentado neste recorte.")
        elif any(r.get("Tempo médio/típico")=="—" for r in table):
            st.caption("— = tempo médio/típico não documentado.")
        with st.expander("Fontes, estações e divergências por destino"):
            chosen=st.selectbox("Detalhar destino", [r["destination_id"] for r in rows],
                                format_func=lambda k:next(destination_name(r) for r in rows if r["destination_id"]==k),
                                key=v["widget_prefix"]+"_route_detail_"+v["city"]["id"]+"_"+str(ROUTE_SCOPES.index(scope)))
            route=next(r for r in rows if r["destination_id"]==chosen)
            cell=route["cell"]
            st.write(cell["label"])
            st.caption(typical_time_label(route))
            st.caption("Data da fonte histórica: "+str(route["source_date"] or "não documentada"))
            if route["historical_typical"] is not None and typical_time_label(route)==cell["typical_label"]:
                st.caption("Tempo típico histórico: "+format_minutes(route["historical_typical"]))
            for field in ("station_caveat","evidence_notes","comparability","gap_checked_at"):
                if cell.get(field):
                    st.caption(str(cell[field]))
            if cell.get("legacy_divergent_sources") or cell.get("reference_differs_from_legacy"):
                st.warning("Tempos publicados diferentes: condições ainda não reconciliadas.")
            for label,field in (("Fonte apresentada","source_url"),("Fonte histórica","historical_source_url"),
                                ("Referência indicativa","reference_source_url")):
                source(cell.get(field),label)
            for obs in route["observations"]:
                fields=[]
                for field,label in (("minimum_oneway_min","Mínimo"),("typical_oneway_min","Típico")):
                    if obs.get(field) is not None:
                        fields.append(label+": "+str(obs[field])+" min")
                for field,label in (("evidence_date","Data"),("origin_station","Origem"),
                                    ("destination_station","Chegada"),("source_dataset","Registro de origem")):
                    if obs.get(field):
                        fields.append(label+": "+str(obs[field]))
                if fields:
                    st.caption(" · ".join(fields))
                if obs.get("notes"):
                    st.caption(str(obs["notes"]))
                for gap in obs.get("missing",[]):
                    st.caption(str(gap))
                source(obs.get("source_url"),"Observação original")
            for gap in route["research_gaps"]:
                st.caption(gap)
            for fare in route["fares"]:
                st.write(money(fare["amount"])+"/pessoa/ida")
                st.caption(str(fare["conditions"] or "Condições a verificar")+" · "+str(fare["observed_at"] or "Data a verificar"))
                source(fare["source_url"],"Fonte da tarifa")
    with st.expander("Cobertura de pesquisa · catálogo e minha lista"):
        for name in ROUTE_SCOPES[:2]:
            data=route_scope(v["routes"],name)
            st.caption(f'{name}: {data["historical"]} históricos · {data["indicative"]} indicativos · '
                       f'{data["local"]} locais · {data["missing"]} sem tempo (total: {data["total"]}).')
    with st.expander("Outras tarifas e frequências da base"):
        found=False
        st.caption("Tarifas de um destino: consulte os detalhes acima. As referências abaixo são históricas e independentes do filtro.")
        if v["market"]:
            for r in v["market"]["rail"]:
                if r["discounted_eur_leg_person"] is not None:
                    found=True
                    st.write(r["destination"]+" · "+money(r["discounted_eur_leg_person"])+"/pessoa/ida")
                    st.caption("Tarifa reduzida Carte Fluo; cartão e elegibilidade separados.")
                    source(r["source_url"])
        for r in v["pack"].get("weekend_rail_references",[]):
            found=True
            st.write(r["destination_id"]+" · "+r["frequency_description"])
            if r["fare_eur_oneway_with_condition"] is not None:
                st.caption(money(r["fare_eur_oneway_with_condition"])+"/pessoa/ida · "+r["fare_condition"])
            source(r["source_url"])
        if not found:
            st.caption("Sem referência adicional de tarifa ou frequência para esta base.")
        st.caption("Não somar tarifas condicionadas como custo confirmado do casal.")
    if v["extra_routes"]:
        with st.expander("Conexões fora do catálogo de destinos"):
            for r in v["extra_routes"]:
                st.write(r["destination_name"]+" · "+str(r["oneway_minutes"])+" min de ida")
                source(r["source_url"])
            st.caption("Não entram na cobertura do catálogo nem confirmam volta.")
    st.markdown("#### Transporte urbano e última milha")
    if v["market"]:
        urban=v["market"]["urban_pass"]
        st.write("Passe mensal: "+money(urban["fare_eur_month_person"])+"/pessoa")
        st.caption(str(urban["price_period"])+" · "+urban["eligibility"]+" · "+urban["note"])
        source(urban["source_url"])
    for item in v["mobility"]:
        st.write(item["label"]+" — "+item["detail"])
        source(item["source_url"])
    for item in v["access_notes"]:
        st.write(item["name"]+" · "+str(item.get("station") or "Estação a verificar")+
                 (" · "+str(item["walk_duration_min"])+" min a pé publicados" if item.get("walk_duration_min") else ""))
        source(item["source_url"])
    for item in v["access_observations"]:
        st.caption(item["attraction_id"]+" · "+str(item.get("station_id") or "Estação a verificar")+
                   " · "+item["direction"]+" · "+str(item.get("duration_min") or "Tempo a verificar"))
        source(item["source_url"])
    if not(v["market"] or v["mobility"] or v["access_notes"] or v["access_observations"]):
        st.caption("Referências locais ainda não pesquisadas.")
    st.caption("Acesso, retorno e condições de 2027 não confirmados. Não somar trajetos sem reconciliar estação e entrada.")
    _evidence(v,"transport")

def _daily(v):
    st.markdown("#### Alimentação e rotina")
    daily=v["pack"].get("daily_life",{})
    cost=v["cost"]
    value=cost["restaurant_two_midrange_eur"] if cost else daily.get("restaurant_two_midrange_eur_2026")
    grocery=daily.get("grocery_basket_eur")
    if value is not None or grocery is not None:
        with st.container(key="ux124b-daily-costs"):
            a,b=st.columns(2,gap="small")
            with a:
                with st.container(border=True):
                    if value is None:
                        st.markdown("**Restaurante para dois**")
                        st.caption("Sem amostra local.")
                    else:
                        st.metric("Restaurante para dois",compact_money(value))
                        st.caption("Amostra colaborativa de 2026.")
            with b:
                with st.container(border=True):
                    if grocery is None:
                        st.markdown("**Supermercado · cesta local**")
                        st.caption("Sem amostra local. Veja a premissa comum abaixo.")
                    else:
                        st.metric("Supermercado · cesta local",compact_money(grocery))
                        st.caption("Referência local, não premissa comum do orçamento.")
    else:
        st.caption("Restaurante e cesta de supermercado: sem amostra local.")
    if v["market"]:
        urban=v["market"]["urban_pass"]
        st.markdown("**Passe urbano mensal:** "+compact_money(urban["fare_eur_month_person"])+" por pessoa")
        st.caption(str(urban["price_period"])+" · "+urban["eligibility"]+" · "+urban["note"])
    common=v["market_common"]
    with st.expander("Premissa histórica compartilhada do orçamento e fontes de custo"):
        if value is not None:
            source(cost["restaurant_source_url"] if cost else daily.get("restaurant_source_url"),"Fonte do restaurante")
        if v["market"]:
            source(v["market"]["urban_pass"]["source_url"],"Fonte do passe urbano")
        st.write(compact_money(common["groceries_eur_week_couple"])+"/semana para o casal")
        st.caption("Não é pesquisa específica desta cidade; não adicionar novamente ao orçamento.")
        source(common["source_url"])
    st.caption("Academia, serviços e cesta comparável ainda exigem pesquisa equivalente.")
    st.markdown("#### Clima de setembro a novembro")
    climate=v["pack"].get("climate",{})
    months=climate.get("months_9_10_11")
    if months:
        st.dataframe([{"Mês":name,"Temperatura média (°C)":months[key]["tmean_c"],
                       "Chuva média (mm)":months[key]["precip_mm"]}
                      for key,name in (("9","Setembro"),("10","Outubro"),("11","Novembro"))],
                     hide_index=True,width="stretch",
                     column_config={"Temperatura média (°C)":st.column_config.NumberColumn(format="%.1f"),
                                    "Chuva média (mm)":st.column_config.NumberColumn(format="%.1f")})
        url=climate["source_url"]
        st.caption("Estação "+climate["station_name"]+" · normais 1991–2020, não previsão de 2027."+
                   (" · [Fonte]("+url+")" if isinstance(url,str) and url.startswith("https://") else ""))
    else:
        st.info("Normais climáticas ainda não pesquisadas.")
    _evidence(v,"daily_costs","climate")

def _remote(v):
    st.markdown("#### Condições para trabalhar")
    st.caption("Internet do imóvel: não confirmada para a estadia de 2027.")
    office=(v["cost"] or {}).get("coworking")
    pack=v["pack"].get("remote_work",{}).get("coworking_reference")
    if office or pack:
        item=office or pack
        with st.container(border=True,key="ux124b-coworking"):
            st.markdown("**"+item["name"]+"**")
            if office:
                st.write(coworking_night_status(office))
                price,schedule=office["price_eur"],office["schedule"]
            else:
                st.caption("Compatibilidade com o expediente a confirmar.")
                price,schedule=pack["price_eur_2026"],pack.get("hours")
            st.write("**"+compact_money(price)+"** · "+item["price_basis"])
            st.write("Horário publicado: "+str(schedule or "Não pesquisado"))
            st.caption((office["note"] if office else pack["limitations"]))
            source(item["source_url"],"Consultar coworking")
    else:
        st.info("Coworking específico ainda não pesquisado.")
    st.caption("Não presumir acesso noturno, conectividade, disponibilidade ou compatibilidade de modalidade.")
    _evidence(v,"remote_work")

@st.cache_data(show_spinner=False,ttl=86400,max_entries=128)
def _attraction_photo(photo,name):
    return photo_markup(photo,name)

def _attraction(item):
    with st.container(border=True):
        photo=item.get("photo")
        if photo:
            left,right=st.columns([1,3],gap="small")
            with left:
                st.markdown(_attraction_photo(photo,item["name"]),unsafe_allow_html=True)
                credit=photo_credit(photo)
                if credit:
                    st.caption(credit)
        else:
            right=st.container()
        with right:
            st.markdown("**"+item["name"]+"**")
            if item.get("place"):
                st.caption(item["place"])
            if item.get("summary") or item.get("notes"):
                st.write(item.get("summary") or item["notes"])
            if item.get("visit_minutes") is not None:
                st.caption(str(item["visit_minutes"])+" min · duração "+str(item.get("visit_minutes_status") or "de referência"))
            ticket=item.get("ticket") or {}
            st.caption(ticket_text(ticket))
            if ticket.get("notes"):
                st.caption(ticket["notes"])
            source(item.get("source_url"),"Fonte turística")
            for url in item.get("additional_sources",[]):
                if isinstance(url,str):
                    source(url,"Fonte complementar")

def _attractions(v):
    st.markdown("#### Atrações locais")
    if not v["local_attractions"]:
        st.info("Ainda não há atrações locais indexadas no catálogo.")
    for item in v["local_attractions"]:
        _attraction(item)
    if v["extra_attractions"] or v["complementary_attractions"]:
        st.markdown("#### Atrações complementares e redondezas")
        for item in v["extra_attractions"]:
            _attraction(item)
        for item in v["complementary_attractions"]:
            st.write(item["name"]+" — "+item["detail"])
            source(item["source_url"])
    st.markdown("#### Destinos regionais com referência de ida")
    if not v["excursions"]:
        st.caption("Ainda não há tempo documentado para destinos com atrações indexadas.")
    regional=v["excursions"][:6]
    if regional:
        st.markdown(route_list_html(regional),unsafe_allow_html=True)
        if v.get("on_discover_destination"):
            # One native selection/action rather than six extra buttons.
            choices={item["destination_id"]:destination_name(item) for item in regional}
            dest=st.selectbox("Destino para conhecer",list(choices),format_func=choices.__getitem__,
                              key=v["widget_prefix"]+"_regional_destination_"+v["city"]["id"])
            st.button("Conhecer destino",key=v["widget_prefix"]+"_regional_discover_"+v["city"]["id"],
                      on_click=v["on_discover_destination"],args=(dest,))
        with st.expander("Atrações e fontes dos destinos regionais"):
            for item in regional:
                st.markdown("**"+item["name"]+"** · "+str(item["attraction_count"])+" atrações indexadas")
                source(item["source_url"],"Fonte turística")
                source(item["cell"].get("source_url"),"Fonte de transporte")
    if v["excursions"]:
        st.caption("Até seis menores referências de ida documentadas; retorno e última milha não comprovados. Consulte todos os destinos em Logística.")
    st.caption("Use Descobrir / Minha lista para selecionar destinos. A ficha não inclui passeios automaticamente.")
    st.caption("Bilhetes, acesso e funcionamento para 2027 ainda precisam de confirmação.")

_RENDERERS=dict(zip(TOPICS,(_overview,_housing,_logistics,_daily,_remote,_attractions)))

@st.cache_data(show_spinner=False,ttl=3600,max_entries=64)
def _public_profile(base_id,research):
    # Cache public research only. st.cache_data returns an independent copy;
    # no user's interests, navigation context or plan enters this cache.
    return city_profile(base_id,research=research)

def render_city_profile(base_id,*,research=None,key_prefix="ux124",on_discover_destination=None):
    interests=st.session_state.get("ux502_interests",empty_interests())
    try:
        v=_public_profile(base_id,research)
    except ImportError:
        st.error("Não foi possível carregar as evidências ferroviárias. Atualize a aplicação; nenhum dado do planejamento foi alterado.")
        return
    priorities={item["destination_id"]:item["priority"] for item in ordered_interests(interests)}
    v["routes"]=personalize_routes(v["routes"],priorities)
    v["widget_prefix"]=key_prefix
    v["on_discover_destination"]=on_discover_destination
    with st.container(key="ux124b-profile-"+key_prefix+"-"+base_id):
        topic=_control("Assunto",TOPICS,TOPICS[0],key_prefix+"_topic_"+base_id,hidden=True)
        _RENDERERS[topic](v)
