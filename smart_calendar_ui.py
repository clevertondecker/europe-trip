"""UX 3.5 integrated smart calendar, keeping one canonical TripPlan.

Advanced research/budget links return to this task. Proposed dates are not
operator bookings, rail timetables or payment events.
"""
from __future__ import annotations

from datetime import date
import json
import streamlit as st

from planning_session import active_plan,accept_approved_plan
from itinerary_flow_model import selected_rows,ITALY_STAGE,FRANCE_STAGE
from smart_calendar_model import (
    availability_matrix,validate_calendar_preferences,suggest_calendar,
    manual_calendar_move,review_calendar_change,apply_calendar_change,
)
from planning_status import save_label


def _jump(area:str,task:str)->None:
    from ux_navigation import set_task
    state=st.session_state
    state["ux35_return"]=True
    state["flow_return_stage"]=state.get("ux35_stage",FRANCE_STAGE)
    state["flow_return_destination"]=state.get("ux35_destination")
    set_task(state,area,task)


def _weekday(iso:str)->str:
    names=("Seg","Ter","Qua","Qui","Sex","Sáb","Dom")
    return names[date.fromisoformat(iso).weekday()]


def _names(catalog,plan):
    return {r["id"]:r["name"] for r in selected_rows(plan,catalog)}


def _preferences():
    with st.expander("Meu horário de trabalho na Europa · opcional",expanded=False):
        st.caption("Não inferimos seu horário europeu do expediente no Brasil. "
                   "Em dias úteis de trabalho, passeios longos ficam bloqueados. "
                   "Atividades à noite não são agendadas automaticamente sem "
                   "horários de abertura e retorno confirmados.")
        timezone=st.selectbox("Fuso dos dias na Europa",
                              ["Europe/Paris","Europe/Rome","Europe/Luxembourg"],
                              key="ux35_timezone")
        custom=st.checkbox("Já sei o horário local do meu expediente",
                           key="ux35_known_hours")
        start=end=None
        if custom:
            start=st.text_input("Início do trabalho (HH:MM, horário europeu)",
                                value="09:00",key="ux35_work_start")
            end=st.text_input("Fim do trabalho (HH:MM, horário europeu)",
                              value="18:00",key="ux35_work_end")
    return validate_calendar_preferences({
        "timezone":st.session_state.get("ux35_timezone","Europe/Paris"),
        "work_start":start,"work_end":end,"allow_evenings":False,
    })


