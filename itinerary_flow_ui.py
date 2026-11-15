"""Integrated itinerary builder: find → choose → organize → review → save.

This UI edits only the existing canonical TripPlan in session. Remote writes are
explicit, owner-gated and disclosed as PUBLIC GitHub storage. The Italian
proposals are not hotel, ticket or timing reservations.
"""
from __future__ import annotations
from html import escape
import json
from datetime import date,timedelta
import streamlit as st

from itinerary_flow_model import (
    destinations,get_choice,selected_rows,choice_counts,is_selected,
    period_options,UNASSIGNED,ITALY_STAGE,FRANCE_STAGE,EUROPE_STAGE_LABEL,
    validate_flow_backup
)
from planning_session import (active_plan,upsert_flexible_choice,
                              remove_flexible_choice,schedule_italy_visit,
                              schedule_package,unschedule_package)
from planning_status import save_label,explain_storage_error
from planning_store import sync_legacy_view
from travel_advisor_ui import _owner_signed_in,_secure_save
from attractions_model import load_base_routes,package_cost
from advisor_finance import advisor_projection


def _navigate(area:str,task:str)->None:
    from ux_navigation import set_task
    set_task(st.session_state,area,task)


def _show_add()->None:
    st.session_state["flow_add_open"]=True
    st.session_state["flow_save_open"]=False
    st.session_state["flow_organize_open"]=False


def _show_organize()->None:
    st.session_state["flow_organize_open"]=True
    st.session_state["flow_add_open"]=False
    st.session_state["flow_save_open"]=False


def _stage_label(stage:str)->str:
    return EUROPE_STAGE_LABEL if stage==FRANCE_STAGE else stage


def _period_label(value:str)->str:
    return {"Durante a estadia na França":"Durante a temporada europeia",
            "Primeiro fim de semana na França":
                "Primeiro fim de semana da temporada europeia"}.get(value,value)


def _show_save()->None:
    st.session_state["flow_save_open"]=True
    st.session_state["flow_add_open"]=False
    st.session_state["flow_organize_open"]=False


def _money(n:float)->str:
    return "R$ "+f"{n:,.0f}".replace(",",".")


def _render_add(plan:dict,catalog:dict)->None:
    if not st.session_state.get("flow_add_open",False):
        return
    with st.container(border=True):
        st.markdown("#### Adicionar ao meu roteiro")
        st.caption("Escolha os lugares e atrações agora. Datas e reservas podem "
                   "ser definidas posteriormente.")
        stage=st.segmented_control(
            "Em qual etapa?",[ITALY_STAGE,FRANCE_STAGE],default=ITALY_STAGE,
            key="flow_stage",selection_mode="single",
            format_func=_stage_label)
        term=st.text_input("Buscar cidade ou atração",key="flow_search",
                           placeholder="Ex.: Amalfi, Ravello, Colmar, Vaticano")
        all_choices=[d for d in destinations(catalog) if d["stage"]==stage]
        if term.strip():
            q=term.strip().casefold()
            all_choices=[d for d in all_choices if
                         q in d["name"].casefold() or
                         any(q in a["name"].casefold() for a in d["attractions"])]
        if not all_choices:
            st.info("Nenhum lugar encontrado. Tente outra busca ou etapa.")
        else:
            lookup={d["id"]:d for d in all_choices}
            dest_id=st.selectbox("Lugar",list(lookup),
                                 format_func=lambda key:lookup[key]["name"],
                                 key="flow_add_destination")
            dest=lookup[dest_id]
            already=is_selected(plan,dest_id)
            current=next((row for row in selected_rows(plan,catalog)
                          if row["id"]==dest_id),None)
            if already:
                st.info(dest["name"]+" já está no seu roteiro. "
                        "Você pode editar suas atrações abaixo.")
            labels={a["id"]:a["name"] for a in dest["attractions"]}
            defaults=(current["attractions"] if current else [])
            picked=st.multiselect("Atrações desejadas (1 a 5)",list(labels),
                                  default=[x for x in defaults if x in labels],
                                  format_func=lambda key:labels[key],
                                  key="flow_pick_"+dest_id,max_selections=5)
            periods=period_options(stage)
            period=st.selectbox("Quando? (opcional)",periods,
                                index=periods.index(current["period"])
                                if current and current["period"] in periods else 0,
                                key="flow_period_"+dest_id,
                                format_func=_period_label)
            st.caption("Sem data obrigatória · Não adiciona reservas nem "
                       "altera o roteiro de outra cidade-base.")
            if not already:
                if st.button("Adicionar ao roteiro",type="primary",
                             key="flow_add_confirm",disabled=not picked):
                    try:
                        upsert_flexible_choice(dest_id,picked,period)
                        st.session_state["flow_notice"]=(
                            dest["name"]+" incluído em Meu roteiro. "
                            "Continue adicionando outros lugares.")
                        st.rerun()
                    except (ValueError,KeyError) as exc:
                        st.error(str(exc))
            else:
                if st.button("Atualizar atrações e período",key="flow_add_update",
                             disabled=not picked):
                    try:
                        upsert_flexible_choice(dest_id,picked,period)
                        st.session_state["flow_notice"]=(
                            dest["name"]+" atualizado no planejamento.")
                        st.rerun()
                    except (ValueError,KeyError) as exc:
                        st.error(str(exc))
        if st.button("Concluir adição",key="flow_add_close"):
            st.session_state["flow_add_open"]=False
            st.rerun()


