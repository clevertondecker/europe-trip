"""Jira-like destination cards, edit actions and reactive scenario comparison.

All draft edits reside in Streamlit session state; only a confirmed review
changes the canonical itinerary.
"""
from __future__ import annotations
from copy import deepcopy
import streamlit as st
from scenario_editor_model import (new_board,is_stale,change_board,undo_board,
                                  reprice_board,board_to_approval)
from recommended_itineraries import approve_profile_scenario
from planning_session import accept_approved_plan, select_package
from scenario_comparison_model import approval_diff
from scenario_comparison_ui import (render_scenario_comparison,render_financial_breakdown,
                                    render_approval_diff)
from finance_margin_metrics import calculate_excursion_margin
from finance_margin_ui import render_finance_margin_summary
from outing_cost_evidence import load_outing_evidence,evidence_for_outing
from draft_controls_ui import render_draft_controls
from predefined_budget_ui import render_predefined_budget_adoption
from outing_guide_model import build_outing_guide
from outing_guide_ui import render_outing_guide
from research_cost_ui import render_research_profiles

def _currency(eur:float,chf:float)->str:
    return f"€ {eur:,.2f}  ·  CHF {chf:,.2f}"

def _photo(dest:dict):
    photo=dest.get("photo")
    if photo and photo.get("url"):
        st.image(photo["url"],use_container_width=True)
        st.caption(f"Foto: {photo['author']} · {photo['license']}")
    else:
        st.caption("Sem fotografia licenciada disponível")

def _update(profile:str,board:dict):
    st.session_state["scenario_edit_"+profile]=board
    # A previously opened confirmation is invalid after any edit.
    st.session_state["scenario_review_"+profile]=False
    st.rerun()

def _navigate_to_my_outings():
    st.session_state["itinerary_section"]="Meus passeios"