def _calendar_overview(plan,catalog,preferences):
    days=availability_matrix(plan,preferences)
    bydate={r["date"]:r for r in days}
    selected=selected_rows(plan,catalog)
    names={r["id"]:r["name"] for r in selected}
    italy=sum(r["stage"]==ITALY_STAGE for r in days)
    setup=sum(r["setup"] for r in days)
    work=sum(r["workday"] for r in days)
    weekend=sum("Fim de semana" in r["activity"] for r in days)
    a,b,c,d=st.columns(4)
    a.metric("Itália",italy)
    b.metric("Instalação",setup)
    c.metric("Dias de trabalho",work)
    d.metric("Fins de semana livres",weekend)
    stage=st.segmented_control("Etapa",
                              [ITALY_STAGE,FRANCE_STAGE],
                              default=ITALY_STAGE,
                              format_func=lambda x:"Temporada europeia" if x==FRANCE_STAGE else x,
                              key="ux35_stage")
    filtered=[r for r in days if r["stage"]==stage]
    weeks=sorted({(date.fromisoformat(r["date"])-date.fromisoformat(
        plan["departure_date"])).days//7 for r in filtered})
    chosen=st.selectbox("Semana da viagem",weeks,
                        format_func=lambda i:("Semana "+str(i+1)),
                        key="ux35_week")
    week=[r for r in filtered if (date.fromisoformat(r["date"])-date.fromisoformat(
         plan["departure_date"])).days//7==chosen]
    st.dataframe([{"Dia":_weekday(r["date"]),
                   "Data":date.fromisoformat(r["date"]).strftime("%d/%m/%Y"),
                   "Etapa":("Itália" if r["stage"]==ITALY_STAGE else "Temporada europeia"),
                   "Contexto":r["activity"],
                   "Passeio":names.get(r["occupied_by"],"Sem data aprovada")
                               if r["occupied_by"] else "Livre/sem passeio",
                   "Situação":r["date_status"]} for r in week],
                 hide_index=True,width="stretch")
    st.caption("Datas **aprovadas no roteiro** não são reservas. A grade mostra "
               "um período ilustrativo segundo as premissas atuais. "
               "Horários de 2027, ingressos e transportes precisam de confirmação.")
    unscheduled=[r for r in selected if not r["exact_dates"]]
    st.caption(str(len(unscheduled))+" lugar(es) selecionado(s) sem dia definido. "
               "Podem continuar organizados só por período flexível.")
    return bydate,selected


def _draft_download(proposal):
    with st.expander("Rascunho portátil (JSON) · avançado"):
        st.caption("Este estudo fica somente na sessão. O download é opcional "
                   "e não publica seus dados no GitHub.")
        raw=json.dumps(proposal,ensure_ascii=False,indent=2).encode("utf-8")
        st.download_button("Baixar proposta",
                           data=raw,file_name="nossa-europa-datas-propostas.json",
                           mime="application/json",key="ux35_download_draft")
        file=st.file_uploader("Reabrir proposta JSON",type=["json"],
                              key="ux35_draft_import")
        if file and st.button("Validar rascunho importado",
                              key="ux35_import_review"):
            try:
                data=file.getvalue()
                if not 0<len(data)<=100_000:
                    raise ValueError("Arquivo inválido ou maior que 100 kB")
                imported=json.loads(data.decode("utf-8"))
                # Validate against current plan and current selected catalog before
                # storing; a public JSON cannot bypass revision/plan safeguards.
                review_calendar_change(active_plan(),imported,
                                       st.session_state["ux35_catalog"])
                st.session_state["ux35_review_proposal"]=imported
                st.session_state["ux35_message"]=(
                    "Rascunho importado e validado, aguardando confirmação.")
                st.rerun()
            except (ValueError,TypeError,KeyError,UnicodeError) as exc:
                st.error("Não foi possível recuperar: "+str(exc))


def _review_panel(plan,catalog):
    proposal=st.session_state.get("ux35_review_proposal")
    if not proposal:return
    with st.container(border=True):
        st.markdown("#### Revisar antes de aplicar")
        try:
            report=review_calendar_change(plan,proposal,catalog)
        except (ValueError,TypeError,KeyError) as exc:
            st.warning("Proposta precisa ser recalculada: "+str(exc))
            st.session_state.pop("ux35_review_proposal",None)
            return
        names=_names(catalog,plan)
        st.caption("Proposta baseada na revisão "+str(report["base_revision"])+
                   ". A confirmação altera exclusivamente as datas desta sessão.")
        for item in report["changes"]:
            before=item["from_date"] or "Sem data"
            after=item["to_date"] or "Voltar ao período flexível"
            st.markdown("**"+names.get(item["destination_id"],item["destination_id"])+
                        "** · "+before+" → "+after)
            st.caption(item["reason"])
            for warning in item["warnings"]:st.caption("A confirmar: "+warning)
        if report["unresolved"]:
            st.warning(str(len(report["unresolved"]))+
                       " passeio(s) permanecem sem data: "+
                       "; ".join(item["reason"] for item in report["unresolved"]))
        st.info("**Diferença de custo: não calculável** sem tarifas normais de "
                "ida/volta para as datas de 2027. A verba de passeios já prevista "
                "não é cobrada novamente.")
        st.caption("Inalterados: "+", ".join(report["unchanged"])+". "
                   "Nenhuma reserva foi criada.")
        approved=st.checkbox("Revisei as datas e quero aplicá-las somente ao roteiro",
                             key="ux35_confirm_ack",value=False)
        a,b=st.columns(2)
        if a.button("Confirmar datas no meu plano",key="ux35_confirm",
                    type="primary",disabled=not approved):
            try:
                if active_plan()["revision"]!=report["base_revision"]:
                    raise ValueError("Revisão mudou; revise novamente")
                next_plan=apply_calendar_change(active_plan(),proposal,catalog,
                                                confirmed=True)
                accept_approved_plan(next_plan)
                st.session_state.pop("ux35_review_proposal",None)
                st.session_state.pop("ux35_proposals",None)
                st.session_state["ux35_message"]=(
                    "Datas aprovadas no roteiro desta sessão. "
                    "Ainda não foram salvas remotamente nem reservadas.")
                st.rerun()
            except (ValueError,TypeError,KeyError) as exc:
                st.error(str(exc))
        if b.button("Cancelar proposta",key="ux35_cancel"):
            st.session_state.pop("ux35_review_proposal",None)
            st.rerun()


def _suggest(plan,catalog,routes,preferences):
    st.markdown("#### Sugerir dias para meus passeios")
    st.caption("Um rascunho não muda o plano. Férias e fins de semana são "
               "priorizados; instalação e expediente ficam protegidos. "
               "As viagens com retorno desconhecido continuam condicionais.")
    if st.button("Sugerir dias",key="ux35_suggest",type="primary"):
        try:
            plans=suggest_calendar(plan,catalog,routes,preferences)
            st.session_state["ux35_proposals"]=plans
            st.session_state.pop("ux35_review_proposal",None)
            if not plans:
                st.session_state["ux35_message"]=(
                    "Não há novas datas sugeríveis com as informações atuais. "
                    "Confira se os passeios já têm datas ou se faltam rotas.")
            st.rerun()
        except (ValueError,KeyError) as exc:
            st.warning(str(exc))
    proposals=st.session_state.get("ux35_proposals",[])
    if proposals:
        selected=st.selectbox("Escolha uma sugestão para avaliar",
                              list(range(len(proposals))),
                              format_func=lambda i:"Opção "+str(i+1)+" · "+
                               str(len(proposals[i]["changes"]))+" passeios",
                              key="ux35_variant")
        proposal=proposals[selected]
        names=_names(catalog,plan)
        for change in proposal["changes"]:
            st.markdown("**"+names.get(change["destination_id"],
                                      change["destination_id"])+
                        "** · "+change["to_date"])
            st.caption(change["reason"])
            for warning in change["warnings"]:st.caption("A confirmar: "+warning)
            if change["source"]:st.markdown("[Fonte da rota]("+change["source"]+")")
        if proposal["unresolved"]:
            st.warning("Sem data por enquanto: "+"; ".join(
                names.get(x["destination_id"],x["destination_id"])+
                " — "+x["reason"] for x in proposal["unresolved"]))
        if st.button("Revisar esta sugestão",key="ux35_review"):
            st.session_state["ux35_review_proposal"]=proposal
            st.rerun()
        _draft_download(proposal)


def _manual(plan,catalog):
    with st.expander("Mover um passeio ou retirar a data",expanded=False):
        rows=selected_rows(plan,catalog)
        if not rows:
            st.caption("Escolha um passeio em Meu planejamento antes de marcar dias.")
            return
        lookup={r["id"]:r for r in rows}
        chosen=st.selectbox("Passeio",list(lookup),
                            format_func=lambda key:lookup[key]["name"],
                            key="ux35_destination")
        row=lookup[chosen]
        existing=row["exact_dates"]
        old=st.selectbox("Visita a reorganizar",
                         [""]+existing,key="ux35_from_date",
                         format_func=lambda key:key or "Sem data / nova visita")
        valid=[r for r in availability_matrix(plan)
               if r["stage"]==row["stage"]]
        choices=[""]+[r["date"] for r in valid]
        if not existing and "ux35_to_date" not in st.session_state:
            st.session_state["ux35_to_date"]=""
        target=st.selectbox("Nova data",choices,key="ux35_to_date",
                            format_func=lambda key:key or "Sem data / retirar dia")
        st.caption("Datas que conflitam com trabalho, instalação, etapa ou "
                   "outro passeio serão rejeitadas antes de aplicar.")
        if st.button("Revisar alteração manual",key="ux35_manual_review"):
            try:
                proposal=manual_calendar_move(
                    plan,catalog,chosen,row["stage"],target or None,
                    from_day=old or "")
                st.session_state["ux35_review_proposal"]=proposal
                st.rerun()
            except (ValueError,KeyError) as exc:
                st.warning(str(exc))


def render_smart_calendar(plan:dict,catalog:dict,routes:dict,
                          trip_data:dict|None=None,
                          sync_sources:dict|None=None)->None:
    """One contextual route, no extra top-level tab or automatic booking."""
    st.markdown("### Organizar a nossa viagem")
    st.caption("Meu roteiro › Organizar viagem · Planejamento, não reserva")
    st.session_state["ux35_catalog"]=catalog
    if st.session_state.get("ux35_message"):
        st.success(st.session_state.pop("ux35_message"))
    with st.container(border=True):
        st.caption("**Plano oficial** · "+plan["base_city"].capitalize()+
                   " · partida proposta "+plan["departure_date"]+
                   " · R$ "+plan["budget_scenario"].replace("k"," mil")+
                   " · datas sujeitas a revisão")
        state=st.session_state
        a,b=st.columns(2)
        a.button("Ver orçamento",key="ux35_go_budget",
                 on_click=_jump,args=("Orçamento","Resumo financeiro"))
        b.button("Pesquisar passeios",key="ux35_go_research",
                 on_click=_jump,args=("Explorar","Passeios"))
    # UX 4.8: optional, sidecar-only weekend grouping; keeps all canonical dates,
    # outings, calendar proposals and remote persistence unchanged.
    from ux48_weekend_groups_ui import render_weekend_planner
    render_weekend_planner(active_plan(),catalog)
    try:
        preferences=_preferences()
    except (ValueError,KeyError,TypeError) as exc:
        st.warning(str(exc));return
    _calendar_overview(plan,catalog,preferences)
    _suggest(plan,catalog,routes,preferences)
    _manual(plan,catalog)
    _review_panel(active_plan(),catalog)
    st.caption("**Salvar:** decisões confirmadas atualizam o TripPlan nesta sessão. "
               "Para manter entre sessões, use Salvar planejamento ou um backup "
               "local em Meu planejamento. GitHub público nunca recebe "
               "rascunhos automaticamente.")
