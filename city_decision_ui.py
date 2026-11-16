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


def _review_official_change(plan:dict,comparison:dict)->None:
    st.markdown("#### Meu plano continua protegido")
    st.caption("Inalterados: "+"; ".join(comparison["unmodified"])+".")
    eligible=[c for c in comparison["candidates"] if c["official_supported"]]
    if not eligible:
        st.warning("As cidades comparadas ainda não possuem integração completa "
                   "com o modelo oficial. Guarde o estudo e continue pesquisando; "
                   "nenhuma mudança pode ser aplicada agora.")
        return
    supported={c["id"]:c["name"] for c in eligible}
    chosen=st.selectbox("Base apta para revisão oficial",list(supported),
                        key="ux34_apply_candidate",
                        format_func=lambda k:supported[k])
    if st.button("Revisar impacto antes de aplicar",key="ux34_open_review"):
        try:
            review=review_base_application(plan,comparison,chosen)
            st.session_state["ux34_review"]=review
            st.session_state["ux34_review_candidate"]=chosen
        except (ValueError,KeyError) as exc:
            st.error(str(exc))
    pending=st.session_state.get("ux34_review")
    if pending is not None:
        if (pending["plan_id"]!=plan["plan_id"] or
            pending["original_revision"]!=plan["revision"] or
            st.session_state.get("ux34_review_candidate")!=chosen):
            st.warning("O plano ou a seleção mudou. Revise novamente.")
            st.session_state.pop("ux34_review",None)
            return
        st.warning("Você vai trocar **somente a cidade-base oficial**: "+
                   comparison["official_name"]+" → "+supported[chosen]+
                   ". Dias, datas, passeios e decisões anteriores permanecem. "
                   "Ainda será preciso revisar hospedagem, traslados e retornos.")
        confirmation=st.checkbox(
            "Confirmo que desejo alterar minha cidade-base oficial",
            key="ux34_apply_ack",value=False)
        a,b=st.columns(2)
        if a.button("Aplicar mudança ao meu plano",key="ux34_confirm_apply",
                    type="primary",disabled=not confirmation):
            try:
                if active_plan()["revision"]!=pending["original_revision"]:
                    raise ValueError("Plano desatualizado. Revise novamente.")
                if pending["changes"]["base_city"]["proposed"]!=chosen:
                    raise ValueError("Cidade em revisão diferente da selecionada")
                update_fields(base_city=chosen)
                st.session_state.pop("ux34_review",None)
                st.session_state["ux34_notice"]=(
                    "Cidade-base oficial atualizada nesta sessão. "
                    "Revise os passeios e salve explicitamente para manter.")
                st.rerun()
            except (ValueError,KeyError) as exc:
                st.error(str(exc))
        if b.button("Cancelar revisão",key="ux34_cancel_review"):
            st.session_state.pop("ux34_review",None)
            st.rerun()


def render_city_decision(plan:dict,trip_data:dict,finance_live:bool,
                         french_days:int)->None:
    """Main task in Explorar → Comparar: 2–3 bases, equal assumptions."""
    names=_names()
    official=plan["base_city"]
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
    if "ux34_candidates" not in st.session_state:
        st.session_state["ux34_candidates"]=defaults
    candidate_ids=st.multiselect("Comparar meu plano com até duas alternativas",
                                 [key for key in names if key!=official],
                                 format_func=lambda key:names[key],
                                 max_selections=2,key="ux34_candidates")
    if not candidate_ids:
        st.info("Escolha ao menos uma cidade-base alternativa.")
        return
    places=destination_catalog()
    defaults=[k for k in shared_destinations(plan) if k in places]
    if "ux34_destinations" not in st.session_state:
        st.session_state["ux34_destinations"]=defaults[:8]
    dest=st.multiselect("Passeios que quero manter acessíveis (mesmos para todas)",
                        list(places),format_func=lambda k:places[k],
                        max_selections=8,key="ux34_destinations")
    if not dest:
        st.info("Escolha ao menos um destino para comparar.")
        return
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
    _draft_panel(comparison)
    _review_official_change(active_plan(),comparison)
    st.caption("**Conclusão responsável:** nenhum vencedor automático. "
               "Faltam retornos verificáveis, moradias equivalentes e custos "
               "completos para avaliar a economia real da mudança.")