def _render_destination(profile:str,board:dict,row:dict,catalog:dict,plan:dict,
                        routes:dict,eurfx:float,chffx:float):
    dest=row["destination"]
    key=dest["id"]
    title=dest["name"]+" · "+dest["country"]
    with st.container(border=True):
        photo_col,details=st.columns([1,2],gap="small")
        with photo_col:_photo(dest)
        with details:
            st.markdown("#### "+title)
            st.caption("Incluído no plano atual · não removível nesta simulação" if row["locked"]
                       else "Incluído nesta proposta · editável")
            st.caption(f"{len(row['attractions'])} atrações · "+
                       ("Aprovado no roteiro" if row["locked"] else "Rascunho editável"))
            if row["attractions"]:
                st.write(" · ".join(a["name"] for a in row["attractions"][:2])+
                         (" · ..." if len(row["attractions"])>2 else ""))
            minutes=row["route"]["train_minutes_one_way"]
            st.caption(("Trem de ida: "+str(minutes)+" minutos (estação a estação), volta a conferir"
                        if minutes is not None else "Tempo ferroviário não confirmado"))
            st.caption("Custos conhecidos para duas pessoas: "+_currency(
                row["known"]["EUR"],row["known"]["CHF"]))
            if row["missing"]:
                st.caption(f"⚠ {len(row['missing'])} despesas ainda sem cotação completa")
        if row["locked"]:
            st.button("Ver em Meus passeios",key="scenario_go_official_"+profile+"_"+key,
                      on_click=_navigate_to_my_outings,width="stretch")
        else:
            if st.button("Adicionar aos meus passeios",key="scenario_add_official_"+profile+"_"+key,
                         width="stretch"):
                try:
                    select_package(key,[a["id"] for a in row["attractions"]])
                    st.session_state["scenario_new_official_notice"]=dest["name"]
                    st.rerun()
                except ValueError as exc:
                    st.error("Não foi possível adicionar: "+str(exc))
        if st.checkbox("Ver guia: viagem, principais pontos e custos",
                       key="scenario_guide_open_"+profile+"_"+key):
            guide=build_outing_guide(plan,catalog,routes,key,
                                     [a["id"] for a in row["attractions"]])
            render_outing_guide(guide,key_prefix="scenario_guide_"+profile+"_"+key,
                                eurfx=eurfx,chffx=chffx)
        with st.expander("Ver despesas, ingressos e fontes"):
            if row["components"]:
                for item in row["components"]:
                    symbol="€" if item["currency"]=="EUR" else "CHF "
                    st.write(f"• {item['name']}: {symbol}{item['value']:.2f} "
                             f"({item['condition']}, referência histórica)")
            else:
                st.write("Nenhuma tarifa ou entrada paga confirmada neste subtotal.")
            for missing in row["missing"]:st.caption("Pendente: "+str(missing))
            evidence=evidence_for_outing(
                key,[a["id"] for a in row["attractions"]],st.session_state.get("outing_evidence_data"))
            verified=[x for x in evidence["items"] if x.get("amount") is not None]
            if verified:
                st.caption("Informações oficiais ou históricas adicionais:")
                for item in verified:
                    st.caption("• "+item["category"].replace("_"," ")+": "+
                               f"{item['amount']} {item['currency']} — "+item["notes"])
                    if item.get("source_url"):
                        st.markdown("[Fonte oficial]("+item["source_url"]+")")
            if evidence["pending"]:
                st.caption("Outras despesas que ainda precisam de pesquisa:")
                for item in evidence["pending"]:
                    category={"local_transport":"Transporte urbano",
                              "dining":"Refeições durante o passeio",
                              "extra_hotel":"Hospedagem adicional",
                              "intercity_return":"Confirmação de volta",
                              "ticket":"Ingresso","other":"Outros custos"}.get(item["category"],item["category"])
                    st.caption("• "+category+": não cotado para 2027")
            for conditional in row["conditional"]:st.caption("Condição: "+str(conditional))
            st.caption("Alimentação, transporte urbano e hospedagem extra: somente "
                       "quando houver valor específico pesquisado; não assumir zero.")
            st.markdown("[Fonte turística]("+dest["source_url"]+")")
            st.markdown("[Fonte do transporte]("+row["route"]["source_url"]+")")
        with st.expander("Editar atrações deste passeio",expanded=False):
            options=[a for a in catalog["attractions"] if a["destination_id"]==key]
            labels={a["id"]:a["name"] for a in options}
            picked=st.multiselect("Atrações incluídas",options=list(labels),
                                  default=[a["id"] for a in row["attractions"]],
                                  format_func=lambda x:labels[x],
                                  key="scenario_attractions_"+profile+"_"+key,
                                  disabled=row["locked"])
            if st.button("Atualizar atrações",key="scenario_update_"+profile+"_"+key,
                         disabled=row["locked"] or len(picked)>5,):
                try:_update(profile,change_board(board,catalog,key,picked))
                except ValueError as exc:st.warning(str(exc))
            if not row["locked"]:
                if st.button("Remover passeio",key="scenario_remove_"+profile+"_"+key):
                    _update(profile,change_board(board,catalog,key,[]))