def _edit_destination(row:dict,catalog:dict)->None:
    item=get_choice(catalog,row["id"])
    labels={x["id"]:x["name"] for x in item["attractions"]}
    with st.expander("Editar "+item["name"],expanded=False):
        attractions=st.multiselect(
            "Atrações em "+item["name"],list(labels),
            default=[x for x in row["attractions"] if x in labels],
            format_func=lambda key:labels[key],
            key="flow_edit_attr_"+row["id"],max_selections=5)
        periods=period_options(row["stage"])
        chosen=st.selectbox("Período flexível",list(periods),
            index=periods.index(row["period"]) if row["period"] in periods else 0,
            key="flow_edit_period_"+row["id"],format_func=_period_label)
        a,b=st.columns(2)
        with a:
            if st.button("Salvar alterações",key="flow_edit_save_"+row["id"],
                         disabled=not attractions,width="stretch"):
                try:
                    upsert_flexible_choice(row["id"],attractions,chosen)
                    st.session_state["flow_notice"]=(
                        item["name"]+" atualizado no seu roteiro.")
                    st.rerun()
                except (ValueError,KeyError) as exc:
                    st.error(str(exc))
        with b:
            if st.button("Remover lugar",key="flow_remove_open_"+row["id"],
                         width="stretch"):
                st.session_state["flow_removing"]=row["id"]
        if st.session_state.get("flow_removing")==row["id"]:
            st.warning("Remover "+item["name"]+
                       " do seu planejamento? As datas desse destino, "
                       "se houver, também serão removidas.")
            yes,no=st.columns(2)
            with yes:
                if st.button("Confirmar remoção",
                             key="flow_remove_confirm_"+row["id"],type="primary"):
                    remove_flexible_choice(row["id"])
                    st.session_state.pop("flow_removing",None)
                    st.session_state["flow_notice"]=item["name"]+" removido."
                    st.rerun()
            with no:
                if st.button("Cancelar",key="flow_remove_cancel_"+row["id"]):
                    st.session_state.pop("flow_removing",None)
                    st.rerun()


