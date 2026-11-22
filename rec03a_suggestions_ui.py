"""REC03A: session-only recommendation UI; no decisions or persistence."""
from __future__ import annotations

import logging
import streamlit as st
from rail_reference_projection_model import format_minutes

_LOG = logging.getLogger(__name__)
from base_recommendation_model import recommend_bases
from base_research_expanded_model import load_research
from recommendation_scope_model import confirm_scope
from trip01_supplemental_discovery import build_exploration_discovery
from ux502_destination_interests_model import (
    empty_interests, ordered_interests, LABELS,
)
from rec03a_session import (SCOPE, DRAFT, ACTIVITY, ACTIVITIES, MANUAL, SUGGESTED,
                            request_navigation, reconcile_session_scope)
from ux503_destination_base_comparison_ui import render_wishlist_base_comparison
from ux_shared_ui_presentation import page_header, section_heading

_REASON = {
    "menor_minimo_ponderado_no_mesmo_escopo_completo": (
        "Entre alternativas com referências para os mesmos trajetos, "
        "esta tem tempos mínimos de ida menores. A viagem completa ainda precisa ser verificada."
    ),
    "fronteira_documental_do_escopo": (
        "Esta cidade reúne informações úteis de deslocamento, "
        "mas isso não significa que seja a melhor opção."
    ),
    "menor_minimo_ponderado_no_mesmo_subconjunto": (
        "Há tempos mínimos de ida menores nos trajetos pesquisados em comum. "
        "Os demais destinos não entram nessa comparação."
    ),
    "imperdiveis_identificados": (
        "Existem referências ou identificação local para todos os destinos imperdíveis."
    ),
    "imperdiveis_com_evidencia_pendente": (
        "Ainda faltam informações para alguns destinos imperdíveis."
    ),
    "acesso_local_a_verificar": "O acesso dentro da cidade ainda precisa de confirmação.",
    "alternativa_individual_sem_grupo_completo": (
        "Esta cidade tem dados úteis, mas falta uma comparação equivalente com outras bases."
    ),
    "comparacao_condicional_disponivel": (
        "Há referências para comparar alguns trajetos em comum, com ressalvas."
    ),
    "sem_tempo_ou_identificacao_local": (
        "Ainda não temos tempos de deslocamento ou acesso local pesquisados nesta cidade."
    ),
    "destinos_com_tempo_pendente": "Há destinos sem tempo de deslocamento pesquisado.",
}


def _go(target):
    request_navigation(st.session_state, target)


def _scope_select(ids, interests, discovery):
    if not ids:
        return
    st.session_state[SCOPE] = confirm_scope(interests, list(ids), discovery)
    st.session_state.pop(DRAFT, None)
    st.session_state.pop("rec03a_edit_scope", None)
    st.session_state.pop("rec03a_page", None)
    st.session_state.pop("rec03a_page_shadow", None)


def _draft_changed():
    st.session_state[DRAFT] = list(st.session_state["rec03a_scope_widget"])


def _draft_all(ids):
    st.session_state[DRAFT] = list(ids)
    st.session_state["rec03a_scope_widget"] = list(ids)


def _edit():
    st.session_state["rec03a_edit_scope"] = True
    scope = st.session_state.get(SCOPE) or {}
    st.session_state[DRAFT] = list(scope.get("destination_ids", []))


def _render_scope(interests, discovery, active, names, checked):
    state = st.session_state
    scope = checked["scope"]
    active_ids = [x["destination_id"] for x in active]
    priorities = {x["destination_id"]: LABELS[x["priority"]] for x in active}
    st.markdown(section_heading(
        "CONFIRME O ESCOPO", "Quais destinos vamos considerar?",
        "Escolha os lugares desta pesquisa, sem alterar a wishlist ou o roteiro.",
        variant="compact",
    ), unsafe_allow_html=True)
    st.caption("A temporada não é inferida pelo país: revise o conjunto antes de analisar.")
    st.caption("Esta seleção não altera sua lista nem o roteiro. A análise vale somente nesta sessão.")
    if scope and scope.get("pending_ids"):
        st.info("Novos interesses precisam de revisão: " + ", ".join(names[x] for x in scope["pending_ids"]))
    default = scope["destination_ids"] if scope else active_ids
    draft = state.get(DRAFT, default)
    if not isinstance(draft, list):
        draft = default
    draft = list(dict.fromkeys(x for x in draft if isinstance(x,str) and x in active_ids))
    state[DRAFT] = draft
    if state.get("rec03a_scope_widget") != draft:
        state["rec03a_scope_widget"] = draft
    st.multiselect("Destinos considerados", active_ids,
                   format_func=lambda x: names[x]+" · "+priorities[x],
                   key="rec03a_scope_widget", on_change=_draft_changed)
    st.caption(f"{len(draft)} de {len(active_ids)} destinos selecionados.")
    st.button("Analisar estes destinos", key="rec03a_confirm_subset", type="primary",
              disabled=not draft, on_click=_scope_select, args=(draft,interests,discovery))
    if scope and scope.get("confirmed"):
        st.button("Cancelar edição do escopo", key="rec03a_cancel_edit", on_click=_cancel_edit)


