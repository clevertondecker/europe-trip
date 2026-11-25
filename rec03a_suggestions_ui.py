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


# A contextual review borrows the EXISTING UX34 workspace and restores its
# prior filters on return. No new plan/persistence model is introduced.
_UX34_CONTEXT_KEYS=(
    "ux34_candidates","ux34_destinations","ux34_apply_candidate",
)
_UX34_CONFIRMATION_KEYS=(
    "ux34_apply_ack","ux34_review","ux34_review_candidate",
    "ux34_review_signature",
)


def _review_destinations(scope_destinations):
    """Never hide destinations that the legacy UX34 catalog cannot compare."""
    from base_change_model import destination_catalog, _canonical_destination
    catalog=destination_catalog()
    supported,unsupported=[],[]
    for item in dict.fromkeys(scope_destinations):
        normalized=_canonical_destination(item)
        if normalized in catalog:
            if normalized not in supported:
                supported.append(normalized)
        else:
            unsupported.append(item)
    return supported,unsupported


def _open_base_review(base,scope_destinations):
    """Start a validated one-base handoff; never write the official TripPlan."""
    from copy import deepcopy
    from trip_plan_model import BASES
    from rec03b_handoffs import CHOICE
    state=st.session_state
    plan=state.get("advisor_plan",{})
    scope=state.get(SCOPE)
    if (base not in BASES or base==plan.get("base_city")
            or not isinstance(scope,dict) or not scope.get("confirmed")
            or tuple(scope.get("destination_ids",()))!=tuple(scope_destinations)
            or base not in state.get(CHOICE,[])):
        return
    from rec03b_handoffs import validate_handoff
    from ux502_destination_interests_model import empty_interests
    from base_research_expanded_model import load_research
    try:
        validate_handoff(scope,state.get("ux502_interests",empty_interests()),
                         build_exploration_discovery(),
                         load_research(include_candidates=True),[],"planning")
    except (ValueError,KeyError,TypeError):
        return
    supported,unsupported=_review_destinations(scope_destinations)
    state["ux114_saved_workspace"]={
        key:deepcopy(state[key]) for key in _UX34_CONTEXT_KEYS if key in state
    }
    state["ux114_review_context"]={
        "base":base,
        "identity":state.get("rec03a_identity"),
        "plan_id":plan["plan_id"],"revision":plan["revision"],
        "official":plan["base_city"],"scope":deepcopy(scope),
        "scope_destinations":list(scope_destinations),
        "supported_destinations":supported,"unsupported_destinations":unsupported,
        "approved_destinations":(
            list(supported) if supported and len(supported)<=8 and not unsupported
            else None),
    }
    state["ux114_review_base"]=base
    if len(supported)>8:
        state["ux114_review_overlimit"]=len(supported)
    else:
        state.pop("ux114_review_overlimit",None)
    state["ux34_candidates"]=[base]
    state["ux34_destinations"]=list(
        state["ux114_review_context"]["approved_destinations"] or [])
    for key in ("ux34_review","ux34_review_candidate","ux34_review_signature",
                "ux34_apply_ack","ux34_apply_candidate","ux114_scope_choice"):
        state.pop(key,None)


def close_base_review():
    """Restore the advanced decision filters; never alter the TripPlan."""
    from copy import deepcopy
    state=st.session_state
    if "ux114_review_context" in state or "ux114_saved_workspace" in state:
        previous=state.get("ux114_saved_workspace",{})
        for key in _UX34_CONTEXT_KEYS+_UX34_CONFIRMATION_KEYS:
            state.pop(key,None)
        for key,value in previous.items():
            state[key]=deepcopy(value)
    for key in ("ux114_review_base","ux114_review_overlimit",
                "ux114_review_context","ux114_saved_workspace",
                "ux114_scope_choice"):
        state.pop(key,None)


