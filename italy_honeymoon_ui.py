"""Read-only Italian honeymoon study with evidence-based daily logistics."""
from __future__ import annotations
import json
from pathlib import Path

import streamlit as st

from italy_honeymoon_model import (
    load_honeymoon,manual_italy_cost,optional_comparison,preview_nights,
    ticket_sample,
)

TRANSFER_PATH=Path(__file__).resolve().parent/"data"/"italy_transfer_risks_2027.json"
INPUTS={
    "rome_hotel_night":"Hotel Roma (€ por noite do casal)",
    "coast_hotel_night":"Hotel Costa Amalfitana (€ por noite do casal)",
    "naples_hotel_night":"Hotel Nápoles (€ por noite do casal)",
    "food_couple_per_day":"Comida e cafés (€ por dia do casal)",
    "extra_local_transport":"Transporte adicional/transfer (€ total casal)",
    "additional_admissions":"Outros passeios e ingressos (€ total casal)",
}
LEGACY={"60k":12545,"70k":14636}


def _eur(value:float)->str:
    return "€ "+f"{value:,.2f}".replace(",","_").replace(".",",").replace("_",".")


def _logistics()->None:
    legs=json.loads(TRANSFER_PATH.read_text(encoding="utf-8"))
    with st.expander("Logística real: malas, alternativas e riscos de retorno"):
        st.caption("Horários, tempos e preços consultados em 2026. Não representam "
                   "um trajeto porta a porta confirmado para os dias de 2027.")
        for leg in legs["legs"]:
            with st.container(border=True):
                st.markdown("**"+leg["label"]+"** · "+leg["mode"])
                st.caption("Duração do operador: "+
                           (str(leg["operator_minutes"])+" min" if
                            leg["operator_minutes"] is not None else
                            "não verificada")+
                           " · Custo do casal de trecho observado: "+
                           (_eur(leg["known_couple_sample_eur"]) if
                            leg["known_couple_sample_eur"] is not None
                            else "não cotado"))
                st.caption(leg["fare_note"]+" · Bagagens: "+leg["luggage"])
                st.caption("Risco: "+leg["risks"]+" · Plano B: "+leg["backup"])
                st.markdown("[Operadora / fonte de referência]("+leg["source_url"]+")")


