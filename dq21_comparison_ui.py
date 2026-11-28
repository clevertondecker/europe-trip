"""Compact DQ 2.1 comparison inside favorites, no new application page."""
from __future__ import annotations

from formatting import minutes as format_duration
from datetime import date
import streamlit as st
from dq21_decision_model import decision_research

NAMES={"mulhouse":"Mulhouse","strasbourg":"Strasbourg",
       "freiburg":"Freiburg","luxembourg_city":"Luxemburgo",
       "interlaken":"Interlaken","brussels":"Bruxelas",
       "bruges_be":"Bruges (Bélgica)","rotterdam":"Rotterdam"}

def _duration(minutes):
    return format_duration(minutes, missing="Não documentado", always_hours=True, strict=False)


def render_dq21_panel(selected:list[str])->None:
    if len(selected)<2 or not set(selected)<={"mulhouse","strasbourg","freiburg"}:
        return
    with st.expander("Pesquisa prática 2.1 · roteiros, rotina e aeroportos"):
        st.caption("Três cidades prioritárias; mesmas cinco viagens piloto em todas. "
                   "Horários históricos de 2026, não reservas ou disponibilidade de 2027. "
                   "As 15 atrações do comparador principal e seu orçamento não mudam.")
        simulate=st.checkbox("Simular horário de trabalho brasileiro",
                             value=False,key="dq21_simulate_brazil_work")
        work_day=None
        hours=None
        if simulate:
            work_date=st.date_input("Dia da temporada para conferir o fuso",
                                    value=date(2027,10,30),
                                    min_value=date(2027,9,5),
                                    max_value=date(2027,11,30),
                                    key="dq21_work_date")
            option=st.selectbox("Horário no Brasil",
                                ["09:00–18:00","08:00–17:00","10:00–19:00"],
                                key="dq21_brazil_hours")
            hours={"09:00–18:00":(9,18),"08:00–17:00":(8,17),
                   "10:00–19:00":(10,19)}[option]
            work_day=work_date.isoformat()
        data=decision_research(list(selected),work_day=work_day,brazil_hours=hours)
        if data["status"]!="available":
            st.info("Os três pacotes de pesquisa precisam estar integrados para "
                    "exibir a comparação aprofundada. Os dados originais continuam disponíveis.")
            return
        t1,t2,t3,t4=st.tabs(["Passeios","Moradia e rotina",
                             "Aeroportos","Fontes e pendências"])
        with t1:
            st.markdown("**Qual passeio cabe no fim de semana?**")
            st.caption("Tempos de ida entre estações. Faltam horários completos "
                       "de retorno, visitas e deslocamento ao hotel.")
            rail=[{"Cidade-base":NAMES[r["base_id"]],
                   "Destino":NAMES[r["destination_id"]],
                   "Menor ida histórica":_duration(r["minimum_rail_minutes_2026"]),
                   "Média disponível":_duration(r["representative_minutes_2026"]),
                   "Retorno completo":"Não comprovado",
                   "Observação":("Trajeto longo · pernoite a avaliar" if
                             r["status"]=="roteiro_longo_pede_pernoite_a_estudar"
                             else "Depende de horários de volta")}
                  for r in data["routes"]]
            st.dataframe(rail,hide_index=True,width="stretch")
            st.info("0 das 15 combinações tem bate-volta comprovado com volta e "
                    "última milha. Isso não significa que sejam impossíveis.")
            bridge=data["belgium"]
            st.markdown("**Bruxelas + Bruges:** a SNCB publica serviço nos dois "
                        "sentidos aos fins de semana (trecho médio ~64 min). "
                        "A viagem completa desde cada base continua pendente.")
            st.markdown("[Horários SNCB]("+bridge["source_url"]+")")
            with st.expander("Ideia de oito fins de semana, incluindo descanso"):
                st.dataframe([{"Fim de semana":x["index"],"Proposta":x["theme"],
                              "Status":"Sem reserva"} for x in data["sample_weekends"]],
                             hide_index=True,width="stretch")
        with t2:
            st.markdown("**Como seria morar e trabalhar nas três cidades?**")
            rows=[]
            for c in data["urban"]:
                d=c["dimensions"]
                climate=d["clima_set_nov"]
                months=climate["months_9_10_11"] or {}
                temps=" / ".join(str(months.get(i,{}).get("tmean_c","?"))+"°C"
                               for i in ("9","10","11"))
                cowork=d["trabalho_remoto"]["coworking_reference"]
                rows.append({"Cidade":NAMES[c["city_id"]],
                             "Médias set/out/nov":temps,
                             "Coworking":cowork["name"] if cowork else "Pendente",
                             "Internet no imóvel":"Não verificada",
                             "Acesso noturno ao imóvel":"Não verificado"})
            st.dataframe(rows,hide_index=True,width="stretch")
            st.caption("Freiburg: médias secundárias atribuídas ao DWD 01443; "
                       "há divergências entre republicações e precipitação ainda não "
                       "reconciliada. Segurança e infraestrutura por endereço permanecem abertas.")
            if simulate:
                sample=data["urban"][0]["work_scenarios"][0]
                start=sample["europe_start"][11:16]
                end=sample["europe_end"][11:16]
                st.info("No dia "+work_day+", expediente escolhido no Brasil "
                        "corresponde a "+start+"–"+end+" na Europa continental. "
                        "Não há comprovação de coworking aberto até esse horário.")
            st.caption("Verifique serviços a pé e internet somente quando existir "
                       "um endereço real de moradia.")
        with t3:
            st.markdown("**Como chegar da Itália e voltar ao Brasil?**")
            st.caption("Opções de aeroporto, não itinerários confirmados. "
                       "Aeroporto e voo dependem de datas, bagagens e cidade final.")
            rows=[]
            for city in data["airports"]:
                for a in city["airport_options"]:
                    code=a["airport_code"]
                    rows.append({"Base":NAMES[city["base_id"]],
                                 "Aeroporto":code,
                                 "Trechos pesquisados":len(a["known_segment_observations"]),
                                 "Tempo porta a porta":"Não validado",
                                 "Voo 2027":"Não confirmado"})
            st.dataframe(rows,hide_index=True,width="stretch")
            st.markdown("Rotas publicadas em 2026 para São Paulo/Guarulhos:")
            for flight in data["direct_flights_2026"]:
                st.markdown("- "+flight["carrier"]+": "+flight["airport_code"]+
                            " → GRU, voo "+flight["flight_example"]+
                            " · [companhia aérea]("+flight["source_url"]+")")
            st.caption("Chegar a GRU não confirma o trecho final no Brasil. "
                       "O Alibus de Nápoles e qualquer transferência desde Maiori "
                       "também exigem conferência no horário escolhido.")
        with t4:
            st.markdown("**Pendências necessárias para uma decisão responsável**")
            for note in [
                "Ida e volta em datas equivalentes de sábado/domingo para os 15 pares",
                "Roteiro inteiro Bruxelas–Bruges com hotel ou volta à base",
                "Deslocamento estação–atrações em Interlaken e demais cidades",
                "Internet, mercado, academia e acesso noturno por endereço de moradia",
                "Normais climáticas DWD Freiburg reconciliadas com fonte primária",
                "Voos de 2027, bagagens, transfers italianos e cidade final no Brasil"]:
                st.caption("• "+note)
            st.markdown("**Fontes da atualização**")
            from dq21_weekend_model import load_weekend_details
            from dq21_living_model import load_living_evidence
            from dq21_travel_model import load_travel_extension
            sources=[]
            for r in load_weekend_details()["dated_services"]:
                sources.append(("Trem "+NAMES.get(r["origin_id"],r["origin_id"])+
                                "–"+NAMES.get(r["destination_id"],r["destination_id"]),r["source_url"]))
            source_climate=load_living_evidence()["freiburg_climate"]
            sources.append(("Clima Freiburg (republicação DWD)",source_climate["temperature_source_url"]))
            for flight in load_travel_extension()["longhaul_examples"]:
                sources.append(("Voo "+flight["airport_code"]+"–GRU",flight["source_url"]))
            seen=set()
            for label,url in sources:
                if url not in seen:
                    seen.add(url)
                    st.markdown("- ["+label+"]("+url+")")
            st.caption("Fontes datadas em 2026. Sem cidade vencedora ou pontuação "
                       "automática; pesquisas não alteram o plano oficial.")