def validate_base_review(plan):
    """Reuse the REC03B scope contract; fail closed when any identity/plan
    revision, selected base, wishlist priority or confirmed scope changes.
    """
    from rec03b_handoffs import CHOICE,validate_handoff
    from ux502_destination_interests_model import empty_interests
    from base_research_expanded_model import load_research
    state=st.session_state
    ctx=state.get("ux114_review_context")
    if not isinstance(ctx,dict):
        return None
    if (ctx.get("base")!=state.get("ux114_review_base")
            or ctx.get("identity")!=state.get("rec03a_identity")
            or ctx.get("plan_id")!=plan.get("plan_id")
            or ctx.get("revision")!=plan.get("revision")
            or ctx.get("official")!=plan.get("base_city")
            or ctx.get("scope")!=state.get(SCOPE)
            or ctx.get("base") not in state.get(CHOICE,[])):
        return None
    try:
        validate_handoff(ctx["scope"],
                         state.get("ux502_interests",empty_interests()),
                         build_exploration_discovery(),
                         load_research(include_candidates=True),[],"planning")
    except (ValueError,KeyError,TypeError):
        return None
    return ctx


def _confirm_base_review_scope(supported):
    state=st.session_state
    context=state.get("ux114_review_context")
    selected=state.get("ux114_scope_choice",[])
    if (not isinstance(context,dict) or not isinstance(selected,list)
            or not 1<=len(selected)<=8 or len(selected)!=len(set(selected))
            or not set(selected)<=set(supported)):
        return
    context["approved_destinations"]=list(selected)
    state["ux34_destinations"]=list(selected)


def render_base_review_scope(ctx):
    """Make subset/unsupported data explicit; never use UX34's defaults."""
    from base_change_model import destination_catalog
    from city_decision_model import MAX_DESTINATIONS
    supported=ctx["supported_destinations"]
    unsupported=ctx["unsupported_destinations"]
    if unsupported:
        visible_names={d["id"]:d["name"]
                       for d in build_exploration_discovery()["destinations"]}
        st.warning(str(len(unsupported))+" destino(s) do seu escopo não são "
                   "suportados pela pesquisa legada: "+
                   ", ".join(visible_names.get(item,item) for item in unsupported)+
                   ". Eles continuam na lista e no roteiro.")
    if not supported:
        st.error("Nenhum destino do escopo é compatível com esta ferramenta. "
                 "Não abriremos uma comparação usando passeios de exemplo.")
        return False
    if ctx.get("approved_destinations") is not None:
        st.caption("Escopo da revisão: "+str(len(ctx["approved_destinations"]))+
                   " destino(s) explicitamente escolhidos. "
                   "A lista original e o roteiro permanecem intactos.")
        return True
    if len(supported)>MAX_DESTINATIONS:
        st.info("O comparador oficial aceita até "+str(MAX_DESTINATIONS)+
                " destinos por revisão. Selecione explicitamente quais usar; "
                "nenhum foi escolhido automaticamente.")
    else:
        st.info("A ferramenta não pesquisa todos os destinos da sua lista. "
                "Confirme o subconjunto antes de avaliar a mudança.")
    catalog=destination_catalog()
    st.multiselect("Destinos compatíveis para esta revisão",supported,
                   format_func=lambda x:catalog[x],max_selections=MAX_DESTINATIONS,
                   key="ux114_scope_choice", placeholder="Escolha uma ou mais opções")
    chosen=st.session_state.get("ux114_scope_choice",[])
    st.button("Confirmar destinos da revisão",key="ux114_confirm_scope",
              disabled=not chosen,on_click=_confirm_base_review_scope,
              args=(tuple(supported),))
    return False


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
                   key="rec03a_scope_widget", on_change=_draft_changed, placeholder="Escolha uma ou mais opções")
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