def _cancel_edit():
    st.session_state.pop("rec03a_edit_scope",None)
    st.session_state.pop(DRAFT,None)


def _label_ids(ids,names):
    return ", ".join(names.get(x,x) for x in ids) or "Nenhum"


def evidence_examples(candidate, destinations, limit=3):
    """Presentation only: priority, then canonical ID; never sort by speed."""
    priority = {"must_visit": 0, "interested": 1, "maybe": 2}
    ordered = sorted(destinations, key=lambda d: (priority[d["priority"]], d["id"]))
    return [(d["id"], candidate["evidence"][d["id"]]) for d in ordered
            if candidate["evidence"][d["id"]]["category"] in ("historical","reference_only","local")][:limit]


def _remember(widget, shadow):
    st.session_state[shadow] = st.session_state[widget]


def _restore_widget(widget, shadow, default, valid=None):
    state=st.session_state
    value=state.get(shadow,default)
    if valid is not None and not valid(value):
        value=default
    if state.get(widget)!=value:
        state[widget]=value
    state[shadow]=value
    return value


def _card(candidate, result, names, cities, official, options):
    """One card per city, with CHOICE as the only base-selection state."""
    from rec03b_handoff_ui import render_card_choice, render_card_actions

    base=candidate["base_id"]
    meta=cities[base]
    with st.container(border=True):
        st.markdown("**"+meta["name"]+"** · "+meta["country"]+
                    (" · Base oficial de referência" if base==official else ""))
        reasons=candidate["reasons"]
        st.write(_REASON.get(reasons[0],"Alternativa para investigação.") if reasons
                 else "Alternativa para investigar com os dados disponíveis.")
        st.caption(f'{candidate["historical_count"]} trajetos com dados históricos · '
                   f'{candidate["indicative_count"]} com referências indicativas')
        st.caption(f'{len(candidate["local_destination_ids"])} destinos com acesso local a verificar · '
                   f'{len(candidate["missing_destination_ids"])} sem tempo pesquisado')
        missing=candidate["must_visit"]["missing"]
        if missing:
            st.write("**O que falta pesquisar?** Tempos para os imperdíveis: "+
                     _label_ids(missing,names)+".")
        elif candidate["local_destination_ids"]:
            st.write("**O que falta pesquisar?** Acesso dentro da cidade e última milha.")
        else:
            st.write("**O que falta pesquisar?** Retorno, acesso às atrações e horários de 2027.")
        st.caption("Referências de ida pesquisadas; não são duração total nem preços confirmados.")
        render_card_choice(base,options)
        with st.expander("Conhecer, ver no mapa ou simular esta cidade"):
            render_card_actions(base,"card")
        if st.checkbox("Ver evidências e limitações",key="rec03a_details_"+base):
            coverage=candidate["weighted_coverage"]
            if coverage["value"] is not None:
                st.write(f'Cobertura documental ponderada: {coverage["value"]:.0%} '
                         f'({coverage["numerator"]}/{coverage["denominator"]} pesos de destinos não locais).')
            else:
                st.caption("Cobertura ferroviária não aplicável.")
            st.caption(candidate["coverage_limitation"])
            for reason in reasons[1:]:
                st.write(_REASON.get(reason,"Informação a investigar."))
            for destination,cell in candidate["evidence"].items():
                st.write(names.get(destination,destination)+" · "+
                         cell.get("label","Sem referência"))
                if cell.get("source_url"):
                    st.link_button("Fonte de "+names.get(destination,destination),
                                   cell["source_url"])
                raw=candidate["raw_rail_evidence"].get(destination,{})
                date=cell.get("gap_checked_at") or raw.get("source_date")
                if date:
                    st.caption("Data registrada: "+str(date))
                for observation in raw.get("observations",[]):
                    st.caption("Observação original: "+
                               str(observation.get("evidence_date") or "data não informada")+
                               " · "+format_minutes(observation.get("minimum_oneway_min")))
                    if observation.get("source_url"):
                        st.link_button("Fonte da observação",observation["source_url"])
            st.caption(candidate["limitation"])


