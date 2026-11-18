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


def parse_user_range(raw: str, *, roundtrip=False):
    """Blank => unknown; two explicitly typed nonnegative EUR amounts => range."""
    if not raw or not raw.strip():
        return None
    value = raw.strip().replace(" ", "")
    if not re.fullmatch(r"\d+(?:[.,]\d{1,2})?-\d+(?:[.,]\d{1,2})?",value):
        raise ValueError("Informe a faixa como 30-60 (euros, mínimo-máximo).")
    a,b=[float(x.replace(",",".")) for x in value.split("-",1)]
    if a>b or b>100000:
        raise ValueError("Faixa inválida: limite máximo inferior ao mínimo.")
    result = {"min_eur":a,"max_eur":b,
              "state":"user_editorial_assumption",
              "method":"premissa preenchida manualmente para planejamento"}
    if roundtrip:
        result["journey_scope"] = "roundtrip_two_adults"
    return result


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


def compose_legacy_attraction_details(entry, *, tourism=None, access=None):
    """Read-only, field-level composition. Unresearched DATA 8 fields never erase
    trustworthy legacy descriptions, ticket details, hours or provenance."""
    legacy = deepcopy(entry)
    card = build_data8_card(entry["attraction_id"], tourism=tourism, access=access)
    ticket = deepcopy(entry.get("ticket_main") or {})
    admission = card["admission"] if card else None
    if admission is not None and admission["state"] != "unknown":
        effective_ticket = {"origin": "data8", **deepcopy(admission)}
    elif ticket.get("amount") is not None:
        effective_ticket = {"origin": "legacy", "state": "published_price", **ticket}
    elif ticket.get("status") == "not_applicable":
        effective_ticket = {"origin": "legacy", "state": "external_no_ticket",
                            "amount": None, **ticket}
    else:
        effective_ticket = {"origin": "none", "state": "unknown", "amount": None}
    opening = (card["opening"] if card and
               card["opening"]["state"] == "published_general_rule" else None)
    opening_rule = (opening["rule"] if opening else entry.get("opening_rule"))
    opening_origin = ("data8" if opening else "legacy" if opening_rule else "none")
    sources = []
    for url in (card["experience_source_url"] if card else None,
                admission.get("source_url") if admission else None,
                opening.get("source_url") if opening else None,
                entry.get("opening_source_url")):
        if url and url not in sources:
            sources.append(url)
    why_new = card["why_visit"] if card else None
    why_old = entry.get("why_visit")
    return {
        "attraction_id": entry["attraction_id"],
        "name": entry.get("name"),
        "description": entry.get("description"),
        "why_visit": why_new or why_old,
        "legacy_why_visit": why_old if why_old and why_new and
            why_old.strip().casefold() != why_new.strip().casefold() else None,
        "opening_rule": opening_rule,
        "opening_origin": opening_origin,
        "admission": effective_ticket,
        "legacy_ticket_reference": ticket if ticket.get("amount") is not None and
            effective_ticket["origin"] == "data8" and
            ticket.get("amount") != effective_ticket.get("amount") else None,
        "additional_activity": deepcopy(entry.get("additional_activity") or {}),
        "legacy_visit_minutes": entry.get("visit_minutes"),
        "legacy_visit_duration_status": entry.get("visit_duration_status"),
        "legacy_last_mile_observations": deepcopy(entry.get("last_mile_observations") or []),
        "data8_duration": deepcopy(card["duration"]) if card else None,
        "data8_walk": deepcopy(card["local_walk"]) if card else None,
        "sources": sources,
        "data8": card,
        "legacy": legacy,
    }


