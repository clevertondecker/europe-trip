"""The visible active-profile itinerary and approval controls for Meus passeios."""
from __future__ import annotations

import streamlit as st

from predefined_budget_ui import _confirm_preset
from active_preset import preset_destination_names
from outing_guide_model import build_outing_guide
from outing_guide_ui import render_outing_guide
from destination_labels import destination_names


def money(value:float)->str:
    return "R$ "+f"{value:,.0f}".replace(",",".")


def render_active_preset(plan:dict,preset:dict,catalog:dict,*,routes:dict|None=None,
                         eurfx:float=6.3,chffx:float=7.1)->None:
    option,summary=preset["option"],preset["summary"]
    names=destination_names(catalog)
    attractions={a["id"]:a["name"] for a in catalog["attractions"]}
    st.markdown("### Roteiro pré-definido · "+summary["label"])
    st.caption("Sugestão calculada para sua base **"+names.get(plan["base_city"],plan["base_city"])+
               "** e perfil atual. Este roteiro **já tem destinos e atrações**; "
               "ainda não foi adicionado ao planejamento confirmado.")
    with st.container(border=True):
        if not summary["packages"]:
            st.warning("O perfil não gerou passeios com os filtros atuais.")
        for destination,ids in summary["packages"].items():
            official=destination in plan["packages"]
            st.markdown(("✓ " if official else "＋ ")+"**"+
                        names.get(destination,destination)+"**"+
                        (" · Já confirmado" if official else " · Pré-selecionado"))
            st.caption("Atrações: "+(", ".join(attractions.get(a,a) for a in ids)
                                   if ids else "A definir"))
            if routes is not None and ids:
                guide=build_outing_guide(plan,catalog,routes,destination,ids)
                minutes=guide["train_minutes_one_way"]
                st.caption("Saída: "+guide["base_name"]+" · "+
                           (str(minutes)+" min de trem (trecho)" if minutes is not None
                            else "Passeio local" if guide["local"]
                            else "Tempo ferroviário pendente")+
                           " · subtotal histórico do casal: "+
                           f"€ {guide['known_cost']['EUR']:.2f} · CHF {guide['known_cost']['CHF']:.2f}")
                if st.checkbox("Ver guia de "+names.get(destination,destination),
                               key="preset_guide_open_"+destination):
                    render_outing_guide(guide,key_prefix="preset_guide_"+destination,
                                        eurfx=eurfx,chffx=chffx)
        a,b,c=st.columns(3)
        a.metric("Verba prevista",money(summary["allowance_brl"]))
        b.metric("Custos históricos do roteiro",money(summary["known_brl"]))
        c.metric("Projeção do casal",money(summary["global_total_brl"]))
        st.caption("Margem até o teto: "+money(summary["margin_brl"])+
                   " · saldo nominal da verba: "+money(summary["remaining_known_allowance_brl"])+".")
        if summary["missing"]:
            st.warning(str(len(summary["missing"]))+" despesa(s) ainda sem preço completo; "
                       "o valor não garante cobertura integral dos passeios.")
        if summary["unresolved"]:
            st.caption(str(len(summary["unresolved"]))+
                       " passeio(s) sem data segura. Nenhum horário de 2027 está reservado.")
        st.caption("Valores históricos de 2026. Os gastos conhecidos não são "
                   "somados novamente à provisão já existente.")

    signature=(plan["plan_id"],plan["revision"],plan["profile"],plan["base_city"])
    if st.session_state.get("active_preset_review_signature")!=signature:
        st.session_state["active_preset_review_open"]=False
    if not summary["new"]:
        st.success("Todos os passeios deste perfil já estão em Meus passeios.")
        return
    if st.button("Usar este roteiro em Meus passeios",key="active_preset_start",
                 type="primary",width="stretch"):
        st.session_state["active_preset_review_open"]=True
        st.session_state["active_preset_review_signature"]=signature
    if st.session_state.get("active_preset_review_open"):
        st.markdown("#### Confirme os passeios que serão adicionados")
        st.caption("Suas escolhas existentes serão mantidas. Não há reservas automáticas.")
        for destination in summary["new"]:
            st.write("• "+names.get(destination,destination)+": "+
                     ", ".join(attractions.get(a,a) for a in summary["packages"][destination]))
        proposed_dates={day:dest for day,dest in summary["assignments"].items()
                        if plan["assignments"].get(day)!=dest}
        if proposed_dates:
            st.markdown("**Datas sugeridas, ainda não confirmadas:**")
            for day,destination in sorted(proposed_dates.items()):
                st.write("• "+day+" — "+names.get(destination,destination))
        col1,col2=st.columns(2)
        with col1:
            st.button("Confirmar e usar roteiro",key="active_preset_confirm",
                      on_click=_confirm_preset,args=(plan,option),width="stretch")
        with col2:
            if st.button("Cancelar",key="active_preset_cancel",width="stretch"):
                st.session_state["active_preset_review_open"]=False
                st.rerun()
    error=st.session_state.pop("budget_preset_error",None)
    if error:
        st.error("Não foi possível adotar: "+error)


def render_active_preset_summary(preset:dict,catalog:dict,context:str)->None:
    summary=preset["summary"]
    places=preset_destination_names(summary,catalog)
    st.info("**Roteiro "+summary["label"]+" sugerido:** "+
            str(len(places))+" destinos · "+(", ".join(places) if places else "nenhum")+
            ". "+str(len(summary["new"]))+
            " ainda não confirmado(s). É uma proposta, não seu roteiro salvo.")
    if context=="calendar":
        names=destination_names(catalog)
        if summary["assignments"]:
            with st.expander("Ver datas sugeridas deste perfil"):
                for day,destination in sorted(summary["assignments"].items()):
                    st.write(day+" · "+names.get(destination,destination))
                st.caption("Datas hipotéticas, não incluídas no seu calendário oficial.")
    if summary["missing"]:
        st.caption(str(len(summary["missing"]))+
                   " despesas sem cotação completa nesta proposta.")