def _render_comparison_groups(result,names,cities):
    # Display only groups involving contextual highlights by default; full
    # matrix remains in the existing manual activity, no duplicated ranking.
    highlights=set(result["highlight_ids"])
    groups=result["complete_groups"]
    conditional=result["conditional_comparisons"]
    if st.checkbox("Como as referências foram comparadas", key="rec03a_groups_open"):
        for group in groups:
            st.write("Escopo completo: "+_label_ids(group["destination_ids"],names))
            st.caption("Bases: "+", ".join(cities[b]["name"] for b in group["base_ids"]))
        relevant=[g for g in conditional if highlights.intersection(g["base_ids"])]
        if relevant:
            by_pair={tuple(g["base_ids"]):g for g in relevant}
            options=list(by_pair)
            def label(pair):
                return " × ".join(cities[b]["name"] for b in pair)
            _restore_widget("rec03a_group","rec03a_group_shadow",options[0],
                            lambda x:isinstance(x,tuple) and x in by_pair)
            selected=st.selectbox("Comparação condicional para consultar",options,
                                  format_func=label,key="rec03a_group",
                                  on_change=_remember,args=("rec03a_group","rec03a_group_shadow"))
            group=by_pair[selected]
            st.write("Trajetos comparados: "+_label_ids(group["destination_ids"],names))
            st.caption("Fora do conjunto comum: "+_label_ids(group["omitted_destination_ids"],names))
            for b in group["base_ids"]:
                st.markdown("**"+cities[b]["name"]+"**")
                st.caption("Tempo conhecido, fora da comparação: "+_label_ids(group["known_not_compared_by_base"][b],names))
                st.caption("Sem tempo pesquisado: "+_label_ids(group["missing_time_by_base"][b],names))
                st.caption("Local: "+_label_ids(group["local_destination_ids_by_base"][b],names))
        st.caption(result["limitation"])


def _featured_ids(result):
    """Up to four documented highlights, preserving REC02 section ordering."""
    sections=result["highlight_sections"]
    valid={c["base_id"] for c in result["candidates"]}
    seen=set()
    featured=[]
    for group in ("complete_reference_groups","conditional_all_must_identified",
                  "conditional_must_pending"):
        for base in sections.get(group,[]):
            if base in valid and base not in seen:
                seen.add(base)
                featured.append(base)
    return featured[:4]


