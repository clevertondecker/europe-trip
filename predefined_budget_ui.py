"""Adoption UX for already generated concrete per-profile budget itineraries."""
from __future__ import annotations

import streamlit as st

from predefined_budget_model import preset_budget_summary
from recommended_itineraries import approve_profile_scenario
from planning_session import accept_approved_plan
from destination_labels import destination_names


def _money(value:float)->str:
    return "R$ "+f"{value:,.0f}".replace(",", ".")


def _confirm_preset(plan:dict,option:dict)->None:
    """Runs before widgets instantiate, so navigation is safe."""
    try:
        next_plan=approve_profile_scenario(plan,option,approved=True)
        accept_approved_plan(next_plan)
        st.session_state["budget_preset_review"]=False
        st.session_state.pop("budget_preset_review_profile",None)
        st.session_state["budget_preset_applied"]=option["label"]
        st.session_state["itinerary_section"]="Meus passeios"
    except ValueError as exc:
        st.session_state["budget_preset_error"]=str(exc)


def render_predefined_budget_adoption(plan:dict,scenarios:list[dict],catalog:dict,
                                      eurfx:float,chffx:float)->None:
    """Let an owner deliberately replace an empty proposal with a chosen preset.

    Existing official outings are always retained, and no proposal is persisted
    to GitHub without the existing owner save flow.
    """
    names=destination_names(catalog)
    attractions={a["id"]:a["name"] for a in catalog["attractions"]}
    options={s["profile"]:s for s in scenarios}
    st.markdown("### Adotar um roteiro pré-definido")
    st.caption("Os três perfis **já incluem destinos e atrações sugeridos**. "
               "Eles são calculados usando a cidade-base e o teto que você escolheu. "
               "Nenhum passeio entra em Meus passeios antes da sua confirmação.")
    chosen=st.selectbox(
        "Qual roteiro você quer usar?",
        ["economy","balanced","experience"],
        format_func=lambda p:options[p]["label"],
        key="budget_preset_profile",
    )
    selected=options[chosen]
    summary=preset_budget_summary(selected,plan,eurfx,chffx)
    with st.container(border=True):
        st.markdown("**Roteiro "+summary["label"]+" — "+
                    str(len(summary["packages"]))+" destinos**")
        if not summary["packages"]:
            st.warning("Nenhum passeio disponível com os critérios atuais.")
        else:
            for dest,ids in summary["packages"].items():
                already=dest in plan["packages"]
                st.markdown(("✓ " if already else "＋ ")+"**"+
                            names.get(dest,dest)+"**"+(
                                " · Já está em Meus passeios" if already
                                else " · Novo passeio sugerido"))
                st.caption("Atrações: "+(", ".join(attractions.get(a,a) for a in ids)
                                       if ids else "Nenhuma selecionada"))
        a,b,c=st.columns(3)
        a.metric("Verba para passeios",_money(summary["allowance_brl"]))
        b.metric("Gastos históricos conhecidos",_money(summary["known_brl"]))
        c.metric("Saldo nominal da provisão",_money(summary["remaining_known_allowance_brl"]))
        st.caption("Projeção total do casal: "+_money(summary["global_total_brl"])+
                   " · Margem até o teto: "+_money(summary["margin_brl"])+".")
        if summary["missing"]:
            st.warning(f"{len(summary['missing'])} componente(s) ainda sem preço completo. "
                       "O saldo nominal não é dinheiro realmente livre.")
        if summary["unresolved"]:
            st.caption(f"{len(summary['unresolved'])} passeio(s) sem data segura no calendário.")
        st.caption("São tarifas e referências históricas, nunca preço completo "
                   "garantido para 2027. Os gastos conhecidos não são somados "
                   "novamente à provisão.")

    error=st.session_state.pop("budget_preset_error",None)
    if error:
        st.error("Roteiro desatualizado ou inválido: "+error)
    review_key="budget_preset_review"
    pending_key="budget_preset_review_profile"
    if st.button("Revisar e adotar roteiro "+summary["label"],
                 key="budget_preset_review_button",type="primary",
                 disabled=not bool(summary["new"]),width="stretch"):
        st.session_state[review_key]=True
        st.session_state[pending_key]=chosen
    if st.session_state.get(review_key) and st.session_state.get(pending_key)==chosen:
        st.markdown("#### Confirmação — o que será adicionado?")
        st.caption("Os passeios que você já escolheu serão mantidos.")
        for dest in summary["new"]:
            st.write("• "+names.get(dest,dest)+": "+
                     ", ".join(attractions.get(a,a) for a in summary["packages"][dest]))
        new_dates={day:dest for day,dest in summary["assignments"].items()
                   if plan["assignments"].get(day)!=dest}
        if new_dates:
            st.markdown("**Datas provisórias sugeridas:**")
            for day,dest in sorted(new_dates.items()):
                st.write("• "+day+" — "+names.get(dest,dest))
        st.warning("A aprovação altera o planejamento da sessão. "
                   "Não compra ingressos nem salva automaticamente online.")
        yes,no=st.columns(2)
        with yes:
            st.button("Confirmar e incluir nos Meus passeios",
                      key="budget_preset_confirm",width="stretch",
                      on_click=_confirm_preset,args=(plan,selected))
        with no:
            if st.button("Cancelar",key="budget_preset_cancel",width="stretch"):
                st.session_state[review_key]=False
                st.session_state.pop(pending_key,None)
                st.rerun()
    st.caption("Você também pode adicionar cada destino individualmente em Simular roteiros.")