def render_composed_attraction_details(entry, *, tourism=None, access=None):
    """Render exactly one primary view per field; retain distinct legacy facts."""
    item = compose_legacy_attraction_details(entry, tourism=tourism, access=access)
    if item["description"]:
        st.write(item["description"])
    if item["why_visit"]:
        st.caption("Por que visitar: " + item["why_visit"])
    if item["legacy_why_visit"]:
        st.caption("Nota do catálogo original: " + item["legacy_why_visit"])
    if item["opening_rule"]:
        st.write("Funcionamento pesquisado: " + item["opening_rule"])
        st.caption("Referência " + ("DATA 8" if item["opening_origin"] == "data8"
                                   else "histórica do catálogo") +
                   "; não confirma abertura em 2027.")
    else:
        st.caption("Horários de visita ainda não pesquisados.")
    admission = item["admission"]
    if admission["state"] == "free_general_entry":
        st.caption("Entrada geral gratuita conforme fonte histórica; "
                   "atividades opcionais são separadas.")
    elif admission["state"] == "published_price":
        st.caption("Ingresso histórico de referência: " + str(admission["amount"]) +
                   " " + str(admission.get("currency") or "") +
                   " · unidade/validade precisam ser conferidas.")
    elif admission["state"] == "external_no_ticket":
        st.caption("Somente visita externa sem ingresso principal segundo " +
                   ("documentação turística" if admission["origin"] == "data8"
                    else "referência histórica") +
                   "; não inclui interiores e serviços.")
    else:
        st.caption("Preço de ingresso desconhecido; não equivale a gratuidade.")
    if item["legacy_ticket_reference"]:
        old = item["legacy_ticket_reference"]
        st.caption("Referência histórica distinta do catálogo: " +
                   str(old["amount"]) + " " + str(old.get("currency") or "") +
                   " · conferir escopo da visita.")
    activity = item["additional_activity"]
    if activity:
        st.caption("Atividade adicional do catálogo: " + str(activity.get("name")) +
                   " — " + str(activity.get("amount")) + " " +
                   str(activity.get("currency") or "") + " · histórica, não 2027.")
    if item["legacy_visit_minutes"] is not None:
        st.caption("Duração registrada no catálogo: " +
                   str(item["legacy_visit_minutes"]) + " min · " +
                   str(item["legacy_visit_duration_status"]))
    elif item["data8_duration"] and item["data8_duration"]["state"] != "unknown":
        d = item["data8_duration"]
        st.caption("Duração " + ("editorial" if d["state"] == "editorial_estimate"
                   else "orientada pelo operador") + ": " +
                   str(d["min_minutes"]) + "–" + str(d["max_minutes"]) +
                   " min · não confirmada para 2027.")
    else:
        st.caption("Duração de visita ainda desconhecida.")
    if item["legacy_last_mile_observations"]:
        st.caption("Acessos históricos registrados: " +
                   str(len(item["legacy_last_mile_observations"])) +
                   " · nenhuma viagem em 2027 confirmada.")
    walk = item["data8_walk"]
    if walk and walk["state"] == "editorial_two_direction_range":
        a, b = walk["to_attraction_range_min"], walk["to_station_range_min"]
        st.caption(f"Caminhada editorial: {a[0]}–{a[1]} min de ida; "
                   f"{b[0]}–{b[1]} min de volta. Não é rota medida.")
    elif not item["legacy_last_mile_observations"]:
        st.caption("Acesso local ainda não medido.")
    for i, url in enumerate(item["sources"], 1):
        st.markdown(f"[Fonte de pesquisa {i}]({url})")
    return item


def render_data8_attraction_details(attraction_id, *, tourism=None, access=None):
    """Returns True if an enriched card was rendered; caller retains legacy fallback."""
    research=tourism if tourism is not None else _tourism()
    if attraction_id not in research["by_id"]:
        return False
    local=access if access is not None else _access()
    card=build_data8_card(attraction_id,tourism=research,access=local)
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


def render_data8_destination_preview(destination_id, *, tourism=None, attraction_names=None):
    """For the existing discovery card's open attraction/source expander."""
    research=tourism if tourism is not None else _tourism()
    attraction_names = attraction_names or {}
    summary=destination_research_overview(destination_id,tourism=research)
    if summary["researched_attractions"]:
        st.caption(str(summary["researched_attractions"]) +
                   " atração(ões) com ficha enriquecida neste lote, "
                   "incluindo estimativas editoriais.")
        for row in research["entries"]:
            if row["destination_id"]==destination_id:
                st.markdown("**"+attraction_names.get(row["attraction_id"], row["attraction_id"])+"**")
                st.caption(row["experience"]["why_visit"])
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
    st.caption("Escolha explicitamente o escopo de cada visita. Desconhecido não é gratuito.")
    visit_scopes={}
    scope_labels={"unknown":"A definir / custo desconhecido",
                  "external_visit":"Somente área externa",
                  "general_entry":"Entrada geral",
                  "optional_activity":"Entrada e atividade opcional"}
    for aid in selected:
        admission=research["by_id"][aid]["admission"]["state"]
        initial="general_entry" if admission in ("free_general_entry","published_price") else "unknown"
        visit_scopes[aid]=st.selectbox("Escopo da visita: "+aid,
            list(scope_labels),format_func=lambda x:scope_labels[x],
            index=list(scope_labels).index(initial),
            key="data8_scope_"+destination_id+"_"+aid)
    st.caption("As faixas de trem e transporte local devem incluir ida e volta de DOIS adultos. "
               "São premissas manuais, não tarifas verificadas.")
    fields={}
    for label,key in (
        ("Trem ida e volta, 2 adultos (€ mín-máx)","intercity"),
        ("Transporte local ida e volta, 2 adultos (€ mín-máx)","local"),
        ("Alimentação opcional, casal (€ mín-máx)","dining"),
    ):
        raw=st.text_input(label,placeholder="Ex.: 30-60",
                          key="data8_cost_"+key+"_"+destination_id)
        try:
            fields[key]=parse_user_range(raw,roundtrip=key in ("intercity","local"))
        except ValueError as exc:
            st.warning(str(exc))
            return
    optional=load_cost_addons()["optional_activities"]
    available=[x for x in optional if x["attraction_id"] in selected and
               visit_scopes[x["attraction_id"]] in ("general_entry","optional_activity")]
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
            selected_addons=addons,visit_scopes=visit_scopes,
            intercity_couple=fields["intercity"],
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
