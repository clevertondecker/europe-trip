"""UX 3.4: choose city bases on a common, explicitly incomplete evidence set.

User sees a decision workspace, not a technical optimizer. Drafts live only in
the Streamlit session unless the user downloads them; applying a supported
official base requires separate review and confirmation.
"""
from __future__ import annotations

import streamlit as st

from base_change_model import destination_catalog,_canonical_destination
from base_scenario_model import base_options
from city_decision_model import (
    compare_city_decisions,shared_destinations,review_base_application,
)
from city_decision_store import (
    make_city_draft,export_city_draft,import_city_draft,
)
from planning_session import active_plan,update_fields


def _currency(value:float|None)->str:
    return "Não calculável" if value is None else (
        "R$ "+f"{value:,.0f}".replace(",","."))


def _names()->dict:
    return {city["id"]:city["name"] for city in base_options()}


def _load_draft(draft:dict)->None:
    """Reopen a study without writing any canonical trip field."""
    current=active_plan()
    names=_names()
    st.session_state["ux34_candidates"]=[
        base for base in draft["alternatives"]
        if base in names and base!=current["base_city"]]
    st.session_state["ux34_destinations"]=list(dict.fromkeys(
        _canonical_destination(d) for d in draft["destination_ids"]))
    st.session_state["ux34_days"]=draft["stay_days"]
    st.session_state["ux34_fx"]=draft["eur_fx"]
    for key,amount in draft["rents_eur_month"].items():
        st.session_state["ux34_rent_"+key]=amount or 0.0
    st.session_state["ux34_saved_reference"]=draft["official_at_creation"]
    st.session_state["ux34_notice"]=(
        "Estudo restaurado. Compare novamente com a base oficial atual. "
        "Nenhuma mudança foi aplicada ao roteiro.")
    st.session_state.pop("ux34_review",None)


def _render_routes(comparison:dict)->None:
    names=_names()
    official=comparison["official_base"]
    alternatives=comparison["alternatives"]
    places=comparison["destination_names"]
    rows={}
    for city in [official]+alternatives:
        rows[city]={r["destination_id"]:r for r in comparison["profiles"][city]["routes"]}
    table=[]
    for dest in comparison["destinations"]:
        entry={"Passeio":places[dest]}
        for city in [official]+alternatives:
            route=rows[city][dest]
            typical=route.get("representative_minutes")
            fastest=route["minutes"]
            label=names[city]+(" (meu plano)" if city==official else "")
            entry[label]=(f"{typical} min típico · {fastest} min mínimo (ida)"
                          if typical is not None and fastest is not None else
                          f"{fastest} min mínimo (ida)" if fastest is not None
                          else "Não pesquisado")
        table.append(entry)
    st.dataframe(table,hide_index=True,width="stretch",height=270)
    st.caption("Referências históricas de novembro/2026, somente ida, estação a estação. "
               "O tempo típico é a média publicada pelo operador, não a garantia "
               "de um trem em qualquer dia. Trocas de estação e última milha "
               "não integram esses tempos. Nenhuma volta de 2027 foi validada.")
    if len(alternatives)==1:
        a,b=official,alternatives[0]
        paired=[(d,rows[a][d].get("representative_minutes"),
                   rows[b][d].get("representative_minutes"))
                for d in comparison["destinations"]]
        pairs=[v for v in paired if v[1] is not None and v[2] is not None]
        if pairs:
            sum_a=sum(v[1] for v in pairs)
            sum_b=sum(v[2] for v in pairs)
            st.markdown("**Subtotal ilustrativo das visitas comparáveis**")
            st.caption(f"{len(pairs)}/{len(paired)} destinos com tempos típicos nas duas bases. "
                       "Uma visita por destino, apenas ida: "
                       f"{names[a]} {sum_a} min e {names[b]} {sum_b} min. "
                       "Uma ida + volta hipotética com duração igual daria "
                       f"{2*sum_a} min e {2*sum_b} min, respectivamente; "
                       "**os retornos não foram pesquisados e isso não é um "
                       "tempo total verificado**. Nenhuma rota incompleta integra a soma.")
    for city in [official]+alternatives:
        with st.expander("Fontes e modalidades · "+names[city],expanded=False):
            for r in comparison["profiles"][city]["routes"]:
                label=places[r["destination_id"]]
                st.markdown("**"+label+"** · "+(
                    str(r["minutes"])+" min" if r["minutes"] is not None else
                    "Tempo não pesquisado"))
                fare=(f"€ {r['fare']:.2f} por pessoa e trecho (valor histórico/desde)"
                      if r["fare"] is not None else "Tarifa não documentada")
                st.caption(fare+" · "+str(r["basis"] or "sem data de pesquisa"))
                if r.get("representative_minutes") is not None:
                    st.caption("Tempo típico de ida: "+str(r["representative_minutes"])+
                               " min · mínimo de ida: "+str(r["minutes"])+" min")
                if r.get("transfers") is not None:
                    st.caption("Conexões no exemplo pesquisado: "+str(r["transfers"]))
                if r.get("frequency_reference"):
                    st.caption(r["frequency_reference"])
                reference=r.get("representative_minutes")
                if reference is not None:
                    st.caption("Logística: "+(
                        "Pernoite a avaliar; ida superior a 4h." if reference>=240 else
                        "Bate-volta a verificar com horários reais de ida e volta."
                    ))
                st.caption(r["note"])
                if r["source"]:
                    st.markdown("[Consultar fonte]("+r["source"]+")")