def _overview_caveats(cell):
    """Only factual qualifications from the existing canonical projection."""
    caveats=[]
    if cell.get("legacy_divergent_sources"):
        caveats.append("Tempos publicados divergentes")
    if cell.get("station_caveat") or cell.get("station_comparability")=="city_level_ambiguous":
        caveats.append("Estações a verificar")
    if cell.get("evidence_notes"):
        caveats.append("Observações da fonte")
    # The canonical label also carries qualifications not present as flags.
    label=str(cell.get("label") or "").lower()
    if any(word in label for word in ("outra referência", "fonte original não reproduzida")):
        caveats.append("Ressalva documental")
    return list(dict.fromkeys(caveats))


def _overview_cell(cell):
    """Short one-way evidence label with an accessible caveat indicator."""
    category = cell["category"]
    if category == "historical":
        label="Histórico · "+format_minutes(cell["display_min"])
    elif category == "reference_only":
        label="Indicativo · "+format_minutes(cell["display_min"])
    elif category == "local":
        label="Local · acesso pendente"
    else:
        label="Sem tempo pesquisado"
    return label + (" · ver ressalvas" if _overview_caveats(cell) else "")


def comparison_overview_rows(result, names, cities, base_ids):
    """Project identical confirmed destinations across each visible base.

    This is a view only: no ranking, no average across different subsets,
    no assumed return journey, and no new selection state.
    """
    candidates = {row["base_id"]: row for row in result["candidates"]}
    chosen = [base for base in dict.fromkeys(base_ids) if base in candidates]
    rows = []
    for destination in result["destinations"]:
        destination_id = destination["id"]
        label = names.get(destination_id, destination_id)
        if destination["priority"] == "must_visit":
            label = "★ " + label
        record = {"Destino desejado": label}
        for base in chosen:
            meta = cities[base]
            heading = meta["name"] + " · " + meta["country"]
            record[heading] = _overview_cell(candidates[base]["evidence"][destination_id])
        rows.append(record)
    return rows


def _render_quick_comparison(result, names, cities, base_ids, selected=()):
    """Discovery preview, not CHOICE. UX87 is authoritative for chosen cities."""
    if not base_ids:
        return
    single=len(base_ids)==1
    title=("Dados disponíveis para "+cities[base_ids[0]]["name"] if single
           else "Prévia das cidades sugeridas")
    subtitle=("Uma cidade visível no filtro; consulte os dados pesquisados."
              if single else "Estas são as cidades visíveis nesta página, não necessariamente as suas selecionadas.")
    # Once CHOICE has enough bases for UX87, avoid a second open comparison.
    with st.container(key="ux96_preview_documentary"):
        with st.expander("Prévia das sugestões · não é sua seleção",
                         expanded=False):
            st.markdown(section_heading(
                "VISÃO DOCUMENTAL" if single else "PRÉVIA DE PESQUISA",title,
                subtitle,variant="compact",
            ),unsafe_allow_html=True)
            rows=comparison_overview_rows(result,names,cities,base_ids)
            if not rows:
                st.info("Nenhum destino confirmado neste escopo.")
                return
            st.dataframe(rows,hide_index=True,width="stretch",
                         height=min(450,70+37*len(rows)),key="rec03a_quick_matrix")
            st.caption("★ Imperdível · Histórico = registro anterior · Indicativo = referência "
                       "não confirmada · Local = acesso urbano a verificar. "
                       "'Ver ressalvas' remete às evidências no cartão da cidade. "
                       "Os tempos são mínimos de ida, não duração de ida e volta; "
                       "sem tempo pesquisado não significa rota inviável.")

