"""UX 4.8 — optional weekend trip groups in Organizar viagem.

All grouped data stays outside TripPlan and requires explicit file export
to persist beyond the browser session. Only selected canonical destinations
can be included, in user-chosen order.
"""
from __future__ import annotations
from datetime import date
import streamlit as st
from ux48_weekend_groups_model import (
    empty_groups,reconcile_removed_outings,create_group,update_group,
    remove_group,ungrouped_outings,available_weekends,
    set_rest_weekend,export_groups,import_groups,PERIODS,
)
from itinerary_flow_model import selected_rows,FRANCE_STAGE

def _state(plan,catalog):
    key="ux48_weekend_groups"
    value=st.session_state.get(key)
    if value is None or value.get("plan_id")!=plan["plan_id"]:
        value=empty_groups(plan)
    else:
        value=reconcile_removed_outings(value,plan,catalog)
    st.session_state[key]=value
    return value

def _save(new):
    st.session_state["ux48_weekend_groups"]=new
    st.session_state["ux48_weekend_message"]="Agrupamentos atualizados apenas nesta sessão. Exporte o rascunho para guardar uma cópia."

def render_weekend_planner(plan,catalog):
    st.markdown("### Organizar viagens de fim de semana")
    st.caption("Agrupe passeios que já estão no seu roteiro. Não cria reservas, "
               "não muda datas oficiais ou orçamento e não duplica atrações.")
    groups=_state(plan,catalog)
    chosen=[r for r in selected_rows(plan,catalog) if r["stage"]==FRANCE_STAGE]
    byid={r["id"]:r for r in chosen}
    if st.session_state.get("ux48_weekend_message"):
        st.success(st.session_state.pop("ux48_weekend_message"))
    if not chosen:
        st.info("Adicione um passeio em Meu planejamento para organizar fins de semana.")
    else:
        with st.expander("Criar viagem de fim de semana",expanded=not groups["groups"]):
            used={d for g in groups["groups"] for d in g["destinations"]}
            options=[id for id in byid if id not in used]
            if not options:
                st.info("Todos os passeios já pertencem a uma viagem. Edite um grupo para alterar.")
            else:
                with st.form("ux48_create_form"):
                    name=st.text_input("Nome da viagem",placeholder="Bruxelas + Bruges")
                    selected=st.multiselect("Passeios na ordem desejada",options,
                        format_func=lambda id:byid[id]["name"],max_selections=6)
                    period=st.selectbox("Período flexível",PERIODS)
                    nights=st.number_input("Pernoites hipotéticos",min_value=0,
                                            max_value=3,value=0,step=1)
                    slots=[r for r in available_weekends(groups,plan,catalog)
                           if r["status"]=="livre · não reservado"]
                    picked=st.selectbox("Data opcional (sábado)",
                        [None]+[r["start"] for r in slots],
                        format_func=lambda d:"Ainda não definida" if d is None else d)
                    notes=st.text_area("Observações e pendências",max_chars=700,
                        placeholder="Verificar trem de retorno e hotel")
                    status=st.selectbox("Estado do rascunho",
                        ["estudo","planejado"],format_func=lambda x:
                        "Em estudo" if x=="estudo" else "Planejado (não reservado)")
                    if st.form_submit_button("Criar agrupamento",disabled=not selected):
                        try:
                            _save(create_group(groups,plan,catalog,name=name,
                               destinations=selected,period=period,start_date=picked,
                               nights=int(nights),notes=notes,status=status))
                            st.rerun()
                        except (ValueError,TypeError) as exc:
                            st.error(str(exc))
    st.markdown("#### Viagens planejadas")
    if not groups["groups"]:
        st.caption("Ainda não há viagens agrupadas. Um roteiro com duas cidades pode formar um único fim de semana.")
    for group in groups["groups"]:
        with st.container(border=True):
            st.markdown("**"+group["name"]+"**")
            st.caption(" → ".join(byid[id]["name"] for id in group["destinations"] if id in byid))
            st.caption(("Sábado "+group["start_date"] if group["start_date"]
                        else "Data ainda não definida")+" · "+group["period"]+" · "+
                       str(group["nights"])+" pernoite(s) hipotético(s) · "+
                       ("Em estudo" if group["status"]=="estudo" else "Planejado, não reservado"))
            st.caption("Cidade-base de referência: "+group["base_city"].capitalize())
            if {"brussels","bruges_be"}.issubset(set(group["destinations"])):
                st.caption("Trecho ferroviário interno Bruxelas ↔ Bruges: média histórica de "
                           "1h04 segundo a SNCB. Isso NÃO confirma o roteiro completo "
                           "desde a cidade-base, nem o retorno em 2027.")
                st.markdown("[Ver horários na SNCB](https://www.belgiantrain.be/en/travel-info/origin-destination/brussels-bruges)")
            st.caption("Roteiro completo de ida, ligações entre destinos, retorno, hotel e custos: a confirmar.")
            if group["notes"]:st.write(group["notes"])
            with st.expander("Editar viagem · "+group["name"]):
                with st.form("ux48_edit_"+group["id"]):
                    name=st.text_input("Nome",value=group["name"])
                    existing=[x for x in group["destinations"] if x in byid]
                    options=existing+[id for id in byid
                                      if id not in existing and all(
                                      id not in other["destinations"]
                                      for other in groups["groups"] if other["id"]!=group["id"])]
                    selected=st.multiselect("Destinos (ordem de seleção)",options,
                         default=existing,format_func=lambda x:byid[x]["name"])
                    st.caption("Para reordenar, remova e selecione novamente os destinos na ordem desejada.")
                    period=st.selectbox("Período",PERIODS,
                        index=PERIODS.index(group["period"]))
                    dates=[r["start"] for r in available_weekends(groups,plan,catalog)
                           if r["status"]=="livre · não reservado"]
                    choice=[None]+([group["start_date"]] if group["start_date"] else [])+[
                        d for d in dates if d!=group["start_date"]]
                    start=st.selectbox("Sábado (opcional)",choice,
                        index=1 if group["start_date"] else 0,
                        format_func=lambda d:"Data ainda indefinida" if d is None else d)
                    nights=st.number_input("Noites possíveis",0,3,group["nights"])
                    notes=st.text_area("Observações",value=group["notes"],max_chars=700)
                    status=st.selectbox("Status",["estudo","planejado"],
                        index=0 if group["status"]=="estudo" else 1)
                    submitted=st.form_submit_button("Guardar alterações",disabled=not selected)
                    if submitted:
                        try:
                            _save(update_group(groups,plan,catalog,group["id"],
                                name=name,destinations=selected,period=period,
                                start_date=start,nights=int(nights),notes=notes,
                                status=status))
                            st.rerun()
                        except (ValueError,TypeError) as exc:
                            st.error(str(exc))
                if st.checkbox("Quero excluir este agrupamento, mantendo os passeios",
                               key="ux48_delete_ack_"+group["id"]):
                    if st.button("Excluir somente agrupamento",
                                 key="ux48_delete_"+group["id"]):
                        _save(remove_group(groups,plan,catalog,group["id"]))
                        st.rerun()
    st.markdown("#### Passeios ainda não organizados")
    free=ungrouped_outings(groups,plan,catalog)
    st.caption(" · ".join(r["name"] for r in free)
               if free else "Todos os passeios escolhidos estão associados a viagens.")
    st.markdown("#### Fins de semana da temporada")
    st.caption("Apenas sábados e domingos dentro da temporada em estudo. "
               "Livres não significam disponíveis para reserva ou obrigatórios para viajar.")
    slots=available_weekends(groups,plan,catalog)
    st.dataframe([{"Sábado":r["start"],"Domingo":r["end"],
                   "Situação":r["status"],"Viagem":r["group"] or "—"}
                  for r in slots],hide_index=True,width="stretch")
    rest_options=[r["start"] for r in slots if r["status"] in (
                  "livre · não reservado","descanso escolhido")]
    if rest_options:
        mark=st.selectbox("Reservar um fim de semana para descanso",
            rest_options,key="ux48_rest_choice")
        if st.button("Alternar descanso / livre",key="ux48_rest_toggle"):
            _save(set_rest_weekend(groups,plan,catalog,mark,
                  mark not in groups["rest_weekends"]))
            st.rerun()
    st.divider()
    st.caption("**Persistência:** esses agrupamentos são rascunhos da sessão, "
               "não são gravados no TripPlan nem automaticamente na nuvem. "
               "Exporte/importa o arquivo para recuperar entre sessões.")
    st.download_button("Exportar rascunho de fins de semana",
        data=export_groups(groups,plan,catalog),
        file_name="nossa-europa-fins-de-semana.json",
        mime="application/json",key="ux48_export_weekends")
    uploaded=st.file_uploader("Importar rascunho anterior (mesmo planejamento)",
        type=["json"],key="ux48_import_weekends")
    if uploaded and st.button("Validar e importar rascunho",key="ux48_confirm_import"):
        try:
            _save(import_groups(uploaded.getvalue().decode("utf-8"),plan,catalog))
            st.rerun()
        except (UnicodeDecodeError,ValueError,TypeError) as exc:
            st.error("Rascunho não importado: "+str(exc))