def render_suggestions(*,plan,discovery=None,research=None):
    from rec03b_handoff_ui import render_card_selection_summary

    st.markdown(page_header(
        "Comparar cidades-base", "NOSSA EUROPA 2027 · EXPLORAR",
        "Encontre cidades para investigar a partir dos destinos que vocês escolheram.",
        tag="Pesquisa, não reserva",variant="compact",
    ),unsafe_allow_html=True)
    try:
        discovery=discovery if discovery is not None else build_exploration_discovery()
        interests=st.session_state.get("ux502_interests",empty_interests())
        active=[x for x in ordered_interests(interests,discovery)
                if x["priority"]!="discarded"]
        names={x["id"]:x["name"] for x in discovery["destinations"]}
        checked=reconcile_session_scope(st.session_state,interests,discovery)
        if checked["state"]=="no_destinations":
            st.info("Nenhum destino ativo. Adicione lugares ou revise as prioridades em Minha lista.")
            st.button("Abrir minha lista",key="rec03a_back_wishlist",
                      on_click=_go,args=("wishlist",))
            return
        if checked["state"]!="ready" or st.session_state.get("rec03a_edit_scope"):
            _render_scope(interests,discovery,active,names,checked)
            return
        research=research if research is not None else load_research(include_candidates=True)
        result=recommend_bases(interests,checked["scope"],
                               discovery=discovery,research=research)
        cities={x["id"]:x for x in research["cities"]}
    except ImportError:
        _LOG.exception("REC03A incompatible module version")
        st.error("A pesquisa está temporariamente indisponível. "
                 "Seus destinos e roteiro permanecem intactos.")
        return
    except Exception:
        _LOG.exception("REC03A analysis failed")
        st.error("Não foi possível carregar a análise. Suas escolhas permanecem intactas.")
        st.button("Tentar novamente",key="rec03a_retry")
        return

    st.markdown(section_heading(
        "SEUS DESTINOS", f'Temporada europeia · {len(result["destinations"])} destinos',
        "Este conjunto foi confirmado para pesquisa, não para o roteiro oficial.",
        variant="compact",
    ),unsafe_allow_html=True)
    st.caption(_label_ids([x["id"] for x in result["destinations"]],names))
    a,b=st.columns(2)
    a.button("Editar destinos",key="rec03a_edit",on_click=_edit)
    b.button("Minha lista",key="rec03a_back_wishlist",
             on_click=_go,args=("wishlist",))
    st.caption("Os dados mostram mínimos de ida pesquisados. "
               "Retorno, última milha, horários e custos de 2027 não confirmados.")
    if result["state"]=="insufficient_evidence":
        st.info("Ainda não há referências suficientes para uma comparação conclusiva.")
    elif result["state"]=="partial_evidence":
        st.info("As evidências são parciais. Não há grupo completo equivalente.")
    if result["has_local_only"]:
        st.caption("Destinos locais têm acesso urbano ainda não confirmado.")

    options=[c["base_id"] for c in result["candidates"]]
    by_id={c["base_id"]:c for c in result["candidates"]}
    st.markdown(section_heading(
        "SUGESTÕES DE PESQUISA", "Cidades que vale investigar",
        "Cidades com referências úteis para começar. Não estão em ordem de preferência.",
        variant="compact",
    ),unsafe_allow_html=True)
    featured=_featured_ids(result)
    _restore_widget("rec03a_show_all","rec03a_show_all_shadow",False,
                    lambda x:type(x) is bool)
    browsing=st.checkbox(f"Ver todas as cidades ({len(result['candidates'])})",
                         key="rec03a_show_all",on_change=_remember,
                         args=("rec03a_show_all","rec03a_show_all_shadow"))
    if browsing:
        # Browse INSTEAD OF highlighting the same IDs a second time.
        # Four visible cards keep the sole comparison CTA close to the last choice.
        st.markdown(section_heading(
            "TODAS AS ALTERNATIVAS", "Explore outras cidades-base",
            "Busque por nome ou país. As cidades em destaque também estão aqui.",
            variant="compact",
        ),unsafe_allow_html=True)
        _restore_widget("rec03a_search","rec03a_search_shadow","",
                        lambda x:isinstance(x,str))
        search=st.text_input("Pesquisar cidade ou país",key="rec03a_search",
                             on_change=_remember,
                             args=("rec03a_search","rec03a_search_shadow")).strip().casefold()
        categories=("Todas","Comparáveis","Condicionais","Para investigar")
        _restore_widget("rec03a_category","rec03a_category_shadow","Todas",
                        lambda x:x in categories)
        category=st.selectbox("Disponibilidade de evidências",categories,
                              key="rec03a_category",on_change=_remember,
                              args=("rec03a_category","rec03a_category_shadow"))
        groups={"Comparáveis":"comparable","Condicionais":"conditional",
                "Para investigar":"investigate"}
        filtered=[c for c in result["candidates"] if
                  (category=="Todas" or c["group"]==groups.get(category)) and
                  (not search or search in
                   (cities[c["base_id"]]["name"]+" "+
                    cities[c["base_id"]]["country"]).casefold())]
        st.caption(f"{len(filtered)} de {len(result['candidates'])} cidades-base encontradas.")
        if filtered:
            size=4
            pages=(len(filtered)+size-1)//size
            _restore_widget("rec03a_page","rec03a_page_shadow",1,
                            lambda x:type(x) is int and 1<=x<=pages)
            page=st.number_input("Página",min_value=1,max_value=pages,step=1,
                                 key="rec03a_page",on_change=_remember,
                                 args=("rec03a_page","rec03a_page_shadow"))
            for candidate in filtered[(page-1)*size:page*size]:
                _card(candidate,result,names,cities,plan["base_city"],options)
        else:
            st.info("Nenhuma cidade corresponde aos filtros.")
    elif featured:
        for base in featured:
            _card(by_id[base],result,names,cities,plan["base_city"],options)
    else:
        st.info("Não há destaques com referências suficientes para este escopo. "
                "Use 'Ver todas as cidades' para explorar as alternativas.")

    # Exactly one native CTA, always AFTER at most four visible cards.
    # UX87 will replace this region with its inline matrix while keeping CHOICE.
    render_card_selection_summary(result,cities)

    if st.checkbox("Metodologia e pesquisas pendentes",
                   key="rec03a_research_open"):
        _render_comparison_groups(result,names,cities)
        from rec05_priority_research_ui import render_research_result
        render_research_result(result,key="rec05_suggestions")
    if st.checkbox("Continuar para o roteiro",key="rec03a_planning_open"):
        from rec03b_handoff_ui import render_planning_handoff
        render_planning_handoff(plan,interests=interests,
                                discovery=discovery,research=research)


def render_recommendation_activity(*,plan,discovery=None,research=None):
    """Suggested research is default; manual view survives validated handoffs."""
    state=st.session_state
    if state.get(ACTIVITY) not in ACTIVITIES:
        state[ACTIVITY]=SUGGESTED
    if state[ACTIVITY]==MANUAL:
        from rec03b_handoff_ui import return_to_suggestions
        # Native return action appears BEFORE the lengthy legacy comparison.
        st.button("Voltar às cidades sugeridas",key="rec03a_handoff_back_manual",
                  on_click=return_to_suggestions)
        render_wishlist_base_comparison(plan=plan,discovery=discovery,
                                        research=research)
    else:
        render_suggestions(plan=plan,discovery=discovery,research=research)
    return state[ACTIVITY]