def _render_coverage(comparison:dict)->None:
    st.markdown("#### O que fica mais fácil ou mais difícil?")
    for item in comparison["candidates"]:
        city=item["name"]
        counts=item["changes"]
        with st.container(border=True):
            st.markdown("**"+city+" versus "+comparison["official_name"]+"**")
            # Linear reading works on narrow screens and assistive technology.
            # All four outcomes remain visible without four metric columns.
            st.markdown(
                f"**{counts['Melhorou']} mais rápidos** · "
                f"**{counts['Piorou']} mais lentos** · "
                f"{counts['Semelhante']} semelhantes · "
                f"{counts['Não pesquisado']} sem comparação pesquisada"
            )
            st.caption("Comparação com tempo nas duas cidades: "+
                       str(item["paired_route_times"])+"/"+
                       str(len(comparison["destinations"]))+
                       " destinos. Critério ilustrativo: ≥15 min de diferença só ida, "
                       "usando tempos típicos quando disponíveis nas duas bases.")
            if (item["candidate_only_researched"] or
                item["official_only_researched"]):
                st.caption("Pesquisa assimétrica: "+
                           str(item["candidate_only_researched"])+
                           " rota(s) conhecida(s) apenas na candidata, "+
                           str(item["official_only_researched"])+
                           " apenas na base oficial. **Não** representam passeios ganhos "
                           "ou perdidos.")
            refs=comparison["profiles"][item["id"]]["country_time_references"]
            st.caption("Países com algum tempo de deslocamento pesquisado, "
                       "não viagens confirmadas: "+
                       (", ".join(refs) if refs else "sem amostra suficiente"))
            st.caption("Sem evidência suficiente para dizer que algum passeio "
                       "se tornou impossível, foi perdido ou exige pernoite.")
    _render_routes(comparison)


