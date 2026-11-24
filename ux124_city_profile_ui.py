"""UX124 shared, topic-based research profile. No planning writes."""
from __future__ import annotations
import streamlit as st
from ux124_city_profile_model import (TOPICS,city_profile,profile_summary_facts,
    personalize_routes,route_scope,ROUTE_SCOPES,TIMED)
from ux502_destination_interests_model import empty_interests,ordered_interests,LABELS
from routes7_comparison_projection import format_minutes
from ux47_photo_ui import photo_markup,photo_credit
from ux113_comparison_panorama_ui import coworking_night_status

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

def _evidence(view,section):
    rows=[e for e in view["profile"]["evidence"] if e["section"]==section]
    if rows:
        with st.expander("Fontes e contexto pesquisado"):
            _facts(rows)

def _overview(v):
    p=v["profile"]
    st.markdown("#### Como seria morar aqui por dois meses?")
    st.write(p["summary"])
    desired=route_scope(v["routes"],ROUTE_SCOPES[0])
    h=v["housing"]
    a,b=st.columns(2,gap="medium")
    with a:
        with st.container(border=True):
            st.metric("Aluguel mensal · mediana histórica",money(h["median_eur_month"]))
            st.caption(f'{h["count"]} anúncios de 2026 · não cotação de 2027'
                       if h["count"] else "Sem amostra — não significa falta de imóveis.")
    with b:
        with st.container(border=True):
            st.metric("Destinos desejados com referência de ida",
                      f'{desired["timed"]}/{desired["eligible"]}' if desired["eligible"] else "—")
            if desired["total"]:
                st.caption(f'{desired["missing"]} sem tempo · {desired["local"]} locais (fora do denominador). Não confirma bate-volta.')
            else:
                st.caption("Escolha destinos em Minha lista para personalizar esta leitura.")
    office=(v["cost"] or {}).get("coworking")
    pack_office=v["pack"].get("remote_work",{}).get("coworking_reference")
    st.markdown("**Trabalho remoto**")
    if office:
        st.write(office["name"]+" — "+coworking_night_status(office))
    elif pack_office:
        st.write(pack_office["name"]+" — horário e modalidade a confirmar.")
    else:
        st.caption("Coworking ainda não pesquisado.")
    st.caption("Internet do imóvel não confirmada.")
    st.markdown("**Vantagens práticas e limitações**")
    facts=profile_summary_facts(p)
    advantages=list(dict.fromkeys([e["summary"] for e in facts]+p["advantages"]))
    for item in [x for x in advantages if x!=p["summary"]][:2]:
        st.write("• "+item)
    if p["limitations"]:
        st.caption(p["limitations"][0])
    if not facts and not p["advantages"]:
        st.caption("Ainda faltam referências práticas específicas.")
    known=[r for r in desired["rows"] if r["cell"]["category"] in TIMED][:3]
    if known:
        st.write("Destinos da sua lista: "+" · ".join(r["name"]+" "+r["cell"]["label"] for r in known))
    missing=[r["name"] for r in desired["rows"] if r["priority"]=="must_visit" and r["cell"]["category"]=="no_time"]
    if missing:
        st.warning("Imperdíveis sem tempo pesquisado: "+", ".join(missing))
    st.markdown("**Ainda pendente para 2027**")
    st.caption("Moradia: contrato, disponibilidade, taxas, caução e internet. Transporte: retorno, frequência e última milha.")
    with st.expander("Características, fontes e contexto histórico"):
        demo=p.get("demographics") or {}
        if demo.get("population_municipal") is not None:
            st.write(f'{demo["population_municipal"]:,}'.replace(",",".")+
                       f' habitantes no município · {demo["reference_year"]} · não área metropolitana')
            source(demo.get("source_url"),"Fonte estatística")
        for item in dict.fromkeys(p["advantages"]+p["limitations"]):
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