def _selected_stage(rows:list[dict],stage:str,catalog:dict)->None:
    stage_rows=[r for r in rows if r["stage"]==stage]
    st.markdown("#### Etapa "+("1 · Lua de mel na Itália" if stage==ITALY_STAGE
                              else "2 · Temporada europeia"))
    if stage==ITALY_STAGE:
        proposal=active_plan().get("italy_proposal")
        if proposal:
            st.caption("**Proposta adotada para estudo:** "+proposal["label"]+
                       " · Roma "+str(proposal["rome_nights"])+" noites · Costa "+
                       str(proposal["coast_nights"])+" noites · Nápoles "+
                       str(proposal["naples_nights"])+" noites · Base costeira proposta: "+
                       proposal["coast_base_proposed"].title()+
                       ". Nenhuma hospedagem ou reserva confirmada.")
            if proposal["days"]!=active_plan()["italy_days"]:
                st.warning("O período italiano do plano foi alterado depois "
                           "da escolha desta proposta. Revise a distribuição "
                           "de noites antes de marcar dias.")
    if not stage_rows:
        if stage==ITALY_STAGE:
            st.caption("**Proposta de ponto de partida:** Roma (~4 noites) e "
                       "Costa Amalfitana (~5 noites), sujeitas à revisão. "
                       "Ainda não estão incluídas no seu plano.")
            st.button("Revisar proposta italiana",key="flow_italy_starter",
                      on_click=_navigate,args=("Meu roteiro","Itália"))
        else:
            st.info("Nenhum lugar escolhido na etapa francesa. "
                    "Você pode adicionar passeios mesmo sem decidir a cidade-base.")
        return
    count=st.session_state.get("flow_visible_"+stage,4)
    for row in stage_rows[:count]:
        item=get_choice(catalog,row["id"])
        with st.container(border=True):
            name_col,status_col=st.columns([3,1],gap="small")
            with name_col:
                st.markdown("**"+escape(row["name"])+"**")
                names={a["id"]:a["name"] for a in item["attractions"]}
                st.caption(" · ".join(names.get(x,x) for x in row["attractions"]))
                period=row["period"]
                if row["exact_dates"]:
                    st.caption("Organizado em "+", ".join(row["exact_dates"]))
                else:
                    st.caption(_period_label(period) if period!=UNASSIGNED
                               else "Sem período definido — pode organizar depois")
            with status_col:
                st.caption("Organizado" if row["period"]!=UNASSIGNED
                           or row["exact_dates"] else "No meu roteiro")
            _edit_destination(row,catalog)
    if len(stage_rows)>count:
        if st.button("Ver mais lugares ("+str(len(stage_rows)-count)+")",
                     key="flow_more_"+stage):
            st.session_state["flow_visible_"+stage]=count+4
            st.rerun()


def _compact_budget(plan:dict,catalog:dict,trip_data:dict,
                    finance_live:bool,eurfx:float,chffx:float)->None:
    if trip_data is None:
        st.caption("Custos disponíveis em Orçamento; ainda há valores sem cotação.")
        return
    try:
        selected=[a for group in plan["packages"].values() for a in group]
        historical=package_cost(catalog,load_base_routes(),
                                plan["base_city"],selected)
        snapshot=advisor_projection(trip_data,finance_live,plan,historical,
                                    eurfx,chffx,False)
    except (ValueError,KeyError,TypeError):
        st.caption("Projeção parcial indisponível; consulte as premissas em Orçamento.")
        return
    projection=snapshot["result"]
    st.caption("**Orçamento resumido:** projeção do casal "+
               _money(projection["total"])+
               " · margem nominal "+_money(projection["margin"])+
               " · "+str(len(historical["missing"]))+
               " componente(s) de passeio com preço pendente.")
    if projection["margin"]<0:
        st.warning("A projeção parcial excede o teto; as escolhas continuam editáveis.")
    st.caption("A Itália permanece na verba agregada, sem somar novamente ingressos. "
               "Valores faltantes não são €0; a margem não é dinheiro livre.")
    st.button("Ver orçamento detalhado",key="flow_go_budget",
              on_click=_navigate,args=("Orçamento","Detalhamento"))