def render_scenario_boards(plan:dict,scenarios:list[dict],catalog:dict,routes:dict,
                           trip_data:dict,source_live:bool,eurfx:float,chffx:float,
                           use_city_rent:bool=True,finance_only:bool=False)->None:
    profiles={s["profile"]:s for s in scenarios}
    if finance_only:
        st.markdown("### Orçamento por estilo")
        st.info("Cada estilo abaixo contém um **roteiro pré-selecionado** de passeios e atrações. "
                "Os números são provisões e custos históricos, não preços finais de 2027.")
        render_scenario_comparison(plan,scenarios,catalog,eurfx,chffx)
        render_research_profiles(plan,scenarios,catalog,routes,eurfx,chffx)
        render_predefined_budget_adoption(plan,scenarios,catalog,eurfx,chffx,routes=routes)
        return
    notice=st.session_state.pop("scenario_new_official_notice",None)
    if notice:
        st.success(notice+" foi adicionado ao seu roteiro. Veja em Meus passeios.")
    render_scenario_comparison(plan,scenarios,catalog,eurfx,chffx)
    render_research_profiles(plan,scenarios,catalog,routes,eurfx,chffx)
    st.markdown("### Personalize uma proposta")
    st.caption("As edições aqui são rascunhos. Seu roteiro atual só muda ao "
               "adicionar um passeio individual ou aprovar uma proposta.")
    profile=st.segmented_control("Estilo para personalizar",list(profiles),
         default=plan["profile"],format_func=lambda p:profiles[p]["label"],
         key="scenario_board_profile")
    profile=profile or plan["profile"]
    scenario=profiles[profile]
    state_key="scenario_edit_"+profile
    if state_key not in st.session_state:
        st.session_state[state_key]=new_board(plan,scenario)
    board=st.session_state[state_key]
    if is_stale(board,plan):
        st.warning("O planejamento oficial mudou. Atualize esta proposta "
                   "antes de continuar editando ou aplicá-la.")
        if st.button("Recriar proposta com o planejamento atual",
                     key="scenario_reset_stale_"+profile):
            _update(profile,new_board(plan,scenario))
        return
    # Loading supplemental evidence does not alter the official plan or prices.
    st.session_state["outing_evidence_data"]=load_outing_evidence(catalog=catalog)
    restored=render_draft_controls(board,plan,catalog,profile=profile)
    if restored is not None:
        _update(profile,restored)
    sim=reprice_board(board,plan,catalog,routes,trip_data,source_live,
                      eurfx,chffx,use_city_rent)
    totals=sim["finance"]["result"]
    details=sim["detail"]
    a,b,c,d=st.columns(4)
    a.metric("Destinos",len(board["packages"]))
    b.metric("Atrações",sim["attractions_count"])
    c.metric("Custos conhecidos",_currency(
        details["total"]["known_by_currency"]["EUR"],
        details["total"]["known_by_currency"]["CHF"]))
    d.metric("Margem até o teto",f"R$ {totals['margin']:,.0f}")
    allowance=sim["finance"]["budget_excursions_allowance_brl"]
    exceeded=sim["finance"]["known_excursions_overage_brl"]
    render_financial_breakdown(sim,eurfx,chffx)
    supplemental_pending=[
        item["category"]+" · "+row["destination"]["name"]
        for row in details["rows"]
        for item in evidence_for_outing(
            row["destination_id"],[a["id"] for a in row["attractions"]],
            st.session_state["outing_evidence_data"])["pending"]]
    margin_metrics=calculate_excursion_margin(
        sim["finance"],details["total"]["known_by_currency"],eurfx,chffx,
        details["total"]["missing"]+supplemental_pending)
    render_finance_margin_summary(margin_metrics,profile=profiles[profile]["label"])
    if details["total"]["missing"]:
        st.warning(f"{len(details['total']['missing'])} componentes ainda sem preço completo. "
                   "Não interpretar o subtotal como custo total.")
    with st.expander("Despesas por categoria — o que está incluído?"):
        expenses={"Trens intermunicipais":{"EUR":0.0,"CHF":0.0},
                  "Ingressos e atrações":{"EUR":0.0,"CHF":0.0}}
        for row in details["rows"]:
            for part in row["components"]:
                category=("Trens intermunicipais" if part["name"].startswith("Transporte ")
                          else "Ingressos e atrações")
                expenses[category][part["currency"]]+=float(part["value"])
        for category,amount in expenses.items():
            st.write("**"+category+":** "+_currency(amount["EUR"],amount["CHF"]))
        st.caption("Transporte urbano, refeições e pernoites extras: não cotados "
                   "individualmente. Valores desconhecidos não são tratados como gratuitos.")
        st.caption("Parte das excursões já está contemplada na verba-base de R$ "+
                   f"{allowance:,.0f}; só o excedente conhecido altera a projeção geral.")
    st.markdown("#### Passeios nesta proposta")
    st.caption("Os passeios atuais são preservados. Sugestões podem ser adicionadas "
               "individualmente sem aplicar todo o cenário.")
    shown_key="workspace_board_visible_"+profile
    visible=st.session_state.get(shown_key,6)
    total_rows=len(details["rows"])
    st.caption(f"{total_rows} destinos · exibindo {min(total_rows,visible)}")
    for row in details["rows"][:visible]:
        _render_destination(profile,board,row,catalog,plan,routes,eurfx,chffx)
    if total_rows>visible and st.button("Ver mais passeios",key="workspace_board_more_"+profile):
        st.session_state[shown_key]=visible+6
        st.rerun()
    remaining=[d for d in catalog["destinations"]
               if d["id"] not in board["packages"]
               and d["id"] not in plan.get("excluded_destinations",[])]
    with st.expander("Adicionar outro passeio",expanded=False):
        if remaining:
            lookup={d["id"]:d for d in remaining}
            chosen=st.selectbox("Destino",list(lookup),key="scenario_add_destination_"+profile,
                                format_func=lambda id:lookup[id]["name"]+" · "+lookup[id]["country"])
            dest=lookup[chosen]
            _photo(dest)
            available=[a for a in catalog["attractions"] if a["destination_id"]==chosen
                       and plan.get("preferences",{}).get(a["id"])!="Descartar"]
            labels={a["id"]:a["name"] for a in available}
            defaults=list(labels)[:2]
            selected=st.multiselect("Atrações deste destino",list(labels),
                                    default=defaults,key="scenario_add_attractions_"+profile+"_"+chosen,
                                    format_func=lambda key:labels[key])
            st.caption("Até cinco atrações por visita; passagens contabilizadas apenas uma vez.")
            if st.button("Adicionar ao cenário",key="scenario_add_confirm_"+profile,
                         disabled=not selected or len(selected)>5):
                try:_update(profile,change_board(board,catalog,chosen,selected))
                except ValueError as exc:st.warning(str(exc))
        else:
            st.info("Todas as opções permitidas já estão incluídas no cenário.")
    b1,b2=st.columns(2)
    with b1:
        if st.button("Desfazer última edição",key="scenario_undo_"+profile,
                     disabled=not board["undo"],use_container_width=True):
            _update(profile,undo_board(board))
    with b2:
        if st.button("Restaurar sugestão original",key="scenario_reset_"+profile,
                     use_container_width=True):
            _update(profile,new_board(plan,scenario))
    st.markdown("#### O que mudou nesta simulação?")
    changed=sim["known_delta"]
    st.write("Diferença no subtotal de passagens e ingressos conhecidos: "+
             _currency(changed["EUR"],changed["CHF"])+
             f" · aproximadamente R$ {sim['known_delta_brl']:,.0f} no câmbio escolhido.")
    if sim["known_delta_brl"]<0:
        st.caption("A redução no subtotal histórico não é economia garantida no orçamento geral.")
    if sim["unresolved"]:
        st.caption(f"{len(sim['unresolved'])} destino(s) ainda sem data segura no calendário.")
    with st.expander("Comparar composição original e personalizada"):
        original=board["original_packages"]
        for dest in sorted(set(original)|set(board["packages"])):
            current=board["packages"].get(dest,[])
            previous=original.get(dest,[])
            if previous!=current:
                st.write(f"• {dest}: {len(previous)} atração(ões) → {len(current)}")
        if original==board["packages"]:
            st.info("Nenhuma edição nesta simulação.")
    st.caption("Para editar ou remover passeios atuais, use Meus passeios.")
    names={d["id"]:d["name"] for d in catalog["destinations"]}
    diff=approval_diff(plan,board,sim,eurfx,chffx,catalog,routes)
    render_approval_diff(diff,names)
    approval_key="scenario_review_"+profile
    if st.button("Revisar e aplicar este roteiro",key="scenario_review_button_"+profile,
                 use_container_width=True):
        st.session_state[approval_key]=True
    if st.session_state.get(approval_key):
        st.warning("Revise destinos, atrações e datas. Nenhuma reserva será realizada.")
        if diff["new"]:
            st.markdown("**Novos passeios e atrações:**")
            attraction_names={a["id"]:a["name"] for a in catalog["attractions"]}
            for destination in diff["new"]:
                st.write("• "+names.get(destination,destination)+": "+
                         ", ".join(attraction_names.get(a,a)
                                   for a in board["packages"][destination]))
        else:
            st.caption("Nenhum destino novo.")
        dates={day:dest for day,dest in sim["calendar"].items()
               if plan["assignments"].get(day)!=dest}
        if dates:
            st.markdown("**Novas datas propostas:**")
            for day,dest in sorted(dates.items()):
                st.write("• "+day+" · "+names.get(dest,dest))
        else:
            st.caption("Nenhuma nova data atribuída.")
        yes,no=st.columns(2)
        with yes:
            if st.button("Confirmar aplicação",key="scenario_approve_"+profile,
                         use_container_width=True):
                try:
                    candidate=board_to_approval(board,plan,sim)
                    updated=approve_profile_scenario(plan,candidate,approved=True)
                    accept_approved_plan(updated)
                    for key in list(st.session_state):
                        if key.startswith("scenario_edit_") or key.startswith("scenario_review_"):
                            del st.session_state[key]
                    st.rerun()
                except ValueError as exc:st.error(str(exc))
        with no:
            if st.button("Cancelar",key="scenario_cancel_"+profile,
                         use_container_width=True):
                st.session_state[approval_key]=False
                st.rerun()
