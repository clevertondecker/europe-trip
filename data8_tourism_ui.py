"""DATA 8.5: compact reusable tourism research inside existing Streamlit flows.

No mutations of the official plan, wishlist, calendar or approved budget.
Never claims that editorial walk/duration ranges are verified 2027 services.
"""
from __future__ import annotations

import re
from copy import deepcopy
import streamlit as st

from data8_priority_tourism_model import load_priority_lot
from data8_local_access_model import load_access_dataset, local_access_scenario
from data8_couple_cost_model import estimate_couple_excursion, load_cost_addons


@st.cache_data(show_spinner=False)
def _tourism():
    return load_priority_lot()


@st.cache_data(show_spinner=False)
def _access():
    return load_access_dataset()


def parse_user_range(raw: str):
    """Blank => unknown; two explicitly typed nonnegative EUR amounts => range."""
    if not raw or not raw.strip():
        return None
    value = raw.strip().replace(" ", "")
    if not re.fullmatch(r"\d+(?:[.,]\d{1,2})?-\d+(?:[.,]\d{1,2})?",value):
        raise ValueError("Informe a faixa como 30-60 (euros, mínimo-máximo).")
    a,b=[float(x.replace(",",".")) for x in value.split("-",1)]
    if a>b or b>100000:
        raise ValueError("Faixa inválida: limite máximo inferior ao mínimo.")
    return {"min_eur":a,"max_eur":b,
            "state":"user_editorial_assumption",
            "method":"premissa preenchida manualmente para planejamento"}


def build_data8_card(attraction_id, *, tourism=None, access=None):
    tourism=tourism if tourism is not None else load_priority_lot()
    access=access if access is not None else load_access_dataset(tourism=tourism)
    row=tourism["by_id"].get(attraction_id)
    if row is None:
        return None
    candidate=deepcopy(row)
    walks=access["by_attraction"].get(attraction_id,[])
    station=next((x["station_id"] for x in walks
                  if x["direction"]=="station_to_attraction"),None)
    walk=local_access_scenario(attraction_id,station_id=station,evidence=access) if station else None
    return {"attraction_id":attraction_id,
            "destination_id":row["destination_id"],
            "why_visit":row["experience"]["why_visit"],
            "experience_source_url":row["experience"]["source_url"],
            "duration":deepcopy(row["duration"]),
            "admission":deepcopy(row["admission"]),
            "opening":deepcopy(row["opening"]),
            "seasonality":deepcopy(row["seasonality"]),
            "location":deepcopy(row["location"]),
            "local_walk":walk,
            "actual_station_connection_verified":False,
            "valid_for_2027":False}


def destination_research_overview(destination_id, *, tourism=None):
    tourism=tourism if tourism is not None else load_priority_lot()
    rows=[x for x in tourism["entries"] if x["destination_id"]==destination_id]
    pending=[x for x in tourism["unreconciled_candidates"]
             if x["destination_id"]==destination_id]
    return {"destination_id":destination_id,"researched_attractions":len(rows),
            "unreconciled_candidates":deepcopy(pending),
            "complete_2027":0,"trip_plan_mutated":False}


def render_data8_attraction_details(attraction_id, *, tourism=None, access=None):
    """Returns True if an enriched card was rendered; caller retains legacy fallback."""
    card=build_data8_card(attraction_id,tourism=tourism,access=access)
    if card is None:
        return False
    st.caption("**Por que visitar:** "+card["why_visit"])
    d=card["duration"]
    if d["state"]=="editorial_estimate":
        st.caption(f'Duração sugerida: {d["min_minutes"]}–{d["max_minutes"]} min '
                   "· estimativa editorial, não tempo oficial.")
    elif d["state"]=="operator_guidance":
        st.caption("Duração indicada pelo operador: "+
                   str(d["min_minutes"])+"–"+str(d["max_minutes"])+" min")
    else:
        st.caption("Duração ainda desconhecida.")
    ticket=card["admission"]
    if ticket["state"]=="free_general_entry":
        st.caption("Entrada geral gratuita na referência publicada; "
                   "atividades especiais podem ser pagas.")
    elif ticket["state"]=="published_price":
        st.caption("Ingresso publicado: "+str(ticket["amount"])+" "+
                   str(ticket.get("currency"))+" por "+str(ticket.get("unit"))+
                   " · histórico, confirmar para a viagem.")
    elif ticket["state"]=="external_no_ticket":
        st.caption("Passeio externo sem ingresso principal; "
                   "interiores e serviços continuam sem preço confirmado.")
    else:
        st.caption("Ingresso: preço não pesquisado; desconhecido não é gratuito.")
    opening=card["opening"]
    if opening["state"]=="published_general_rule":
        st.caption("Regra de funcionamento pesquisada: "+opening["rule"])
        st.caption("Não comprova abertura em uma data de 2027.")
    else:
        st.caption("Horário de funcionamento não pesquisado.")
    loc=card["location"]
    if loc["state"]=="published_address":
        st.caption("Localização: "+loc["address"])
    season=card["seasonality"]
    if season["state"]=="published_note":
        st.caption("Sazonalidade: "+season["note"])
    walk=card["local_walk"]
    if walk and walk["state"]=="editorial_two_direction_range":
        to=walk["to_attraction_range_min"]
        back=walk["to_station_range_min"]
        st.caption(f'Caminhada preliminar: {to[0]}–{to[1]} min da estação; '
                   f'{back[0]}–{back[1]} min no sentido de volta. '
                   "Faixas editoriais; não são rota ferroviária comprovada.")
    else:
        st.caption("Última milha: não estimada para estação/entrada específicas.")
    st.markdown("[Fonte turística]("+card["experience_source_url"]+")")
    return True