def _render_finance(comparison:dict)->None:
    st.markdown("#### Quanto poderia mudar o orçamento?")
    st.caption("Somente moradia: valores **hipotéticos inseridos por você**, "
               "para a mesma duração e o mesmo cenário financeiro. "
               "Os trajetos e ingressos continuam fora do cálculo da diferença.")
    official=comparison["official_base"]
    reference_name=comparison["official_name"]
    for item in comparison["candidates"]:
        cost=item["housing_whatif"]
        with st.container(border=True):
            st.markdown("**"+reference_name+" → "+item["name"]+"**")
            if not cost["known"]:
                st.info("Diferença de moradia não calculável: informe os dois "
                        "aluguéis mensais hipotéticos, ou mantenha ambos como "
                        "não cotados. Ausência de dado não é €0.")
            else:
                amount=item["financial_delta_brl"]
                st.metric("Variação apenas da moradia (R$)",
                          _currency(amount),delta=_currency(amount))
                st.caption("Projeção condicionada às demais parcelas atuais: "+
                           _currency(cost["official_total_brl"])+" na base oficial, "+
                           _currency(cost["candidate_total_brl"])+" na alternativa.")
                st.warning("**Não é a economia total.** Não inclui variação real "
                           "dos passeios, traslados, alimentação, taxas de imóvel "
                           "nem bilhetes de retorno.")
        if item["missing"]:
            st.caption("Pendências: "+"; ".join(item["missing"][:4])+".")
    st.caption("A verba de passeios já existe no orçamento. "
               "Não somamos tarifas ferroviárias 'desde' por cima dela nem "
               "multiplicamos passagens por atração do mesmo destino.")


def _draft_panel(comparison:dict)->None:
    with st.expander("Guardar ou recuperar um estudo",expanded=False):
        st.caption("Estudos locais ficam nesta sessão; para continuar em outro dispositivo, "
                   "use Meus estudos privados abaixo. O backup JSON continua disponível. "
                   "**Nada é publicado no GitHub.**")
        a,b=st.columns([2,1])
        name=a.text_input("Nome da alternativa",value="Comparar "+
                          ", ".join(_names()[c] for c in comparison["alternatives"]),
                          key="ux34_draft_name")
        notes=st.text_area("Anotações opcionais",max_chars=1000,
                           key="ux34_draft_notes")
        if b.button("Guardar na sessão",key="ux34_save_draft"):
            try:
                draft=make_city_draft(name,comparison,notes)
                st.session_state.setdefault("ux34_drafts",{})[draft["name"]]=draft
                st.success("Estudo guardado na sessão, sem alterar o roteiro oficial.")
            except (ValueError,TypeError) as exc:
                st.error(str(exc))
        drafts=st.session_state.get("ux34_drafts",{})
        if drafts:
            chosen=st.selectbox("Estudos nesta sessão",list(drafts),
                                key="ux34_saved_choice")
            l,r=st.columns(2)
            if l.button("Reabrir estudo",key="ux34_restore_draft"):
                _load_draft(drafts[chosen])
                st.rerun()
            r.download_button("Baixar JSON",export_city_draft(drafts[chosen]),
                              file_name="nossa-europa-estudo-cidades.json",
                              mime="application/json",key="ux34_export_json")
        from private_city_studies_ui import render_private_studies
        render_private_studies(comparison,_load_draft)
        file=st.file_uploader("Importar estudo JSON",type=["json"],
                              key="ux34_import_file")
        if file is not None and st.button("Validar e recuperar",
                                          key="ux34_import_draft"):
            try:
                draft=import_city_draft(file.getvalue())
                st.session_state.setdefault("ux34_drafts",{})[draft["name"]]=draft
                _load_draft(draft)
                st.rerun()
            except (ValueError,TypeError) as exc:
                st.error("Arquivo recusado: "+str(exc))


def _review_signature(comparison:dict,chosen:str)->tuple:
    """Bind consent to this plan revision, candidate and exact assumptions."""
    return (comparison["plan_id"],comparison["plan_revision"],
            comparison["official_base"],chosen,
            tuple(comparison["destinations"]),comparison["french_days"],
            comparison["eur_fx"],
            tuple(sorted(comparison["rents_eur_month"].items())))


def _discard_review():
    for key in ("ux34_review","ux34_review_candidate",
                "ux34_review_signature","ux34_apply_ack"):
        st.session_state.pop(key,None)