def _render_organize(plan:dict,catalog:dict)->None:
    """Organize by flexible period or precise day without leaving this editor."""
    if not st.session_state.get("flow_organize_open",False):
        return
    with st.container(border=True):
        st.markdown("#### Organizar os passeios")
        st.caption("Escolha primeiro um período flexível ou, se já souber, "
                   "uma data. Nenhuma das opções cria reservas.")
        rows=selected_rows(plan,catalog)
        if not rows:
            st.info("Adicione um lugar antes de organizar.")
        else:
            by_id={r["id"]:r for r in rows}
            dest_id=st.selectbox("Lugar do meu roteiro",list(by_id),
                                 format_func=lambda key:by_id[key]["name"],
                                 key="flow_organize_destination")
            row=by_id[dest_id]
            mode=st.segmented_control(
                "Como organizar?",["Por período","Definir data"],
                default="Por período",key="flow_organize_mode",
                selection_mode="single")
            if mode!="Definir data":
                options=period_options(row["stage"])
                value=st.selectbox("Período sugerido",options,
                    index=options.index(row["period"]) if row["period"] in options else 0,
                    key="flow_organize_period",format_func=_period_label)
                if st.button("Guardar período",key="flow_organize_save_period",
                             type="primary"):
                    upsert_flexible_choice(dest_id,row["attractions"],value)
                    st.session_state["flow_notice"]="Período de "+row["name"]+" atualizado."
                    st.rerun()
            else:
                start=date.fromisoformat(plan["departure_date"])
                if row["stage"]==FRANCE_STAGE:
                    start+=timedelta(days=plan["italy_days"])
                    end=date.fromisoformat(plan["departure_date"])+timedelta(
                        days=plan["total_days"]-1)
                else:
                    end=start+timedelta(days=plan["italy_days"]-1)
                previous=next((date.fromisoformat(d) for d in row["exact_dates"]
                               if start<=date.fromisoformat(d)<=end),start)
                chosen=st.date_input("Data proposta",value=previous,
                    min_value=start,max_value=end,
                    key="flow_organize_date_"+row["stage"])
                st.caption("Datas baseadas na partida planejada; sujeitas a alterações. "
                           "A data deve permanecer dentro da etapa selecionada.")
                if st.button("Definir data",key="flow_organize_save_date",
                             type="primary"):
                    try:
                        if row["stage"]==ITALY_STAGE:
                            schedule_italy_visit(dest_id,chosen.isoformat())
                        else:
                            schedule_package(chosen.isoformat(),dest_id)
                        st.session_state["flow_notice"]="Data proposta registrada para "+row["name"]+"."
                        st.rerun()
                    except (ValueError,KeyError) as exc:
                        st.error(str(exc))
                if row["exact_dates"]:
                    if st.button("Retirar data definida",key="flow_organize_remove_date"):
                        if row["stage"]==ITALY_STAGE:
                            schedule_italy_visit(dest_id,None)
                        else:
                            unschedule_package(row["exact_dates"][0])
                        st.session_state["flow_notice"]="Data removida; o lugar permanece escolhido."
                        st.rerun()
        st.button("Abrir calendário completo",key="flow_organize_full_calendar",
                  on_click=_navigate,args=("Meu roteiro","Calendário"))
        if st.button("Concluir organização",key="flow_organize_close"):
            st.session_state["flow_organize_open"]=False
            st.rerun()


def _save_panel(plan:dict,catalog:dict)->None:
    if not st.session_state.get("flow_save_open"):
        return
    with st.container(border=True):
        st.markdown("#### Salvar e recuperar planejamento")
        st.caption("As alterações são mantidas na sessão até salvar ou baixar um backup.")
        st.download_button("Baixar backup JSON",data=json.dumps(
            plan,ensure_ascii=False,indent=2),
            file_name="nossa-europa-planejamento.json",
            mime="application/json",key="flow_backup_download")
        uploaded=st.file_uploader("Recuperar backup local (JSON)",
                                  type=["json"],key="flow_import_json")
        if uploaded is not None:
            try:
                candidate=json.loads(uploaded.getvalue().decode("utf-8"))
                validate_flow_backup(candidate,catalog)
            except (ValueError,KeyError,TypeError,UnicodeDecodeError) as exc:
                st.error("Backup incompatível ou inválido. Nenhum dado foi substituído.")
            else:
                st.warning("Revisão do backup: "+
                           str(len(selected_rows(candidate,catalog)))+
                           " lugares. Restaurar substituirá o plano DESTA SESSÃO, "
                           "sem modificar automaticamente arquivos do GitHub.")
                if st.button("Confirmar recuperação nesta sessão",
                             key="flow_import_confirm"):
                    st.session_state["advisor_plan"]=candidate
                    st.session_state["advisor_saved_snapshot"]=None
                    st.session_state["advisor_github_sha"]=None
                    st.session_state["advisor_autosave_pending"]=False
                    st.session_state["advisor_autosave_optin"]=False
                    st.session_state["advisor_local_changed"]=True
                    sync_legacy_view(candidate,st.session_state)
                    st.session_state["flow_notice"]=(
                        "Backup recuperado nesta sessão; salve ou exporte para não perder.")
                    st.session_state["flow_save_open"]=False
                    st.rerun()
        if _owner_signed_in():
            st.warning("O repositório GitHub deste aplicativo é PÚBLICO: "
                       "as escolhas gravadas ficam acessíveis a outras pessoas.")
            agree=st.checkbox("Compreendo e autorizo salvar este planejamento "
                              "no repositório público",
                              key="flow_public_repo_ack")
            if st.button("Confirmar salvamento online",key="flow_save_confirm",
                         disabled=not agree,type="primary"):
                st.session_state["advisor_public_repo_ack"]=True
                try:
                    _secure_save(plan)
                    st.session_state["flow_notice"]="Planejamento salvo no GitHub público."
                    st.session_state["flow_save_open"]=False
                    st.rerun()
                except Exception as exc:
                    st.error(explain_storage_error(exc))
        else:
            st.info("Salvamento remoto disponível somente para o proprietário "
                    "autenticado. O backup JSON funciona sem login. "
                    "Recarregue o backup pelo painel avançado de salvamento.")
        if st.button("Fechar",key="flow_save_close"):
            st.session_state["flow_save_open"]=False
            st.rerun()


