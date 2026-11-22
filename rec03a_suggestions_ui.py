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

_REASON = {
    "menor_minimo_ponderado_no_mesmo_escopo_completo": "Menor mínimo ponderado de ida no mesmo conjunto completo de trajetos.",
    "fronteira_documental_do_escopo": "Documentação útil que merece investigação; não é prova de melhor logística.",
    "menor_minimo_ponderado_no_mesmo_subconjunto": "Menor mínimo ponderado de ida neste subconjunto equivalente, não na lista inteira.",
    "imperdiveis_identificados": "Todos os destinos imperdíveis têm tempo registrado ou identificação local.",
    "imperdiveis_com_evidencia_pendente": "Ainda há destinos imperdíveis sem tempo documentado.",
    "acesso_local_a_verificar": "Acesso urbano e última milha ainda precisam ser verificados.",
    "alternativa_individual_sem_grupo_completo": "Alternativa individual; não há grupo completo equivalente.",
    "comparacao_condicional_disponivel": "Há comparação de trajetos em comum, com ressalvas.",
    "sem_tempo_ou_identificacao_local": "Sem tempo ou identificação local documentados neste escopo.",
    "destinos_com_tempo_pendente": "Há destinos sem tempo pesquisado.",
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
    st.markdown("#### Destinos da temporada europeia")
    st.write("Escolha os destinos que serão usados para investigar onde ficar durante a temporada. "
             "A lua de mel e a temporada são escolhas separadas; não inferimos a etapa pelo país.")
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
    st.button("Selecionar todos", key="rec03a_select_all", on_click=_draft_all, args=(active_ids,))
    st.button("Limpar seleção", key="rec03a_clear_selection", on_click=_draft_all, args=([],))
    st.button("Usar toda a lista para a temporada", key="rec03a_confirm_all", type="primary",
              on_click=_scope_select, args=(active_ids,interests,discovery))
    st.button("Analisar destinos selecionados", key="rec03a_confirm_subset",
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


def _card(candidate, result, names, cities, official, prefix):
    b = candidate["base_id"]
    meta = cities[b]
    with st.container(border=True):
        st.markdown("**"+meta["name"]+"** · "+meta["country"]+
                    (" · Base oficial de referência" if b==official else ""))
        reasons = candidate["reasons"]
        if reasons:
            st.write(_REASON.get(reasons[0], "Alternativa para investigação."))
        known = candidate["known_destination_ids"]
        local = candidate["local_destination_ids"]
        missing = candidate["missing_destination_ids"]
        examples=evidence_examples(candidate,result["destinations"])
        for d,cell in examples:
            category=cell["category"]
            detail=("Acesso local a verificar" if category=="local" else
                    format_minutes(cell["display_min"])+" · mínimo de ida publicado · "+
                    ("histórico" if category=="historical" else "indicativo"))
            st.write(names.get(d,d)+" — "+detail)
        st.caption(f"{len(known)} destinos com tempo · {len(local)} locais · {len(missing)} sem tempo")
        st.caption("Retorno e horários de 2027 não confirmados.")
        must = candidate["must_visit"]
        if must["missing"]:
            st.write("Imperdíveis sem tempo: "+_label_ids(must["missing"],names))
        elif must["known"] or must["local"]:
            st.write("Imperdíveis identificados: "+_label_ids(must["known"]+must["local"],names))
        if known:
            st.caption("Históricos: "+str(candidate["historical_count"])+
                       " · Indicativos: "+str(candidate["indicative_count"]))
        if local:
            st.caption("Acesso local a verificar: "+_label_ids(local,names))
        # An expander alone eagerly renders every child on each rerun.
        # A keyed checkbox makes detailed provenance genuinely on demand.
        detail_key="rec03a_details_"+prefix+"_"+b
        if st.checkbox("Consultar referências e limitações",key=detail_key):
            coverage = candidate["weighted_coverage"]
            if coverage["value"] is not None:
                st.write(f'Cobertura ponderada: {coverage["value"]:.0%} '
                         f'({coverage["numerator"]}/{coverage["denominator"]} pesos de destinos não locais).')
            else:
                st.caption("Cobertura ferroviária não aplicável.")
            st.caption(candidate["coverage_limitation"])
            for reason in reasons[1:]:
                st.write(_REASON.get(reason,"Informação a investigar."))
            for d, cell in candidate["evidence"].items():
                st.write(names.get(d,d)+" · "+cell.get("label","Sem referência"))
                if cell.get("source_url"):
                    st.link_button("Fonte de "+names.get(d,d),cell["source_url"])
                raw=candidate["raw_rail_evidence"].get(d,{})
                date=cell.get("gap_checked_at") or raw.get("source_date")
                if date:
                    st.caption("Data registrada: "+str(date))
                for observation in raw.get("observations",[]):
                    st.caption("Observação original: "+str(observation.get("evidence_date") or "data não informada")+
                               " · "+format_minutes(observation.get("minimum_oneway_min")))
                    if observation.get("source_url"):
                        st.link_button("Fonte da observação",observation["source_url"])
            st.caption(candidate["limitation"])
        from rec03b_handoff_ui import render_card_actions
        render_card_actions(b,prefix)


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


def render_suggestions(*, plan, discovery=None, research=None):
    st.markdown("### Cidades-base para investigar")
    st.button("Voltar à minha lista", key="rec03a_back_wishlist", on_click=_go,args=("wishlist",))
    try:
        discovery=discovery if discovery is not None else build_exploration_discovery()
        interests=st.session_state.get("ux502_interests",empty_interests())
        active=[x for x in ordered_interests(interests,discovery) if x["priority"]!="discarded"]
        names={x["id"]:x["name"] for x in discovery["destinations"]}
        checked=reconcile_session_scope(st.session_state,interests,discovery)
        if checked["state"]=="no_destinations":
            st.info("Nenhum destino ativo. Adicione lugares ou revise as prioridades em Minha lista.")
            return
        if checked["state"]!="ready" or st.session_state.get("rec03a_edit_scope"):
            _render_scope(interests,discovery,active,names,checked)
            return
        research=research if research is not None else load_research(include_candidates=True)
        result=recommend_bases(interests,checked["scope"],discovery=discovery,research=research)
        cities={x["id"]:x for x in research["cities"]}
    except ImportError:
        _LOG.exception("REC03A incompatible module version")
        st.error("A análise de cidades sugeridas está temporariamente indisponível. "
                 "Se o aplicativo acabou de ser atualizado, reinicie-o para carregar a versão atual. "
                 "Sua lista e o planejamento permanecem intactos.")
        return
    except Exception:
        _LOG.exception("REC03A analysis failed")
        # No stale or empty-looking recommendations after a loader failure.
        st.error("Não foi possível carregar a análise. Suas escolhas permanecem intactas.")
        st.button("Tentar novamente",key="rec03a_retry")
        return
    st.write("Temporada europeia · "+str(len(result["destinations"]))+" destinos considerados")
    st.caption(_label_ids([x["id"] for x in result["destinations"]],names))
    st.button("Editar destinos considerados",key="rec03a_edit",on_click=_edit)
    st.button("Revisar prioridades na minha lista",key="rec03a_priorities",on_click=_go,args=("wishlist",))
    st.caption("Sugestões de pesquisa — não são reservas, decisão oficial ou garantia de viabilidade.")
    if result["state"]=="insufficient_evidence":
        st.info("Ainda não há referências suficientes. Consulte as cidades e as lacunas abaixo.")
    elif result["state"]=="partial_evidence":
        st.info("Não há grupo completo equivalente. As possibilidades abaixo são condicionais.")
    if result["has_local_only"]:
        st.caption("Destinos locais são tratados separadamente; acesso urbano ainda não confirmado.")
    from rec03b_handoff_ui import render_compare_selection, render_planning_handoff
    render_compare_selection(result,cities)
    render_planning_handoff(plan,interests=interests,discovery=discovery,research=research)
    candidates={c["base_id"]:c for c in result["candidates"]}
    sections=result["highlight_sections"]
    ordered_sections=(("Alternativas com evidências comparáveis",sections["complete_reference_groups"]),
                      ("Outras possibilidades para investigar",sections["conditional_all_must_identified"]+
                       sections["conditional_must_pending"]))
    for index,(label,ids) in enumerate(ordered_sections):
        if ids:
            st.markdown("#### "+label)
            size=6
            count=(len(ids)+size-1)//size
            key="rec03a_highlight_page_"+str(index)
            _restore_widget(key,key+"_shadow",1,lambda x:type(x) is int and 1<=x<=count)
            page=st.number_input("Página de destaques "+str(index+1),1,count,step=1,key=key,
                                 on_change=_remember,args=(key,key+"_shadow")) if count>1 else 1
            for b in ids[(page-1)*size:page*size]:
                _card(candidates[b],result,names,cities,plan["base_city"],"highlight")
    _render_comparison_groups(result,names,cities)
    st.markdown("#### Todas as cidades-base")
    _restore_widget("rec03a_search","rec03a_search_shadow","",lambda x:isinstance(x,str))
    text=st.text_input("Pesquisar cidade ou país",key="rec03a_search",
                       on_change=_remember,args=("rec03a_search","rec03a_search_shadow")).strip().casefold()
    categories=("Todas","Comparáveis","Condicionais","Para investigar")
    _restore_widget("rec03a_category","rec03a_category_shadow","Todas",lambda x:x in categories)
    category=st.selectbox("Disponibilidade de evidências",categories,key="rec03a_category",
                          on_change=_remember,args=("rec03a_category","rec03a_category_shadow"))
    groups={"Comparáveis":"comparable","Condicionais":"conditional","Para investigar":"investigate"}
    filtered=[c for c in result["candidates"] if
              (category=="Todas" or c["group"]==groups.get(category)) and
              (not text or text in (cities[c["base_id"]]["name"]+" "+cities[c["base_id"]]["country"]).casefold())]
    st.caption(f"{len(filtered)} de {len(candidates)} cidades-base.")
    if not filtered:
        st.info("Nenhuma cidade corresponde aos filtros.")
        return
    size=8
    pages=(len(filtered)+size-1)//size
    _restore_widget("rec03a_page","rec03a_page_shadow",1,lambda x:type(x) is int and 1<=x<=pages)
    page=st.number_input("Página",min_value=1,max_value=pages,step=1,key="rec03a_page",
                         on_change=_remember,args=("rec03a_page","rec03a_page_shadow"))
    for c in filtered[(page-1)*size:page*size]:
        if c["highlight"]:
            with st.expander(cities[c["base_id"]]["name"]+" · destaque também listado acima"):
                if st.checkbox("Consultar cartão",key="rec03a_all_card_"+c["base_id"]):
                    _card(c,result,names,cities,plan["base_city"],"all")
        else:
            _card(c,result,names,cities,plan["base_city"],"all")


def render_recommendation_activity(*,plan,discovery=None,research=None):
    state=st.session_state
    if state.get(ACTIVITY) not in ACTIVITIES:
        state[ACTIVITY]=MANUAL
    # Separate durable view state from widget lifecycle cleanup.
    if state.get("rec03a_activity_widget")!=state[ACTIVITY]:
        state["rec03a_activity_widget"]=state[ACTIVITY]
    def changed():
        state[ACTIVITY]=state["rec03a_activity_widget"]
    choice=st.radio("Tipo de comparação",ACTIVITIES,horizontal=True,
                    key="rec03a_activity_widget",on_change=changed)
    if choice==SUGGESTED:
        # Scenario and finance handoffs remain REC04.
        render_suggestions(plan=plan,discovery=discovery,research=research)
    else:
        render_wishlist_base_comparison(plan=plan,discovery=discovery,research=research)
    return choice