def render_data8_destination_preview(destination_id, *, tourism=None):
    """For the existing discovery card's open attraction/source expander."""
    research=tourism if tourism is not None else _tourism()
    summary=destination_research_overview(destination_id,tourism=research)
    if summary["researched_attractions"]:
        st.caption(str(summary["researched_attractions"]) +
                   " atração(ões) com ficha enriquecida neste lote, "
                   "incluindo estimativas editoriais.")
        for row in research["entries"]:
            if row["destination_id"]==destination_id:
                st.markdown("**"+row["attraction_id"]+"** · "+row["experience"]["why_visit"])
    for row in summary["unreconciled_candidates"]:
        st.caption("Atração ainda não cadastrada: "+row["name"]+
                   " · documentação turística disponível, identidade pendente.")
        st.markdown("[Fonte oficial]("+row["source_url"]+")")


def render_data8_cost_simulator(destination_id, *, tourism=None):
    """Optional user-input scenario, not a booking or budget-plan edit."""
    research=tourism if tourism is not None else _tourism()
    options=[x["attraction_id"] for x in research["entries"]
             if x["destination_id"]==destination_id]
    if not options:
        return
    st.markdown("##### Simular custos do casal (opcional)")
    st.caption("Valores de alimentação e transporte só entram se você informar "
               "faixas em euros. Não alteram o orçamento da viagem.")
    if not st.checkbox("Abrir simulação com premissas próprias",
                       key="data8_enable_cost_"+destination_id):
        return
    selected=st.multiselect("Atrações a incluir",options,
                            key="data8_cost_attractions_"+destination_id)
    if not selected:
        st.info("Selecione atrações para simular, sem adicioná-las ao roteiro.")
        return
    fields={}
    for label,key in (
        ("Trem intermunicipal, casal (€ mín-máx)","intercity"),
        ("Transporte local, casal (€ mín-máx)","local"),
        ("Alimentação opcional, casal (€ mín-máx)","dining"),
    ):
        raw=st.text_input(label,placeholder="Ex.: 30-60",
                          key="data8_cost_"+key+"_"+destination_id)
        try:
            fields[key]=parse_user_range(raw)
        except ValueError as exc:
            st.warning(str(exc))
            return
    optional=load_cost_addons()["optional_activities"]
    available=[x for x in optional if x["attraction_id"] in selected]
    addons=st.multiselect("Atividades extras publicadas (opcionais)",
                          [x["activity_id"] for x in available],
                          format_func=lambda key:next(x["name"] for x in available
                                                      if x["activity_id"]==key),
                          key="data8_addons_"+destination_id)
    fx_raw=st.text_input("Câmbio hipotético EUR→BRL (opcional)",
                         placeholder="Ex.: 6.00",
                         key="data8_fx_"+destination_id)
    try:
        fx=float(fx_raw.replace(",",".")) if fx_raw.strip() else None
        result=estimate_couple_excursion(selected,research=research,
            selected_addons=addons,intercity_couple=fields["intercity"],
            local_couple=fields["local"],dining_couple=fields["dining"],
            eur_to_brl=fx)
    except (ValueError,TypeError) as exc:
        st.warning("Premissas inválidas: "+str(exc))
        return
    lo,hi=result["partial_planning_range_eur"]
    st.caption(f"Parcela de custos conhecidos + hipóteses informadas: € {lo:.2f}–€ {hi:.2f}")
    if result["full_scenario_range_eur"] is None:
        st.warning("Estimativa incompleta. Faltam: "+
                   ", ".join(result["missing"])+
                   ". Não é preço total nem cotação para 2027.")
    else:
        st.success("Cenário completo apenas nas premissas fornecidas; "
                   "preços e viagens ainda precisam de conferência.")
    if result["partial_planning_range_brl"] is not None:
        brl=result["partial_planning_range_brl"]
        st.caption(f"R$ {brl[0]:.2f}–R$ {brl[1]:.2f} ao câmbio manual informado; "
                   "não é cotação cambial atual.")