def _card(candidate, result, names, cities, official, options):
    """Compact choice card; documentary details stay available on demand."""
    from rec03b_handoff_ui import render_card_choice

    base=candidate["base_id"]
    meta=cities[base]
    from rec03b_handoff_ui import selected_card_bases
    from ux96_comparison_visual_ui import city_card_header
    with st.container(border=True,key="ux96_city_"+base):
        from ux100_base_card_photos import render_base_card_photo
        render_base_card_photo(base,meta["name"])
        from trip_plan_model import BASES
        st.markdown(city_card_header(
            candidate,meta,
            is_selected=base in selected_card_bases(st.session_state,options),
            is_official=base==official,
            official_supported=base in BASES,
        ),unsafe_allow_html=True)
        from ux98_base_insights_presentation import project_base_insights
        from ux99_base_cards_presentation import insight_panels
        st.markdown(insight_panels(project_base_insights(candidate)),
                    unsafe_allow_html=True)
        from ux105_base_city_context import render_base_context_summary
        render_base_context_summary(base)
        missing=candidate["must_visit"]["missing"]
        render_card_choice(base,options,show_selection_hint=False)
        # UX112: primary investigation handoffs must not be hidden behind research details.
        from rec03b_handoff_ui import render_card_actions
        render_card_actions(base,"card",compact=True)
        if st.checkbox("Detalhes da pesquisa e fontes",
                       key="rec03a_details_"+base):
            from ux105_base_city_context import render_base_context_details
            render_base_context_details(base)
            reasons=candidate["reasons"]
            st.write(_REASON.get(reasons[0],"Alternativa para investigação.") if reasons
                     else "Alternativa para investigar com os dados disponíveis.")
            if missing:
                st.write("**O que falta pesquisar?** Tempos para os imperdíveis: "+
                         _label_ids(missing,names)+".")
            elif candidate["local_destination_ids"]:
                st.write("**O que falta pesquisar?** Acesso dentro da cidade e última milha.")
            else:
                st.write("**O que falta pesquisar?** Retorno, acesso às atrações e horários de 2027.")
            st.caption("Referências de ida pesquisadas; não são duração total nem preços confirmados.")
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
                for caveat in _overview_caveats(cell):
                    st.caption("Ressalva: "+caveat)
                for field,prefix in (("station_caveat","Estações"),
                                     ("evidence_notes","Observação")):
                    if cell.get(field):
                        st.caption(prefix+": "+str(cell[field]))
                if cell.get("source_url"):
                    st.link_button("Fonte de "+names.get(destination,destination),
                                   cell["source_url"])
                raw=candidate["raw_rail_evidence"].get(destination,{})
                date=cell.get("gap_checked_at") or raw.get("source_date")
                if date:
                    st.caption("Data registrada: "+str(date))
                for observation in raw.get("observations",[]):
                    st.caption("Observação original: "+
                               str(observation.get("evidence_date") or "data não informada")
                               +" · "+format_minutes(observation.get("minimum_oneway_min")))
                    if observation.get("source_url"):
                        st.link_button("Fonte da observação",observation["source_url"])
            st.caption(candidate["limitation"])


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
    from ux99_base_cards_presentation import scope_chips
    st.markdown(scope_chips([x["id"] for x in result["destinations"]],names),
                unsafe_allow_html=True)
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
    from rec03b_handoff_ui import selected_card_bases, render_selection_toolbar, render_planning_handoff
    selected=selected_card_bases(st.session_state,options)
    st.caption("Compare até cinco cidades; a base oficial só muda após uma confirmação explícita.")
    modes=("Explorar alternativas","Minha comparação")
    _restore_widget("ux112_active_view","ux112_active_view_shadow",
                    modes[0],lambda x:x in modes)
    view=st.segmented_control("Área da pesquisa",list(modes),
                              key="ux112_active_view",default=modes[0],
                              on_change=_remember,
                              args=("ux112_active_view","ux112_active_view_shadow"))
    if view=="Explorar alternativas":
        st.markdown(section_heading(
            "EXPLORAR ALTERNATIVAS", "Cidades-base para investigar",
            "Pesquise por cidade ou país. Selecione candidatas para comparar, ou conheça sua ficha individual.",
            variant="compact",
        ),unsafe_allow_html=True)
        # Search is always accessible, without an extra checkbox first.
        _restore_widget("rec03a_search","rec03a_search_shadow","",
                        lambda x:isinstance(x,str))
        search=st.text_input("Pesquisar cidade ou país",key="rec03a_search",
                             placeholder="Ex.: Metz, Nancy, França",
                             on_change=_remember,
                             args=("rec03a_search","rec03a_search_shadow")).strip().casefold()
        _restore_widget("rec03a_show_all","rec03a_show_all_shadow",False,
                        lambda x:type(x) is bool)
        show_all=st.checkbox(f"Ver todas as cidades ({len(result['candidates'])})",
                             key="rec03a_show_all",on_change=_remember,
                             args=("rec03a_show_all","rec03a_show_all_shadow"))
        browsing=bool(search) or show_all
        if browsing:
            if show_all:
                categories=("Todas","Comparáveis","Condicionais","Para investigar")
                _restore_widget("rec03a_category","rec03a_category_shadow","Todas",
                                lambda x:x in categories)
                category=st.selectbox("Disponibilidade de evidências",categories,
                                      key="rec03a_category",on_change=_remember,
                                      args=("rec03a_category","rec03a_category_shadow"))
            else:
                category="Todas"
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
                visible=filtered[(page-1)*size:page*size]
                with st.container(key="ux99_base_gallery_all"):
                    columns=st.columns(min(2,len(visible)),gap="medium")
                    for index,candidate in enumerate(visible):
                        with columns[index%len(columns)]:
                            _card(candidate,result,names,cities,plan["base_city"],options)
            else:
                st.info("Nenhuma cidade corresponde aos filtros.")
        else:
            featured=_featured_ids(result)
            if featured:
                with st.container(key="ux99_base_gallery_featured"):
                    columns=st.columns(min(2,len(featured)),gap="medium")
                    for index,base in enumerate(featured):
                        with columns[index%len(columns)]:
                            _card(by_id[base],result,names,cities,plan["base_city"],options)
            else:
                st.info("Não há destaques para este escopo. Pesquise uma cidade acima "
                        "ou abra todas as alternativas.")
        render_selection_toolbar(options,cities,navigation="explore")
    else:
        st.markdown(section_heading(
            "MINHA COMPARAÇÃO", "Comparar minhas cidades",
            "Os mesmos destinos em cada alternativa. A seleção não altera seu roteiro oficial.",
            variant="compact",
        ),unsafe_allow_html=True)
        render_selection_toolbar(options,cities,navigation="compare")
        selected=selected_card_bases(st.session_state,options)
        if 2<=len(selected)<=5:
            from ux87_inline_base_comparison_ui import render_inline_comparison
            render_inline_comparison(interests,checked["scope"],selected,
                                     discovery=discovery,research=research)
        elif len(selected)>5:
            st.warning("Seleção anterior acima do limite de cinco cidades. "
                       "Remova as excedentes sem perder suas escolhas restantes.")
        elif len(selected)==1:
            st.info("Uma cidade selecionada. Explore e adicione outra para comparar.")
        else:
            st.info("Selecione de duas a cinco cidades na aba Explorar alternativas.")
        st.markdown("#### Próximos passos")
        from trip_plan_model import BASES
        eligible=[base for base in selected if base in BASES and base!=plan["base_city"]]
        unsupported=[base for base in selected if base not in BASES]
        if eligible and len(selected)<=5:
            preferred=st.selectbox(
                "Cidade-base para revisão oficial",eligible,
                format_func=lambda base:cities[base]["name"],
                key="ux114_preferred_base")
            st.button("Revisar esta cidade-base no meu plano",
                      key="ux114_open_review",type="primary",
                      on_click=_open_base_review,
                      args=(preferred,tuple(checked["scope"]["destination_ids"])))
            st.caption("Abre a revisão existente. Nada muda até você confirmar "
                       "explicitamente a alteração e salvar o roteiro.")
        elif 2<=len(selected)<=5:
            st.info("Nenhuma das alternativas selecionadas pode substituir a base "
                    "oficial atual. Continue investigando ou adicione uma base elegível.")
        if unsupported:
            st.caption("Somente pesquisa, sem aplicação oficial nesta versão: "+
                       ", ".join(cities[base]["name"] for base in unsupported)+".")
        st.markdown("#### Continuar montando meu roteiro")
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