def _review_official_change(plan:dict,comparison:dict,
                            *,contextual_base:str|None=None)->None:
    if contextual_base is None:
        st.markdown("#### Meu plano continua protegido")
        st.caption("Inalterados: "+"; ".join(comparison["unmodified"])+".")
    else:
        st.markdown("#### Confirmar a troca")
        st.caption("Somente a cidade-base será alterada no plano da sessão. "
                   "Datas, passeios, orçamento e demais decisões permanecem.")
    eligible=[c for c in comparison["candidates"] if c["official_supported"]]
    if not eligible:
        st.warning("As cidades comparadas ainda não possuem integração completa "
                   "com o modelo oficial. Continue pesquisando; nenhuma mudança "
                   "pode ser aplicada agora.")
        return
    supported={c["id"]:c["name"] for c in eligible}
    if contextual_base is not None:
        if contextual_base not in supported or comparison["alternatives"]!=[contextual_base]:
            st.error("A candidata mudou. Retorne à comparação para escolher outra cidade.")
            return
        chosen=contextual_base
        st.caption("Candidata fixa: "+supported[chosen]+
                   ". Para escolher outra cidade, volte à comparação.")
    else:
        chosen=st.selectbox("Base apta para revisão oficial",list(supported),
                            key="ux34_apply_candidate",
                            format_func=lambda k:supported[k])
    action_label=("Revisar e confirmar "+supported[chosen]
                  if contextual_base is not None else "Revisar impacto antes de aplicar")
    if contextual_base is not None:
        keep,proceed=st.columns(2)
        if keep.button("Manter "+comparison["official_name"],
                       key="ux115_keep_base",use_container_width=True):
            from rec03a_suggestions_ui import close_base_review
            close_base_review()
            st.rerun()
        open_review=proceed.button(action_label,key="ux34_open_review",
                                   type="primary",use_container_width=True)
    else:
        open_review=st.button(action_label,key="ux34_open_review")
    if open_review:
        try:
            review=review_base_application(plan,comparison,chosen)
            _discard_review()
            st.session_state["ux34_review"]=review
            st.session_state["ux34_review_candidate"]=chosen
            st.session_state["ux34_review_signature"]=_review_signature(comparison,chosen)
        except (ValueError,KeyError) as exc:
            st.error(str(exc))
    pending=st.session_state.get("ux34_review")
    if pending is None:
        return
    if (pending["plan_id"]!=plan["plan_id"] or
        pending["original_revision"]!=plan["revision"] or
        st.session_state.get("ux34_review_candidate")!=chosen or
        st.session_state.get("ux34_review_signature")!=
            _review_signature(comparison,chosen)):
        st.warning("O plano, os destinos ou as premissas mudaram. Revise novamente.")
        _discard_review()
        return
    st.warning("Você vai trocar **somente a cidade-base oficial**: "+
               comparison["official_name"]+" → "+supported[chosen]+
               ". Dias, datas, passeios e decisões anteriores permanecem. "
               "Revise hospedagem, traslados e retornos antes de reservar.")
    confirmation=st.checkbox("Confirmo que desejo alterar minha cidade-base oficial",
                             key="ux34_apply_ack",value=False)
    left,right=st.columns(2)
    if left.button("Aplicar mudança ao meu plano",key="ux34_confirm_apply",
                   type="primary",disabled=not confirmation):
        try:
            fresh=active_plan()
            if (fresh["plan_id"]!=pending["plan_id"] or
                    fresh["revision"]!=pending["original_revision"]):
                raise ValueError("Plano desatualizado. Revise novamente.")
            if pending["changes"]["base_city"]["proposed"]!=chosen:
                raise ValueError("Cidade em revisão diferente da selecionada")
            if contextual_base is not None:
                from rec03a_suggestions_ui import validate_base_review
                ctx=validate_base_review(fresh)
                if ctx is None or ctx["base"]!=chosen:
                    raise ValueError("O contexto da escolha mudou. Revise novamente.")
            update_fields(base_city=chosen)
            _discard_review()
            st.session_state["ux34_notice"]=(
                "Cidade-base oficial atualizada apenas nesta sessão. "
                "Revise passeios e custos e salve explicitamente para persistir.")
            st.rerun()
        except (ValueError,KeyError) as exc:
            st.error(str(exc))
    if right.button("Cancelar revisão",key="ux34_cancel_review"):
        _discard_review()
        if contextual_base is not None:
            from rec03a_suggestions_ui import close_base_review
            close_base_review()
        st.rerun()