def _housing(v):
    st.markdown("#### Quanto custa morar aqui e quais bairros investigar?")
    h=v["housing"]
    st.metric("Mediana mensal da amostra",money(h["median_eur_month"]))
    st.caption("Faixa observada: "+money(h["minimum_eur_month"])+" a "+money(h["maximum_eur_month"])+
               f' · {h["count"]} anúncios históricos')
    st.caption("Valores mensais da mesma amostra histórica usada no comparador, não cotações de 2027.")
    offers=v["city"]["housing_offers"]
    if offers:
        with st.expander("Consultar anúncios históricos"):
            st.dataframe([{"Imóvel":o["observed_title_or_address"],
                           "€/mês":o["monthly_eur"],"m²":o["size_m2"],
                           "Dois adultos":"Documentados" if o.get("two_adults_confirmed") is True else "Não confirmados",
                           "Contas":o.get("utilities"),"Data":o.get("checked_at"),
                           "Fonte":o.get("listing_url") or o["catalogue_url"]} for o in offers],
                         hide_index=True,width="stretch",
                         column_config={"Fonte":st.column_config.LinkColumn(display_text="Consultar")})
    else:
        st.caption("Nenhum anúncio na amostra — não significa falta de imóveis.")
    st.markdown("**Bairros identificados em fontes locais**")
    neighborhoods=v["pack"].get("neighborhoods",[])
    if not neighborhoods:
        st.caption("Ainda não pesquisados.")
    for item in neighborhoods:
        st.write(item["name"]+" — "+item["reason_to_investigate"])
        source(item["source_url"])
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
    st.warning("Estadia para dois em 2027, internet, taxas, caução e disponibilidade ainda não confirmadas.")
    _evidence(v,"housing")

def _logistics(v):
    st.markdown("#### Quais destinos posso conhecer e em quanto tempo?")
    desired=route_scope(v["routes"],ROUTE_SCOPES[0])
    scope=st.segmented_control("Destinos",list(ROUTE_SCOPES),
                               default=ROUTE_SCOPES[0] if desired["total"] else ROUTE_SCOPES[1],
                               key=v["widget_prefix"]+"_routes_"+v["city"]["id"])
    scope=scope or (ROUTE_SCOPES[0] if desired["total"] else ROUTE_SCOPES[1])
    selection=route_scope(v["routes"],scope)
    rows=selection["rows"]
    st.caption(f'{scope}: {selection["timed"]}/{selection["eligible"]} destinos não locais com tempo de ida · '
               f'{selection["local"]} locais · {selection["missing"]} sem tempo. Não confirma bate-volta.')
    if not rows:
        st.info("Nenhum destino neste recorte. Altere o filtro ou consulte Minha lista.")
    else:
        st.dataframe([{"Destino":r["name"],"Prioridade":LABELS.get(r["priority"],"—"),
                       "Tempo de ida":r["cell"]["label"],
                       "Tempo médio/típico":r["cell"]["typical_label"]
                       if r["cell"].get("average_min") is not None or r["historical_typical"] is None
                       else format_minutes(r["historical_typical"])+" · típico histórico"}
                      for r in rows],hide_index=True,width="stretch")
        with st.expander("Fontes, estações e divergências por destino"):
            chosen=st.selectbox("Detalhar destino", [r["destination_id"] for r in rows],
                                format_func=lambda k:next(r["name"] for r in rows if r["destination_id"]==k),
                                key=v["widget_prefix"]+"_route_detail_"+v["city"]["id"]+"_"+str(ROUTE_SCOPES.index(scope)))
            route=next(r for r in rows if r["destination_id"]==chosen)
            cell=route["cell"]
            st.write(cell["label"])
            st.caption(cell["typical_label"])
            if route["historical_typical"] is not None:
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
                st.caption(" · ".join(str(x) for x in (obs.get("minimum_oneway_min"),obs.get("typical_oneway_min"),
                    obs.get("evidence_date"),obs.get("source_dataset"),obs.get("origin_station"),obs.get("destination_station")) if x is not None))
                source(obs.get("source_url"),"Observação original")
            for gap in route["research_gaps"]:
                st.caption(gap)
    with st.expander("Cobertura de pesquisa · catálogo e minha lista"):
        for name in ROUTE_SCOPES[:2]:
            data=route_scope(v["routes"],name)
            st.caption(f'{name}: {data["historical"]} históricos · {data["indicative"]} indicativos · '
                       f'{data["local"]} locais · {data["missing"]} sem tempo (total: {data["total"]}).')
    with st.expander("Tarifas condicionadas e outras referências de trem"):
        found=False
        for r in rows:
            for fare in r["fares"]:
                found=True
                st.write(r["name"]+" · "+money(fare["amount"])+"/pessoa/ida")
                st.caption(str(fare["conditions"] or "Condições a verificar")+" · "+str(fare["observed_at"] or "Data a verificar"))
                source(fare["source_url"])
        st.caption("Referências históricas adicionais da base inteira, independentes do filtro acima.")
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
            st.caption("Sem tarifa ou frequência publicada nesta seleção.")
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
    st.markdown("#### Como seria minha rotina e meu custo de vida?")
    daily=v["pack"].get("daily_life",{})
    cost=v["cost"]
    value=cost["restaurant_two_midrange_eur"] if cost else daily.get("restaurant_two_midrange_eur_2026")
    st.write("Restaurante para dois: "+money(value))
    source(cost["restaurant_source_url"] if cost else daily.get("restaurant_source_url"))
    st.caption("Amostra colaborativa de 2026, não média comprovada nem orçamento integral.")
    st.write("Cesta de supermercado específica: "+money(daily.get("grocery_basket_eur")))
    common=v["market_common"]
    with st.expander("Premissa histórica compartilhada do orçamento"):
        st.write(money(common["groceries_eur_week_couple"])+"/semana para o casal")
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
                     hide_index=True,width="stretch")
        st.caption("Estação "+climate["station_name"]+" · normais 1991–2020, não previsão de 2027.")
        source(climate["source_url"])
    else:
        st.info("Normais climáticas ainda não pesquisadas.")
    _evidence(v,"daily_costs")
    _evidence(v,"climate")

