"""UX124 shared, topic-based research profile. No planning writes."""
from __future__ import annotations
import streamlit as st
from ux124_city_profile_model import TOPICS,city_profile,profile_summary_facts
from ux502_destination_interests_model import empty_interests,LABELS
from ux47_photo_ui import photo_markup,photo_credit
from ux113_comparison_panorama_ui import coworking_night_status

def money(value,unit="€"):
    return "Não pesquisado" if value is None else f"{value:,.2f} {unit}"

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
    st.markdown("#### Pesquisa em resumo")
    st.write(p["summary"])
    demo=p.get("demographics") or {}
    if demo.get("population_municipal") is not None:
        st.caption(f'{demo["population_municipal"]:,}'.replace(",",".")+
                   f' habitantes no município · {demo["reference_year"]} · não área metropolitana')
        source(demo.get("source_url"),"Fonte estatística")
    else:
        st.caption("População municipal ainda não pesquisada.")
    left,right=st.columns(2,gap="medium")
    with left:
        with st.container(border=True):
            st.markdown("**Já documentado**")
            facts=profile_summary_facts(p)
            if facts:
                _facts(facts)
            else:
                st.caption("Ainda faltam referências práticas específicas.")
    with right:
        with st.container(border=True):
            st.markdown("**Ainda pendente para 2027**")
            st.write("Moradia: contrato, disponibilidade, taxas, caução e internet.")
            st.write("Transporte: retorno, frequência e última milha.")
    with st.expander("Características e contexto histórico"):
        for item in dict.fromkeys(p["advantages"]):
            st.write(item)
        for item in dict.fromkeys(p["limitations"]):
            st.caption(item)
        historical=v["editorial"]
        if historical:
            st.caption("Avaliação editorial de 2026, não pontuação atual.")
            st.write(historical["summary"])
            for item in historical["advantages"]+historical["risks"]:
                st.caption(item)
            source(v["editorial_source"],"Matriz histórica")
        _facts([e for e in p["evidence"] if e["section"]=="quality_of_life"])
        source(p["official_statistics_source"]["url"],"Base estatística oficial")

def _housing(v):
    st.markdown("#### Moradia e bairros")
    h=v["housing"]
    a,b,c=st.columns(3)
    a.metric("Mínimo observado",money(h["minimum_eur_month"]))
    b.metric("Mediana da amostra",money(h["median_eur_month"]))
    c.metric("Máximo observado",money(h["maximum_eur_month"]))
    st.caption("Valores mensais da mesma amostra histórica usada no comparador, não cotações de 2027.")
    offers=v["city"]["housing_offers"]
    if offers:
        for offer in offers:
            with st.container(border=True):
                st.markdown("**"+offer["observed_title_or_address"]+"**")
                st.write(money(offer["monthly_eur"])+"/mês · "+str(offer["size_m2"])+" m²")
                st.caption("Dois adultos: "+("documentados" if offer.get("two_adults_confirmed") is True else "não confirmados")+
                           " · "+str(offer.get("utilities") or "Contas a verificar"))
                source(offer.get("listing_url") or offer["catalogue_url"],
                       "Anúncio individual" if offer.get("listing_url") else "Catálogo de 2026")
    else:
        st.info("Nenhum anúncio na amostra — não significa falta de imóveis.")
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
    st.markdown("#### Conexões ferroviárias")
    counts=v["counts"]
    st.caption(f'{counts.get("historical",0)} históricos · {counts.get("reference_only",0)} indicativos · '
               f'{counts.get("local",0)} locais · {counts.get("no_time",0)} sem tempo. '
               "Ida somente; não é confirmação de viagem de 2027.")
    options=["Minha lista","Todos os destinos","Com tempo pesquisado"]
    has_wishes=any(r["priority"] in ("must_visit","interested","maybe") for r in v["routes"])
    scope=st.segmented_control("Destinos",options,default=options[0] if has_wishes else options[1],
                               key="ux124_routes_"+v["city"]["id"])
    rows=v["routes"]
    if scope=="Minha lista":
        rows=[r for r in rows if r["priority"] in ("must_visit","interested","maybe")]
    elif scope=="Com tempo pesquisado":
        rows=[r for r in rows if r["cell"]["category"] in ("historical","reference_only")]
    if not rows:
        st.info("Nenhum destino desejado nesse recorte.")
    else:
        st.dataframe([{"Destino":r["name"],"Prioridade":LABELS.get(r["priority"],"—"),
                       "Tempo de ida":r["cell"]["label"],"Tempo médio":r["cell"]["typical_label"],
                       "Fonte":r["cell"].get("source_url")}
                      for r in rows],hide_index=True,width="stretch",
                     column_config={"Fonte":st.column_config.LinkColumn(display_text="Consultar")})
    with st.expander("Tarifas condicionadas e outras referências de trem"):
        found=False
        for r in rows:
            for fare in r["fares"]:
                found=True
                st.write(r["name"]+" · "+money(fare["amount"])+"/pessoa/ida")
                st.caption(str(fare["conditions"] or "Condições a verificar")+" · "+str(fare["observed_at"] or "Data a verificar"))
                source(fare["source_url"])
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
    st.markdown("#### Alimentação e rotina")
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
    st.markdown("#### Trabalho remoto")
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
    st.markdown("#### Atrações na cidade")
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
    st.caption("Use Descobrir / Minha lista para selecionar destinos. A ficha não inclui passeios automaticamente.")
    st.caption("Bilhetes, acesso e funcionamento para 2027 ainda precisam de confirmação.")

_RENDERERS=dict(zip(TOPICS,(_overview,_housing,_logistics,_daily,_remote,_attractions)))

def render_city_profile(base_id,*,research=None,key_prefix="ux124"):
    interests=st.session_state.get("ux502_interests",empty_interests())
    v=city_profile(base_id,research=research,interests=interests)
    timed=v["counts"].get("historical",0)+v["counts"].get("reference_only",0)
    total=v["catalog_destination_count"]-v["counts"].get("local",0)
    a,b=st.columns(2,gap="medium")
    with a:
        with st.container(border=True):
            st.metric("Anúncios históricos de 2026",v["housing"]["count"])
            st.caption("Amostra documental, não imóveis disponíveis." if v["housing"]["count"] else
                       "Nenhuma amostra — não significa falta de imóveis.")
    with b:
        with st.container(border=True):
            st.metric("Destinos com tempo pesquisado",f"{timed}/{total}")
            st.caption("Catálogo atual, sem destino local. Históricos e indicativos de ida; não confirma bate-volta.")
    st.markdown("### Investigue por assunto")
    topic=st.segmented_control("Assunto",list(TOPICS),default=TOPICS[0],
                               key=key_prefix+"_topic_"+base_id)
    _RENDERERS.get(topic,_overview)(v)
    with st.expander("Fontes e pendências da pesquisa",expanded=False):
        for item in dict.fromkeys(v["profile"]["research_gaps"]+v["pack"].get("missing",[])+v["context_gaps"]):
            st.caption(item)
        if v["city"].get("screening_notes"):
            st.caption(v["city"]["screening_notes"])
        st.caption("Dados ausentes não equivalem a zero. Pesquisa histórica não é cotação, reserva ou nota de qualidade.")