def render_italy_honeymoon()->None:
    d=load_honeymoon()
    by_id={s["id"]:s for s in d["scenarios"]}
    st.markdown("### Nossa Itália: 10 dias, sem correr entre cidades")
    st.info("Roma e Costa Amalfitana são destinos obrigatórios. O restante "
            "continua como **proposta exploratória**, não altera o roteiro oficial "
            "ou a planilha de orçamento do casal.")
    st.caption("4 noites Roma + 5 noites na costa = 9 noites / 10 dias de calendário. "
               "10 noites completas normalmente exigem 11 dias. Sem hora real "
               "do voo, a distribuição é editorial, não uma agenda reservada.")

    choice=st.segmented_control("Comparar estilos",
                                ["Equilibrado","Econômico e logístico",
                                 "Lua de mel e experiência"],
                                default="Equilibrado",key="italy_honeymoon_variant")
    chosen={"Equilibrado":"balanced","Econômico e logístico":"economy",
            "Lua de mel e experiência":"experience"}.get(choice,"balanced")
    s=by_id[chosen]
    extra=st.checkbox("Comparar com 10 noites completas (+1 noite na costa)",
                      value=False,key="italy_honeymoon_extra_night")
    nights=preview_nights(s,extra)
    col1,col2,col3=st.columns(3)
    col1.metric("Roma",str(nights["rome"])+" noites")
    col2.metric("Costa",str(nights["coast"])+" noites")
    col3.metric("Nápoles",str(nights["naples"])+" noites")
    st.caption(str(nights["nights"])+" noites e "+
               str(nights["calendar_days"])+" dias de calendário.")
    if extra:
        st.warning("A noite adicional é somente uma comparação de experiência. "
                   "Ela **não cabe** automaticamente nos 10 dias da etapa italiana "
                   "do planejamento atual; seria necessário mudar esse parâmetro "
                   "após aprovar datas, voo e hospedagem.")

    with st.expander("Por que esta proposta funciona (e quais os custos de esforço)",
                     expanded=True):
        st.markdown("**Vantagens**")
        for x in s["pros"]:st.caption("• "+x)
        st.markdown("**Desvantagens e riscos**")
        for x in s["cons"]:st.caption("• "+x)
    st.markdown("#### Onde dormir e o que fazer em cada dia")
    st.caption("Dia 1 é chegada; dia 10 é saída. Nenhum horário de check-in, "
               "reserva de atração ou voo foi inventado.")
    for n,(title,place,activities,intensity,mode,attention) in enumerate(s["days_detail"],1):
        with st.container(border=True):
            st.markdown("**Dia "+str(n)+" · "+title+"** — "+place)
            st.write(activities)
            st.caption("Intensidade: "+intensity+" · Transporte: "+mode+
                       " · Prioridade de revisão: "+attention)
    st.markdown("#### Base na Costa Amalfitana: custos e experiência")
    for b in d["coast_bases"]:
        with st.expander(b["label"]+(" · nesta proposta" if
                                    s["coast_base"]==b["id"] else "")):
            st.write("**Praia:** "+b["beach"])
            st.write("**Lua de mel:** "+b["romance"])
            st.write("**Acessos:** "+b["access"])
            st.caption("Malas: "+b["luggage"]+" · Riscos: "+b["risk"])
            st.warning("Hotel por 5 noites para 2027: não cotado.")

    st.markdown("#### Bilhetes pesquisados — apenas parte dos gastos")
    sample=ticket_sample(d,chosen)
    for row in sample["items"]:
        st.markdown("• "+row["name"]+" — **"+_eur(row["couple_sample_eur"])+
                    " / casal** ([fonte]("+row["url"]+"))")
    st.metric("Subtotal de bilhetes selecionados (2026, parcialmente promocionais)",
              _eur(sample["known_sample_subtotal_eur"]))
    st.warning("Não é custo total do casal. Tarifas 'desde' e ferries de 2026 "
               "dependem de disponibilidade. Não adicionamos essa soma ao orçamento "
               "global porque a Itália e os voos já possuem verbas agregadas.")

    st.markdown("#### Capri versus Pompeia: escolhas opcionais")
    st.caption("Referências de ingressos/ferry; não incluem refeições, transporte "
               "terrestre, transfers, clima, hospedagem e guias.")
    for option in optional_comparison(d):
        st.write("• **"+option["title"]+"** · "+
                 _eur(option["known_ticket_reference_eur"])+
                 " para 2 pessoas · falta: "+option["extra_needed"])
    st.caption("Capri é mais associado a mar e paisagens, mas envolve travessia "
               "sujeita a cancelamento. Pompeia favorece arqueologia e pode "
               "ser planejada num dia alternativo; não tentar incluir ambos "
               "obrigatoriamente em dez dias.")
    _logistics()

    with st.expander("Quanto custaria? Simulação manual separada do orçamento"):
        st.caption("Preencha preços totais do casal em €. Sem valores preenchidos, "
                   "não convertemos referências de 2026 em preços de 2027. "
                   "Zero digitado significa custo zero declarado; campo vazio "
                   "é **desconhecido**.")
        vals={}
        for key,label in INPUTS.items():
            if key=="naples_hotel_night" and s["naples_nights"]==0:continue
            raw=st.text_input(label,value="",key="italy_budget_"+key)
            if not raw.strip():
                vals[key]=None
            else:
                try:vals[key]=float(raw.replace(",","."))
                except ValueError:
                    st.error("Informe um número válido para "+label)
                    return
        fx=st.number_input("Câmbio hipotético R$/€",min_value=0.01,
                           value=6.3,step=0.1,key="italy_budget_fx")
        try:
            preview=manual_italy_cost(d,chosen,vals,fx)
        except ValueError as e:
            st.error(str(e))
            return
        if preview["missing_manual_inputs"]:
            st.info("Ainda faltam "+", ".join(INPUTS[k] for k in
                    preview["missing_manual_inputs"])+
                    ". Subtotal conhecido não é total da Itália.")
        else:
            st.metric("Estimativa manual da etapa Itália (€)",
                      _eur(preview["illustrative_italy_total_eur"]))
            st.metric("Estimativa manual da etapa Itália (R$)",
                      "R$ "+f"{preview['illustrative_italy_total_brl']:,.2f}")
        st.caption("Referências originais de orçamento do casal: Itália R$12.545 "
                   "(teto global 60k) / R$14.636 (teto global 70k). "
                   "Voos e seguro já possuem verba própria; não foram somados. "
                   "Esta simulação não salva nem altera os números originais.")
        st.warning("Saída Itália → França e voos internacionais seguem fora "
                   "deste simulador, pois dependem do aeroporto da próxima base. "
                   "Preços introduzidos manualmente não são cotações.")