def _remote(v):
    st.markdown("#### Existem condições para trabalhar no meu horário?")
    st.caption("Internet do imóvel: não confirmada para a estadia de 2027.")
    office=(v["cost"] or {}).get("coworking")
    pack=v["pack"].get("remote_work",{}).get("coworking_reference")
    if office:
        st.markdown("**"+office["name"]+"**")
        st.write(money(office["price_eur"])+" · "+office["price_basis"])
        st.write("Horário: "+(office["schedule"] or "Não pesquisado"))
        st.caption(coworking_night_status(office)+" · "+office["note"])
        source(office["source_url"])
    elif pack:
        st.markdown("**"+pack["name"]+"**")
        st.write(money(pack["price_eur_2026"])+" · "+pack["price_basis"])
        st.write("Horário: "+str(pack.get("hours") or "Não pesquisado"))
        st.caption(pack["limitations"])
        source(pack["source_url"])
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
            left,right=st.columns([1,3])
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
            if ticket.get("amount") is not None:
                st.caption(money(ticket["amount"],ticket.get("currency") or "")+" · "+str(ticket.get("per"))+
                           " · "+str(ticket.get("validity") or "validade a verificar"))
            if ticket.get("notes"):
                st.caption(ticket["notes"])
            source(item.get("source_url"),"Fonte turística")
            for url in item.get("additional_sources",[]):
                if isinstance(url,str):
                    source(url,"Fonte complementar")

def _attractions(v):
    st.markdown("#### O que conhecer na cidade e nas redondezas?")
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
    st.markdown("#### Outros destinos com atrações e tempo de ida documentados")
    if not v["excursions"]:
        st.caption("Ainda não há tempo documentado para destinos com atrações indexadas.")
    for item in v["excursions"][:6]:
        with st.container(border=True):
            st.markdown("**"+item["name"]+"** · "+item["cell"]["label"])
            st.caption(str(item["attraction_count"])+" atrações indexadas")
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

def render_city_profile(base_id,*,research=None,key_prefix="ux124"):
    interests=st.session_state.get("ux502_interests",empty_interests())
    v=_public_profile(base_id,research)
    priorities={item["destination_id"]:item["priority"] for item in ordered_interests(interests)}
    v["routes"]=personalize_routes(v["routes"],priorities)
    v["widget_prefix"]=key_prefix
    st.markdown("### Investigue por assunto")
    topic=st.segmented_control("Assunto",list(TOPICS),default=TOPICS[0],
                               key=key_prefix+"_topic_"+base_id)
    _RENDERERS.get(topic,_overview)(v)
    with st.expander("Fontes e pendências da pesquisa",expanded=False):
        st.caption(f'{v["housing"]["count"]} anúncios históricos · {v["catalog_destination_count"]} destinos no catálogo atual.')

        for item in dict.fromkeys(v["profile"]["research_gaps"]+v["pack"].get("missing",[])+v["context_gaps"]):
            st.caption(item)
        if v["city"].get("screening_notes"):
            st.caption(v["city"]["screening_notes"])
        st.caption("Dados ausentes não equivalem a zero. Pesquisa histórica não é cotação, reserva ou nota de qualidade.")