def contextual_impact_projection(comparison:dict)->dict:
    """Read-only view of the same UX34 model; never rank or infer viability."""
    if len(comparison["candidates"])!=1:
        raise ValueError("A revisão contextual requer uma candidata")
    entry=comparison["candidates"][0]
    groups={"Melhorou":[],"Piorou":[],"Semelhante":[],"Não pesquisado":[]}
    for row in entry["routes"]:
        groups[row["status"]].append({
            "name":row["destination"],"delta_minutes":row["delta_minutes"],
            "before":row["official_minutes"],"after":row["candidate_minutes"],
            "official_gap_reason":row.get("official_gap_reason"),
            "candidate_gap_reason":row.get("candidate_gap_reason"),
        })
    return {
        "candidate":entry["id"],"candidate_name":entry["name"],
        "official_name":comparison["official_name"],
        "groups":groups,"comparable":entry["paired_route_times"],
        "total":len(comparison["destinations"]),
        "housing_known":entry["housing_whatif"]["known"],
        "housing_delta_brl":entry["financial_delta_brl"],
        "changes_official_plan":False,
    }


def _render_contextual_review(plan:dict,comparison:dict)->None:
    """Decision first; retain all existing technical comparisons on demand."""
    view=contextual_impact_projection(comparison)
    groups=view["groups"]
    st.markdown("#### Impacto nos meus passeios")
    st.caption("Comparação de tempos ferroviários históricos de ida, "
               "somente quando ambas as cidades têm evidências. "
               "Cobertura de pesquisa não significa cidade melhor.")
    a,b,c=st.columns(3)
    a.metric("Idas menores",len(groups["Melhorou"]))
    b.metric("Idas maiores",len(groups["Piorou"]))
    c.metric("Sem comparação",len(groups["Não pesquisado"]))
    for title,status in (("Deslocamentos menores","Melhorou"),
                         ("Deslocamentos maiores","Piorou"),
                         ("Deslocamentos semelhantes","Semelhante")):
        if not groups[status]:
            continue
        st.markdown("**"+title+"**")
        for route in groups[status]:
            minutes=abs(route["delta_minutes"])
            st.write("• **"+route["name"]+"**: "+
                     str(route["before"])+" → "+str(route["after"])+
                     " min de ida ("+str(minutes)+" min "+
                     ("a menos" if status=="Melhorou" else
                      "a mais" if status=="Piorou" else "de diferença")+
                     ").")
    st.markdown("#### O que ainda preciso verificar?")
    if groups["Não pesquisado"]:
        for route in groups["Não pesquisado"]:
            base=view["official_name"]
            alt=view["candidate_name"]
            if route["before"] is None and route["after"] is None:
                reason="sem tempo ferroviário comparável nas duas cidades"
            elif route["before"] is None:
                reason=(base+" sem referência comparável; "+alt+" tem "+
                        str(route["after"])+" min de ida documentados")
            else:
                reason=(alt+" sem referência comparável; "+base+" tem "+
                        str(route["before"])+" min de ida documentados")
            st.caption("• "+route["name"]+": "+reason+".")
            if route.get("official_gap_reason"):
                st.caption("Pesquisa pendente da base atual: "+
                           route["official_gap_reason"])
            if route.get("candidate_gap_reason"):
                st.caption("Pesquisa pendente da alternativa: "+
                           route["candidate_gap_reason"])
    else:
        st.caption("Todos os destinos têm referências de ida nas duas cidades. "
                   "Ainda é preciso validar os horários e retornos reais.")
    st.caption("Retorno, última milha, conexões compatíveis, hospedagem e "
               "datas de 2027 não estão confirmados. "
               "Ausência de pesquisa não significa passeio impossível.")
    st.markdown("#### Impacto no orçamento")
    if view["housing_known"]:
        st.metric("Variação hipotética de moradia (R$)",
                  _currency(view["housing_delta_brl"]))
        st.caption("Somente aluguel inserido manualmente, para a mesma duração "
                   "e câmbio. Não é a diferença total da viagem.")
    else:
        st.info("Ainda não há dois valores de aluguel comparáveis. "
                "Você pode informar hipóteses em 'Premissas financeiras' acima; "
                "a ausência de dados não equivale a custo zero.")
    _review_official_change(active_plan(),comparison,
                            contextual_base=view["candidate"])
    if st.checkbox("Ver comparação detalhada, fontes e modalidades",
                   key="ux115_details_open"):
        st.markdown("#### Cobertura documental")
        cols=st.columns(2)
        for col,city in zip(cols,[comparison["official_base"],view["candidate"]]):
            profile=comparison["profiles"][city]
            with col:
                st.metric(
                    view["official_name"] if city==comparison["official_base"]
                    else view["candidate_name"],
                    str(profile["route_time_count"])+"/"+str(view["total"])+
                    " idas documentadas",
                )
        _render_coverage(comparison)
        _render_finance(comparison)
        st.caption(comparison["methodology"])
    st.caption("Nenhuma cidade vencedora foi escolhida automaticamente; "
               "seu planejamento oficial só muda após confirmação explícita.")


