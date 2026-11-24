"""UX121 read-only overview of the existing planning projection."""
from datetime import date
import streamlit as st
from itinerary_flow_model import ITALY_STAGE, FRANCE_STAGE
from ux_planning_journey_presentation import header_html


def _date(value):
    return date.fromisoformat(value).strftime("%d/%m/%Y")


def _italy_proposal():
    from ux_navigation import set_from_legacy
    set_from_legacy(st.session_state,"Roteiro","Itália")


def render_overview(plan,catalog,view,storage_label,storage_hint,trip_data,finance_live,eurfx,chffx):
    from ux_planning_journey_ui import request_planning,_discover,_choose,_workspace_base
    from ux64_navigation_model import select_public_task
    from itinerary_flow_ui import _compact_budget
    from data_model import get_scenario,money_brl
    state=st.session_state
    counts=view["counts"]
    base=_workspace_base(plan)
    st.markdown(header_html(storage_label,storage_hint,saved=view["private_saved"],
                            title="Nossa viagem",
                            tag="Partida proposta "+_date(plan["departure_date"])+" · "+str(plan["total_days"])+" dias"),
                unsafe_allow_html=True)
    st.caption("Roteiro oficial · Base europeia: "+base+" · Nenhuma reserva inferida")
    a,b,c=st.columns(3,gap="small")
    a.metric("Incluídos",counts["planned"])
    b.metric("Organizados",counts["organized"])
    c.metric("A organizar",len(view["pending"]))
    st.caption(f'{counts["wished"]} destinos desejados · {view["eligible_count"]} compatíveis fora do roteiro · '
               f'{len(view["unsupported"])} somente pesquisa · '
               f'{counts["dated"]} destinos com data individual')
    action=view["next"]
    stage=view["next_stage"]
    with st.container(border=True,key="ux121_next"):
        st.markdown("#### Próximo passo")
        if action=="build":
            st.write(f'{view["eligible_count"]} destinos da sua lista podem entrar no roteiro.')
            label="Incluir destinos da minha lista"
        elif action=="organize":
            st.write(f'{len(view["pending"])} destinos ainda sem período ou data. Organizar é opcional; você pode salvar agora.')
            label="Organizar visitas pendentes"
        elif action=="review":
            st.write("Os destinos incluídos têm período ou data, individual ou em viagem agrupada. Consulte seu roteiro quando quiser.")
            label="Consultar meus destinos"
        elif action=="exploratory":
            st.write("Seus desejos permanecem na lista; ainda não possuem passeios compatíveis.")
            label="Revisar minha lista"
        else:
            st.write("Escolha os lugares que deseja conhecer para começar.")
            label="Escolher destinos"
        st.button(label,key="flow_journey_primary",type="primary",
                  on_click=_discover if action=="choose" else _choose if action=="exploratory" else request_planning,
                  args=() if action in ("choose","exploratory") else (state,action,stage))
    st.markdown("#### Etapas da viagem")
    for col,stage in zip(st.columns(2,gap="small"),(ITALY_STAGE,FRANCE_STAGE)):
        stage_info=view["stages"][stage]
        with col:
            with st.container(border=True,key="ux121_stage_"+stage):
                st.markdown("**"+("01 · Lua de mel na Itália" if stage==ITALY_STAGE else "02 · Temporada europeia")+"**")
                st.markdown("### "+str(stage_info["days"])+" dias")
                if stage==FRANCE_STAGE:
                    st.caption("Base oficial: "+base)
                    st.caption(f'{stage_info["groups"]} viagens agrupadas')
                elif plan.get("italy_proposal"):
                    st.caption("Proposta italiana adotada no roteiro.")
                else:
                    st.caption("Proposta italiana ainda não adotada.")
                st.write(f'{stage_info["planned"]} incluídos · {stage_info["organized"]} organizados · {stage_info["pending"]} a organizar')
                if stage_info["eligible"]:
                    st.button("Incluir destinos",key="ux121_include_"+stage,on_click=request_planning,args=(state,"build",stage),width="stretch")
                elif stage_info["pending"]:
                    st.button("Organizar visitas",key="ux121_organize_"+stage,on_click=request_planning,args=(state,"organize",stage),width="stretch")
                elif stage_info["planned"]:
                    st.button("Ver destinos",key="ux121_destinations_"+stage,on_click=request_planning,args=(state,"review",stage),width="stretch")
                elif stage==ITALY_STAGE:
                    st.button("Revisar proposta italiana",key="ux121_italy_proposal",on_click=_italy_proposal,width="stretch")
                else:
                    st.button("Explorar destinos",key="ux121_europe_discover",on_click=_discover,width="stretch")
    with st.container(border=True,key="ux121_commitments"):
        st.markdown("#### Próximos compromissos planejados")
        commitments=view["commitments"]
        if not commitments:
            st.caption("Nenhuma data individual ou viagem com período definido. Não é necessário agendar agora.")
        for entry in commitments[:4]:
            label="Viagem agrupada" if entry["kind"]=="group" else "Visita individual"
            if entry["start"]:
                timing=_date(entry["start"])
                if entry["end"]!=entry["start"]:
                    timing+=" a "+_date(entry["end"])
            else:
                timing=entry["period"]+" · data a definir"
            st.write(f'{entry["name"]} · {timing}')
            st.caption(label+" · não reservado")
        if len(commitments)>4:
            st.caption(f'Mais {len(commitments)-4} compromissos em Organizar.')
        st.button("Abrir organização",key="ux121_open_organize",on_click=request_planning,args=(state,"organize",next((s for s in (ITALY_STAGE,FRANCE_STAGE)
                        if view["stages"][s]["planned"]),None)))
    with st.container(border=True,key="ux121_budget"):
        st.markdown("#### Orçamento da viagem")
        try:
            scenario=get_scenario(trip_data,plan["budget_scenario"])
            st.write("Teto oficial: **"+money_brl(scenario["cap_brl"])+"**")
        except (ValueError,KeyError,TypeError,StopIteration):
            st.caption("Teto oficial: A verificar")
        if trip_data is not None:
            _compact_budget(plan,catalog,trip_data,finance_live,eurfx,chffx,show_link=False)
        else:
            st.caption("Estimativa total: A verificar")
        st.button("Abrir orçamento",key="flow_journey_budget",on_click=select_public_task,args=(state,"Orçamento","Visão financeira"))
    # Sidebar owns the existing primary save. The overview links to the full
    # canonical review for local recovery or saving, without a second writer.
    st.button("Consultar meus destinos",
              key="ux121_save_review",
              on_click=request_planning,args=(state,"review"))