def render_itinerary_workbench(plan:dict,catalog:dict,
                               trip_data:dict|None=None,finance_live:bool=False,
                               eurfx:float=6.3,chffx:float=7.1)->None:
    """Continuously edit a single TripPlan, with no automatic remote write."""
    stats=choice_counts(plan,catalog)
    saved=st.session_state.get("advisor_saved_snapshot")
    signed_in=_owner_signed_in()
    label,hint=save_label(plan,saved,signed_in)
    if not signed_in:
        dirty=(saved!=plan) if saved is not None else plan["revision"]>0
        label="Alterações não salvas" if dirty else "Ainda não salvo"
        hint="Você pode baixar um backup local; armazenamento remoto exige autenticação"
    st.markdown("### Meu roteiro")
    st.caption("Organize a viagem sem precisar decidir datas e reservas agora.")
    metrics=st.columns(3)
    metrics[0].metric("Itália",str(plan["italy_days"])+" dias")
    metrics[1].metric("Temporada europeia",str(plan["total_days"]-plan["italy_days"])+" dias")
    metrics[2].metric("Lugares escolhidos",stats["destinations"])
    st.caption(label+" · "+hint+" · "+
               str(stats["organized"])+" lugar(es) organizado(s) por período ou data")
    a,b,c=st.columns(3,gap="small")
    a.button("＋ Adicionar passeio",key="flow_add_open_button",
             on_click=_show_add,type="primary",width="stretch")
    b.button("Organizar dias",key="flow_go_calendar",
             on_click=_show_organize,width="stretch")
    c.button("Salvar planejamento",key="flow_open_save",
             on_click=_show_save,width="stretch")
    if st.session_state.get("flow_notice"):
        st.success(st.session_state.pop("flow_notice"))
    _render_add(active_plan(),catalog)
    _render_organize(active_plan(),catalog)
    _save_panel(active_plan(),catalog)
    rows=selected_rows(active_plan(),catalog)
    _selected_stage(rows,ITALY_STAGE,catalog)
    _selected_stage(rows,FRANCE_STAGE,catalog)
    with st.expander("Melhorar meu roteiro",expanded=False):
        st.caption("As sugestões abaixo não alteram suas escolhas automaticamente.")
        if not any(r["stage"]==ITALY_STAGE for r in rows):
            st.write("• Comece por Roma e Costa Amalfitana, que fazem parte da lua de mel.")
        if any(r["period"]==UNASSIGNED for r in rows):
            st.write("• Organize os períodos dos lugares que ainda estão sem previsão.")
        st.write("• Compare deslocamentos e distribua os dias antes de reservar.")
        st.button("Abrir sugestões detalhadas",key="flow_go_suggestions",
                  on_click=_navigate,args=("Meu roteiro","Sugestões"))
    _compact_budget(active_plan(),catalog,trip_data,finance_live,eurfx,chffx)
    st.caption("Escolhido = incluído no plano · Organizado = com período ou data "
               "· Reservado = somente com confirmação externa (não inferida).")