def render_city_decision(plan:dict,trip_data:dict,finance_live:bool,
                         french_days:int,*,contextual_base:str|None=None)->None:
    """Main task in Explorar → Comparar: 2–3 bases, equal assumptions."""
    names=_names()
    official=plan["base_city"]
    if contextual_base is not None and contextual_base in names:
        st.markdown("### Trocar "+names[official]+" por "+names[contextual_base]+"?")
        st.caption("Você escolheu uma candidata em Minha comparação. "
                   "Revise o que sabemos antes de alterar o plano da sessão.")
    else:
        st.markdown("### Comparar cidades-base e decidir com segurança")
        st.caption("**Meu plano:** "+names[official]+" · "+
                   str(plan["total_days"]-plan["italy_days"])+" dias na temporada europeia · "+
                   plan["budget_scenario"]+" · dois adultos.")
        st.caption("Cidades pesquisadas são alternativas, nunca reservas ou "
                   "alterações automáticas do planejamento.")
    if st.session_state.get("ux34_notice"):
        st.success(st.session_state.pop("ux34_notice"))
    defaults=[st.session_state.get("scenario_base_selected")]
    defaults=[x for x in defaults if x in names and x!=official]
    if not defaults:
        defaults=["strasbourg" if official!="strasbourg" else "mulhouse"]
    if contextual_base is not None:
        if contextual_base not in names or contextual_base==official:
            st.error("Candidata inválida para esta revisão.")
            return
        st.session_state["ux34_candidates"]=[contextual_base]
        candidate_ids=[contextual_base]
    else:
        if "ux34_candidates" not in st.session_state:
            st.session_state["ux34_candidates"]=defaults
        candidate_ids=st.multiselect(
            "Comparar meu plano com até duas alternativas",
            [key for key in names if key!=official],
            format_func=lambda key:names[key],
            max_selections=2,key="ux34_candidates")
    if not candidate_ids:
        st.info("Escolha ao menos uma cidade-base alternativa.")
        return
    places=destination_catalog()
    defaults=[k for k in shared_destinations(plan) if k in places]
    if contextual_base is None and "ux34_destinations" not in st.session_state:
        st.session_state["ux34_destinations"]=defaults[:8]
    if contextual_base is not None:
        from rec03a_suggestions_ui import validate_base_review
        ctx=validate_base_review(plan)
        if ctx is None or not ctx.get("approved_destinations"):
            st.error("Escopo da revisão inválido ou não confirmado.")
            return
        dest=list(ctx["approved_destinations"])
        st.session_state["ux34_destinations"]=list(dest)
        st.caption("Destinos desta revisão: "+
                   ", ".join(places.get(key,key) for key in dest)+".")
    else:
        dest=st.multiselect("Passeios que quero manter acessíveis (mesmos para todas)",
                            list(places),format_func=lambda k:places[k],
                            max_selections=8,key="ux34_destinations")
    if not dest:
        st.info("Escolha ao menos um destino para comparar.")
        return
    if contextual_base is not None:
        st.caption("Os destinos do escopo confirmado servem apenas como referência "
                   "para esta revisão; nenhum passeio é incluído, excluído ou "
                   "modificado no roteiro. Sem tempo não significa inviável.")
    else:
        st.caption("Se você já escolheu passeios no roteiro, eles são usados como "
                   "referência. Destinos sem trajeto pesquisado não são considerados perdidos.")
    with st.expander("Premissas financeiras opcionais · mesma duração e câmbio"):
        st.caption("Valores mensais são apenas suposições suas, sem anúncio "
                   "validado para 2027. Deixe €0 para indicar que não há cotação.")
        if "ux34_days" not in st.session_state:
            st.session_state["ux34_days"]=int(french_days)
        days=int(st.number_input("Dias na temporada europeia",min_value=40,
                                 max_value=80,step=1,key="ux34_days"))
        if "ux34_fx" not in st.session_state:
            st.session_state["ux34_fx"]=float(
                st.session_state.get("advisor_eurfx",6.3))
        fx=float(st.number_input("Câmbio hipotético (R$/€)",min_value=4.0,
                                 max_value=10.0,step=.05,key="ux34_fx"))
        rents={}
        for city in [official]+candidate_ids:
            key="ux34_rent_"+city
            if key not in st.session_state:st.session_state[key]=0.0
            amount=st.number_input("Provisão mensal para dois em "+names[city]+
                                   " (€ / mês)",min_value=0.0,max_value=20000.0,
                                   step=50.0,key=key)
            rents[city]=float(amount) if amount>0 else None
        st.caption("Demais parcelas do mesmo orçamento continuam constantes "
                   "para isolar a diferença hipotética do aluguel. "
                   "Não é uma cotação nem um total confirmado.")
    try:
        comparison=compare_city_decisions(plan,candidate_ids,dest,rents,
                     trip_data,finance_live,days,fx)
    except (ValueError,KeyError,TypeError) as exc:
        st.warning("Comparação indisponível com as premissas atuais: "+str(exc))
        return
    if contextual_base is not None:
        _render_contextual_review(plan,comparison)
        return
    st.markdown("#### Comparação em condições iguais")
    cols=st.columns(1+len(candidate_ids))
    for col,city in zip(cols,[official]+candidate_ids):
        evidence=comparison["profiles"][city]
        with col:
            with st.container(border=True):
                st.markdown("**"+names[city]+(" · Meu plano" if city==official
                                               else " · Alternativa")+"**")
                st.metric("Tempos pesquisados",
                          str(evidence["route_time_count"])+"/"+str(len(dest)))
                st.caption(str(evidence["fare_from_count"])+"/"+str(len(dest))+
                           " tarifas históricas de ida pesquisadas")
                st.caption("Países observados em rotas da seleção: "+
                           (", ".join(evidence["country_time_references"]) or
                            "Não pesquisado"))
    _render_coverage(comparison)
    _render_finance(comparison)
    if contextual_base is None:
        _draft_panel(comparison)
    else:
        st.caption("Estudos guardados e comparação avançada permanecem disponíveis "
                   "fora desta revisão contextual.")
    _review_official_change(active_plan(),comparison,
                            contextual_base=contextual_base)
    st.caption("**Conclusão responsável:** nenhum vencedor automático. "
               "Faltam retornos verificáveis, moradias equivalentes e custos "
               "completos para avaliar a economia real da mudança.")
