"""Compact Data Quality 2.0 evidence panel inside UX 4.1 favorites.

No new main page, no automatic change of itinerary, budget or basket.
"""
from __future__ import annotations
import streamlit as st
from dq20_comparison_model import pilot_comparison

def _time(minutes):
    if minutes is None:
        return "Sem dado"
    return f"{minutes//60}h{minutes%60:02d}" if minutes>=60 else f"{minutes} min"

def _weather(months):
    if not months:
        return "Normal climática pendente"
    values=[]
    for k in ("9","10","11"):
        row=months.get(k) or {}
        if row.get("tmean_c") is not None:
            values.append(f'{k}: {row["tmean_c"]}°C')
    return " · ".join(values) if values else "Não pesquisado"

def render_dq20_panel(selected_ids:list[str])->None:
    if len(selected_ids)<2 or not set(selected_ids)<= {"mulhouse","strasbourg","freiburg"}:
        return
    with st.expander("Arquivo de pesquisa 2.0 · referências históricas detalhadas"):
        st.caption("Piloto independente para Luxemburgo, Interlaken, Bruxelas, "
                   "Bruges e Rotterdam. Não altera sua cesta de passeios de cima.")
        as_brazil=st.checkbox("Simular expediente 9h–18h no Brasil (hipótese)",
                             value=False,key="dq20_brazil_hours_example")
        view=pilot_comparison(list(selected_ids),work_hours=(9,18) if as_brazil else None)
        if view["status"]!="research_available":
            st.info("As pesquisas A, B e C estão em revisão separada. "
                    "A comparação aprofundada será exibida após as integrações.")
            return
        st.markdown("#### 1. Quais passeios são logisticamente possíveis?")
        st.caption("Tempos de ida entre estações: alguns são mínimos e outros "
                   "apenas amostras. Nenhuma volta de fim de semana está comprovada.")
        rows=[]
        for r in view["routes"]:
            rows.append({"Cidade-base":r["base_name"],
                         "Destino":r["destination_name"],
                         "Menor ida observada":_time(r["station_to_station_fastest_min"]),
                         "Média publicada":_time(r["representative_min"]),
                         "Conexões em exemplo":r["transfers_in_example"],
                         "Viabilidade":("Trajeto longo · investigar pernoite" if
                              r["feasibility"]=="viagem_longa_ou_exigente_indicativa"
                              else "Dados insuficientes")})
        st.dataframe(rows,hide_index=True,width="stretch")
        st.info("0 bate-voltas comprovados nesta pesquisa. Isso NÃO significa "
                "que os demais destinos sejam impossíveis.")
        bridge=view["brussels_bruges"]
        st.markdown("**Bruxelas + Bruges:** conexão direta de ~"+
                    _time(bridge["between_cities_min"])+" entre as duas cidades. "
                    "[Fonte SNCB]("+bridge["source_url"]+"). "
                    "Ainda falta provar o roteiro completo com retorno à base.")
        st.markdown("**Exemplo de distribuição de fins de semana (sem datas):**")
        st.dataframe([{"Fim de semana":w["index"],"Ideia":w["theme"],
                       "Status":w["status"]} for w in view["illustrative_weekends"]],
                     hide_index=True,width="stretch")
        st.markdown("#### 2. Como seria morar e trabalhar?")
        u=[]
        for city in view["urban"]:
            d=city["dimensions"]
            cowork=d["trabalho_remoto"]["coworking_reference"]
            u.append({"Cidade":city["city_id"],
                      "Transporte":d["mobilidade_sem_carro"]["network"],
                      "Coworking":cowork["name"] if cowork else "A pesquisar",
                      "Clima set/out/nov":_weather(d["clima_set_nov"]["months_9_10_11"]),
                      "Internet no imóvel":"Não verificada",
                      "Segurança municipal comparável":"Sem base padronizada"})
        st.dataframe(u,hide_index=True,width="stretch")
        if as_brazil:
            st.caption("Hipótese 9h–18h no Brasil: aproximadamente 14h–23h na "
                       "Europa no horário de verão e 13h–22h no inverno. "
                       "Não há confirmação de coworking aberto até o término.")
        st.markdown("#### 3. Como chegar da Itália e voltar ao Brasil?")
        airport_rows=[]
        for city in view["logistics"]:
            for opt in city["airport_options"]:
                airport_rows.append({"Base":city["base_id"],
                    "Aeroporto":opt["airport_name"],
                    "Ligação documentada":" → ".join(opt["path"]),
                    "Tempo porta a porta":"Não verificado",
                    "Voo Brasil":"Não verificado"})
        st.dataframe(airport_rows,hide_index=True,width="stretch")
        st.caption("A saída da Itália depende do roteiro aprovado. Nenhum voo, "
                   "preço aéreo de 2027 ou conexão hotel–terminal foi presumido.")
        st.markdown("#### 4. O que ainda precisa ser validado?")
        st.caption("Ida e volta em sábados/domingos, tempo nos locais, estação–hotel, "
                   "trabalho noturno conforme endereço, voos e bagagens, e "
                   "cotações efetivas de estadia. Sem nota geral ou cidade vencedora.")
        with st.container(border=True):
            st.markdown("**Fontes ferroviárias por trecho com observação histórica:**")
            unique=set()
            for r in view["routes"]:
                for source in r["source_records"]:
                    url=source.get("source_url")
                    if url and url not in unique:
                        unique.add(url)
                        if len(unique)<=12:
                            st.markdown("- ["+r["base_name"]+" – "+r["destination_name"]+
                                        "]("+url+")")
            st.caption("Datas e modalidades variam entre fontes; não combinar "
                       "bilhetes ou tempos de referências diferentes sem validação.")
